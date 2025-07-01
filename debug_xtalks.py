#!/usr/bin/env python3

from scrapers.base_scraper import XtalksScraper
import json

def debug_xtalks():
    print("=== Xtalks Scraper Debug ===")
    
    # Create scraper and load existing data
    scraper = XtalksScraper()
    print(f"Initial webinars loaded: {len(scraper.webinars)}")
    print(f"Initial Xtalks webinars: {len([w for w in scraper.webinars if w['provider'] == 'Xtalks'])}")
    
    # Run scraper
    print("\nRunning scraper...")
    scraper.scrape()
    print(f"After scraping - Total webinars: {len(scraper.webinars)}")
    print(f"After scraping - Xtalks webinars: {len([w for w in scraper.webinars if w['provider'] == 'Xtalks'])}")
    
    # Check for invalid data
    print("\nChecking for invalid data...")
    invalid_count = 0
    for i, webinar in enumerate(scraper.webinars):
        try:
            json.dumps(webinar)
        except Exception as e:
            print(f"Invalid webinar {i}: {e}")
            print(f"Webinar data: {webinar}")
            invalid_count += 1
    
    print(f"Invalid webinars found: {invalid_count}")
    
    # Save data
    print("\nSaving data...")
    scraper.save_data()
    
    # Check saved file
    print("\nChecking saved file...")
    with open('src/webinars.json', 'r') as f:
        data = json.load(f)
    
    print(f"Total in saved file: {len(data['webinars'])}")
    print(f"Xtalks in saved file: {len([w for w in data['webinars'] if w['provider'] == 'Xtalks'])}")
    
    # Show all Xtalks webinars in memory
    print("\nXtalks webinars in memory:")
    xtalks_in_memory = [w for w in scraper.webinars if w['provider'] == 'Xtalks']
    for i, webinar in enumerate(xtalks_in_memory):
        print(f"{i+1}. {webinar['title']}")
    
    # Show all Xtalks webinars in file
    print("\nXtalks webinars in file:")
    xtalks_in_file = [w for w in data['webinars'] if w['provider'] == 'Xtalks']
    for i, webinar in enumerate(xtalks_in_file):
        print(f"{i+1}. {webinar['title']}")

if __name__ == "__main__":
    debug_xtalks() 