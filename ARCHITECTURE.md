# Architecture & Design Documentation

## System Overview

The Telugu Actor Face Dataset Builder is a comprehensive system for automatically creating clean, accurate, and verified face datasets for Telugu film industry actors. It orchestrates multiple components working together in a pipeline.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACTOR FACE DATASET BUILDER                   │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐           ┌──────────┐          ┌─────────┐
   │  STAGE  │           │  STAGE   │          │ STAGE   │
   │    1    │           │    2     │          │   3     │
   │         │           │          │          │         │
   │ IDENTIFY│  SUCCESS  │ DOWNLOAD │ SUCCESS  │ DETECT  │
   │ ACTOR   │──────────▶│ IMAGES   │─────────▶│ FACES   │
   └─────────┘           └──────────┘          └─────────┘
        │                                           │
        │  • TMDb lookup                            │  • InsightFace
        │  • Disambiguate                           │  • Validate size
        │  • Verify Telugu                          │  • Crop faces
        │                                           │
                                                    ▼
                                            ┌────────────────┐
                                            │   STAGE 4      │
                                            │                │
                                            │   VERIFY       │
                                            │   ACTOR        │
                                            └────────────────┘
                                                    │
                                                    │  • Embeddings
                                                    │  • Similarity
                                                    │  • Threshold
                                                    │
                                                    ▼
                                            ┌────────────────┐
                                            │   STAGE 5      │
                                            │                │
                                            │  REMOVE        │
                                            │  DUPLICATES    │
                                            └────────────────┘
                                                    │
                                                    │  • pHash
                                                    │  • Keep best
                                                    │
                                                    ▼
                                            ┌────────────────┐
                                            │   STAGE 6      │
                                            │                │
                                            │   SAVE         │
                                            │   DATASET      │
                                            └────────────────┘
                                                    │
                                                    ▼
                                            ┌─────────────────┐
                                            │  FINAL DATASET  │
                                            │                 │
                                            │ ~50 clean faces │
                                            └─────────────────┘
```

## Component Architecture

### 1. Core Modules (`src/modules/`)

#### `tmdb_identifier.py`
**Purpose**: Identify and retrieve actor information from TMDb API

**Key Classes**:
- `TMDbActorIdentifier`: Main API client
  - `search_actors(name)`: Search for actor by name
  - `disambiguate_actor(name)`: Find best matching actor
  - `get_complete_actor_profile(name)`: Get all necessary info
  - `verify_actor_is_telugu(person_id)`: Confirm Telugu presence

**Features**:
- Automatic retry with exponential backoff
- Popularity-based ranking
- Telugu language/country detection
- Minimum credit count validation
- Rate limiting compliance

**API**: TMDb v3 REST API

#### `image_downloader.py`
**Purpose**: Download images from multiple sources

**Key Classes**:
- `ImageDownloader`: Main downloader
  - `download_from_tmdb()`: TMDb profile/gallery images
  - `download_from_duckduckgo()`: DuckDuckGo Images search
  - `download_and_save()`: Download and persist single image

**Features**:
- Multi-source support (TMDb, DuckDuckGo, Bing fallback)
- Rate limiting (1-3 second delays)
- Retry logic with exponential backoff
- Image dimension validation
- Search query enhancement (add "actor", "telugu film", etc.)
- User-Agent spoofing to avoid blocks

**Sources**:
- TMDb API (professional, high quality)
- DuckDuckGo Images (diverse, no rate limit)
- Bing Images (fallback, reliable)

#### `face_detector.py`
**Purpose**: Detect, validate, and crop faces using InsightFace

**Key Classes**:
- `FaceDetector`: InsightFace wrapper
  - `detect_faces(image_path)`: Find all faces in image
  - `validate_and_crop_faces()`: Validate and extract faces
  - `get_face_embedding()`: Extract face embedding
  - `get_reference_embedding()`: Get TMDb profile reference

**Features**:
- InsightFace buffalo_l model (high accuracy)
- Automatic size validation (MIN_FACE_SIZE)
- Face count validation (MAX_FACES_PER_IMAGE)
- Confidence thresholding
- Padding for face context
- GPU/CPU support (auto-detect)

**Models**:
- buffalo_l: High accuracy (default)
- buffalo_m: Medium (faster)
- buffalo_s: Small (CPU-friendly)

#### `actor_verifier.py`
**Purpose**: Verify faces match target actor and remove duplicates

**Key Classes**:
- `ActorVerifier`: Face embedding-based verification
  - `set_reference_actor()`: Set comparison baseline
  - `verify_image()`: Check single image
  - `verify_batch()`: Check multiple images

- `DuplicateDetector`: Image deduplication
  - `find_duplicates()`: Identify duplicate groups
  - `remove_duplicates()`: Keep best versions
  - `compute_hash()`: Perceptual hash calculation

**Features**:
- Cosine similarity matching
- Configurable threshold (default: 0.42)
- Batch processing support
- Multiple hash algorithms (pHash, dHash, etc.)
- Quality-based duplicate retention

### 2. Utility Modules (`src/utils/`)

#### `logger.py`
**Purpose**: Centralized logging configuration

**Loggers**:
- `logger`: Main system logger
- `download_logger`: Download operations
- `face_detection_logger`: Face detection operations
- `validation_logger`: Verification operations
- `duplicate_logger`: Deduplication operations

**Features**:
- Rotating file handlers (10MB max)
- Console + file output
- Configurable log levels
- Separate component logs

#### `helpers.py`
**Purpose**: Utility functions for common operations

**Key Functions**:
- `normalize_actor_name()`: Format names consistently
- `get_actor_dir()`: Locate actor directories
- `save/load_metadata()`: JSON persistence
- `save/load_checkpoint()`: Resume support
- `cosine_similarity()`: Vector comparison
- `is_valid_image_format()`: Format validation

### 3. Main Orchestration (`src/main.py`)

#### `ActorDatasetBuilder`
**Purpose**: Orchestrate entire pipeline

**Main Method**: `build_dataset(actor_name, resume=True, verify_actor=True)`

**Pipeline**:
```
1. identify_actor() → TMDb lookup
2. download_images() → Multi-source download
3. detect_and_validate_faces() → Face extraction
4. verify_actor_faces() → Embedding verification
5. remove_duplicates() → Deduplication
6. save_final_dataset() → Persist to disk
```

**Features**:
- Checkpoint saving after each stage
- Resume capability
- Comprehensive error handling
- Detailed reporting
- Progress logging

## Data Flow

### Raw Data → Processing → Final Dataset

```
Raw Downloaded Images (120)
    │
    ├─ Format validation
    ├─ Size validation
    └─ Download integrity check
    │
    ▼
