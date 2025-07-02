#!/usr/bin/env python3

import sys
import os
sys.path.append('scrapers')

from base_scraper import ISPEScraper

def test_ispe_scraper():
    print("Testing ISPE scraper...")
    
    # Create a fresh scraper
    scraper = ISPEScraper()
    
    print(f"Initial webinar count: {len(scraper.webinars)}")
    
    # Run the scraper
    scraper.run()
    
    print(f"Final webinar count: {len(scraper.webinars)}")
    
    # Show all ISPE webinars
    ispe_webinars = [w for w in scraper.webinars if w.get('provider') == 'ISPE']
    print(f"\nFound {len(ispe_webinars)} ISPE webinars:")
    for i, webinar in enumerate(ispe_webinars, 1):
        print(f"{i}. {webinar['title']} ({webinar['provider']})")
        print(f"   live_date: {webinar.get('live_date', 'N/A')}")
        print(f"   url: {webinar.get('url', 'N/A')}")
        print()

if __name__ == "__main__":
    test_ispe_scraper() 