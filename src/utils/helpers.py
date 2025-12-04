"""
Utility functions for the actor face dataset collection system.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Tuple
from datetime import datetime
import numpy as np
from config.settings import PEOPLE_DIR, RAW_DATA_DIR


def normalize_actor_name(name: str) -> str:
    """
    Normalize actor name for folder structure.
    
    Args:
        name: Actor name
        
    Returns:
        Normalized name (lowercase, no special chars, underscores for spaces)
    """
    # Convert to lowercase
    name = name.lower().strip()
    
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    
    # Remove special characters except underscores
    name = "".join(c for c in name if c.isalnum() or c == "_")
    
    # Remove multiple consecutive underscores
    while "__" in name:
        name = name.replace("__", "_")
    
    return name


def get_actor_dir(actor_name: str, raw: bool = False) -> Path:
    """
    Get the directory path for an actor.
    
    Args:
        actor_name: Actor name
        raw: If True, return raw_data directory; else people directory
        
    Returns:
        Actor directory path
    """
    normalized_name = normalize_actor_name(actor_name)
    base_dir = RAW_DATA_DIR if raw else PEOPLE_DIR
    actor_dir = base_dir / normalized_name
    actor_dir.mkdir(parents=True, exist_ok=True)
    return actor_dir


def get_raw_images_dir(actor_name: str) -> Path:
    """Get directory for raw images of an actor."""
    return get_actor_dir(actor_name, raw=True)


def get_final_images_dir(actor_name: str) -> Path:
    """Get directory for final processed images of an actor."""
    final_dir = get_actor_dir(actor_name, raw=False) / "images"
    final_dir.mkdir(parents=True, exist_ok=True)
    return final_dir


def get_metadata_file(actor_name: str, raw: bool = False) -> Path:
    """Get metadata JSON file path for an actor."""
    actor_dir = get_actor_dir(actor_name, raw=raw)
    return actor_dir / "metadata.json"


def get_checkpoint_file(actor_name: str) -> Path:
    """Get checkpoint file path for an actor."""
    actor_dir = get_actor_dir(actor_name, raw=True)
    return actor_dir / "checkpoint.json"


def get_embeddings_file(actor_name: str) -> Path:
    """Get embeddings file path for an actor."""
    final_dir = get_final_images_dir(actor_name)
    return final_dir.parent / "embeddings.npy"


def save_metadata(actor_name: str, metadata: dict, raw: bool = False) -> None:
    """
    Save metadata to JSON file.
    
    Args:
        actor_name: Actor name
        metadata: Dictionary of metadata
        raw: If True, save in raw_data; else in people
    """
    metadata_file = get_metadata_file(actor_name, raw=raw)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)


def load_metadata(actor_name: str, raw: bool = False) -> dict:
    """
    Load metadata from JSON file.
    
    Args:
        actor_name: Actor name
        raw: If True, load from raw_data; else from people
        
    Returns:
        Metadata dictionary or empty dict if not found
    """
    metadata_file = get_metadata_file(actor_name, raw=raw)
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    return {}


def save_checkpoint(actor_name: str, checkpoint: dict) -> None:
    """
    Save checkpoint state for resuming.
    
    Args:
        actor_name: Actor name
        checkpoint: Dictionary with checkpoint data
    """
    checkpoint["timestamp"] = datetime.now().isoformat()
    checkpoint_file = get_checkpoint_file(actor_name)
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2, default=str)


def load_checkpoint(actor_name: str) -> dict:
    """
    Load checkpoint state.
    
    Args:
        actor_name: Actor name
        
    Returns:
        Checkpoint dictionary or empty dict if not found
    """
    checkpoint_file = get_checkpoint_file(actor_name)
    if checkpoint_file.exists():
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    return {}


def get_image_hash(image_path: Path) -> str:
    """
    Calculate SHA256 hash of an image file.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Hex string of hash
    """
    sha256_hash = hashlib.sha256()
    with open(image_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_image_size(image_path: Path) -> Tuple[int, int]:
    """
    Get image dimensions without loading entire image.
    
    Args:
        image_path: Path to image file
        
    Returns:
        (width, height) tuple
    """
    from PIL import Image
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception:
        return (0, 0)


def is_valid_image_format(file_path: Path) -> bool:
    """
    Check if file is a valid image format.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if valid image format
    """
    valid_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
    return file_path.suffix.lower() in valid_formats


def get_available_images(actor_name: str) -> list:
    """
    Get list of all available images for an actor (raw and final).
    
    Args:
        actor_name: Actor name
        
    Returns:
        List of image paths
    """
    images = []
    
    # Get raw images
    raw_dir = get_raw_images_dir(actor_name)
    if raw_dir.exists():
        images.extend([f for f in raw_dir.glob("*") if is_valid_image_format(f)])
    
    # Get final images
    final_dir = get_final_images_dir(actor_name)
    if final_dir.exists():
        images.extend([f for f in final_dir.glob("*") if is_valid_image_format(f)])
    
    return sorted(list(set(images)))


def ensure_actor_structure(actor_name: str) -> dict:
    """
    Ensure all necessary directories and files exist for an actor.
    
    Args:
        actor_name: Actor name
        
    Returns:
        Dictionary with paths for all actor resources
    """
    paths = {
        "raw_dir": get_raw_images_dir(actor_name),
        "final_dir": get_final_images_dir(actor_name),
        "metadata_file": get_metadata_file(actor_name),
        "checkpoint_file": get_checkpoint_file(actor_name),
        "embeddings_file": get_embeddings_file(actor_name),
    }
    
    for path in paths.values():
        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
    
    return paths


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    if len(vec1) == 0 or len(vec2) == 0:
        return 0.0
    
    vec1 = np.array(vec1, dtype=np.float32)
    vec2 = np.array(vec2, dtype=np.float32)
    
    # Normalize vectors
    vec1_norm = np.linalg.norm(vec1)
    vec2_norm = np.linalg.norm(vec2)
    
    if vec1_norm == 0 or vec2_norm == 0:
        return 0.0
    
    vec1 = vec1 / vec1_norm
    vec2 = vec2 / vec2_norm
    
    # Calculate cosine similarity
    similarity = np.dot(vec1, vec2)
    
    # Clamp to [0, 1]
    return float(max(0.0, min(1.0, similarity)))


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()
