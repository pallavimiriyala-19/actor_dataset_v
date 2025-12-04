"""
Actor verification using face embeddings and duplicate detection.
"""

import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from config.settings import (
    FACE_SIMILARITY_THRESHOLD,
    DUPLICATE_THRESHOLD,
    HASH_ALGORITHM,
    HASH_SIZE,
)
from src.modules.face_detector import FaceDetector
from src.utils.helpers import cosine_similarity


logger = logging.getLogger(__name__)


class ActorVerifier:
    """
    Verifies if faces in images match the target actor using embedding similarity.
    """

    def __init__(self, face_detector: FaceDetector):
        """
        Initialize verifier.

        Args:
            face_detector: FaceDetector instance
        """
        self.face_detector = face_detector
        self.reference_embedding = None
        self.actor_name = None

    def set_reference_actor(
        self,
        actor_name: str,
        reference_embedding: Optional[np.ndarray] = None,
        tmdb_profile_url: str = None
    ) -> bool:
        """
        Set reference actor for verification.

        Args:
            actor_name: Actor name
            reference_embedding: Pre-computed reference embedding
            tmdb_profile_url: TMDb profile image URL to extract reference

        Returns:
            True if reference was set successfully
        """
        logger.info(f"Setting reference actor: {actor_name}")
        
        self.actor_name = actor_name
        
        # Use provided embedding
        if reference_embedding is not None:
            self.reference_embedding = reference_embedding
            logger.info("Using provided reference embedding")
            return True
        
        # Try to get embedding from TMDb profile
        if tmdb_profile_url:
            embedding = self.face_detector.get_reference_embedding(actor_name, tmdb_profile_url)
            if embedding is not None:
                self.reference_embedding = embedding
                logger.info("Extracted reference embedding from TMDb profile")
                return True
        
        logger.warning(f"Could not set reference embedding for {actor_name}")
        return False

    def verify_image(self, image_path: Path, threshold: float = None) -> Tuple[bool, float]:
        """
        Verify if image contains the target actor.

        Args:
            image_path: Path to image file
            threshold: Similarity threshold (uses config if not provided)

        Returns:
            Tuple of (is_actor, similarity_score)
        """
        if self.reference_embedding is None:
            logger.warning("No reference embedding set for verification")
            return False, 0.0
        
        if threshold is None:
            threshold = FACE_SIMILARITY_THRESHOLD
        
        try:
            # Get embedding from image
            embedding = self.face_detector.get_embedding_from_file(image_path)
            
            if embedding is None:
                logger.debug(f"Could not extract embedding from {image_path.name}")
                return False, 0.0
            
            # Calculate similarity
            similarity = cosine_similarity(self.reference_embedding, embedding)
            
            logger.debug(f"Image {image_path.name}: similarity={similarity:.4f}, threshold={threshold}")
            
            is_actor = similarity >= threshold
            
            return is_actor, similarity
        except Exception as e:
            logger.error(f"Error verifying image {image_path}: {str(e)}")
            return False, 0.0

    def verify_batch(
        self,
        image_paths: List[Path],
        threshold: float = None,
        return_scores: bool = False
    ) -> Tuple[List[Path], Dict]:
        """
        Verify multiple images in batch.

        Args:
            image_paths: List of image paths
            threshold: Similarity threshold
            return_scores: If True, return similarity scores

        Returns:
            Tuple of (valid_images, scores_dict)
        """
        if self.reference_embedding is None:
            logger.warning("No reference embedding set for verification")
            return [], {}
        
        logger.info(f"Verifying {len(image_paths)} images against {self.actor_name}")
        
        valid_images = []
        scores = {}
        
        for image_path in image_paths:
            is_actor, similarity = self.verify_image(image_path, threshold)
            
            if is_actor:
                valid_images.append(image_path)
                logger.debug(f"✓ Verified: {image_path.name} (similarity: {similarity:.4f})")
            else:
                logger.debug(f"✗ Rejected: {image_path.name} (similarity: {similarity:.4f})")
            
            if return_scores:
                scores[str(image_path)] = similarity
        
        logger.info(f"Verified {len(valid_images)}/{len(image_paths)} images")
        
        return valid_images, scores


