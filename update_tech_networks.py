#!/usr/bin/env python3
"""
Script to update existing Technology Networks webinar entries with correct format and date information
"""

import json
import re
import time
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Optional

def get_headers():
    """Get realistic browser headers to avoid blocking"""
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }

def make_request(url: str, timeout: int = 30) -> Optional[requests.Response]:
    """Make a request with proper headers and delays"""
    try:
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except Exception as e:
        print(f"Error making request to {url}: {e}")
        return None

def extract_date_and_format_from_page(url: str) -> tuple[Optional[str], str]:
    """Extract date and determine format from webinar page"""
    try:
        page_response = make_request(url)
        if not page_response:
            return None, 'on-demand'
        
        page_soup = BeautifulSoup(page_response.content, 'html.parser')
        page_text = page_soup.get_text()
        
        # Date patterns to look for on the page
        date_patterns = [
            r'(\d{1,2} [A-Za-z]+ \d{4})',         # 16 July 2025
            r'([A-Za-z]+ \d{1,2}, \d{4})',         # July 16, 2025
            r'(\d{1,2}/\d{1,2}/\d{4})',           # 16/07/2025 or 07/16/2025
            r'(\d{4}-\d{2}-\d{2})'                # 2025-07-16
        ]
        
        now = datetime.now()
        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                date_str = match.group(1)
                for fmt in ["%d %B %Y", "%B %d, %Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"]:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        if dt > now:
                            return dt.strftime('%Y-%m-%d'), 'scheduled'
                    except ValueError:
                        continue
        
        # If no future date found, check for on-demand indicators
        page_text_lower = page_text.lower()
        if 'on-demand' in page_text_lower or 'on demand' in page_text_lower:
            return None, 'on-demand'
        elif re.search(r'\b(live|scheduled|upcoming|register)\b', page_text_lower):
            return None, 'scheduled'
        else:
            return None, 'on-demand'
            
    except Exception as e:
        print(f"Error extracting date from {url}: {e}")
        return None, 'on-demand'

def update_technology_networks_entries():
    """Update existing Technology Networks webinar entries"""
    
    # Load the current data
    with open('src/webinars.json', 'r') as f:
        data = json.load(f)
    
    # Find Technology Networks entries
    tech_networks_entries = [
        webinar for webinar in data['webinars']
        if webinar.get('provider') == 'Technology Networks'
    ]
    
    print(f"Found {len(tech_networks_entries)} Technology Networks entries to update")
    
    updated_count = 0
    for i, entry in enumerate(tech_networks_entries, 1):
        url = entry.get('url')
        if not url:
            continue
        
        print(f"Processing {i}/{len(tech_networks_entries)}: {entry.get('title', 'Unknown')[:50]}...")
        
        # Extract date and format from page
        webinar_date, format_type = extract_date_and_format_from_page(url)
        
        # Update the entry
        entry['format'] = format_type
        if webinar_date:
            entry['webinar_date'] = webinar_date
        elif 'webinar_date' in entry:
            del entry['webinar_date']  # Remove if no date found
        
        updated_count += 1
    
    # Save the updated data
    with open('src/webinars.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Updated {updated_count} Technology Networks entries")
    print("Update completed successfully!")

if __name__ == "__main__":
    update_technology_networks_entries() 