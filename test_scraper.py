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
    
    # Show some of the webinars
    for i, webinar in enumerate(scraper.webinars[-5:], 1):
        print(f"{i}. {webinar['title']} ({webinar['provider']})")
        print(f"   Certificate: {webinar['certificate_available']}")
        print()

if __name__ == "__main__":
    test_ispe_scraper() 