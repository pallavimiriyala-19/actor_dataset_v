# Windows GPU Installation Guide

## 🖥️ Installing on Windows with NVIDIA GPU

This guide helps you fix version compatibility issues when installing on Windows with GPU support.

---

## ⚠️ Common Windows GPU Issues & Solutions

### Issue 1: "onnxruntime" vs "onnxruntime-gpu" Conflict
**Error**: `ERROR: pip's dependency resolver does not currently take into account all the packages...`

**Solution**: Use GPU-specific requirements file
```bash
pip install -r requirements-windows-gpu.txt
```

### Issue 2: Missing CUDA/cuDNN
**Error**: `RuntimeError: ONNX Runtime GPU package is not installed`

**Solution**: 
1. Install NVIDIA CUDA Toolkit (version 11.8 or 12.x)
2. Install cuDNN libraries
3. Add to Windows PATH
4. Then install: `pip install onnxruntime-gpu`

### Issue 3: Version Conflicts with insightface
**Error**: `ERROR: Could not find a version that satisfies the requirement...`

**Solution**: Pin numpy and opencv versions first
```bash
pip install numpy==1.24.3 opencv-python==4.8.1.78
pip install insightface==0.7.3
```

### Issue 4: "No module named '_ssl'"
**Error**: SSL certificate issue on Windows

**Solution**: 
```bash
# Run this first
pip install --upgrade certifi
# Then install requirements
pip install -r requirements-windows-gpu.txt
```

---

## 📋 Step-by-Step Windows GPU Setup

### Prerequisites
- Windows 10 or 11
- Python 3.9, 3.10, or 3.11 (3.12 has compatibility issues)
- NVIDIA GPU (GeForce RTX, Quadro, etc.)
- Visual C++ Build Tools installed

### Step 1: Check Python & CUDA
```bash
# Check Python version (should be 3.9-3.11)
python --version

# Check if NVIDIA GPU is available
nvidia-smi

# Note your CUDA version from nvidia-smi output
# Common versions: 11.8, 12.0, 12.1, 12.2
```

### Step 2: Create Virtual Environment
```bash
# Navigate to project
cd /home/mango201/dataset_vscode

# Create venv
python -m venv venv

# Activate it
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 3: Install Core Dependencies First
```bash
# Install in order to avoid conflicts
pip install numpy==1.24.3
pip install opencv-python==4.8.1.78
pip install Pillow==10.0.0
```

### Step 4: Install ONNX Runtime GPU
```bash
# CRITICAL: Remove CPU version if installed
pip uninstall onnxruntime -y

# Install GPU version
pip install onnxruntime-gpu==1.17.1
```

**Note**: Choose version based on your CUDA:
- CUDA 11.8: `onnxruntime-gpu==1.17.1`
- CUDA 12.x: `onnxruntime-gpu==1.18.0`

### Step 5: Install Face Detection
```bash
pip install insightface==0.7.3
```

### Step 6: Install Remaining Dependencies
```bash
# Install from the Windows GPU requirements file
pip install -r requirements-windows-gpu.txt
```

### Step 7: Verify GPU Setup
```bash
python test_system.py
```

Check output for:
- ✓ ONNX Runtime with GPU support
- ✓ CUDA availability detected
- ✓ Face detector initialized with GPU

---

## 🔧 Troubleshooting Specific Errors

### Error: "No CUDA-capable device"
```bash
# Check if GPU is detected
python -c "import onnxruntime as rt; print(rt.get_available_providers())"

# Should show: ['CUDAExecutionProvider', 'CPUExecutionProvider']
```

**If not showing CUDA**:
1. Reinstall Visual C++ Build Tools
2. Reinstall NVIDIA drivers (latest version)
3. Reinstall CUDA Toolkit
4. Reinstall onnxruntime-gpu

### Error: "DLL load failed"
```bash
# Usually CUDA/cuDNN path issue on Windows
# Add to System PATH:
# C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin
# C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\extras\CUPTI\lib64

# Then restart terminal and try again
pip install onnxruntime-gpu==1.17.1
```

### Error: "version mismatch"
```bash
# Clean install approach:
pip uninstall -y numpy opencv-python onnxruntime onnxruntime-gpu insightface

# Then reinstall from scratch
pip install -r requirements-windows-gpu.txt
```

### Error: "No module named 'insightface'"
```bash
# Insightface needs onnxruntime installed first
pip install onnxruntime-gpu==1.17.1
pip install insightface==0.7.3

# Then install from requirements
pip install -r requirements-windows-gpu.txt
```

---

## 🐍 Python Version Compatibility

| Python Version | Status | Notes |
|---|---|---|
| 3.8 | ❌ Too old | Doesn't support latest packages |
| 3.9 | ✅ **Best** | Most stable for GPU |
| 3.10 | ✅ **Good** | Works well |
| 3.11 | ✅ **Good** | Latest compatible |
| 3.12 | ❌ Too new | Package compatibility issues |

**Recommended**: Python 3.10 on Windows with GPU

---

## 🔄 Alternative: Install Without GPU (CPU Only)

If GPU installation fails, use CPU mode:

```bash
# Install CPU version
pip install -r requirements.txt

