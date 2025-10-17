#!/usr/bin/env python3
"""
URL Validation Script for CPE Webinar Directory

This script validates all webinar URLs in webinars.json and removes entries
that return 404 errors or other unrecoverable HTTP errors.

Usage:
    python validate_urls.py [--dry-run] [--backup] [--timeout 10] [--max-workers 10]
"""

import json
import os
import sys
import argparse
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class URLValidator:
    def __init__(self, timeout=10, max_workers=10, max_retries=3):
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = self._create_session(max_retries)
        self.results = {
            'valid': [],
            'invalid': [],
            'errors': []
        }
    
    def _create_session(self, max_retries):
        """Create a requests session with retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def validate_url(self, webinar):
        """Validate a single webinar URL"""
        url = webinar.get('url', '')
        webinar_id = webinar.get('id', 'unknown')
        title = webinar.get('title', 'Unknown')
        
        if not url:
            return {
                'webinar': webinar,
                'status': 'invalid',
                'reason': 'No URL provided',
                'status_code': None
            }
        
        try:
            # Parse URL to validate format
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    'webinar': webinar,
                    'status': 'invalid',
                    'reason': 'Invalid URL format',
                    'status_code': None
                }
            
            # Make HEAD request first (faster than GET)
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            
            # If HEAD fails, try GET
            if response.status_code == 405 or response.status_code == 501:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            
            # Check if URL is accessible
            if response.status_code == 200:
                return {
                    'webinar': webinar,
                    'status': 'valid',
                    'reason': 'URL accessible',
                    'status_code': response.status_code
                }
            elif response.status_code == 404:
                return {
                    'webinar': webinar,
                    'status': 'invalid',
                    'reason': '404 Not Found',
                    'status_code': response.status_code
                }
            elif response.status_code in [403, 401]:
                return {
                    'webinar': webinar,
                    'status': 'invalid',
                    'reason': f'Access denied ({response.status_code})',
                    'status_code': response.status_code
                }
            else:
                return {
                    'webinar': webinar,
                    'status': 'invalid',
                    'reason': f'HTTP {response.status_code}',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                'webinar': webinar,
                'status': 'invalid',
                'reason': 'Request timeout',
                'status_code': None
            }
        except requests.exceptions.ConnectionError:
            return {
                'webinar': webinar,
                'status': 'invalid',
                'reason': 'Connection error',
                'status_code': None
            }
        except requests.exceptions.RequestException as e:
            return {
                'webinar': webinar,
                'status': 'invalid',
                'reason': f'Request error: {str(e)}',
                'status_code': None
            }
        except Exception as e:
            return {
                'webinar': webinar,
                'status': 'error',
                'reason': f'Unexpected error: {str(e)}',
                'status_code': None
            }
    
    def validate_webinars(self, webinars):
        """Validate all webinar URLs using thread pool"""
        print(f"Validating {len(webinars)} webinar URLs...")
        print(f"Using {self.max_workers} workers with {self.timeout}s timeout")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all validation tasks
            future_to_webinar = {
                executor.submit(self.validate_url, webinar): webinar 
                for webinar in webinars
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_webinar):
                result = future.result()
                completed += 1
                
                # Categorize results
                if result['status'] == 'valid':
                    self.results['valid'].append(result)
                elif result['status'] == 'invalid':
                    self.results['invalid'].append(result)
                else:  # error
                    self.results['errors'].append(result)
                
                # Progress indicator
                if completed % 10 == 0 or completed == len(webinars):
                    print(f"Progress: {completed}/{len(webinars)} ({completed/len(webinars)*100:.1f}%)")
        
        return self.results
    
    def print_summary(self):
        """Print validation summary"""
        total = len(self.results['valid']) + len(self.results['invalid']) + len(self.results['errors'])
        
        print(f"\n{'='*60}")
        print(f"URL VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total webinars checked: {total}")
        print(f"Valid URLs: {len(self.results['valid'])}")
        print(f"Invalid URLs: {len(self.results['invalid'])}")
        print(f"Errors: {len(self.results['errors'])}")
        
        if self.results['invalid']:
            print(f"\nINVALID URLs (will be removed):")
            print(f"{'-'*60}")
            for result in self.results['invalid']:
                webinar = result['webinar']
                print(f"ID: {webinar.get('id', 'unknown')}")
                print(f"Title: {webinar.get('title', 'Unknown')[:60]}...")
                print(f"URL: {webinar.get('url', 'No URL')}")
                print(f"Reason: {result['reason']}")
                print(f"Status Code: {result['status_code']}")
                print()
        
        if self.results['errors']:
            print(f"\nERRORS (will be removed):")
            print(f"{'-'*60}")
            for result in self.results['errors']:
                webinar = result['webinar']
                print(f"ID: {webinar.get('id', 'unknown')}")
                print(f"Title: {webinar.get('title', 'Unknown')[:60]}...")
                print(f"URL: {webinar.get('url', 'No URL')}")
                print(f"Error: {result['reason']}")
                print()


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


def main():
    parser = argparse.ArgumentParser(description='Validate webinar URLs and remove broken links')
    parser.add_argument('--file', default='webinars.json', help='Path to webinars.json file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed without making changes')
    parser.add_argument('--backup', action='store_true', help='Create backup before making changes')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    parser.add_argument('--max-workers', type=int, default=10, help='Number of concurrent workers')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum number of retries for failed requests')
    
    args = parser.parse_args()
    
    # Load webinars
    print(f"Loading webinars from {args.file}...")
    webinars = load_webinars(args.file)
    if webinars is None:
        sys.exit(1)
    
    print(f"Loaded {len(webinars)} webinars")
    
    # Validate URLs
    validator = URLValidator(
        timeout=args.timeout,
        max_workers=args.max_workers,
        max_retries=args.max_retries
    )
    
    results = validator.validate_webinars(webinars)
    validator.print_summary()
    
    # Determine which webinars to keep
    valid_webinars = [result['webinar'] for result in results['valid']]
    
    print(f"\nWebinars to keep: {len(valid_webinars)}")
    print(f"Webinars to remove: {len(results['invalid']) + len(results['errors'])}")
    
    if args.dry_run:
        print("\nDRY RUN - No changes made")
        return
    
    # Confirm before proceeding
    if len(results['invalid']) + len(results['errors']) > 0:
        response = input(f"\nRemove {len(results['invalid']) + len(results['errors'])} broken webinars? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return
    
    # Save updated data
    if save_webinars(valid_webinars, args.file, backup=args.backup):
        print("URL validation completed successfully!")
    else:
        print("Failed to save updated data")
        sys.exit(1)


if __name__ == '__main__':
    main()
