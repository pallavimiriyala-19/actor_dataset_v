"""
Face detection, validation, and cropping using InsightFace.
"""

import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from PIL import Image
import cv2

from config.settings import (
    INSIGHTFACE_MODEL,
    FACE_DETECTION_THRESHOLD,
    MIN_FACE_SIZE,
    MAX_FACES_PER_IMAGE,
    MIN_FACE_QUALITY_SCORE,
    EMBEDDING_MODEL,
    OUTPUT_IMAGE_SIZE,
    USE_GPU,
)


logger = logging.getLogger(__name__)


class FaceDetector:
    """
    Detects, validates, and crops faces using InsightFace.
    """

    def __init__(self):
        """Initialize face detector with InsightFace model."""
        try:
            import insightface
            
            logger.info(f"Loading InsightFace model: {INSIGHTFACE_MODEL}")
            
            # Load detection model
            self.detector = insightface.app.FaceAnalysis(
                name=INSIGHTFACE_MODEL,
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider'] if USE_GPU else ['CPUExecutionProvider']
            )
            self.detector.prepare(ctx_id=0 if USE_GPU else -1, det_size=(640, 640))
            
            logger.info("Face detector initialized successfully")
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize face detector: {str(e)}")
            self.initialized = False
            self.detector = None
            raise

    def detect_faces(self, image_path: Path) -> List[Dict]:
        """
        Detect faces in an image.

        Args:
            image_path: Path to image file

        Returns:
            List of face dictionaries with detection info
        """
        if not self.initialized or self.detector is None:
            logger.error("Detector not initialized")
            return []
        
        try:
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning(f"Could not read image: {image_path}")
                return []
            
            # Detect faces
            faces = self.detector.get(img)
            
            logger.debug(f"Detected {len(faces)} faces in {image_path.name}")
            
            # Process each face
            results = []
            for idx, face in enumerate(faces):
                face_data = self._extract_face_data(img, face, idx)
                if face_data:
                    results.append(face_data)
            
            return results
        except Exception as e:
            logger.error(f"Error detecting faces in {image_path}: {str(e)}")
            return []

    def _extract_face_data(self, image: np.ndarray, face, face_idx: int) -> Optional[Dict]:
        """
        Extract useful data from detected face.

        Args:
            image: Original image array
            face: InsightFace face object
            face_idx: Face index in image

        Returns:
            Dictionary with face data or None if invalid
        """
        try:
            # Get bounding box
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            
            # Validate face size
            width = x2 - x1
            height = y2 - y1
            
            if width < MIN_FACE_SIZE or height < MIN_FACE_SIZE:
                logger.debug(f"Face too small: {width}x{height} (min: {MIN_FACE_SIZE})")
                return None
            
            # Get landmarks if available
            landmarks = face.landmark_2d if hasattr(face, 'landmark_2d') else None
            
            # Get quality score (confidence)
            confidence = float(face.det_score) if hasattr(face, 'det_score') else 0.5
            
            if confidence < FACE_DETECTION_THRESHOLD:
                logger.debug(f"Face confidence too low: {confidence} (min: {FACE_DETECTION_THRESHOLD})")
                return None
            
            return {
                "index": face_idx,
                "bbox": bbox,
                "width": width,
                "height": height,
                "confidence": confidence,
                "landmarks": landmarks,
                "face_object": face,
            }
        except Exception as e:
            logger.debug(f"Error extracting face data: {str(e)}")
            return None

    def validate_and_crop_faces(
        self,
        image_path: Path,
        output_dir: Path = None
    ) -> Tuple[List[np.ndarray], List[Dict], bool]:
        """
        Validate and crop faces from image.

        Args:
            image_path: Path to input image
            output_dir: Optional directory to save cropped faces

        Returns:
            Tuple of (cropped_images, face_data_list, is_valid)
            is_valid = True if image has exactly 1 dominant face (or <=MAX_FACES)
        """
        logger.debug(f"Processing image: {image_path.name}")
        
        try:
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning(f"Could not read image: {image_path}")
                return [], [], False
            
            # Detect faces
            faces = self.detect_faces(image_path)
            
            # Validate face count
            if len(faces) == 0:
                logger.debug(f"No faces detected in {image_path.name}")
                return [], [], False
            
            if len(faces) > MAX_FACES_PER_IMAGE:
                logger.debug(f"Too many faces ({len(faces)}) in {image_path.name}")
                return [], [], False
            
            # Crop faces (prefer largest/most confident face)
            faces = sorted(faces, key=lambda x: x["confidence"], reverse=True)
            
            cropped_images = []
            valid_faces = []
            
            for face_data in faces:
                cropped = self._crop_face(img, face_data)
                if cropped is not None:
                    cropped_images.append(cropped)
                    valid_faces.append(face_data)
                    
                    # Save if output directory specified
                    if output_dir:
                        try:
                            save_path = output_dir / f"{image_path.stem}_face_{face_data['index']}.jpg"
                            cv2.imwrite(str(save_path), cropped)
                        except Exception as e:
                            logger.warning(f"Could not save cropped face: {str(e)}")
            
            is_valid = len(cropped_images) > 0
            
            logger.debug(f"Successfully processed {len(cropped_images)} faces from {image_path.name}")
            
            return cropped_images, valid_faces, is_valid
        except Exception as e:
            logger.error(f"Error validating and cropping faces from {image_path}: {str(e)}")
            return [], [], False

    def _crop_face(self, image: np.ndarray, face_data: Dict) -> Optional[np.ndarray]:
        """
        Crop face from image with padding.

        Args:
            image: Image array
            face_data: Face data dictionary

        Returns:
            Cropped face image or None if error
        """
        try:
            x1, y1, x2, y2 = face_data["bbox"]
            
            # Add padding (10% of face size)
            width = x2 - x1
            height = y2 - y1
            pad_x = int(width * 0.1)
            pad_y = int(height * 0.1)
            
            # Apply padding with boundary checking
            x1 = max(0, x1 - pad_x)
            y1 = max(0, y1 - pad_y)
            x2 = min(image.shape[1], x2 + pad_x)
            y2 = min(image.shape[0], y2 + pad_y)
            
            # Crop face
            cropped = image[y1:y2, x1:x2]
            
            if cropped.size == 0:
                return None
            
            return cropped
        except Exception as e:
            logger.debug(f"Error cropping face: {str(e)}")
            return None

    def get_face_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Get face embedding for a face image.

        Args:
            face_image: Face image array (BGR format)

        Returns:
            Face embedding vector or None if error
        """
        if not self.initialized or self.detector is None:
            logger.error("Detector not initialized")
            return None
        
        try:
            # Detect face in image
            faces = self.detector.get(face_image)
            
            if not faces:
                logger.warning("No face found for embedding extraction")
                return None
            
            # Get embedding from first (main) face
            embedding = faces[0].embedding
            
            if embedding is None or len(embedding) == 0:
                return None
            
            # Normalize embedding
            embedding = np.array(embedding, dtype=np.float32)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
        except Exception as e:
            logger.error(f"Error extracting embedding: {str(e)}")
            return None

    def get_embedding_from_file(self, image_path: Path) -> Optional[np.ndarray]:
        """
        Get face embedding from image file.

        Args:
            image_path: Path to image file

        Returns:
            Face embedding vector or None
        """
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning(f"Could not read image: {image_path}")
                return None
            
            return self.get_face_embedding(img)
        except Exception as e:
            logger.error(f"Error getting embedding from {image_path}: {str(e)}")
            return None

    def get_reference_embedding(self, actor_name: str, tmdb_profile_image_url: str = None) -> Optional[np.ndarray]:
        """
        Get reference embedding for actor comparison.

        Args:
            actor_name: Actor name
            tmdb_profile_image_url: Optional TMDb profile image URL

        Returns:
            Reference face embedding or None
        """
        logger.info(f"Getting reference embedding for {actor_name}")
        
        if tmdb_profile_image_url:
            try:
                import requests
                from io import BytesIO
                
                logger.debug(f"Downloading reference image from: {tmdb_profile_image_url}")
                
                response = requests.get(tmdb_profile_image_url, timeout=30)
                response.raise_for_status()
                
                # Convert to numpy array
                img_array = np.frombuffer(response.content, dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                if img is not None:
                    embedding = self.get_face_embedding(img)
                    if embedding is not None:
                        logger.info(f"Successfully extracted reference embedding for {actor_name}")
                        return embedding
            except Exception as e:
                logger.warning(f"Could not get reference embedding from TMDb image: {str(e)}")
        
        return None

    def resize_face_image(
        self,
        image: np.ndarray,
        size: Tuple[int, int] = None
    ) -> np.ndarray:
        """
        Resize face image to standard size.

        Args:
            image: Face image array
            size: Target size (width, height), uses OUTPUT_IMAGE_SIZE if not specified

        Returns:
            Resized image array
        """
        if size is None:
            size = OUTPUT_IMAGE_SIZE
        
        try:
            resized = cv2.resize(image, size, interpolation=cv2.INTER_LANCZOS4)
            return resized
        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}")
            return image

    def save_face_image(
        self,
        face_image: np.ndarray,
        output_path: Path,
        resize: bool = True,
        quality: int = 95
    ) -> bool:
        """
        Save face image to file with optional resizing.

        Args:
            face_image: Face image array (BGR format)
            output_path: Output file path
            resize: Whether to resize to standard size
            quality: JPEG quality (1-100)

        Returns:
            True if successful
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Resize if requested
            if resize:
                face_image = self.resize_face_image(face_image)
            
            # Save image
            success = cv2.imwrite(
                str(output_path),
                face_image,
                [cv2.IMWRITE_JPEG_QUALITY, quality]
            )
            
            if success:
                logger.debug(f"Saved face image: {output_path}")
            else:
                logger.error(f"Failed to save image: {output_path}")
            
            return success
        except Exception as e:
            logger.error(f"Error saving face image: {str(e)}")
            return False