class DuplicateDetector:
    """
    Detects and removes duplicate images using perceptual hashing.
    """

    def __init__(self, algorithm: str = None, hash_size: int = None, threshold: float = None):
        """
        Initialize duplicate detector.

        Args:
            algorithm: Hash algorithm (phash, dhash, ahash, whash)
            hash_size: Hash size
            threshold: Similarity threshold (0-1)
        """
        self.algorithm = algorithm or HASH_ALGORITHM
        self.hash_size = hash_size or HASH_SIZE
        self.threshold = threshold or DUPLICATE_THRESHOLD
        
        logger.info(f"Initializing duplicate detector: {self.algorithm}, size={self.hash_size}, threshold={self.threshold}")

    def _get_hash_function(self):
        """Get hash function from imagehash."""
        try:
            import imagehash
            
            hash_methods = {
                "phash": imagehash.phash,
                "dhash": imagehash.dhash,
                "ahash": imagehash.average_hash,
                "whash": imagehash.whash,
            }
            
            return hash_methods.get(self.algorithm, imagehash.phash)
        except ImportError:
            logger.error("imagehash library not installed")
            return None

    def compute_hash(self, image_path: Path) -> Optional[str]:
        """
        Compute perceptual hash for image.

        Args:
            image_path: Path to image file

        Returns:
            Hash string or None if error
        """
        try:
            from PIL import Image
            
            hash_func = self._get_hash_function()
            if hash_func is None:
                return None
            
            img = Image.open(image_path)
            img_hash = hash_func(img, hash_size=self.hash_size)
            
            return str(img_hash)
        except Exception as e:
            logger.warning(f"Error computing hash for {image_path}: {str(e)}")
            return None

    def compute_hashes(self, image_paths: List[Path]) -> Dict[Path, str]:
        """
        Compute hashes for multiple images.

        Args:
            image_paths: List of image paths

        Returns:
            Dictionary mapping image paths to hashes
        """
        logger.info(f"Computing hashes for {len(image_paths)} images")
        
        hashes = {}
        for image_path in image_paths:
            img_hash = self.compute_hash(image_path)
            if img_hash:
                hashes[image_path] = img_hash
        
        logger.info(f"Successfully computed hashes for {len(hashes)} images")
        return hashes

    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two hashes.

        Args:
            hash1: First hash string
            hash2: Second hash string

        Returns:
            Hamming distance
        """
        try:
            # Remove imagehash prefix if present
            hash1 = str(hash1).split(':')[-1]
            hash2 = str(hash2).split(':')[-1]
            
            return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        except Exception:
            return float('inf')

    def hash_similarity(self, hash1: str, hash2: str) -> float:
        """
        Calculate similarity between two hashes (0-1).

        Args:
            hash1: First hash string
            hash2: Second hash string

        Returns:
            Similarity score (1.0 = identical, 0.0 = completely different)
        """
        distance = self.hamming_distance(hash1, hash2)
        max_distance = len(str(hash1).split(':')[-1])
        
        if max_distance == 0:
            return 0.0
        
        similarity = 1.0 - (distance / max_distance)
        return max(0.0, min(1.0, similarity))

    def find_duplicates(self, image_paths: List[Path]) -> List[List[Path]]:
        """
        Find groups of duplicate images.

        Args:
            image_paths: List of image paths

        Returns:
            List of duplicate groups (each group is a list of similar images)
        """
        logger.info(f"Finding duplicates among {len(image_paths)} images")
        
        # Compute hashes
        hashes = self.compute_hashes(image_paths)
        
        if not hashes:
            logger.warning("No valid hashes computed")
            return []
        
        # Find duplicates
        duplicate_groups = []
        processed = set()
        
        image_list = list(hashes.keys())
        
        for i, img1 in enumerate(image_list):
            if img1 in processed:
                continue
            
            group = [img1]
            
            for img2 in image_list[i+1:]:
                if img2 in processed:
                    continue
                
                similarity = self.hash_similarity(hashes[img1], hashes[img2])
                
                if similarity >= self.threshold:
                    group.append(img2)
                    processed.add(img2)
            
            if len(group) > 1:
                duplicate_groups.append(group)
                logger.debug(f"Found duplicate group: {[p.name for p in group]}")
            
            processed.add(img1)
        
        logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups

    def remove_duplicates(self, image_paths: List[Path], keep_largest: bool = True) -> Tuple[List[Path], List[Path]]:
        """
        Remove duplicate images, keeping best quality version.

        Args:
            image_paths: List of image paths
            keep_largest: If True, keep largest file; else keep first

        Returns:
            Tuple of (unique_images, removed_images)
        """
        logger.info(f"Removing duplicates from {len(image_paths)} images")
        
        duplicate_groups = self.find_duplicates(image_paths)
        
        unique_images = set(image_paths)
        removed_images = []
        
        for group in duplicate_groups:
            # Sort by file size if keeping largest
            if keep_largest:
                group = sorted(group, key=lambda p: p.stat().st_size, reverse=True)
            
            # Keep first (best), remove rest
            keep = group[0]
            remove = group[1:]
            
            for img in remove:
                unique_images.discard(img)
                removed_images.append(img)
            
            logger.debug(f"Keeping {keep.name}, removing {len(remove)} duplicates")
        
        result = sorted(list(unique_images))
        
        logger.info(f"Removed {len(removed_images)} duplicate images. Remaining: {len(result)}")
        
        return result, removed_images
