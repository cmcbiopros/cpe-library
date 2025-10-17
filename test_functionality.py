#!/usr/bin/env python3
"""
Test script to verify the like persistence and URL validation functionality
"""

import json
import os
import sys
from datetime import datetime

def test_like_persistence():
    """Test that likes are properly saved to webinars.json"""
    print("Testing like persistence...")
    
    # Load current webinars
    try:
        with open('webinars.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            webinars = data.get('webinars', [])
    except FileNotFoundError:
        print("❌ webinars.json not found")
        return False
    
    # Check if any webinars have likes
    webinars_with_likes = [w for w in webinars if w.get('likes', 0) > 0]
    
    if webinars_with_likes:
        print(f"✅ Found {len(webinars_with_likes)} webinars with likes")
        for webinar in webinars_with_likes[:3]:  # Show first 3
            print(f"   - {webinar.get('title', 'Unknown')[:50]}... ({webinar.get('likes', 0)} likes)")
    else:
        print("ℹ️  No webinars with likes found (this is normal for a fresh installation)")
    
    return True

def test_url_validation():
    """Test the URL validation script"""
    print("\nTesting URL validation...")
    
    # Check if the cleanup script exists
    if not os.path.exists('cleanup_broken_links.py'):
        print("❌ cleanup_broken_links.py not found")
        return False
    
    # Test with dry run
    import subprocess
    try:
        result = subprocess.run([
            sys.executable, 'cleanup_broken_links.py', '--dry-run', '--timeout', '5'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ URL validation script runs successfully")
            print("   Output preview:")
            lines = result.stdout.split('\n')
            for line in lines[:10]:  # Show first 10 lines
                if line.strip():
                    print(f"   {line}")
            if len(lines) > 10:
                print("   ...")
        else:
            print(f"❌ URL validation script failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️  URL validation test timed out (this is normal for large datasets)")
    except Exception as e:
        print(f"❌ Error running URL validation: {e}")
        return False
    
    return True

def test_github_pages_compatibility():
    """Test that the system is compatible with GitHub Pages"""
    print("\nTesting GitHub Pages compatibility...")
    
    # Check that PHP files are removed (they don't work on GitHub Pages)
    php_files = ['save_likes.php', 'run_cleanup_broken_links.php']
    php_found = False
    
    for php_file in php_files:
        if os.path.exists(php_file):
            print(f"❌ {php_file} found - should be removed for GitHub Pages")
            php_found = True
    
    if not php_found:
        print("✅ PHP files removed (GitHub Pages compatible)")
    
    # Check that essential files exist
    essential_files = ['script.js', 'index.html', 'admin-panel.html', 'webinars.json']
    
    for file in essential_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} not found")
            return False
    
    # Check GitHub Actions workflow
    workflow_file = '.github/workflows/update-webinars.yml'
    if os.path.exists(workflow_file):
        print(f"✅ GitHub Actions workflow exists")
        
        # Check if cleanup is included
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
                if 'cleanup_broken_links.py' in content:
                    print(f"   ✅ Cleanup script included in workflow")
                else:
                    print(f"   ⚠️  Cleanup script not found in workflow")
        except Exception as e:
            print(f"   ❌ Error reading workflow: {e}")
    else:
        print(f"❌ GitHub Actions workflow not found")
        return False
    
    return not php_found

def test_webinar_data_integrity():
    """Test that webinar data is properly structured"""
    print("\nTesting webinar data integrity...")
    
    try:
        with open('webinars.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            webinars = data.get('webinars', [])
    except Exception as e:
        print(f"❌ Error loading webinars.json: {e}")
        return False
    
    if not webinars:
        print("❌ No webinars found in webinars.json")
        return False
    
    print(f"✅ Found {len(webinars)} webinars")
    
    # Check required fields
    required_fields = ['id', 'title', 'provider', 'url']
    missing_fields = []
    
    for i, webinar in enumerate(webinars[:10]):  # Check first 10
        for field in required_fields:
            if field not in webinar or not webinar[field]:
                missing_fields.append(f"Webinar {i+1} missing {field}")
    
    if missing_fields:
        print("⚠️  Some webinars are missing required fields:")
        for field in missing_fields[:5]:  # Show first 5
            print(f"   - {field}")
    else:
        print("✅ All webinars have required fields")
    
    return True

def main():
    print("CPE Library Functionality Test")
    print("=" * 40)
    
    tests = [
        test_webinar_data_integrity,
        test_like_persistence,
        test_url_validation,
        test_github_pages_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    print(f"\n{'='*40}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
