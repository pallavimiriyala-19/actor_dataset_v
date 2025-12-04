# Setup Guide - Telugu Actor Face Dataset Builder

This guide walks you through setting up the system step by step.

## Prerequisites

- **Python 3.8 or higher**
- **pip** (Python package manager)
- **8GB+ RAM** (16GB recommended)
- **GPU** (optional, but recommended for faster processing)

Check Python version:
```bash
python3 --version
```

## Installation Steps

### Step 1: Navigate to Project Directory
```bash
cd /home/mango201/dataset_vscode
```

### Step 2: Create Virtual Environment

This isolates project dependencies:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# On Windows, use:
# venv\Scripts\activate
```

You should see `(venv)` at the start of your terminal prompt.

### Step 3: Upgrade pip

```bash
pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This may take 5-15 minutes depending on your internet speed.

**Note**: If you have a GPU:
```bash
# For NVIDIA CUDA support (optional)
pip install onnxruntime-gpu
```

### Step 5: Get TMDb API Key

1. Go to https://www.themoviedb.org
2. Click on your profile icon → Settings
3. Click on "API" in the left menu
4. Click "Create" or request access
5. Accept terms and fill in application details
6. Copy your API key (format: long string of characters)

### Step 6: Configure Environment

Create `.env` file:

```bash
echo "TMDB_API_KEY=your_api_key_here" > .env
```

Replace `your_api_key_here` with your actual TMDb API key.

**Verify it worked:**
```bash
cat .env
```

You should see:
```
TMDB_API_KEY=abc123xyz...
```

### Step 7: Verify Installation

Test that everything is installed:

```bash
python3 -c "import insightface; print('✓ InsightFace installed')"
python3 -c "import cv2; print('✓ OpenCV installed')"
python3 -c "import requests; print('✓ Requests installed')"
```

You should see three checkmarks.

## Testing the System

### Test 1: Check TMDb API Connection

```bash
python3 -c "
from src.modules.tmdb_identifier import TMDbActorIdentifier
import os
tmdb = TMDbActorIdentifier(os.getenv('TMDB_API_KEY'))
print('✓ TMDb API connection successful')
"
```

### Test 2: Check Face Detection

```bash
python3 -c "
from src.modules.face_detector import FaceDetector
detector = FaceDetector()
print('✓ Face detector initialized successfully')
print(f'  Model: buffalo_l')
"
```

### Test 3: Run Help Command

```bash
python run.py --help
```

You should see usage information.

## Quick Start

### Build Dataset for Your First Actor

```bash
python run.py "Prabhas"
```

This will:
1. Identify actor from TMDb
2. Download ~120 images
3. Detect faces
4. Verify actor match
5. Remove duplicates
6. Save ~50 final images to `people/prabhas/images/`

### Monitor Progress

In another terminal, watch the logs:

```bash
tail -f logs/actor_dataset.log
```

### Check Results

After completion:

```bash
# See final images
ls -la people/prabhas/images/

# View metadata
cat people/prabhas/metadata.json

# View report (if saved)
cat report.json
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'insightface'"

**Solution**: Reinstall dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Issue: "TMDB_API_KEY not set"

**Solution**: Verify `.env` file exists
```bash
# Check .env exists
ls -la .env

# Check content
cat .env

# Should show: TMDB_API_KEY=your_key
```

If missing, create it:
```bash
echo "TMDB_API_KEY=your_api_key_here" > .env
```

### Issue: "No module named 'onnxruntime'"

**Solution**: Install ONNX Runtime
```bash
pip install onnxruntime
```

For GPU:
```bash
pip install onnxruntime-gpu
```

### Issue: "Virtual environment not activated"

**Solution**: Activate venv
```bash
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

You should see `(venv)` in your prompt.

### Issue: ImportError with imports

**Solution**: Add project to Python path
```bash
export PYTHONPATH=/home/mango201/dataset_vscode:$PYTHONPATH

# Or in .env:
PYTHONPATH=/home/mango201/dataset_vscode
```

### Issue: Out of memory errors

**Solution**: Reduce batch size
```bash
# Edit config/settings.py:
MAX_IMAGES_PER_SOURCE = 30  # reduce from 60
```

Or run on CPU with smaller models:
```bash
# Edit config/settings.py:
INSIGHTFACE_MODEL = "buffalo_s"  # smaller model
USE_GPU = False
```

## Directory Structure

After installation, you should have:

```
dataset_vscode/
├── config/
│   └── settings.py           # Configuration
├── src/
│   ├── modules/
│   │   ├── tmdb_identifier.py
│   │   ├── image_downloader.py
│   │   ├── face_detector.py
│   │   └── actor_verifier.py
│   ├── utils/
│   │   ├── logger.py
│   │   └── helpers.py
│   └── main.py              # Main orchestration
├── people/                  # Final datasets (created on first run)
├── raw_data/                # Raw downloaded images (created on first run)
├── logs/                    # Log files (created on first run)
├── venv/                    # Virtual environment
├── .env                     # Your API key (created by you)
├── requirements.txt         # Dependencies
├── run.py                   # CLI entry point
└── README.md               # Full documentation
```

## Next Steps

1. **Read the README.md** for full documentation
2. **Review config/settings.py** to understand configuration options
3. **Try building a test dataset** for a popular actor
4. **Check logs** if anything goes wrong
5. **Customize settings** for your specific needs

## Common Customizations

### Process More Images

Edit `config/settings.py`:
```python
MIN_RAW_IMAGES = 200       # Download more
TARGET_IMAGES = 100        # Keep more
MAX_IMAGES_PER_SOURCE = 100
```

### Stricter Face Verification

Edit `config/settings.py`:
```python
FACE_SIMILARITY_THRESHOLD = 0.50  # Higher = stricter
```

### Faster Processing

Edit `config/settings.py`:
```python
INSIGHTFACE_MODEL = "buffalo_s"  # Smaller model
FACE_DETECTION_THRESHOLD = 0.6   # Skip lower confidence
```

### Use CPU Only

Edit `config/settings.py`:
```python
USE_GPU = False
```

## Getting Help

1. Check **logs/** directory for error messages
2. Review **troubleshooting** section above
3. Check Python version compatibility
4. Verify TMDb API key is valid
5. Ensure internet connection is stable

## Performance Tips

- **First run is slowest** (needs to download models)
- **Use GPU** if available (10x faster)
- **Run multiple actors** in sequence
- **Monitor disk space** (each actor needs ~2GB temp)
- **Keep logs** for debugging

## Next: Build Your Dataset

Once setup is complete, try:

```bash
python run.py "Allu Arjun" --target 50
```

Or see more examples in README.md!

---

**Setup Complete!** 🎉

Your system is ready to build Telugu actor face datasets.