# Then disable GPU in config
# Edit config/settings.py:
USE_GPU = False
INSIGHTFACE_MODEL = "buffalo_s"  # Smaller model for CPU
```

Processing will be slower (10-20x) but will work.

---

## 📦 Windows-Specific Package Issues

### opencv-python on Windows
**Issue**: Multiple opencv versions conflict

**Solution**:
```bash
pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless
pip install opencv-python==4.8.1.78
```

### numpy on Windows
**Issue**: Incompatible with some GPU packages

**Solution**:
```bash
pip install numpy==1.24.3  # Before installing other packages
```

### insightface on Windows
**Issue**: Missing dependencies

**Solution**:
```bash
# Install prerequisites first
pip install numpy==1.24.3 opencv-python==4.8.1.78
pip install onnxruntime-gpu==1.17.1

# Then install insightface
pip install insightface==0.7.3

# Finally install everything else
pip install -r requirements-windows-gpu.txt
```

---

## ✅ Verification Steps

### Test 1: Check GPU Detection
```bash
python -c "import onnxruntime; print(onnxruntime.get_available_providers())"
```

Expected output:
```
['CUDAExecutionProvider', 'CPUExecutionProvider']
```

### Test 2: Check Face Detector
```bash
python -c "from src.modules.face_detector import FaceDetector; detector = FaceDetector(); print('✓ Face detector ready with GPU')"
```

### Test 3: Full System Test
```bash
python test_system.py
```

Should show all ✓ marks and GPU support.

---

## 🚀 Install Commands Summary

### Quick Install (GPU)
```bash
# One-liner for Windows GPU (if versions compatible)
pip install -r requirements-windows-gpu.txt
```

### Safe Install (GPU) - Step by Step
```bash
# 1. Create venv
python -m venv venv
venv\Scripts\activate

# 2. Upgrade pip
python -m pip install --upgrade pip

# 3. Install core first
pip install numpy==1.24.3 opencv-python==4.8.1.78

# 4. Install GPU runtime
pip uninstall onnxruntime -y
pip install onnxruntime-gpu==1.17.1

# 5. Install face detection
pip install insightface==0.7.3

# 6. Install everything else
pip install -r requirements-windows-gpu.txt

# 7. Verify
python test_system.py
```

### If GPU Install Fails - Use CPU
```bash
pip install -r requirements.txt
# Edit config/settings.py: USE_GPU = False
```

---

## 📋 CUDA Version Selection

Find your CUDA version:
```bash
nvidia-smi
```

Look at "CUDA Version" line. Then:

| CUDA | onnxruntime-gpu |
|---|---|
| 11.0-11.7 | 1.16.3 |
| 11.8 | **1.17.1** ✓ |
| 12.0-12.3 | **1.18.0** ✓ |
| 12.4+ | Latest (check PyPI) |

---

## 💡 Pro Tips for Windows GPU

1. **Always activate venv first**
   ```bash
   venv\Scripts\activate  # NOT source venv/bin/activate
   ```

2. **Don't mix CPU and GPU packages**
   ```bash
   # If you have both installed, uninstall CPU version
   pip uninstall onnxruntime -y
   pip install onnxruntime-gpu
   ```

3. **Use PowerShell or Command Prompt**
   - Avoid WSL (Windows Subsystem for Linux) for GPU
   - Use native Windows terminal

4. **Update NVIDIA Drivers**
   ```bash
   # Download from https://www.nvidia.com/Download/index.aspx
   # Restart after install
   ```

5. **Check PATH**
   ```bash
   # Make sure CUDA is in PATH
   echo %PATH%
   # Should include: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin
   ```

---

## 🎯 Expected Performance

| Aspect | CPU | GPU |
|--------|-----|-----|
| Face Detection | 2-4 img/s | 20-30 img/s |
| Verification | 5-10 img/s | 50-100 img/s |
| Full Pipeline | 30-40 min | 10-15 min |
| **Speed Gain** | - | **2-3x faster** |

---

## ❓ Still Having Issues?

### Collect Debug Info
```bash
# Run this and save output
python -c "
import sys
import numpy as np
import cv2
import onnxruntime as rt
import insightface
print('Python:', sys.version)
print('NumPy:', np.__version__)
print('OpenCV:', cv2.__version__)
print('ONNX Runtime:', rt.__version__)
print('Available Providers:', rt.get_available_providers())
print('InsightFace: OK')
"
```

### Check Windows System
```bash
# In PowerShell
systeminfo | find "System"
systeminfo | find "RAM"
```

### Check NVIDIA Setup
```bash
nvidia-smi
# Should show:
# - GPU model
# - Driver version
# - CUDA version
# - GPU memory
```

---

## 📞 Common Solutions Matrix

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | Run pip install again |
| DLL load failed | Add CUDA to PATH |
| No CUDA devices | Check nvidia-smi output |
| Version conflict | Use requirements-windows-gpu.txt |
| Out of memory | Reduce batch size in settings |
| Slow processing | Check GPU usage with nvidia-smi |

---

## ✅ Success Checklist

After installation:
- [ ] `python --version` shows 3.9-3.11
- [ ] `nvidia-smi` shows your GPU
- [ ] `pip list` shows onnxruntime-gpu (not onnxruntime)
- [ ] `python test_system.py` shows all ✓
- [ ] Logs show "GPU" or "CUDA" mentioned
- [ ] Face detector loads without errors
- [ ] `python run.py "Test"` starts downloading

---

## 🎊 Ready!

Once all checks pass, you're ready to use:

```bash
python run.py "Actor Name"
```

GPU acceleration should be working - watch logs for "GPU" or "CUDA" mentions!

---

**Last Updated**: 2025-01-10  
**For Windows GPU Setup**
