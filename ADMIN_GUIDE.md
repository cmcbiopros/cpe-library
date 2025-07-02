# CPE Webinar Directory - Admin Guide

This guide explains how to use the admin functionality to manage webinars in the CPE Directory.

## Overview

The admin functionality allows you to:
- **Add** new webinars
- **Edit** existing webinars
- **Delete** webinars
- **Export** updated data
- **View** comprehensive statistics

## Accessing Admin Features

### 1. Main Directory Page (`index.html`)
- **Clean Interface**: Focused on browsing and viewing webinars
- **View Links**: Each webinar has "View" and "Copy Link" buttons
- **Admin Access**: Discreet "Admin" link in the top-right corner

### 2. Admin Panel (`admin-panel.html`)
- **Add New Webinar**: Modal form for adding new webinars
- **Statistics**: View counts of total, live, on-demand, and certificate webinars
- **Search & Filter**: Find specific webinars by title, provider, format, or certificate status
- **Bulk Management**: Edit, delete, or view details for any webinar
- **Export Changes**: Download only modified data (highlighted when changes are made)
- **Export All Data**: Download the complete dataset
- **Refresh Data**: Reload from the original JSON file
- **Clear Changes**: Reset to original data

## How to Update the JSON File

Since this is a static frontend, here's the workflow to update the `webinars.json` file:

### Option 1: Using Export Changes (Recommended)
1. Go to the Admin Panel (click "Admin" in top-right corner)
2. Make your changes (add, edit, delete webinars)
3. The "Export Changes" button will become active (green) when changes are detected
4. Click "Export Changes" to download the updated data
5. Replace the existing `src/webinars.json` with the downloaded file
6. Commit and push the changes

### Option 2: Using Export All Data
1. Go to the Admin Panel
2. Click "Export All Data" to download the complete dataset
3. Replace the existing `src/webinars.json` with the downloaded file
4. Commit and push the changes

## Data Structure

Each webinar has the following structure:
```json
{
  "id": "unique-identifier",
  "title": "Webinar Title",
  "provider": "Provider Name",
  "topics": ["topic1", "topic2"],
  "format": "on-demand|live",
  "duration_min": 60,
  "certificate_available": true,
  "certificate_process": "Description of certificate process",
  "date_added": "YYYY-MM-DD",
  "url": "https://webinar-url.com",
  "description": "Webinar description",
  "live_date": "YYYY-MM-DD|on-demand"
}
```

## Best Practices

1. **Backup**: Always backup the original `webinars.json` before making changes
2. **Test**: Test changes locally before deploying
3. **Validate**: Ensure all required fields are filled when adding new webinars
4. **Consistent IDs**: Use consistent ID generation (provider-title format)
5. **Topics**: Use kebab-case for topics (e.g., "cell-therapy", "drug-development")
6. **Use Admin Panel**: All admin functions are centralized in the admin panel for better organization
7. **Clean Interface**: Main directory page is kept clean for browsing, admin functions are separate

## Troubleshooting

### Changes Not Appearing
- Check if you exported the data after making changes
- Ensure you replaced the correct `webinars.json` file
- Clear browser cache if needed
- Verify the "Export Changes" button is active (green) before exporting

### Form Not Working
- Ensure all required fields are filled
- Check browser console for JavaScript errors
- Verify the JSON file is accessible

### Export Issues
- Check browser permissions for file downloads
- Ensure you have sufficient disk space
- Try refreshing the page and exporting again
- Make sure you have made changes before trying to export changes

## Security Notes

- This is a client-side application with no server-side validation
- Always validate exported JSON before replacing the original file
- Consider implementing server-side validation for production use
- The admin functionality is accessible to anyone who can access the files

## Future Enhancements

Potential improvements for the admin system:
- Server-side API for real-time updates
- User authentication and authorization
- Audit trail for changes
- Bulk import/export functionality
- Advanced search and filtering
- Image upload for webinar thumbnails
- Email notifications for new webinars 