Face Detection & Cropping (115)
    │
    ├─ InsightFace analysis
    ├─ Face count validation
    ├─ Size validation
    └─ Quality filtering
    │
    ▼
Actor Verification (92)
    │
    ├─ Embedding extraction
    ├─ Similarity calculation
    └─ Threshold filtering (>=0.42)
    │
    ▼
Duplicate Removal (60)
    │
    ├─ Perceptual hashing
    ├─ Similarity comparison
    └─ Quality ranking
    │
    ▼
Final Dataset (50-60)
    │
    └─ Saved to people/actor_name/images/
```

## Configuration Hierarchy

```
Defaults (in config/settings.py)
    │
    └─ Can be overridden by:
       ├─ Command-line arguments
       ├─ Environment variables
       └─ Direct settings modification
```

## Checkpoint System

Saves progress at strategic points:

```json
{
  "download": {
    "actor": "Prabhas",
    "downloaded_images": 125,
    "timestamp": "2025-01-10T10:30:00"
  },
  "face_detection": {
    "processed": 125,
    "valid_faces": 115,
    "timestamp": "2025-01-10T10:45:00"
  },
  "verification": {
    "verified_faces": 92,
    "timestamp": "2025-01-10T11:00:00"
  }
}
```

Allows resuming from last successful stage.

## Error Handling Strategy

### Network Errors
- Retry with exponential backoff (max 3 attempts)
- Fallback to alternate sources
- Continue with partial data

### Face Detection Errors
- Log and skip problematic images
- Continue with other images
- Report rejection reasons

### Verification Errors
- Log similarity scores
- Keep scores for debugging
- Continue with next batch

### File I/O Errors
- Verify disk space
- Check permissions
- Create parent directories automatically

## Performance Characteristics

### Time Complexity
- Actor lookup: O(1) - TMDb API
- Download: O(n) - n images × network latency
- Face detection: O(n) - n images × model time
- Verification: O(n) - n images × embedding time
- Deduplication: O(n²) worst case - pairwise comparison

### Space Complexity
- Raw images: ~600MB (120 images)
- Cropped faces: ~200MB (115 faces)
- Final dataset: ~50MB (50 faces, 256×256)
- Embeddings: ~100KB (128-dim float32 vectors)

### Optimization Opportunities
- Batch processing for face detection
- GPU acceleration for embeddings
- Lazy loading of images
- Incremental hashing for duplicates

## Testing Strategy

### Unit Tests
- Module initialization
- Individual function logic
- Error handling

### Integration Tests
- End-to-end pipeline
- Multi-source downloads
- Face verification accuracy

### System Tests
- Resume capability
- Checkpoint recovery
- Large-scale processing

## Security Considerations

### API Key Management
- Stored in .env file (never committed)
- Read from environment variable
- Clear error messages if missing

### Network Security
- HTTPS for all API calls
- Timeout protection (30 seconds)
- User-Agent headers
- No sensitive data in logs

### File Permissions
- Data directories created with appropriate permissions
- Logs not world-readable
- Embeddings not exposed

## Future Enhancements

1. **Parallel Processing**
   - Download multiple sources simultaneously
   - Batch face detection on GPU
   - Parallel verification

2. **Additional Sources**
   - Instagram scraping (if allowed)
   - IMDb photo gallery
   - YouTube thumbnails

3. **Advanced Filtering**
   - Emotion detection (no sad faces)
   - Head pose validation
   - Lighting quality assessment

4. **Quality Metrics**
   - Sharpness scoring
   - Brightness assessment
   - Age estimation

5. **Interactive UI**
   - Web dashboard for monitoring
   - Real-time progress tracking
   - Manual verification tools

## Dependencies Graph

```
run.py
  └─ src/main.py
     ├─ src/modules/tmdb_identifier.py
     │  └─ requests, tenacity, config/settings.py
     ├─ src/modules/image_downloader.py
     │  ├─ requests, tenacity
     │  └─ config/settings.py
     ├─ src/modules/face_detector.py
     │  ├─ insightface, opencv, numpy
     │  └─ config/settings.py
     ├─ src/modules/actor_verifier.py
     │  ├─ imagehash, opencv, numpy
     │  └─ src/utils/helpers.py
     └─ src/utils/logger.py
        └─ config/settings.py
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-10
