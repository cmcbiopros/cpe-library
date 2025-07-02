#!/usr/bin/env python3
"""
Script to clean up Technology Networks navigation page entries from webinars.json
"""

import json
import os

def cleanup_technology_networks():
    """Remove Technology Networks navigation page entries"""
    
    # Load the current data
    with open('src/webinars.json', 'r') as f:
        data = json.load(f)
    
    # Navigation page titles to remove
    navigation_titles = [
        'Webinars & Online Events',
        'Next',
        'Last',
        '2',
        '3', 
        '4',
        '5'
    ]
    
    # Filter out navigation pages
    original_count = len(data['webinars'])
    data['webinars'] = [
        webinar for webinar in data['webinars']
        if not (webinar.get('provider') == 'Technology Networks' and 
                webinar.get('title') in navigation_titles)
    ]
    new_count = len(data['webinars'])
    removed_count = original_count - new_count
    
    print(f"Removed {removed_count} Technology Networks navigation page entries")
    print(f"Original count: {original_count}, New count: {new_count}")
    
    # Update the total count
    data['total_count'] = new_count
    
    # Save the cleaned data
    with open('src/webinars.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Cleanup completed successfully!")

if __name__ == "__main__":
    cleanup_technology_networks() 