#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def test_ispe_date_extraction():
    """Test ISPE date extraction logic"""
    
    # Get the ISPE webinars page
    url = "https://ispe.org/webinars"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to access ISPE webinars page: {e}")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Look for webinar blocks - ISPE uses column column-block structure
    webinar_blocks = soup.find_all('div', class_='column column-block')
    
    print(f"Found {len(webinar_blocks)} webinar blocks")
    
    for i, block in enumerate(webinar_blocks):
        print(f"\n--- Block {i+1} ---")
        
        # Extract title
        title_elem = block.find('h5')
        if title_elem:
            title_link = title_elem.find('a')
            if title_link:
                title = title_link.get_text(strip=True)
                print(f"Title: {title}")
                
                # Look for all <p> elements in this block
                p_elements = block.find_all('p')
                print(f"Found {len(p_elements)} <p> elements:")
                
                for j, p_elem in enumerate(p_elements):
                    p_text = p_elem.get_text(strip=True)
                    print(f"  {j+1}. '{p_text}'")
                    
                    # Check if this looks like a date
                    if re.search(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)', p_text):
                        print(f"     *** This looks like a date! ***")
                        
                        # Test the current date parsing logic
                        date_text = p_text
                        parsed_date = parse_ispe_date(date_text)
                        print(f"     Parsed date: {parsed_date}")
        
        print("-" * 50)

def parse_ispe_date(date_text: str) -> str:
    """Parse ISPE date format - current logic"""
    if not date_text:
        return "Unknown"
    
    try:
        # Handle ISPE date format: "Tuesday, 1 July 2025" or "Wednesday, 9 July 2025" or "Thursday, 4 Sep 2025"
        # More flexible pattern to handle abbreviated months
        date_pattern = r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})'
        
        match = re.search(date_pattern, date_text)
        if match:
            day, month, year = match.groups()
            print(f"     DEBUG: day={day}, month={month}, year={year}")
            
            # Convert month name to number (handle both full and abbreviated names)
            month_map = {
                'january': '01', 'jan': '01',
                'february': '02', 'feb': '02',
                'march': '03', 'mar': '03',
                'april': '04', 'apr': '04',
                'may': '05',
                'june': '06', 'jun': '06',
                'july': '07', 'jul': '07',
                'august': '08', 'aug': '08',
                'september': '09', 'sep': '09',
                'october': '10', 'oct': '10',
                'november': '11', 'nov': '11',
                'december': '12', 'dec': '12'
            }
            
            month_num = month_map.get(month.lower(), '01')
            day_num = day.zfill(2)
            
            result = f"{year}-{month_num}-{day_num}"
            print(f"     DEBUG: result={result}")
            return result
        
        return "Unknown"
        
    except Exception as e:
        print(f"Error parsing date '{date_text}': {e}")
        return "Unknown"

def test_specific_date():
    """Test the specific date that's causing issues"""
    print("\n=== Testing specific date ===")
    test_date = "Wednesday, 9 July 2025"
    print(f"Testing: '{test_date}'")
    result = parse_ispe_date(test_date)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_specific_date()
    test_ispe_date_extraction() 