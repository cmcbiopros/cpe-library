#!/usr/bin/env python3

import json
from datetime import datetime
from base_scraper import (
    LabrootsScraper, XtalksScraper, ISPEScraper, 
    TechnologyNetworksScraper, FDACDERScraper, 
    SOCRAScraper, PMIScraper
)

def run_all_scrapers():
    """Run all scrapers and accumulate results"""
    
    # Load existing data
    try:
        with open("../src/webinars.json", 'r') as f:
            data = json.load(f)
            existing_webinars = data.get('webinars', [])
    except FileNotFoundError:
        existing_webinars = []
    
    print(f"Starting with {len(existing_webinars)} existing webinars")
    
    # List of scrapers to run
    scrapers = [
        LabrootsScraper(),
        XtalksScraper(),
        ISPEScraper(),
        TechnologyNetworksScraper(),
        FDACDERScraper(),
        SOCRAScraper(),
        PMIScraper()
    ]
    
    all_webinars = existing_webinars.copy()
    
    # Run each scraper
    for scraper in scrapers:
        print(f"\nRunning {scraper.__class__.__name__}...")
        
        # Load existing data into scraper
        scraper.webinars = all_webinars.copy()
        
        try:
            # Run the scraper
            scraper.scrape()
            
            # Get new webinars (those not in original list)
            new_webinars = [w for w in scraper.webinars if w not in all_webinars]
            
            print(f"Added {len(new_webinars)} new webinars from {scraper.__class__.__name__}")
            
            # Add new webinars to our collection
            all_webinars.extend(new_webinars)
            
        except Exception as e:
            print(f"Error running {scraper.__class__.__name__}: {e}")
    
    # Save final results
    final_data = {
        "webinars": all_webinars,
        "last_updated": datetime.now().isoformat(),
        "total_count": len(all_webinars)
    }
    
    with open("../src/webinars.json", 'w') as f:
        json.dump(final_data, f, indent=2)
    
    print(f"\nFinal result: {len(all_webinars)} total webinars")
    print(f"Added {len(all_webinars) - len(existing_webinars)} new webinars")

if __name__ == "__main__":
    run_all_scrapers() 