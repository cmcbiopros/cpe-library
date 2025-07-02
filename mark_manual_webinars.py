#!/usr/bin/env python3
"""
Utility script to mark webinars as manually added
This helps protect them from being overwritten by scrapers
"""

import json
import argparse
from typing import List, Dict, Any


def load_webinars(file_path: str = "src/webinars.json") -> Dict[str, Any]:
    """Load webinar data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        return None


def save_webinars(data: Dict[str, Any], file_path: str = "src/webinars.json"):
    """Save webinar data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved {len(data['webinars'])} webinars to {file_path}")
    except Exception as e:
        print(f"Error saving data: {e}")


def mark_by_id(webinars: List[Dict], webinar_id: str, dry_run: bool = False) -> int:
    """Mark a webinar as manual by its ID"""
    for webinar in webinars:
        if webinar.get('id') == webinar_id:
            if webinar.get('source') == 'manual':
                print(f"Webinar '{webinar.get('title', 'Unknown')}' is already marked as manual")
                return 0
            
            if not dry_run:
                webinar['source'] = 'manual'
                print(f"Marked webinar '{webinar.get('title', 'Unknown')}' as manual")
            else:
                print(f"Would mark webinar '{webinar.get('title', 'Unknown')}' as manual")
            return 1
    
    print(f"No webinar found with ID: {webinar_id}")
    return 0


def mark_by_title_pattern(webinars: List[Dict], pattern: str, dry_run: bool = False) -> int:
    """Mark webinars as manual by title pattern"""
    count = 0
    pattern_lower = pattern.lower()
    
    for webinar in webinars:
        title = webinar.get('title', '').lower()
        if pattern_lower in title:
            if webinar.get('source') == 'manual':
                print(f"Webinar '{webinar.get('title', 'Unknown')}' is already marked as manual")
                continue
            
            if not dry_run:
                webinar['source'] = 'manual'
                print(f"Marked webinar '{webinar.get('title', 'Unknown')}' as manual")
            else:
                print(f"Would mark webinar '{webinar.get('title', 'Unknown')}' as manual")
            count += 1
    
    if count == 0:
        print(f"No webinars found matching pattern: {pattern}")
    
    return count


def mark_by_provider(webinars: List[Dict], provider: str, dry_run: bool = False) -> int:
    """Mark all webinars from a provider as manual"""
    count = 0
    
    for webinar in webinars:
        if webinar.get('provider', '').lower() == provider.lower():
            if webinar.get('source') == 'manual':
                print(f"Webinar '{webinar.get('title', 'Unknown')}' is already marked as manual")
                continue
            
            if not dry_run:
                webinar['source'] = 'manual'
                print(f"Marked webinar '{webinar.get('title', 'Unknown')}' as manual")
            else:
                print(f"Would mark webinar '{webinar.get('title', 'Unknown')}' as manual")
            count += 1
    
    if count == 0:
        print(f"No webinars found from provider: {provider}")
    
    return count


def list_manual_webinars(webinars: List[Dict]):
    """List all manually added webinars"""
    manual_webinars = [w for w in webinars if w.get('source') == 'manual']
    
    if not manual_webinars:
        print("No manually added webinars found")
        return
    
    print(f"\nFound {len(manual_webinars)} manually added webinars:")
    print("-" * 80)
    
    for webinar in manual_webinars:
        print(f"ID: {webinar.get('id', 'Unknown')}")
        print(f"Title: {webinar.get('title', 'Unknown')}")
        print(f"Provider: {webinar.get('provider', 'Unknown')}")
        print(f"Date Added: {webinar.get('date_added', 'Unknown')}")
        print("-" * 80)


def show_statistics(webinars: List[Dict]):
    """Show statistics about manual vs scraped webinars"""
    manual_count = len([w for w in webinars if w.get('source') == 'manual'])
    scraped_count = len([w for w in webinars if w.get('source') == 'scraped'])
    no_source_count = len([w for w in webinars if 'source' not in w])
    
    print(f"\nWebinar Source Statistics:")
    print(f"  Total webinars: {len(webinars)}")
    print(f"  Manually added: {manual_count}")
    print(f"  Scraped: {scraped_count}")
    print(f"  No source field: {no_source_count}")


def main():
    parser = argparse.ArgumentParser(description="Mark webinars as manually added")
    parser.add_argument("--data-file", default="src/webinars.json", 
                       help="Path to webinars.json file (default: src/webinars.json)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")
    parser.add_argument("--list", action="store_true",
                       help="List all manually added webinars")
    parser.add_argument("--stats", action="store_true",
                       help="Show statistics about manual vs scraped webinars")
    parser.add_argument("--id", help="Mark webinar as manual by ID")
    parser.add_argument("--title", help="Mark webinars as manual by title pattern")
    parser.add_argument("--provider", help="Mark all webinars from provider as manual")
    
    args = parser.parse_args()
    
    # Load data
    data = load_webinars(args.data_file)
    if not data:
        return 1
    
    webinars = data['webinars']
    
    # Handle different commands
    if args.list:
        list_manual_webinars(webinars)
        return 0
    
    if args.stats:
        show_statistics(webinars)
        return 0
    
    # Mark webinars
    total_marked = 0
    
    if args.id:
        total_marked += mark_by_id(webinars, args.id, args.dry_run)
    
    if args.title:
        total_marked += mark_by_title_pattern(webinars, args.title, args.dry_run)
    
    if args.provider:
        total_marked += mark_by_provider(webinars, args.provider, args.dry_run)
    
    if not any([args.list, args.stats, args.id, args.title, args.provider]):
        print("No action specified. Use --help for usage information.")
        return 1
    
    # Save changes if not dry run
    if total_marked > 0 and not args.dry_run:
        save_webinars(data, args.data_file)
        print(f"\nSuccessfully marked {total_marked} webinars as manual")
    elif args.dry_run and total_marked > 0:
        print(f"\nWould mark {total_marked} webinars as manual")
    
    return 0


if __name__ == "__main__":
    exit(main()) 