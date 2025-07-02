# Manual Webinar Protection System

## Overview

The CPE Library now includes a protection system to prevent manually added webinars from being overwritten or accidentally deleted by the automated scraper process. This ensures that carefully curated content is preserved while still allowing the system to clean up expired scraped content.

## How It Works

### Source Field
Each webinar now has a `source` field that can be:
- `"scraped"` - Added by automated scrapers (default for new entries)
- `"manual"` - Added manually by administrators

### Protection Mechanisms

1. **Scraper Protection**: When scrapers run, they will skip updating any webinar marked as `source: "manual"`
2. **Cleanup Protection**: The cleanup process is more conservative with manually added webinars:
   - Manually added webinars with past live dates are still removed (as they're truly expired)
   - Manually added webinars without clear dates or with old `date_added` are protected from removal
   - Detailed logging shows which webinars are being protected

## Usage

### Marking Webinars as Manual

Use the `mark_manual_webinars.py` utility script:

```bash
# Mark a specific webinar by ID
python mark_manual_webinars.py --id "webinar-id-here"

# Mark webinars by title pattern
python mark_manual_webinars.py --title "pattern"

# Mark all webinars from a specific provider
python mark_manual_webinars.py --provider "Provider Name"

# List all manually added webinars
python mark_manual_webinars.py --list

# Show statistics
python mark_manual_webinars.py --stats

# Dry run to see what would be changed
python mark_manual_webinars.py --title "pattern" --dry-run
```

### Examples

```bash
# Mark a specific FDA webinar as manual
python mark_manual_webinars.py --id "fda-cder-advancing-transparency-and-regulatory-science-activities-on-the-risk-evaluation-and-mitigation-strategy-rems"

# Mark all USP webinars as manual
python mark_manual_webinars.py --provider "USP"

# Mark webinars with "training" in the title as manual
python mark_manual_webinars.py --title "training"

# See what would be marked without making changes
python mark_manual_webinars.py --provider "PMI" --dry-run
```

### Adding New Manual Webinars

When adding webinars through the admin panel or directly editing the JSON file, ensure you set:

```json
{
  "id": "unique-webinar-id",
  "title": "Webinar Title",
  "provider": "Provider Name",
  "source": "manual",
  "date_added": "2025-01-15",
  // ... other fields
}
```

## Monitoring and Logging

### Scraper Logs
When scrapers run, you'll see messages like:
```
Skipping update of manually added webinar: Webinar Title
```

### Cleanup Logs
During cleanup, you'll see detailed information:
```
PROTECTED: Manually added webinar 'Webinar Title' is old but will be kept
Removing manually added webinar with past live date: Webinar Title (live_date: 2024-12-01)
```

### Statistics
The cleanup process now reports:
```
Manually added webinars:
  - Protected: 15
  - Removed (past live dates): 2
```

## Migration from Legacy Data

For existing webinars without a `source` field:
- The system automatically assigns `source: "scraped"` to legacy entries
- You can then manually mark specific entries as `"manual"` using the utility script

## Best Practices

1. **Mark Important Content**: Use the manual marking for:
   - High-quality, carefully vetted webinars
   - Content from trusted sources that might not be scraped
   - Webinars with special requirements or notes

2. **Regular Review**: Periodically review manually added webinars to ensure they're still relevant

3. **Use Dry Runs**: Always use `--dry-run` first when marking multiple webinars to verify the selection

4. **Document Decisions**: Keep notes on why certain webinars were marked as manual

## Troubleshooting

### Webinar Still Getting Updated
- Check that the `source` field is exactly `"manual"` (case sensitive)
- Verify the webinar ID matches exactly

### Webinar Still Getting Removed
- Manually added webinars with past live dates will still be removed
- Check the cleanup logs for the specific reason
- Consider updating the `live_date` field if the webinar is still relevant

### Legacy Data Issues
- Run the scraper once to ensure all legacy entries get the `source` field
- Use `--stats` to see the current state of your data

## Technical Details

### File Changes
- `scrapers/base_scraper.py` - Added protection logic in `add_webinar()`
- `cleanup_expired_webinars.py` - Enhanced cleanup with manual webinar protection
- `scrapers/run_all_scrapers.py` - Added source field migration for legacy data
- `mark_manual_webinars.py` - New utility script for managing manual webinars

### Data Structure
```json
{
  "webinars": [
    {
      "id": "webinar-id",
      "title": "Webinar Title",
      "provider": "Provider",
      "source": "manual",  // or "scraped"
      "date_added": "2025-01-15",
      // ... other fields
    }
  ]
}
```

This protection system ensures that your manually curated content is preserved while maintaining the automated benefits of the scraper system. 