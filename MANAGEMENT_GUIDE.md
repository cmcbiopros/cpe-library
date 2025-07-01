# CPE Webinar Directory - Management Guide

## 🎯 **Overview**

This guide explains how to manage and maintain your CPE webinar directory. The system automatically scrapes webinars from multiple providers and presents them in a searchable, filterable interface.

## 📊 **How It Works**

### **Data Flow**
```
Scrapers → JSON File → Web Interface → GitHub Pages
    ↓           ↓           ↓              ↓
Daily Run → Update Data → User Search → Live Site
```

### **Key Components**

1. **Scrapers** (`scrapers/base_scraper.py`)
   - Automatically fetch webinars from provider websites
   - Validate certificate availability
   - Prevent duplicates
   - Normalize data format

2. **Data Storage** (`data/webinars.json`)
   - Single source of truth for all webinar data
   - JSON format for easy reading and editing
   - Includes metadata (last updated, total count)

3. **Web Interface** (`src/`)
   - Search and filter functionality
   - Mobile-responsive design
   - Direct links to webinars

4. **Automation** (`.github/workflows/`)
   - Daily scraping at 2 AM UTC
   - Automatic deployment to GitHub Pages
   - Error reporting via GitHub Issues

## 🛠 **Daily Management Tasks**

### **1. Monitor Automated Updates**
- **Where**: GitHub Actions tab in your repository
- **What to check**: 
  - Scrapers ran successfully (green checkmarks)
  - New webinars were added
  - No errors occurred

### **2. Review New Webinars**
- **Frequency**: Weekly
- **Process**:
  1. Check `data/webinars.json` for new entries
  2. Verify certificate information is accurate
  3. Test a few random webinar links
  4. Update certificate process descriptions if needed

### **3. Handle Scraper Failures**
- **Signs**: GitHub Issues with "scraper-failure" label
- **Actions**:
  1. Check the scraper code for website changes
  2. Update selectors/URLs if needed
  3. Test locally before committing
  4. Close the issue when resolved

## 📝 **Manual Webinar Management**

### **Adding Webinars Manually**

1. **Via Admin Form**:
   - Go to `src/admin.html`
   - Fill out the form with webinar details
   - Submit to add immediately

2. **Via JSON File**:
   - Edit `data/webinars.json` directly
   - Follow the existing format
   - Ensure `certificate_available: true`

### **Webinar Data Format**
```json
{
  "id": "provider-title-slug",
  "title": "Webinar Title",
  "provider": "Provider Name",
  "topics": ["topic1", "topic2"],
  "format": "on-demand",
  "duration_min": 60,
  "certificate_available": true,
  "certificate_process": "Auto-issued after quiz",
  "date_added": "2025-01-15",
  "url": "https://webinar-url.com",
  "description": "Brief description"
}
```

### **Certificate Validation Rules**
Only include webinars that explicitly mention:
- ✅ Certificate of completion
- ✅ CE credit availability
- ✅ Professional development credit
- ✅ Email with attendee name and duration

**Do NOT include** webinars that only mention:
- ❌ "Certificate of attendance" (without completion requirements)
- ❌ "Participation certificate" (without educational value)
- ❌ No certificate information

## 🔧 **Technical Maintenance**

### **Adding New Providers**

1. **Create New Scraper Class**:
```python
class NewProviderScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://provider.com"
        self.webinars_url = "https://provider.com/webinars"
    
    def scrape(self):
        # Implementation here
        pass
```

2. **Add to Scraper List**:
```python
scrapers = [
    # ... existing scrapers
    NewProviderScraper()
]
```

3. **Test Locally**:
```bash
cd scrapers
python base_scraper.py
```

### **Updating Existing Scrapers**

**Common Issues & Solutions**:

1. **Website Structure Changed**:
   - Update CSS selectors in scraper
   - Test with new HTML structure
   - Verify data extraction still works

2. **New URL Patterns**:
   - Update regex patterns
   - Add new URL variations
   - Test link generation

3. **Certificate Process Changed**:
   - Update `check_certificate_availability()` method
   - Add new certificate indicators
   - Test with sample content

### **Performance Optimization**

1. **Reduce Scraping Frequency**:
   - Edit `.github/workflows/update-webinars.yml`
   - Change cron schedule (e.g., `0 2 * * 1` for weekly)
   - Consider provider-specific schedules

2. **Filter Irrelevant Content**:
   - Update `_is_relevant_event()` methods
   - Add more specific keywords
   - Exclude non-webinar content

## 📈 **Analytics & Monitoring**

### **Key Metrics to Track**

1. **Total Webinars**: Check `total_count` in JSON
2. **New Additions**: Compare daily/weekly counts
3. **Provider Distribution**: Count by provider
4. **Certificate Coverage**: Percentage with certificates
5. **Link Health**: Monitor broken links

### **Quality Assurance**

**Weekly Checklist**:
- [ ] All new webinars have certificates
- [ ] Links are working
- [ ] Descriptions are accurate
- [ ] Topics are properly tagged
- [ ] No duplicate entries

**Monthly Review**:
- [ ] Remove outdated webinars
- [ ] Update certificate processes
- [ ] Review scraper performance
- [ ] Add new relevant providers

## 🚀 **Deployment & Updates**

### **Local Testing**
```bash
# Install dependencies
pip install -r requirements.txt

# Test scrapers
cd scrapers
python base_scraper.py

# Test web interface
cd src
python -m http.server 8000
# Open http://localhost:8000
```

### **Production Deployment**
1. **Push to GitHub**: Changes auto-deploy to GitHub Pages
2. **Verify Deployment**: Check GitHub Pages settings
3. **Test Live Site**: Ensure all features work
4. **Monitor Logs**: Watch for any errors

### **Rollback Process**
1. **Revert Last Commit**: If issues occur
2. **Restore Previous JSON**: If data corruption
3. **Disable Automation**: Temporarily stop GitHub Actions
4. **Manual Recovery**: Add webinars manually if needed

## 🆘 **Troubleshooting**

### **Common Issues**

1. **Scrapers Not Running**:
   - Check GitHub Actions permissions
   - Verify Python dependencies
   - Review error logs

2. **No New Webinars**:
   - Check if websites changed structure
   - Verify URLs are still valid
   - Test scrapers locally

3. **Broken Links**:
   - Update scraper URL patterns
   - Check provider website changes
   - Remove outdated entries

4. **Certificate Validation Issues**:
   - Review certificate indicators
   - Update validation logic
   - Check provider policy changes

### **Getting Help**

1. **Check GitHub Issues**: Look for similar problems
2. **Review Scraper Logs**: Look for specific error messages
3. **Test Manually**: Try accessing provider websites directly
4. **Update Documentation**: Document any new procedures

## 📞 **Support Contacts**

- **GitHub Issues**: For technical problems
- **Provider Websites**: For content questions
- **Documentation**: This guide and README.md

---

**Remember**: The goal is to maintain a high-quality, reliable directory of webinars with guaranteed certificates. Quality over quantity! 