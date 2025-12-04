"""
Main orchestration pipeline for actor face dataset collection.
Coordinates all components: actor identification, image download, face detection,
verification, and duplicate removal.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config.settings import (
    MIN_RAW_IMAGES,
    TARGET_IMAGES,
    CHECKPOINT_INTERVAL,
    SAVE_METADATA,
    SAVE_EMBEDDINGS,
    FACE_SIMILARITY_THRESHOLD,
)
from src.modules.tmdb_identifier import TMDbActorIdentifier
from src.modules.image_downloader import ImageDownloader
from src.modules.face_detector import FaceDetector
from src.modules.actor_verifier import ActorVerifier, DuplicateDetector
from src.utils.helpers import (
    normalize_actor_name,
    get_actor_dir,
    get_raw_images_dir,
    get_final_images_dir,
    get_metadata_file,
    get_checkpoint_file,
    get_embeddings_file,
    save_metadata,
    load_metadata,
    save_checkpoint,
    load_checkpoint,
    is_valid_image_format,
    get_timestamp,
)
from src.utils.logger import logger, download_logger, face_detection_logger, validation_logger


class ActorDatasetBuilder:
    """
    Main class for building actor face datasets.
    """

    def __init__(self, tmdb_api_key: str = None):
        """
        Initialize dataset builder.

        Args:
            tmdb_api_key: TMDb API key
        """
        logger.info("Initializing ActorDatasetBuilder")
        
        self.tmdb_identifier = TMDbActorIdentifier(tmdb_api_key)
        self.image_downloader = ImageDownloader()
        
        try:
            self.face_detector = FaceDetector()
        except Exception as e:
            logger.error(f"Failed to initialize face detector: {str(e)}")
            raise
        
        self.actor_verifier = None
        self.duplicate_detector = DuplicateDetector()
        
        self.current_actor = None
        self.current_actor_tmdb_id = None
        self.checkpoint = {}

    def _log_progress(self, stage: str, message: str) -> None:
        """Log progress with stage prefix."""
        logger.info(f"[{stage}] {message}")

    def _get_raw_images(self, actor_name: str) -> List[Path]:
        """Get all raw images for an actor."""
        raw_dir = get_raw_images_dir(actor_name)
        if not raw_dir.exists():
            return []
        
        images = [f for f in raw_dir.iterdir() if is_valid_image_format(f)]
        return sorted(images)

    def identify_actor(self, actor_name: str) -> Optional[Dict]:
        """
        Identify actor using TMDb API.

        Args:
            actor_name: Actor name to identify

        Returns:
            Actor profile dictionary or None
        """
        self._log_progress("IDENTIFICATION", f"Identifying actor: {actor_name}")
        
        try:
            profile = self.tmdb_identifier.get_complete_actor_profile(actor_name)
            
            if not profile:
                self._log_progress("IDENTIFICATION", f"✗ Could not identify actor: {actor_name}")
                return None
            
            # Verify it's a Telugu actor
            if not profile.get("is_telugu_actor"):
                self._log_progress("IDENTIFICATION", f"⚠ Warning: {actor_name} may not be primarily Telugu actor")
                self._log_progress("IDENTIFICATION", f"  Verification: {profile.get('telugu_verification')}")
            else:
                self._log_progress("IDENTIFICATION", f"✓ Verified Telugu actor: {profile.get('name')}")
            
            self.current_actor = actor_name
            self.current_actor_tmdb_id = profile["tmdb_id"]
            
            # Save actor profile
            save_metadata(actor_name, profile)
            
            return profile
        except Exception as e:
            logger.error(f"Error identifying actor: {str(e)}")
            return None

    def download_images(self, actor_name: str, actor_profile: Dict, target_count: int = None) -> int:
        """
        Download images from multiple sources.

        Args:
            actor_name: Actor name
            actor_profile: Actor profile from TMDb
            target_count: Target number of images to download

        Returns:
            Number of images downloaded
        """
        if target_count is None:
            target_count = MIN_RAW_IMAGES
        
        self._log_progress("DOWNLOAD", f"Starting image download for {actor_name}")
        self._log_progress("DOWNLOAD", f"Target: {target_count} raw images")
        
        try:
            raw_dir = get_raw_images_dir(actor_name)
            downloaded_count = 0
            
            # 1. Download from TMDb profile + gallery
            self._log_progress("DOWNLOAD", "Downloading from TMDb...")
            tmdb_images = actor_profile.get("images", [])
            
            if tmdb_images:
                count = self.image_downloader.download_from_tmdb(
                    actor_name,
                    tmdb_images,
                    raw_dir,
                    limit=min(40, target_count // 3)
                )
                downloaded_count += count
            
            # 2. Download from DuckDuckGo
            if downloaded_count < target_count:
                self._log_progress("DOWNLOAD", "Downloading from DuckDuckGo...")
                
                search_query = self.image_downloader.build_search_query(
                    f"{actor_profile.get('name')} actor"
                )
                
                try:
                    count = self.image_downloader.download_from_duckduckgo(
                        search_query,
                        raw_dir,
                        limit=target_count - downloaded_count
                    )
                    downloaded_count += count
                except Exception as e:
                    logger.warning(f"DuckDuckGo download failed: {str(e)}")
            
            self._log_progress("DOWNLOAD", f"✓ Downloaded {downloaded_count} images")
            
            # Save checkpoint
            self.checkpoint["download"] = {
                "actor": actor_name,
                "downloaded_images": downloaded_count,
                "timestamp": get_timestamp(),
            }
            save_checkpoint(actor_name, self.checkpoint)
            
            return downloaded_count
        except Exception as e:
            logger.error(f"Error downloading images: {str(e)}")
            return 0

    def detect_and_validate_faces(self, actor_name: str, use_checkpoint: bool = True) -> List[Path]:
        """
        Detect faces in raw images and validate quality.

        Args:
            actor_name: Actor name
            use_checkpoint: Resume from checkpoint if available

        Returns:
            List of valid face images
        """
        self._log_progress("FACE_DETECTION", f"Starting face detection for {actor_name}")
        
        try:
            raw_dir = get_raw_images_dir(actor_name)
            face_dir = raw_dir / "faces"
            face_dir.mkdir(exist_ok=True)
            
            raw_images = self._get_raw_images(actor_name)
            
            if not raw_images:
                self._log_progress("FACE_DETECTION", f"✗ No raw images found for {actor_name}")
                return []
            
            self._log_progress("FACE_DETECTION", f"Processing {len(raw_images)} raw images")
            
            valid_faces = []
            processed_count = 0
            skipped_count = 0
            
            for idx, image_path in enumerate(raw_images, 1):
                try:
                    cropped_images, face_data, is_valid = self.face_detector.validate_and_crop_faces(
                        image_path,
                        output_dir=face_dir
                    )
                    
                    if is_valid and cropped_images:
                        # Save cropped face
                        for face_img in cropped_images:
                            face_file = face_dir / f"face_{len(valid_faces):05d}.jpg"
                            if self.face_detector.save_face_image(face_img, face_file):
                                valid_faces.append(face_file)
                        processed_count += 1
                    else:
                        skipped_count += 1
                    
                    # Progress logging
                    if idx % 10 == 0:
                        self._log_progress("FACE_DETECTION", f"Processed {idx}/{len(raw_images)} images...")
                    
                    # Checkpoint every N images
                    if idx % CHECKPOINT_INTERVAL == 0:
                        self.checkpoint["face_detection"] = {
                            "actor": actor_name,
                            "processed": processed_count,
                            "valid_faces": len(valid_faces),
                            "timestamp": get_timestamp(),
                        }
                        save_checkpoint(actor_name, self.checkpoint)
                
                except Exception as e:
                    face_detection_logger.warning(f"Error processing {image_path.name}: {str(e)}")
                    skipped_count += 1
                    continue
            
            self._log_progress(
                "FACE_DETECTION",
                f"✓ Detected {len(valid_faces)} valid faces from {processed_count} images ({skipped_count} skipped)"
            )
            
            return valid_faces
        except Exception as e:
            logger.error(f"Error in face detection: {str(e)}")
            return []

    def verify_actor_faces(
        self,
        actor_name: str,
        actor_profile: Dict,
        face_images: List[Path]
    ) -> Tuple[List[Path], Dict]:
        """
        Verify that detected faces match the target actor.

        Args:
            actor_name: Actor name
            actor_profile: Actor profile from TMDb
            face_images: List of face image paths

        Returns:
            Tuple of (verified_images, similarity_scores)
        """
        self._log_progress("VERIFICATION", f"Starting actor verification for {actor_name}")
        
        try:
            if not face_images:
                self._log_progress("VERIFICATION", f"✗ No faces to verify")
                return [], {}
            
            # Initialize verifier
            self.actor_verifier = ActorVerifier(self.face_detector)
            
            # Get reference embedding from TMDb profile
            tmdb_profile_url = None
            if actor_profile.get("profile_image"):
                tmdb_profile_url = self.face_detector.detector.get_image_url(
                    actor_profile["profile_image"]
                ) if hasattr(self.face_detector.detector, 'get_image_url') else None
            
            # Set reference actor
            if not self.actor_verifier.set_reference_actor(actor_name, tmdb_profile_url=tmdb_profile_url):
                self._log_progress("VERIFICATION", f"⚠ Warning: Could not extract reference embedding")
            
            # Verify faces
            self._log_progress("VERIFICATION", f"Verifying {len(face_images)} faces...")
            
            verified_images, similarity_scores = self.actor_verifier.verify_batch(
                face_images,
                return_scores=True
            )
            
            # Statistics
            if similarity_scores:
                import numpy as np
                scores_list = list(similarity_scores.values())
                avg_score = np.mean(scores_list)
                min_score = np.min(scores_list)
                max_score = np.max(scores_list)
                
                self._log_progress(
                    "VERIFICATION",
                    f"Similarity scores - Min: {min_score:.4f}, Max: {max_score:.4f}, Avg: {avg_score:.4f}"
                )
            
            self._log_progress(
                "VERIFICATION",
                f"✓ Verified {len(verified_images)}/{len(face_images)} faces as target actor"
            )
            
            return verified_images, similarity_scores
        except Exception as e:
            logger.error(f"Error in actor verification: {str(e)}")
            return [], {}

    def remove_duplicates(self, actor_name: str, image_paths: List[Path]) -> Tuple[List[Path], List[Path]]:
        """
        Remove duplicate images from dataset.

        Args:
            actor_name: Actor name
            image_paths: List of image paths

        Returns:
            Tuple of (unique_images, removed_images)
        """
        self._log_progress("DEDUPLICATION", f"Starting duplicate detection for {actor_name}")
        
        try:
            if not image_paths:
                return [], []
            
            self._log_progress("DEDUPLICATION", f"Analyzing {len(image_paths)} images for duplicates...")
            
            unique_images, removed_images = self.duplicate_detector.remove_duplicates(image_paths)
            
            self._log_progress(
                "DEDUPLICATION",
                f"✓ Removed {len(removed_images)} duplicates. Remaining: {len(unique_images)}"
            )
            
            return unique_images, removed_images
        except Exception as e:
            logger.error(f"Error removing duplicates: {str(e)}")
            return image_paths, []

    def save_final_dataset(
        self,
        actor_name: str,
        image_paths: List[Path],
        similarity_scores: Dict = None
    ) -> int:
        """
        Save final verified images to dataset directory.

        Args:
            actor_name: Actor name
            image_paths: List of verified image paths
            similarity_scores: Optional similarity scores dictionary

        Returns:
            Number of images saved
        """
        self._log_progress("SAVE", f"Saving final dataset for {actor_name}")
        
        try:
            final_dir = get_final_images_dir(actor_name)
            final_dir.mkdir(parents=True, exist_ok=True)
            
            saved_count = 0
            
            for idx, image_path in enumerate(image_paths, 1):
                try:
                    # Copy/link final image
                    final_path = final_dir / f"{idx:05d}.jpg"
                    
                    import shutil
                    shutil.copy2(image_path, final_path)
                    
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"Error saving {image_path.name}: {str(e)}")
            
            # Save metadata
            if SAVE_METADATA:
                metadata = {
                    "actor": actor_name,
                    "total_images": saved_count,
                    "timestamp": get_timestamp(),
                }
                
                if similarity_scores:
                    scores_list = list(similarity_scores.values())
                    import numpy as np
                    metadata["similarity_stats"] = {
                        "min": float(np.min(scores_list)),
                        "max": float(np.max(scores_list)),
                        "mean": float(np.mean(scores_list)),
                        "std": float(np.std(scores_list)),
                    }
                
                save_metadata(actor_name, metadata, raw=False)
            
            # Save embeddings if needed
            if SAVE_EMBEDDINGS and self.actor_verifier and self.actor_verifier.reference_embedding is not None:
                try:
                    import numpy as np
                    embeddings_file = get_embeddings_file(actor_name)
                    np.save(embeddings_file, self.actor_verifier.reference_embedding)
                    logger.info(f"Saved reference embedding to {embeddings_file}")
                except Exception as e:
                    logger.warning(f"Could not save embeddings: {str(e)}")
            
            self._log_progress("SAVE", f"✓ Saved {saved_count} images to {final_dir}")
            
            return saved_count
        except Exception as e:
            logger.error(f"Error saving final dataset: {str(e)}")
            return 0

    def build_dataset(
        self,
        actor_name: str,
        resume: bool = True,
        verify_actor: bool = True,
        target_images: int = None
    ) -> Dict:
        """
        Build complete dataset for an actor.

        Args:
            actor_name: Actor name
            resume: Resume from checkpoint if available
            verify_actor: Verify actor identity before downloading
            target_images: Target number of final images (default: TARGET_IMAGES)

        Returns:
            Dataset building report
        """
        if target_images is None:
            target_images = TARGET_IMAGES
        
        logger.info("="*80)
        self._log_progress("MAIN", f"Building dataset for actor: {actor_name}")
        logger.info("="*80)
        
        report = {
            "actor": actor_name,
            "status": "failed",
            "start_time": datetime.now().isoformat(),
            "stages": {},
        }
        
        try:
            # Load checkpoint if resuming
            if resume:
                self.checkpoint = load_checkpoint(actor_name)
                if self.checkpoint:
                    self._log_progress("MAIN", f"Resuming from checkpoint...")
            
            # Stage 1: Identify Actor
            self._log_progress("MAIN", "=" * 60)
            actor_profile = self.identify_actor(actor_name)
            
            if not actor_profile:
                report["status"] = "failed"
                report["error"] = "Could not identify actor"
                return report
            
            report["stages"]["identification"] = {
                "status": "success",
                "tmdb_id": actor_profile.get("tmdb_id"),
                "name": actor_profile.get("name"),
                "is_telugu_actor": actor_profile.get("is_telugu_actor"),
            }
            
            # Stage 2: Download Images
            self._log_progress("MAIN", "=" * 60)
            downloaded = self.download_images(actor_name, actor_profile, MIN_RAW_IMAGES)
            
            if downloaded == 0:
                report["status"] = "failed"
                report["error"] = "Could not download any images"
                return report
            
            report["stages"]["download"] = {
                "status": "success",
                "images_downloaded": downloaded,
            }
            
            # Stage 3: Detect Faces
            self._log_progress("MAIN", "=" * 60)
            detected_faces = self.detect_and_validate_faces(actor_name)
            
            if not detected_faces:
                report["status"] = "failed"
                report["error"] = "Could not detect any valid faces"
                return report
            
            report["stages"]["face_detection"] = {
                "status": "success",
                "faces_detected": len(detected_faces),
            }
            
            # Stage 4: Verify Actor
            self._log_progress("MAIN", "=" * 60)
            if verify_actor:
                verified_faces, similarity_scores = self.verify_actor_faces(
                    actor_name,
                    actor_profile,
                    detected_faces
                )
                
                report["stages"]["verification"] = {
                    "status": "success",
                    "faces_verified": len(verified_faces),
                    "similarity_threshold": FACE_SIMILARITY_THRESHOLD,
                }
            else:
                verified_faces = detected_faces
                similarity_scores = {}
                report["stages"]["verification"] = {
                    "status": "skipped",
                    "reason": "verify_actor=False",
                }
            
            if not verified_faces:
                report["status"] = "partial"
                report["error"] = "No faces passed verification"
                return report
            
            # Stage 5: Remove Duplicates
            self._log_progress("MAIN", "=" * 60)
            unique_faces, removed_dupes = self.remove_duplicates(actor_name, verified_faces)
            
            report["stages"]["deduplication"] = {
                "status": "success",
                "duplicates_removed": len(removed_dupes),
                "unique_faces": len(unique_faces),
            }
            
            # Stage 6: Save Final Dataset
            self._log_progress("MAIN", "=" * 60)
            saved_count = self.save_final_dataset(actor_name, unique_faces, similarity_scores)
            
            report["stages"]["save"] = {
                "status": "success",
                "images_saved": saved_count,
            }
            
            # Final summary
            self._log_progress("MAIN", "=" * 60)
            
            if saved_count >= target_images:
                report["status"] = "success"
                self._log_progress("MAIN", f"✓ Dataset complete! {saved_count}/{target_images} images")
            elif saved_count > 0:
                report["status"] = "partial"
                self._log_progress(
                    "MAIN",
                    f"⚠ Partial dataset: {saved_count}/{target_images} images"
                )
            else:
                report["status"] = "failed"
                self._log_progress("MAIN", f"✗ Dataset creation failed")
            
            logger.info("="*80)
            
        except Exception as e:
            logger.error(f"Fatal error building dataset: {str(e)}")
            report["status"] = "error"
            report["error"] = str(e)
        
        report["end_time"] = datetime.now().isoformat()
        return report
