#!/usr/bin/env python3
"""
Test script to verify the dataset builder system is properly configured.

Usage:
    python test_system.py
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_environment():
    """Test environment configuration."""
    print("\n" + "="*70)
    print("ENVIRONMENT TESTS")
    print("="*70)
    
    # Check Python version
    print(f"\n✓ Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("✗ ERROR: Python 3.8+ required")
        return False
    
    # Check .env file
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        print(f"✓ .env file found: {env_path}")
    else:
        print(f"⚠ .env file not found at {env_path}")
        print("  Create it with: echo 'TMDB_API_KEY=your_key' > .env")
    
    # Check TMDB API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("TMDB_API_KEY")
    if api_key:
        print(f"✓ TMDB_API_KEY set: {api_key[:10]}...")
    else:
        print("✗ TMDB_API_KEY not set")
        return False
    
    return True


def test_imports():
    """Test required imports."""
    print("\n" + "="*70)
    print("IMPORT TESTS")
    print("="*70)
    
    dependencies = {
        "requests": "HTTP requests",
        "cv2": "OpenCV (image processing)",
        "numpy": "NumPy (arrays)",
        "PIL": "Pillow (image IO)",
        "bs4": "BeautifulSoup (HTML parsing)",
    }
    
    all_ok = True
    
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {module:<15} ({description})")
        except ImportError as e:
            print(f"✗ {module:<15} NOT INSTALLED - {description}")
            print(f"  Install with: pip install -r requirements.txt")
            all_ok = False
    
    return all_ok


def test_optional_deps():
    """Test optional but recommended imports."""
    print("\n" + "="*70)
    print("OPTIONAL DEPENDENCY TESTS")
    print("="*70)
    
    optional = {
        "insightface": "InsightFace (face detection)",
        "onnx": "ONNX (deep learning)",
        "imagehash": "ImageHash (deduplication)",
        "tenacity": "Tenacity (retries)",
    }
    
    for module, description in optional.items():
        try:
            __import__(module)
            print(f"✓ {module:<15} ({description})")
        except ImportError:
            print(f"⚠ {module:<15} MISSING - {description}")
    
    return True


def test_directories():
    """Test required directories."""
    print("\n" + "="*70)
    print("DIRECTORY STRUCTURE TESTS")
    print("="*70)
    
    root = Path(__file__).parent
    required_dirs = [
        "config",
        "src",
        "src/modules",
        "src/utils",
        "people",
        "raw_data",
        "logs",
    ]
    
    all_ok = True
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if dir_path.exists():
            print(f"✓ {dir_name:<30}")
        else:
            print(f"✗ {dir_name:<30} MISSING")
            all_ok = False
    
    return all_ok


def test_modules():
    """Test core module imports."""
    print("\n" + "="*70)
    print("CORE MODULE TESTS")
    print("="*70)
    
    try:
        from config.settings import TMDB_API_KEY
        print(f"✓ config.settings              (TMDB_API_KEY={str(TMDB_API_KEY)[:10]}...)")
    except Exception as e:
        print(f"✗ config.settings              ERROR: {str(e)}")
        return False
    
    try:
        from src.utils.logger import logger
        print(f"✓ src.utils.logger             (logging configured)")
    except Exception as e:
        print(f"✗ src.utils.logger             ERROR: {str(e)}")
        return False
    
    try:
        from src.utils.helpers import normalize_actor_name
        print(f"✓ src.utils.helpers            (utility functions)")
    except Exception as e:
        print(f"✗ src.utils.helpers            ERROR: {str(e)}")
        return False
    
    try:
        from src.modules.tmdb_identifier import TMDbActorIdentifier
        print(f"✓ src.modules.tmdb_identifier  (TMDb API)")
    except Exception as e:
        print(f"✗ src.modules.tmdb_identifier  ERROR: {str(e)}")
        # This is expected if TMDb dependencies not installed
    
    return True


def test_tmdb_connection():
    """Test TMDb API connection."""
    print("\n" + "="*70)
    print("TMDb API CONNECTION TEST")
    print("="*70)
    
    try:
        from src.modules.tmdb_identifier import TMDbActorIdentifier
        import os
        
        api_key = os.getenv("TMDB_API_KEY")
        if not api_key:
            print("⚠ Skipping TMDb test - no API key configured")
            return True
        
        tmdb = TMDbActorIdentifier(api_key)
        print("✓ TMDb API client initialized")
        
        # Try a simple search
        results = tmdb.search_actors("Prabhas")
        if results:
            print(f"✓ TMDb API responding - found {len(results)} results for 'Prabhas'")
            return True
        else:
            print("✗ TMDb API not responding properly")
            return False
    except Exception as e:
        print(f"⚠ TMDb connection test failed: {str(e)}")
        print("  This may indicate missing dependencies or invalid API key")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*20 + "SYSTEM VERIFICATION TEST" + " "*24 + "║")
    print("╚" + "="*68 + "╝")
    
    results = {
        "Environment": test_environment(),
        "Imports": test_imports(),
        "Optional Dependencies": test_optional_deps(),
        "Directories": test_directories(),
        "Core Modules": test_modules(),
        "TMDb Connection": test_tmdb_connection(),
    }
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}  {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED - System is ready to use!")
        print("\nNext steps:")
        print("1. Make sure TMDB_API_KEY is set in .env file")
        print("2. Run: python run.py 'Actor Name'")
        print("3. Check logs in logs/ directory")
        print("="*70 + "\n")
        return 0
    else:
        print("✗ SOME TESTS FAILED - Please fix errors above")
        print("\nCommon fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Create .env file: echo 'TMDB_API_KEY=your_key' > .env")
        print("3. Activate venv: source venv/bin/activate")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
