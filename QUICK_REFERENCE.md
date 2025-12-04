# Quick Reference Guide

## Installation (3 steps)

```bash
# 1. Setup environment
python3 -m venv venv && source venv/bin/activate

# 2. Install dependencies  
pip install -r requirements.txt

# 3. Configure API key
echo "TMDB_API_KEY=your_key_here" > .env
```

## Basic Usage

```bash
# Build dataset for actor
python run.py "Actor Name"

# With target of 100 images
python run.py "Actor Name" --target 100

# Skip actor verification (faster)
python run.py "Actor Name" --no-verify

# Start fresh (no resume)
python run.py "Actor Name" --no-resume

# Save report to file
python run.py "Actor Name" --output-report report.json
```

## File Locations

```
people/prabhas/images/          # Final verified faces
raw_data/prabhas/               # Downloaded raw images
raw_data/prabhas/faces/         # Detected faces
raw_data/prabhas/checkpoint.json # Resume point
logs/actor_dataset.log          # Main log
```

## Configuration

Edit `config/settings.py`:

```python
MIN_RAW_IMAGES = 120            # How many to download
TARGET_IMAGES = 50              # How many in final
FACE_SIMILARITY_THRESHOLD = 0.42 # Verification strictness
MAX_FACES_PER_IMAGE = 2         # Skip if more faces
INSIGHTFACE_MODEL = "buffalo_l" # Model choice
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No API key | Create .env with TMDB_API_KEY |
| Import error | `pip install -r requirements.txt` |
| Virtual env | `source venv/bin/activate` |
| Out of memory | Reduce batch size in settings |
| No faces found | Lower FACE_DETECTION_THRESHOLD |

## Monitoring

```bash
# Watch main log
tail -f logs/actor_dataset.log

# Watch download log
tail -f logs/download.log

# Watch face detection
tail -f logs/face_detection.log
```

## Quick Customization

### More images (100 per actor)
```python
# In config/settings.py
TARGET_IMAGES = 100
MIN_RAW_IMAGES = 200
```

### Stricter verification (safer but fewer)
```python
FACE_SIMILARITY_THRESHOLD = 0.50
```

### Faster processing (lower quality)
```python
INSIGHTFACE_MODEL = "buffalo_s"
FACE_DETECTION_THRESHOLD = 0.6
```

### CPU only (no GPU)
```python
USE_GPU = False
```

## Common Commands

```bash
# Test system is working
python test_system.py

# View examples
python examples.py

# Get help
python run.py --help

# Build for "Prabhas"
python run.py "Prabhas"

# Build for "Allu Arjun" with 75 images
python run.py "Allu Arjun" --target 75

# Quick build without verification
python run.py "Nani" --no-verify

# Build and save report
python run.py "Ravi Teja" --output-report report.json

# Check final images
ls -la people/prabhas/images/ | wc -l

# View metadata
cat people/prabhas/metadata.json

# Resume after interruption
python run.py "Prabhas"  # Just run again, resume enabled by default
```

## Performance Tips

1. **GPU available?** → Much faster (10x+)
2. **Many actors?** → Run sequentially, not parallel
3. **First run?** → Slowest (model downloads)
4. **Need speed?** → Use buffalo_s model
5. **Need quality?** → Use buffalo_l (default)

## Data Quality Check

After building, verify:

```bash
# Count images
ls people/prabhas/images/ | wc -l

# Check metadata exists
cat people/prabhas/metadata.json

# Spot check images
ls -lah people/prabhas/images/ | head

# View similarity stats
grep -A 5 similarity_stats people/prabhas/metadata.json
```

## API Limits

- **TMDb**: 40 requests/10 seconds (built-in retry)
- **DuckDuckGo**: No limit
- **Bing**: No limit
- **System delays**: 1-3 seconds between requests

## What Gets Saved

```
people/prabhas/
├── images/                  # 50 final verified faces
├── metadata.json           # Actor info & stats
└── embeddings.npy          # Reference face embedding

raw_data/prabhas/
├── tmdb_0000.jpg           # Raw downloads
├── duckduckgo_0000.jpg
├── faces/                  # Detected faces
└── checkpoint.json         # Resume state
```

## Typical Processing Flow

```
Raw Image (from internet)
    ↓
Face Detection (InsightFace)
    ↓ 
Face Cropping (256×256)
    ↓
Similarity Check (vs reference)
    ↓
Duplicate Check (perceptual hash)
    ↓
Final Dataset (50 verified faces)
```

## Expected Results

```
Actor: Prabhas
Raw images downloaded: 125
Faces detected: 115
Faces verified: 92
Duplicates removed: 32
Final dataset: 60 images
Average similarity: 0.75
Processing time: 35 minutes
Status: ✓ SUCCESS
```

## Adjustment Guide

| Scenario | Change |
|----------|--------|
| **Too few images** | ↑ `TARGET_IMAGES` |
| **Too many false positives** | ↑ `FACE_SIMILARITY_THRESHOLD` |
| **Too slow** | ↓ `INSIGHTFACE_MODEL` to "s" |
| **Out of memory** | ↓ `MIN_RAW_IMAGES` |
| **Missing some faces** | ↓ `FACE_DETECTION_THRESHOLD` |

## Folder Structure Explained

```
dataset_vscode/
├── config/          → Settings & config
├── src/             → Source code
│   ├── modules/     → Core functionality
│   └── utils/       → Helper functions
├── people/          → FINAL DATASETS
├── raw_data/        → Temporary downloads
├── logs/            → Diagnostic logs
└── venv/            → Python environment
```

## Getting Help

1. Check **README.md** for features
2. Check **SETUP.md** for installation
3. Check **ARCHITECTURE.md** for design
4. Run **test_system.py** for diagnostics
5. Check **logs/** for error details

## Resume After Crash

Just run the same command again:
```bash
python run.py "Actor Name"
```

The system automatically resumes from the last checkpoint!

## Environment Variables

```bash
# Required
TMDB_API_KEY=your_api_key

# Optional  
PYTHONPATH=/path/to/dataset_vscode
```

## Key Concepts

| Term | Meaning |
|------|---------|
| **Actor ID** | Unique identifier from TMDb |
| **Embedding** | 512-dim vector of face features |
| **Similarity** | How similar two faces are (0-1) |
| **pHash** | Perceptual hash for duplicate detection |
| **Checkpoint** | Saved progress point |
| **Threshold** | Minimum acceptable value |

---

**Last Updated**: 2025-01-10  
**Version**: 1.0.0
