"""
Configuration settings for the actor face dataset collection system.
"""

import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.absolute()

# Directories
PEOPLE_DIR = PROJECT_ROOT / "people"
RAW_DATA_DIR = PROJECT_ROOT / "raw_data"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Ensure directories exist
PEOPLE_DIR.mkdir(exist_ok=True)
RAW_DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ============ TMDb Configuration ============
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")  # Set via environment variable
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"

# ============ Image Download Configuration ============
# Minimum number of raw images to download per actor
MIN_RAW_IMAGES = 120

# Target number of valid images per actor (after filtering)
TARGET_IMAGES = 50

# Maximum images to download per source
MAX_IMAGES_PER_SOURCE = 60

# Image quality
MIN_IMAGE_SIZE = (150, 150)  # Minimum width and height in pixels
MAX_IMAGE_SIZE = (4000, 4000)  # Maximum width and height

# ============ Face Detection Configuration ============
# InsightFace model configuration
INSIGHTFACE_MODEL = "buffalo_l"  # buffalo_l, buffalo_m, buffalo_s

# Face detection thresholds
FACE_DETECTION_THRESHOLD = 0.5
MIN_FACE_SIZE = 50  # Minimum face width/height in pixels
MAX_FACES_PER_IMAGE = 2  # Skip if more than 2 faces detected

# Face quality thresholds
MIN_FACE_QUALITY_SCORE = 0.50  # Minimum face quality (0-1)

# Embedding settings
EMBEDDING_MODEL = "buffalo_l"  # Same as face detection model
FACE_SIMILARITY_THRESHOLD = 0.42  # Threshold for actor verification
SIMILARITY_PERCENTILE = 20  # For adaptive threshold if needed

# ============ Duplicate Detection ============
# Image hash algorithm for duplicate detection
HASH_ALGORITHM = "phash"  # phash, dhash, ahash, whash
HASH_SIZE = 8
DUPLICATE_THRESHOLD = 0.95  # 95% similarity considered duplicate

# ============ Rate Limiting ============
# Delays between requests (in seconds)
DOWNLOAD_DELAY_MIN = 0.5
DOWNLOAD_DELAY_MAX = 1.5
REQUEST_DELAY_MIN = 1
REQUEST_DELAY_MAX = 3

# Maximum retries for failed requests
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2

# Request timeout (seconds)
REQUEST_TIMEOUT = 30

# ============ Search Configuration ============
# Search terms enhancement (to avoid mythological content)
SEARCH_ENHANCEMENTS = [
    "actor",
    "telugu film actor",
    "movie star",
    "cinema",
    "film",
]

# Terms to exclude from results
EXCLUDE_TERMS = [
    "mythology",
    "mythological",
    "god",
    "goddess",
    "statue",
    "sculpture",
    "cartoon",
    "animated",
]

# ============ Logging Configuration ============
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============ Checkpoint & Resume ============
# Save checkpoint after every N images processed
CHECKPOINT_INTERVAL = 10

# ============ GPU Configuration ============
# Use GPU if available
USE_GPU = True
GPU_MEMORY_FRACTION = 0.5  # Fraction of GPU memory to use

# ============ Validation Rules ============
# Minimum confidence for face detection
MIN_FACE_CONFIDENCE = 0.6

# Face detection must find face in expected region
EXPECTED_FACE_REGION = (0.2, 0.2, 0.8, 0.8)  # (x_min, y_min, x_max, y_max) as fractions

# ============ Output Settings ============
# Image format for final dataset
OUTPUT_IMAGE_FORMAT = "jpg"
OUTPUT_IMAGE_QUALITY = 95  # For JPEG (1-100)
OUTPUT_IMAGE_SIZE = (256, 256)  # Standard face size

# Metadata to save
SAVE_METADATA = True
SAVE_EMBEDDINGS = True  # Save face embeddings for later use

# ============ Source Priorities ============
# Order of image sources to try
IMAGE_SOURCES = [
    "tmdb",           # TMDb actor profile + gallery
    "duckduckgo",     # DuckDuckGo Images
    "bing",           # Bing Images (slower but reliable)
]

# ============ Actor Validation ============
# Minimum number of movies/shows to confirm actor identity
MIN_ACTOR_CREDITS = 3

# Accept only if actor is from Telugu film industry
REQUIRED_INDUSTRIES = ["Film"]  # TMDb department
REQUIRED_LANGUAGES = ["te"]  # Telugu language code

# ============ Debug Settings ============
DEBUG_MODE = False
SAVE_DEBUG_IMAGES = False  # Save all intermediate processing steps
VERBOSE_OUTPUT = True
