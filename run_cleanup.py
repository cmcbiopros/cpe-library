#!/usr/bin/env python3
"""
Simple script to run cleanup independently
"""

from cleanup_expired_webinars import cleanup_expired_webinars

if __name__ == "__main__":
    print("Running webinar cleanup...")
    
    # Run cleanup with default settings
    stats = cleanup_expired_webinars(
        data_file="src/webinars.json",
        max_age_days=365,  # Remove on-demand webinars older than 1 year
        dry_run=False
    )
    
    if "error" in stats:
        print(f"Error: {stats['error']}")
        exit(1)
    
    print("Cleanup completed successfully!") 