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
├── data/
│   └── webinars.json          # Master webinar database
├── scrapers/
│   ├── labroots.py           # Labroots scraper
│   ├── fda_cder.py           # FDA CDER scraper
│   └── base_scraper.py       # Common scraper utilities
├── src/
│   ├── index.html            # Main interface
│   ├── styles.css            # Styling
│   └── script.js             # Search & filter logic
├── .github/
│   └── workflows/
│       └── update-webinars.yml # Automated scraping
└── requirements.txt          # Python dependencies
```

## Quick Start

1. **Manual Entry**: Add webinars to `data/webinars.json`
2. **View Directory**: Open `src/index.html` in browser
3. **Automated Updates**: Scrapers run via GitHub Actions

## Certificate Validation Rules

Only include webinars that explicitly mention:
- Certificate of completion
- CE credit availability
- Email with attendee name and duration

## Providers

- **Labroots**: Broad life-science catalog
- **FDA CDER**: Regulatory & QA topics
- **ASGCT**: Cell & gene therapy
- **PELOBIOTECH**: Stem-cell & biotech methods

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run scrapers locally
python scrapers/labroots.py
python scrapers/fda_cder.py

# Test locally
python -m http.server 8000
# Open http://localhost:8000/src/
```

## Deployment

The directory is automatically deployed to GitHub Pages when `data/webinars.json` is updated. 