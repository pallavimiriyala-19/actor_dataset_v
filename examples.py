#!/usr/bin/env python3
"""
Quick Start Example - Building a Face Dataset for a Telugu Actor

This example demonstrates the complete workflow:
1. Identifying the actor
2. Downloading images
3. Detecting faces
4. Verifying actor match
5. Removing duplicates
6. Saving final dataset
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
from dotenv import load_dotenv
load_dotenv()


def example_basic_usage():
    """Example 1: Basic usage - build dataset with defaults."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Dataset Building")
    print("="*80)
    
    from src.main import ActorDatasetBuilder
    
    # Initialize builder
    builder = ActorDatasetBuilder()
    
    # Build dataset
    report = builder.build_dataset(
        actor_name="Prabhas",
        resume=True,
        verify_actor=True,
        target_images=50
    )
    
    # Print report
    print("\nDataset Building Report:")
    print(f"  Status: {report['status'].upper()}")
    print(f"  Actor: {report['actor']}")
    
    if report['status'] == 'success':
        print("\n✓ Dataset successfully created!")
        print(f"  Location: people/prabhas/images/")
    
    return report


def example_multiple_actors():
    """Example 2: Build datasets for multiple actors."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Building Datasets for Multiple Actors")
    print("="*80)
    
    from src.main import ActorDatasetBuilder
    
    actors = [
        "Prabhas",
        "Allu Arjun",
        "Nani",
    ]
    
    builder = ActorDatasetBuilder()
    results = {}
    
    for actor in actors:
        print(f"\nBuilding dataset for {actor}...")
        
        report = builder.build_dataset(
            actor_name=actor,
            resume=True,
            verify_actor=True,
            target_images=50
        )
        
        results[actor] = report['status']
        
        print(f"  → {report['status'].upper()}")
    
    # Summary
    print("\n" + "-"*80)
    print("Summary:")
    for actor, status in results.items():
        print(f"  {actor:<20} {status.upper()}")
    
    return results


def example_custom_config():
    """Example 3: Build with custom configuration."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Custom Configuration")
    print("="*80)
    
    from src.main import ActorDatasetBuilder
    from config import settings
    
    # Temporarily modify settings
    original_target = settings.TARGET_IMAGES
    original_threshold = settings.FACE_SIMILARITY_THRESHOLD
    
    try:
        # Custom settings
        settings.TARGET_IMAGES = 100  # Target 100 images
        settings.FACE_SIMILARITY_THRESHOLD = 0.50  # Stricter verification
        
        builder = ActorDatasetBuilder()
        
        report = builder.build_dataset(
            actor_name="Ravi Teja",
            target_images=100
        )
        
        print(f"\n✓ Built dataset with custom configuration")
        print(f"  Target images: 100")
        print(f"  Similarity threshold: 0.50")
        print(f"  Result: {report['status'].upper()}")
        
        return report
    finally:
        # Restore settings
        settings.TARGET_IMAGES = original_target
        settings.FACE_SIMILARITY_THRESHOLD = original_threshold


def example_resume_on_interrupt():
    """Example 4: Resume from checkpoint after interruption."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Resume from Checkpoint")
    print("="*80)
    
    from src.main import ActorDatasetBuilder
    from src.utils.helpers import load_checkpoint
    
    actor = "Ram Charan"
    
    print(f"\nStarting dataset build for {actor}...")
    print("(Note: You can press Ctrl+C to interrupt and resume later)")
    
    try:
        builder = ActorDatasetBuilder()
        
        report = builder.build_dataset(
            actor_name=actor,
            resume=True  # Enable resume
        )
        
        print(f"\n✓ Build completed: {report['status'].upper()}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted! Your progress has been saved.")
        print(f"Resume later with: python run.py '{actor}'")
        
        # Show checkpoint info
        checkpoint = load_checkpoint(actor)
        if checkpoint:
            print(f"\nCheckpoint saved:")
            print(f"  Timestamp: {checkpoint.get('timestamp')}")
            if 'download' in checkpoint:
                print(f"  Downloaded: {checkpoint['download'].get('downloaded_images')} images")
            if 'face_detection' in checkpoint:
                print(f"  Detected: {checkpoint['face_detection'].get('valid_faces')} faces")


def example_direct_module_usage():
    """Example 5: Using modules directly for custom workflows."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Direct Module Usage")
    print("="*80)
    
    from src.modules.tmdb_identifier import TMDbActorIdentifier
    from src.modules.face_detector import FaceDetector
    
    # Example: Just identify an actor
    print("\n1. Identifying actor...")
    tmdb = TMDbActorIdentifier()
    actor_profile = tmdb.get_complete_actor_profile("Mahesh Babu")
    
    if actor_profile:
        print(f"   ✓ Found: {actor_profile['name']}")
        print(f"   ✓ TMDB ID: {actor_profile['tmdb_id']}")
        print(f"   ✓ Telugu Actor: {actor_profile['is_telugu_actor']}")
        print(f"   ✓ Available Images: {len(actor_profile['images'])}")
    
    # Example: Just detect faces
    print("\n2. Face detection example...")
    detector = FaceDetector()
    print(f"   ✓ Face detector ready")
    print(f"   ✓ Model: buffalo_l")
    
    return actor_profile


def example_view_results():
    """Example 6: View and analyze results."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Viewing Results")
    print("="*80)
    
    from pathlib import Path
    import json
    
    actors_dir = Path(__file__).parent / "people"
    
    if not actors_dir.exists():
        print("\nNo datasets found yet. Build one first with:")
        print("  python run.py 'Actor Name'")
        return
    
    # List available datasets
    datasets = [d for d in actors_dir.iterdir() if d.is_dir()]
    
    if not datasets:
        print("\nNo datasets found.")
        return
    
    print(f"\nFound {len(datasets)} actor dataset(s):\n")
    
    for actor_dir in sorted(datasets):
        images_dir = actor_dir / "images"
        metadata_file = actor_dir / "metadata.json"
        
        image_count = len(list(images_dir.glob("*.jpg"))) if images_dir.exists() else 0
        
        print(f"  {actor_dir.name.replace('_', ' ').title()}")
        print(f"    ├─ Final images: {image_count}")
        
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
            print(f"    ├─ Created: {metadata.get('timestamp', 'Unknown')}")
            if 'similarity_stats' in metadata:
                stats = metadata['similarity_stats']
                print(f"    └─ Similarity (min/max/mean): {stats['min']:.3f}/{stats['max']:.3f}/{stats['mean']:.3f}")
        
        print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "Telugu Actor Face Dataset Builder - Examples" + " "*19 + "║")
    print("╚" + "="*78 + "╝")
    
    print("""
This script demonstrates various usage patterns:

1. Basic usage
2. Multiple actors
3. Custom configuration
4. Resume from checkpoint
5. Direct module usage
6. View results

Choose an example to run, or modify the code to create your own workflow.
""")
    
    # Uncomment the example you want to run:
    
    # example_basic_usage()
    # example_multiple_actors()
    # example_custom_config()
    # example_resume_on_interrupt()
    # example_direct_module_usage()
    example_view_results()
