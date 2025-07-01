#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup

def test_xtalks_urls():
    urls_to_try = [
        'https://xtalks.com/?post_type=webinars&type=recorded-webinars',
        'https://xtalks.com/webinars/?type=recorded-webinars', 
        'https://xtalks.com/webinars/',
        'https://xtalks.com/?post_type=webinars&webinar-topics=&type=recorded-webinars&s=&paged=2',
        'https://xtalks.com/?post_type=webinars&webinar-topics=&type=recorded-webinars&s=&paged=3'
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    
    for url in urls_to_try:
        print(f"\nTrying: {url}")
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            webinar_dates = soup.find_all(class_='webinar-date')
            print(f"Found {len(webinar_dates)} webinar dates")
            
            if webinar_dates:
                print("Sample dates:", [date.get_text().strip() for date in webinar_dates[:3]])
                
                # Check for different date ranges
                all_dates = [date.get_text().strip() for date in webinar_dates]
                unique_dates = set(all_dates)
                print(f"Unique dates: {len(unique_dates)}")
                print("Date range:", min(unique_dates), "to", max(unique_dates))
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_xtalks_urls() 