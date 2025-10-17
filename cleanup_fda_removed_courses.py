#!/usr/bin/env python3
"""
Cleanup Script for FDA CDER Removed Courses

This script specifically targets FDA CDER courses that show "course was removed" 
pages instead of proper 404 redirects. These pages return 200 status but contain
content indicating the course is no longer available.

Usage:
    python cleanup_fda_removed_courses.py [--dry-run] [--backup]
"""

import json
import os
import sys
import argparse
import time
import re
from datetime import datetime
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup


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


def is_course_removed(url, timeout=15):
    """
    Check if a URL shows a 'course was removed' page.
    Returns (is_removed, reason) tuple.
    """
    if not url:
        return True, "No URL provided"
    
    try:
        # Parse URL to validate format
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return True, "Invalid URL format"
        
        # Make GET request to get page content
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        
        # Check HTTP status first
        if response.status_code == 404:
            return True, "404 Not Found"
        elif response.status_code in [403, 401]:
            return True, f"Access denied ({response.status_code})"
        elif response.status_code != 200:
            return True, f"HTTP {response.status_code}"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()
        
        # Patterns that indicate a course was removed or is no longer available
        removal_patterns = [
            r'course.*removed',
            r'no longer available',
            r'has been removed',
            r'is no longer available',
            r'course.*discontinued',
            r'content.*removed',
            r'page.*removed',
            r'resource.*removed',
            r'course.*unavailable',
            r'content.*unavailable',
            r'this.*course.*has.*been',
            r'training.*no.*longer',
            r'webinar.*removed',
            r'webinar.*no.*longer',
            r'event.*removed',
            r'event.*no.*longer',
            r'archived.*removed',
            r'content.*archived.*removed'
        ]
        
        # Check for removal patterns
        for pattern in removal_patterns:
            if re.search(pattern, page_text):
                return True, f"Course removed (matched: {pattern})"
        
        # Skip short content check - legitimate courses might have minimal content
        # Focus on explicit removal indicators instead
        
        # Check for specific FDA error messages
        fda_error_patterns = [
            r'error.*page',
            r'not.*found',
            r'content.*not.*available',
            r'resource.*not.*found'
        ]
        
        for pattern in fda_error_patterns:
            if re.search(pattern, page_text):
                return True, f"FDA error page (matched: {pattern})"
        
        # If we get here, the course appears to be available
        return False, f"OK (content appears available)"
        
    except requests.exceptions.Timeout:
        return True, "Request timeout"
    except requests.exceptions.ConnectionError:
        return True, "Connection error"
    except requests.exceptions.RequestException as e:
        return True, f"Request error: {str(e)}"
    except Exception as e:
        return True, f"Unexpected error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description='Clean up FDA CDER removed courses')
    parser.add_argument('--file', default='webinars.json', help='Path to webinars.json file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed without making changes')
    parser.add_argument('--backup', action='store_true', help='Create backup before making changes')
    parser.add_argument('--timeout', type=int, default=15, help='Request timeout in seconds')
    parser.add_argument('--provider', default='FDA CDER', help='Provider to check (default: FDA CDER)')
    
    args = parser.parse_args()
    
    # Load webinars
    print(f"Loading webinars from {args.file}...")
    webinars = load_webinars(args.file)
    if webinars is None:
        sys.exit(1)
    
    print(f"Loaded {len(webinars)} webinars")
    
    # Filter for FDA CDER webinars only
    fda_webinars = [w for w in webinars if w.get('provider') == args.provider]
    print(f"Found {len(fda_webinars)} {args.provider} webinars")
    
    if not fda_webinars:
        print(f"No {args.provider} webinars found to check")
        return
    
    # Check URLs
    valid_webinars = []
    removed_webinars = []
    
    print(f"\nChecking {args.provider} URLs for removed courses (timeout: {args.timeout}s)...")
    
    for i, webinar in enumerate(fda_webinars, 1):
        url = webinar.get('url', '')
        title = webinar.get('title', 'Unknown')[:60]
        webinar_id = webinar.get('id', 'unknown')
        
        print(f"[{i}/{len(fda_webinars)}] Checking: {title}...")
        
        is_removed, reason = is_course_removed(url, args.timeout)
        
        if is_removed:
            removed_webinars.append({
                'webinar': webinar,
                'reason': reason
            })
            print(f"  ✗ {reason}")
        else:
            valid_webinars.append(webinar)
            print(f"  ✓ {reason}")
        
        # Small delay to be respectful to servers
        time.sleep(1)
    
    # Add non-FDA webinars back to valid list
    non_fda_webinars = [w for w in webinars if w.get('provider') != args.provider]
    valid_webinars.extend(non_fda_webinars)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"FDA CDER CLEANUP SUMMARY")
    print(f"{'='*70}")
    print(f"Total webinars: {len(webinars)}")
    print(f"FDA CDER webinars: {len(fda_webinars)}")
    print(f"Removed FDA courses: {len(removed_webinars)}")
    print(f"Valid FDA courses: {len(valid_webinars) - len(non_fda_webinars)}")
    print(f"Other providers: {len(non_fda_webinars)}")
    
    if removed_webinars:
        print(f"\nREMOVED FDA COURSES (will be deleted):")
        print(f"{'-'*70}")
        for item in removed_webinars:
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
    if removed_webinars:
        response = input(f"\nRemove {len(removed_webinars)} removed FDA courses? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return
    
    # Save updated data
    if save_webinars(valid_webinars, args.file, backup=args.backup):
        print("FDA cleanup completed successfully!")
    else:
        print("Failed to save updated data")
        sys.exit(1)


if __name__ == '__main__':
    main()
