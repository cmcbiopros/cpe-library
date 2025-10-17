#!/usr/bin/env python3
"""
Cleanup Script for Broken Webinar Links

This script checks all webinar URLs and removes entries that return 404 errors
or other unrecoverable HTTP errors. It's designed to be safe and conservative.

Usage:
    python cleanup_broken_links.py [--dry-run] [--backup]
"""

import json
import os
import sys
import argparse
import time
from datetime import datetime
import requests
from urllib.parse import urlparse


def load_webinars(file_path):
    """Load webinar data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('webinars', [])
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        return None


def save_webinars(webinars, file_path, backup=True):
    """Save webinar data to JSON file"""
    if backup and os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(file_path, backup_path)
        print(f"Created backup: {backup_path}")
    
    data = {
        'webinars': webinars,
        'last_updated': datetime.now().isoformat(),
        'total_count': len(webinars)
    }
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(webinars)} webinars to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


def check_url(url, timeout=10):
    """Check if a URL is accessible"""
    if not url:
        return False, "No URL provided"
    
    try:
        # Parse URL to validate format
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format"
        
        # Make HEAD request first (faster than GET)
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        
        # If HEAD fails, try GET
        if response.status_code == 405 or response.status_code == 501:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
        
        # Check if URL is accessible
        if response.status_code == 200:
            return True, f"OK ({response.status_code})"
        elif response.status_code == 404:
            return False, f"404 Not Found"
        elif response.status_code in [403, 401]:
            return False, f"Access denied ({response.status_code})"
        else:
            return False, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description='Clean up broken webinar links')
    parser.add_argument('--file', default='webinars.json', help='Path to webinars.json file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed without making changes')
    parser.add_argument('--backup', action='store_true', help='Create backup before making changes')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    # Load webinars
    print(f"Loading webinars from {args.file}...")
    webinars = load_webinars(args.file)
    if webinars is None:
        sys.exit(1)
    
    print(f"Loaded {len(webinars)} webinars")
    
    # Check URLs
    valid_webinars = []
    broken_webinars = []
    
    print(f"\nChecking URLs (timeout: {args.timeout}s)...")
    
    for i, webinar in enumerate(webinars, 1):
        url = webinar.get('url', '')
        title = webinar.get('title', 'Unknown')[:50]
        webinar_id = webinar.get('id', 'unknown')
        
        print(f"[{i}/{len(webinars)}] Checking: {title}...")
        
        is_valid, reason = check_url(url, args.timeout)
        
        if is_valid:
            valid_webinars.append(webinar)
            print(f"  ✓ {reason}")
        else:
            broken_webinars.append({
                'webinar': webinar,
                'reason': reason
            })
            print(f"  ✗ {reason}")
        
        # Small delay to be respectful to servers
        time.sleep(0.5)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"CLEANUP SUMMARY")
    print(f"{'='*60}")
    print(f"Total webinars: {len(webinars)}")
    print(f"Valid URLs: {len(valid_webinars)}")
    print(f"Broken URLs: {len(broken_webinars)}")
    
    if broken_webinars:
        print(f"\nBROKEN URLs (will be removed):")
        print(f"{'-'*60}")
        for item in broken_webinars:
            webinar = item['webinar']
            print(f"ID: {webinar.get('id', 'unknown')}")
            print(f"Title: {webinar.get('title', 'Unknown')}")
            print(f"URL: {webinar.get('url', 'No URL')}")
            print(f"Reason: {item['reason']}")
            print()
    
    if args.dry_run:
        print("\nDRY RUN - No changes made")
        return
    
    # Confirm before proceeding
    if broken_webinars:
        response = input(f"\nRemove {len(broken_webinars)} broken webinars? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return
    
    # Save updated data
    if save_webinars(valid_webinars, args.file, backup=args.backup):
        print("Cleanup completed successfully!")
    else:
        print("Failed to save updated data")
        sys.exit(1)


if __name__ == '__main__':
    main()
