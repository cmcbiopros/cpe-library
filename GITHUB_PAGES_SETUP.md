# GitHub Pages Setup - CPE Library

This document explains how the CPE Library works on GitHub Pages and how to maintain it.

## 🚀 **How It Works on GitHub Pages**

### ✅ **What Works**
- **Like System**: Likes are stored in browser localStorage and persist across sessions
- **Export/Import**: Users can export and import like data via JSON files
- **Broken Link Cleanup**: Automated via GitHub Actions (runs weekly)
- **All Core Features**: Search, filtering, admin panel, etc.

### ❌ **What Doesn't Work**
- **Server-side Like Persistence**: Likes are local to each user's browser
- **Real-time Updates**: Changes require page refresh

## 🔧 **Maintenance**

### **Automatic (GitHub Actions)**
- **Weekly Scraping**: Every Sunday at 2 AM UTC
- **Broken Link Cleanup**: Runs after scraping
- **Data Updates**: Automatically committed to repository

### **Manual Tasks**
1. **Export Like Data**: Use admin panel to export likes periodically
2. **Share Like Data**: Distribute exported like files to users
3. **Monitor Issues**: Check GitHub Issues for scraper failures

## 📊 **Like System Management**

### **For Users**
- Likes are automatically saved to your browser
- Use "Export Likes" to backup your like data
- Use "Import Likes" to restore like data

### **For Administrators**
1. **Export Global Likes**: Use admin panel to export all like data
2. **Share with Community**: Post exported like files for others to import
3. **Backup Regularly**: Export like data before major updates

## 🛠️ **Manual Cleanup (If Needed)**

If you need to manually run cleanup:

```bash
# Clone the repository
git clone https://github.com/yourusername/cpe-library.git
cd cpe-library

# Install dependencies
pip install -r requirements.txt

# Run cleanup
python cleanup_broken_links.py --backup --dry-run  # Preview
python cleanup_broken_links.py --backup            # Actual cleanup

# Commit and push changes
git add webinars.json
git commit -m "Manual cleanup of broken links"
git push
```

## 🔄 **Workflow**

### **Weekly Automation**
1. GitHub Actions runs scrapers
2. Cleanup script removes broken links
3. Updated data is committed to repository
4. GitHub Pages automatically updates

### **User Experience**
1. Users visit the site
2. Likes are loaded from localStorage
3. Users can export/import like data
4. All features work normally

## 📈 **Benefits of This Approach**

1. **No Server Costs**: Runs entirely on GitHub Pages
2. **Automatic Updates**: Weekly data refresh
3. **User Control**: Users can manage their own like data
4. **Community Sharing**: Like data can be shared between users
5. **Reliable**: GitHub's infrastructure handles hosting

## 🚨 **Important Notes**

- **Like Data is Local**: Each user's likes are stored in their browser
- **Export Regularly**: Users should export their like data periodically
- **Share Data**: Administrators can share like data with the community
- **Backup Important**: Always backup before major changes

## 🎯 **Getting Started**

1. **Push Changes**: Your changes are already pushed to GitHub
2. **Wait for Deployment**: GitHub Pages will update automatically
3. **Test Features**: Visit your site and test the like system
4. **Export Likes**: Use the admin panel to export like data

## 📞 **Support**

- **GitHub Issues**: Report problems via GitHub Issues
- **Documentation**: Check this file and README.md
- **Community**: Share like data files with other users

---

The system is now fully compatible with GitHub Pages and will work reliably with automatic updates!
