# CPE Webinar Directory

A searchable and filterable directory of continuing education webinars for QA, regulatory, bioprocess, biotech, and life sciences professionals.

## Features

- 🔍 **Search & Filter**: Find webinars by title, topics, provider, or format
- 📜 **Certificate Guarantee**: Only includes webinars with verified certificates
- 📱 **Mobile Responsive**: Works on all devices
- 🔄 **Automated Updates**: Scrapers keep the directory fresh
- 💰 **Free Hosting**: Deployed on GitHub Pages

## Data Model

Each webinar includes:
- `id`: Unique identifier (slug)
- `title`: Webinar title
- `provider`: Source organization
- `topics`: Array of relevant topics
- `format`: live/on-demand
- `duration_min`: Length in minutes
- `certificate_available`: Boolean
- `certificate_process`: How to obtain certificate
- `date_added`: When added to directory
- `url`: Direct link to webinar
- `description`: Brief description

## Project Structure

```
├── webinars.json             # Master webinar database
├── index.html                # Main interface
├── styles.css                # Styling
├── script.js                 # Search & filter logic
├── admin-panel.html          # Admin interface
├── scrapers/
│   ├── run_all_scrapers.py   # Main scraper runner
│   ├── base_scraper.py       # Common scraper utilities
│   └── providers/            # Individual provider scrapers
│       ├── labroots_scraper.py
│       ├── fda_cder_scraper.py
│       ├── xtalks_scraper.py
│       ├── ispe_scraper.py
│       ├── technology_networks_scraper.py
│       ├── pmi_scraper.py
│       └── usp_scraper.py
├── cleanup_expired_webinars.py # Data cleanup utility
├── run_cleanup.py            # Simple cleanup runner
└── requirements.txt          # Python dependencies
```

## Quick Start

1. **Manual Entry**: Add webinars to `data/webinars.json`
2. **View Directory**: Open `index.html` in browser
3. **Automated Updates**: Scrapers run via GitHub Actions

## Certificate Validation Rules

Only include webinars that explicitly mention:
- Certificate of completion
- CE credit availability
- Email with attendee name and duration

## Providers

- **Labroots**: Broad life-science catalog
- **FDA CDER**: Regulatory & QA topics  
- **Xtalks**: Life sciences webinars
- **ISPE**: Pharmaceutical engineering
- **Technology Networks**: Cell & gene therapy
- **PMI**: Project management
- **USP**: Pharmaceutical standards

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run scrapers locally
python scrapers/run_all_scrapers.py

# Run cleanup to remove expired webinars
python cleanup_expired_webinars.py --dry-run  # Preview what would be removed
python cleanup_expired_webinars.py            # Actually remove expired webinars

# Test locally
python -m http.server 8000
# Open http://localhost:8000/
```

## Data Cleanup

The system includes automatic cleanup functionality to keep the database lean:

### Automatic Cleanup
- Runs automatically after each scraping session
- Removes webinars with past live dates
- Removes on-demand webinars older than 1 year (365 days)
- Removes entries with invalid date formats

### Manual Cleanup
```bash
# Preview what would be removed (dry run)
python cleanup_expired_webinars.py --dry-run

# Remove expired webinars with custom age threshold
python cleanup_expired_webinars.py --max-age-days 90

# Clean up specific file
python cleanup_expired_webinars.py --data-file path/to/webinars.json
```

### Cleanup Criteria
- **Past Live Dates**: Any webinar with a `live_date` in the past
- **Old On-Demand**: On-demand webinars older than specified days (default: 365 days / 1 year)
- **Invalid Dates**: Entries with malformed date formats
- **Unknown Dates**: Webinars with unknown live dates older than threshold

## Deployment

The directory is automatically deployed to GitHub Pages when `webinars.json` is updated. 