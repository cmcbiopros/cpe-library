#!/usr/bin/env python3

import json
import sys
import os
from datetime import datetime
from providers.labroots_scraper import LabrootsScraper
from providers.xtalks_scraper import XtalksScraper
from providers.ispe_scraper import ISPEScraper
from providers.technology_networks_scraper import TechnologyNetworksScraper
from providers.fda_cder_scraper import FDACDERScraper
from providers.pmi_scraper import PMIScraper
from providers.usp_scraper import USPScraper

# Add parent directory to path to import cleanup function
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cleanup_expired_webinars import cleanup_expired_webinars

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
        PMIScraper(),
        USPScraper()
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
            
            # Update all_webinars to include all unique webinars from this scraper
            existing_ids = {w['id'] for w in all_webinars}
            added_count = 0
            for w in scraper.webinars:
                if w['id'] not in existing_ids:
                    all_webinars.append(w)
                    existing_ids.add(w['id'])
                    added_count += 1
            print(f"Added {added_count} new webinars from {scraper.__class__.__name__}")
            
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
    
    # Run cleanup to remove expired webinars
    print(f"\nRunning cleanup to remove expired webinars...")
    cleanup_stats = cleanup_expired_webinars(
        data_file="../src/webinars.json",
        max_age_days=365,  # Remove on-demand webinars older than 1 year
        dry_run=False
    )
    
    if "error" not in cleanup_stats:
        print(f"Cleanup completed: {cleanup_stats['total_removed']} expired webinars removed")
    else:
        print(f"Cleanup failed: {cleanup_stats['error']}")

if __name__ == "__main__":
    run_all_scrapers() 