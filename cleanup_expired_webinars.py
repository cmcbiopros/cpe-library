#!/usr/bin/env python3
"""
Script to clean up expired webinars from webinars.json
Removes webinars with past live dates and old entries to keep the database lean
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any


def cleanup_expired_webinars(data_file: str = "webinars.json", 
                           max_age_days: int = 365,
                           dry_run: bool = False) -> Dict[str, int]:
    """
    Clean up expired webinars from the database
    
    Args:
        data_file: Path to the webinars.json file
        max_age_days: Maximum age in days for on-demand webinars (default: 365 days)
        dry_run: If True, only show what would be removed without actually removing
    
    Returns:
        Dictionary with cleanup statistics
    """
    
    # Load the current data
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {data_file} not found")
        return {"error": "File not found"}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {data_file}: {e}")
        return {"error": "Invalid JSON"}
    
    original_count = len(data['webinars'])
    print(f"Starting cleanup of {original_count} webinars...")
    
    # Calculate cutoff dates
    today = datetime.now()
    max_age_cutoff = today - timedelta(days=max_age_days)
    
    print(f"Removing webinars with live dates before: {today.strftime('%Y-%m-%d')}")
    print(f"Removing on-demand webinars older than: {max_age_cutoff.strftime('%Y-%m-%d')} ({max_age_days} days)")
    
    # Track what we're removing
    removed_past_live = []
    removed_old_on_demand = []
    removed_invalid_dates = []
    kept_webinars = []
    protected_manual = 0
    removed_manual = 0
    
    for webinar in data['webinars']:
        should_remove = False
        removal_reason = ""
        
        # Check if this is a manually added webinar
        is_manual = webinar.get('source') == 'manual'
        
        # Check live_date field
        live_date = webinar.get('live_date', 'on-demand')
        
        if live_date == 'on-demand':
            # For on-demand webinars, check the date_added field
            date_added = webinar.get('date_added', 'Unknown')
            if date_added != 'Unknown':
                try:
                    added_date = datetime.strptime(date_added, '%Y-%m-%d')
                    if added_date < max_age_cutoff:
                        # For manually added webinars, be more conservative
                        if is_manual:
                            print(f"  PROTECTED: Manually added webinar '{webinar.get('title', 'Unknown')}' is old but will be kept")
                            kept_webinars.append(webinar)
                            protected_manual += 1
                            continue
                        else:
                            should_remove = True
                            removal_reason = f"On-demand webinar older than {max_age_days} days (added: {date_added})"
                            removed_old_on_demand.append({
                                'id': webinar.get('id', 'Unknown'),
                                'title': webinar.get('title', 'Unknown'),
                                'provider': webinar.get('provider', 'Unknown'),
                                'reason': removal_reason
                            })
                            removed_manual += 1
                except ValueError:
                    # Invalid date format
                    if is_manual:
                        print(f"  PROTECTED: Manually added webinar '{webinar.get('title', 'Unknown')}' has invalid date but will be kept")
                        kept_webinars.append(webinar)
                        protected_manual += 1
                        continue
                    else:
                        should_remove = True
                        removal_reason = f"Invalid date_added format: {date_added}"
                        removed_invalid_dates.append({
                            'id': webinar.get('id', 'Unknown'),
                            'title': webinar.get('title', 'Unknown'),
                            'provider': webinar.get('provider', 'Unknown'),
                            'reason': removal_reason
                        })
                        removed_manual += 1
            else:
                # No date_added, keep it (could be legacy data)
                if is_manual:
                    print(f"  PROTECTED: Manually added webinar '{webinar.get('title', 'Unknown')}' has no date but will be kept")
                kept_webinars.append(webinar)
                protected_manual += 1
                continue
                
        elif live_date in ['Unknown', 'unknown']:
            # Unknown live date, check date_added as fallback
            date_added = webinar.get('date_added', 'Unknown')
            if date_added != 'Unknown':
                try:
                    added_date = datetime.strptime(date_added, '%Y-%m-%d')
                    if added_date < max_age_cutoff:
                        # For manually added webinars, be more conservative
                        if is_manual:
                            print(f"  PROTECTED: Manually added webinar '{webinar.get('title', 'Unknown')}' has unknown live date but will be kept")
                            kept_webinars.append(webinar)
                            protected_manual += 1
                            continue
                        else:
                            should_remove = True
                            removal_reason = f"Webinar with unknown live date older than {max_age_days} days (added: {date_added})"
                            removed_old_on_demand.append({
                                'id': webinar.get('id', 'Unknown'),
                                'title': webinar.get('title', 'Unknown'),
                                'provider': webinar.get('provider', 'Unknown'),
                                'reason': removal_reason
                            })
                            removed_manual += 1
                except ValueError:
                    # Invalid date format, keep it
                    if is_manual:
                        print(f"  PROTECTED: Manually added webinar '{webinar.get('title', 'Unknown')}' has invalid date but will be kept")
                    kept_webinars.append(webinar)
                    protected_manual += 1
                    continue
            else:
                # No date information, keep it
                if is_manual:
                    print(f"  PROTECTED: Manually added webinar '{webinar.get('title', 'Unknown')}' has no date info but will be kept")
                kept_webinars.append(webinar)
                protected_manual += 1
                continue
                
        else:
            # Has a specific live date, check if it's in the past
            try:
                live_datetime = datetime.strptime(live_date, '%Y-%m-%d')
                if live_datetime < today:
                    # For manually added webinars with past live dates, still remove them
                    # but log it clearly
                    if is_manual:
                        print(f"  Removing manually added webinar with past live date: {webinar.get('title', 'Unknown')} (live_date: {live_date})")
                    should_remove = True
                    removal_reason = f"Past live date: {live_date}"
                    removed_past_live.append({
                        'id': webinar.get('id', 'Unknown'),
                        'title': webinar.get('title', 'Unknown'),
                        'provider': webinar.get('provider', 'Unknown'),
                        'live_date': live_date,
                        'reason': removal_reason,
                        'was_manual': is_manual
                    })
                    removed_manual += 1
            except ValueError:
                # Invalid date format, keep it
                if is_manual:
                    print(f"  PROTECTED: Manually added webinar '{webinar.get('title', 'Unknown')}' has invalid live date format but will be kept")
                kept_webinars.append(webinar)
                protected_manual += 1
                continue
        
        if should_remove:
            if not dry_run:
                source_info = " (MANUALLY ADDED)" if is_manual else ""
                print(f"  Removing: {webinar.get('title', 'Unknown')}{source_info} ({removal_reason})")
        else:
            kept_webinars.append(webinar)
    
    # Update the data
    if not dry_run:
        data['webinars'] = kept_webinars
        data['total_count'] = len(kept_webinars)
        data['last_updated'] = datetime.now().isoformat()
        
        # Save the cleaned data
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Calculate statistics
    new_count = len(kept_webinars)
    total_removed = original_count - new_count
    
    stats = {
        "original_count": original_count,
        "new_count": new_count,
        "total_removed": total_removed,
        "removed_past_live": len(removed_past_live),
        "removed_old_on_demand": len(removed_old_on_demand),
        "removed_invalid_dates": len(removed_invalid_dates),
        "protected_manual": protected_manual,
        "removed_manual": removed_manual,
        "dry_run": dry_run
    }
    
    # Print summary
    print(f"\n{'DRY RUN - ' if dry_run else ''}Cleanup Summary:")
    print(f"  Original webinars: {original_count}")
    print(f"  Kept webinars: {new_count}")
    print(f"  Total removed: {total_removed}")
    print(f"  - Past live dates: {len(removed_past_live)}")
    print(f"  - Old on-demand: {len(removed_old_on_demand)}")
    print(f"  - Invalid dates: {len(removed_invalid_dates)}")
    print(f"  Manually added webinars:")
    print(f"    - Protected: {protected_manual}")
    print(f"    - Removed (past live dates): {removed_manual}")
    
    if dry_run and total_removed > 0:
        print(f"\nWould remove {total_removed} webinars. Run without --dry-run to actually remove them.")
    elif not dry_run:
        print(f"\nSuccessfully removed {total_removed} webinars from {data_file}")
    
    return stats


def show_removal_details(removed_items: List[Dict], category: str):
    """Show details of removed items"""
    if not removed_items:
        return
    
    print(f"\n{category} ({len(removed_items)} items):")
    for item in removed_items[:10]:  # Show first 10
        print(f"  - {item['title']} ({item['provider']}) - {item['reason']}")
    
    if len(removed_items) > 10:
        print(f"  ... and {len(removed_items) - 10} more")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up expired webinars from webinars.json")
    parser.add_argument("--data-file", default="webinars.json",
                        help="Path to webinars.json file (default: webinars.json)")
    parser.add_argument("--max-age-days", type=int, default=365,
                       help="Maximum age in days for on-demand webinars (default: 365)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be removed without actually removing")
    parser.add_argument("--show-details", action="store_true",
                       help="Show details of removed webinars")
    
    args = parser.parse_args()
    
    # Run cleanup
    stats = cleanup_expired_webinars(
        data_file=args.data_file,
        max_age_days=args.max_age_days,
        dry_run=args.dry_run
    )
    
    if "error" in stats:
        exit(1)
    
    print(f"\nCleanup completed successfully!") 