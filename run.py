#!/usr/bin/env python3
"""
CLI Entry point for actor face dataset collection system.

Usage:
    python -m run <actor_name> [--tmdb-key <key>] [--no-resume] [--no-verify]
    python -m run --help
"""

import sys
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from src.main import ActorDatasetBuilder
from src.utils.logger import logger


def print_banner():
    """Print welcome banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         Telugu Actor Face Dataset Collection System              ║
║                                                                  ║
║  Create high-quality, verified face datasets for Telugu actors   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_report(report: dict):
    """Print dataset building report."""
    print("\n" + "="*80)
    print("DATASET BUILDING REPORT")
    print("="*80 + "\n")
    
    print(f"Actor:         {report.get('actor', 'Unknown')}")
    print(f"Status:        {report.get('status', 'Unknown').upper()}")
    print(f"Start Time:    {report.get('start_time', 'N/A')}")
    print(f"End Time:      {report.get('end_time', 'N/A')}")
    
    if "error" in report:
        print(f"Error:         {report['error']}")
    
    print("\nStage Results:")
    print("-" * 80)
    
    for stage, results in report.get("stages", {}).items():
        status = results.get("status", "unknown").upper()
        status_icon = "✓" if status == "SUCCESS" else "✗" if status == "FAILED" else "⊘"
        
        print(f"{status_icon} {stage.upper():<25} {status:<10}")
        
        for key, value in results.items():
            if key != "status":
                print(f"  └─ {key:<23} {value}")
    
    print("\n" + "="*80 + "\n")


def main():
    """Main CLI entry point."""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Build a clean, verified face dataset for Telugu movie actors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build dataset for an actor with default settings
  python run.py "Prabhas" 
  
  # Specify TMDb API key
  python run.py "Allu Arjun" --tmdb-key your_api_key_here
  
  # Start fresh (no resume from checkpoint)
  python run.py "Nani" --no-resume
  
  # Skip actor verification (faster, but less accurate)
  python run.py "Ravi Teja" --no-verify
        """
    )
    
    parser.add_argument(
        "actor",
        help="Actor name to build dataset for"
    )
    
    parser.add_argument(
        "--tmdb-key",
        help="TMDb API key (or set TMDB_API_KEY environment variable)",
        default=os.getenv("TMDB_API_KEY")
    )
    
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start fresh without resuming from checkpoint"
    )
    
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip actor face verification (faster but less accurate)"
    )
    
    parser.add_argument(
        "--target",
        type=int,
        help="Target number of final images (default: 50)",
        default=50
    )
    
    parser.add_argument(
        "--output-report",
        help="Save report to JSON file"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.tmdb_key:
        print("ERROR: TMDb API key not provided!")
        print("Please set TMDB_API_KEY environment variable or use --tmdb-key option")
        sys.exit(1)
    
    if not args.actor or len(args.actor.strip()) == 0:
        print("ERROR: Actor name not provided")
        sys.exit(1)
    
    try:
        # Initialize builder
        logger.info(f"Initializing dataset builder with TMDb API key: {args.tmdb_key[:10]}...")
        builder = ActorDatasetBuilder(tmdb_api_key=args.tmdb_key)
        
        # Build dataset
        report = builder.build_dataset(
            actor_name=args.actor,
            resume=not args.no_resume,
            verify_actor=not args.no_verify,
            target_images=args.target
        )
        
        # Print report
        print_report(report)
        
        # Save report if requested
        if args.output_report:
            output_file = Path(args.output_report)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Report saved to {output_file}")
        
        # Exit with appropriate code
        if report.get("status") == "success":
            logger.info("Dataset building completed successfully!")
            sys.exit(0)
        elif report.get("status") == "partial":
            logger.warning("Dataset building completed with partial results")
            sys.exit(1)
        else:
            logger.error("Dataset building failed")
            sys.exit(2)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        logger.info("Process interrupted by user")
        sys.exit(3)
    
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
