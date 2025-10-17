#!/usr/bin/env python3
"""
Simple runner for the broken links cleanup script
"""

import subprocess
import sys
import os

def main():
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run the cleanup script with dry-run first
    print("Running broken links cleanup (dry-run first)...")
    print("=" * 60)
    
    # First run with dry-run to show what would be removed
    result = subprocess.run([
        sys.executable, 'cleanup_broken_links.py', '--dry-run', '--backup'
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    if result.returncode != 0:
        print("Dry run failed. Exiting.")
        return
    
    # Ask user if they want to proceed
    response = input("\nProceed with actual cleanup? (y/N): ")
    if response.lower() != 'y':
        print("Cleanup cancelled.")
        return
    
    # Run the actual cleanup
    print("\nRunning actual cleanup...")
    print("=" * 60)
    
    result = subprocess.run([
        sys.executable, 'cleanup_broken_links.py', '--backup'
    ])
    
    if result.returncode == 0:
        print("Cleanup completed successfully!")
    else:
        print("Cleanup failed. Check the output above for details.")

if __name__ == '__main__':
    main()
