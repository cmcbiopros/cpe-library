import json
import os
import re
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from slugify import slugify
import requests
from bs4 import BeautifulSoup


class BaseScraper:
    """Base class for all webinar scrapers"""
    
    def __init__(self, data_file: str = "../webinars.json"):
        self.data_file = data_file
        self.webinars = []
        self.load_existing_data()
    
    def load_existing_data(self):
        """Load existing webinar data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.webinars = data.get('webinars', [])
            else:
                self.webinars = []
        except Exception as e:
            print(f"Error loading existing data: {e}")
            self.webinars = []
    
    def save_data(self):
        """Save webinar data to JSON file"""
        data = {
            'webinars': self.webinars,
            'last_updated': datetime.now().isoformat(),
            'total_count': len(self.webinars)
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(self.webinars)} webinars to {self.data_file}")
    
    def generate_id(self, title: str, provider: str, date: str = None) -> str:
        """Generate a unique ID for a webinar"""
        base = slugify(f"{provider}-{title}")
        if date:
            base = f"{base}-{date}"
        return base
    
    def extract_duration(self, text: str) -> int:
        """Extract duration in minutes from text"""
        if not text:
            return 60  # Default duration
        
        # Look for patterns like "60 minutes", "1 hour", "90 min", etc.
        patterns = [
            r'(\d+)\s*minutes?',
            r'(\d+)\s*min',
            r'(\d+)\s*hours?',
            r'(\d+)\s*hr',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                minutes = int(match.group(1))
                if 'hour' in pattern or 'hr' in pattern:
                    minutes *= 60
                return minutes
        
        return 60  # Default duration
    
    def check_certificate_availability(self, text: str) -> tuple[bool, str]:
        """Check if certificate is available and extract process info"""
        if not text:
            return False, ""
        
        text_lower = text.lower()
        
        # Certificate indicators
        certificate_indicators = [
            'certificate of completion',
            'ce certificate',
            'continuing education certificate',
            'certificate available',
            'certificate provided',
            'earn a certificate',
            'receive a certificate',
            'ce credit',
            'continuing education credit',
            'professional development credit'
        ]
        
        # Process indicators
        process_indicators = [
            'after quiz',
            'post-test',
            'completion survey',
            'attendance verification',
            'email certificate',
            'auto-issued',
            'upon completion',
            'after webinar',
            'following completion'
        ]
        
        has_certificate = any(indicator in text_lower for indicator in certificate_indicators)
        
        # Extract process information
        process_info = ""
        for indicator in process_indicators:
            if indicator in text_lower:
                # Find the sentence containing the indicator
                sentences = re.split(r'[.!?]', text)
                for sentence in sentences:
                    if indicator in sentence.lower():
                        process_info = sentence.strip()
                        break
                if process_info:
                    break
        
        if has_certificate and not process_info:
            process_info = "Certificate available upon completion"
        
        return has_certificate, process_info
    
    def normalize_topics(self, topics: List[str]) -> List[str]:
        """Normalize topic tags"""
        normalized = []
        topic_mapping = {
            'cell therapy': 'cell-therapy',
            'gene therapy': 'gene-therapy',
            'quality assurance': 'quality-assurance',
            'quality management': 'quality-management',
            'regulatory affairs': 'regulatory',
            'bioprocessing': 'bioprocess',
            'biotechnology': 'biotech',
            'life sciences': 'life-sciences',
            'clinical trials': 'clinical-trials',
            'manufacturing': 'manufacturing',
            'compliance': 'compliance',
            'validation': 'validation',
            'gmp': 'gmp',
            'fda': 'regulatory',
            'ema': 'regulatory',
            'drug discovery': 'drug-discovery',
            'pharmaceutical': 'pharmaceutical',
            'biopharmaceutical': 'biopharmaceutical',
            'project management': 'project-management',
            'laboratory management': 'laboratory-management',
            'research': 'research',
            'development': 'development',
            'clinical research': 'clinical-research',
            'monitoring': 'monitoring',
            'data management': 'data-management',
            'process validation': 'process-validation',
            'cell culture': 'cell-culture',
            'flow cytometry': 'flow-cytometry',
            'pcr': 'pcr',
            'western blotting': 'western-blotting',
            'microbiology': 'microbiology',
            'chemistry': 'chemistry',
            'materials science': 'materials-science'
        }
        
        for topic in topics:
            topic_lower = topic.lower().strip()
            normalized_topic = topic_mapping.get(topic_lower, topic_lower)
            if normalized_topic not in normalized:
                normalized.append(normalized_topic)
        
        return normalized
    
    def _is_valid_webinar(self, title: str, url: str) -> bool:
        """Check if a link represents a valid webinar"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        # Skip common non-webinar content
        skip_keywords = [
            'submit proposal', 'submit proposals', 'call for proposals', 'call for papers',
            'proposal submission', 'submission form', 'application form', 'registration form',
            'sign up', 'signup', 'login', 'log in', 'register', 'registration',
            'contact us', 'about us', 'about', 'home', 'main', 'index',
            'faq', 'frequently asked questions', 'help', 'support',
            'privacy policy', 'terms of service', 'terms and conditions',
            'webinar faq', 'webinar faqs', 'webinar information', 'webinar info',
            'webinar series', 'webinar library', 'webinar archive', 'webinar catalog',
            'all webinars', 'browse webinars', 'find webinars', 'search webinars',
            'upcoming webinars', 'past webinars', 'recorded webinars',
            'webinar schedule', 'webinar calendar', 'webinar events'
        ]
        
        # Check for skip keywords in title
        for keyword in skip_keywords:
            if keyword in title_lower:
                return False
        
        # Skip URLs that are clearly not individual webinars
        skip_url_patterns = [
            '/events/', '/education/',
            '/learning/', '/training/', '/resources/', '/library/',
            '/archive/', '/catalog/', '/browse/', '/search/',
            '/submit/', '/proposal/', '/application/', '/registration/',
            '/contact/', '/about/', '/help/', '/support/',
            '/faq/', '/terms/', '/privacy/'
        ]
        
        # Special handling for webinar URLs - only skip if they're clearly topic pages
        if '/webinar/' in url_lower or '/webinars/' in url_lower:
            # If it's a webinar URL but title doesn't look like a specific webinar, skip
            if not self._looks_like_specific_webinar(title):
                return False
        
        # If URL contains other generic patterns but title doesn't look like a specific webinar, skip
        has_generic_url = any(pattern in url_lower for pattern in skip_url_patterns)
        if has_generic_url and not self._looks_like_specific_webinar(title):
            return False
        
        # For Xtalks specifically, if it's from the on-demand page, it's likely valid
        # Remove the educational keywords requirement since Xtalks content is curated
        return True
    
    def _looks_like_specific_webinar(self, title: str) -> bool:
        """Check if title looks like a specific webinar rather than a general page"""
        title_lower = title.lower()
        
        # Specific webinar indicators
        specific_indicators = [
            'webinar:', 'presentation:', 'lecture:', 'session:',
            'overview of', 'introduction to', 'advanced', 'fundamentals of',
            'best practices for', 'guidelines for', 'standards for',
            'regulations for', 'manufacturing', 'quality', 'regulatory',
            'clinical', 'biotechnology', 'pharmaceutical', 'cell therapy',
            'gene therapy', 'crispr', 'gmp', 'fda', 'ich', 'validation'
        ]
        
        return any(indicator in title_lower for indicator in specific_indicators)
    
    def get_headers(self) -> Dict[str, str]:
        """Get realistic browser headers to avoid blocking"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def make_request(self, url: str, timeout: int = 30) -> Optional[requests.Response]:
        """Make a request with proper headers and delays"""
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            headers = self.get_headers()
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def add_webinar(self, webinar_data: Dict[str, Any]) -> bool:
        """Add or update a webinar in the database by id"""
        # Check if webinar already exists
        existing_ids = [w['id'] for w in self.webinars]
        if webinar_data['id'] in existing_ids:
            # Update the existing entry, but preserve the original date_added
            idx = existing_ids.index(webinar_data['id'])
            existing_webinar = self.webinars[idx]
            
            # PROTECTION: If existing webinar was manually added, don't overwrite it
            if existing_webinar.get('source') == 'manual':
                print(f"  Skipping update of manually added webinar: {webinar_data['title']}")
                return False
            
            # Preserve the original date_added unless it's missing
            if 'date_added' in existing_webinar and existing_webinar['date_added']:
                webinar_data['date_added'] = existing_webinar['date_added']
            
            # Preserve the original source if it exists
            if 'source' in existing_webinar:
                webinar_data['source'] = existing_webinar['source']
            
            self.webinars[idx] = webinar_data
            return True
        
        # Validate required fields
        required_fields = ['id', 'title', 'provider', 'url']
        for field in required_fields:
            if field not in webinar_data or not webinar_data[field]:
                print(f"Missing required field: {field}")
                return False
        
        # Ensure certificate_available is present (can be True or False)
        if 'certificate_available' not in webinar_data:
            webinar_data['certificate_available'] = False
        
        # Set default values
        if 'date_added' not in webinar_data:
            webinar_data['date_added'] = datetime.now().strftime('%Y-%m-%d')
        
        if 'topics' not in webinar_data:
            webinar_data['topics'] = []
        
        if 'format' not in webinar_data:
            webinar_data['format'] = 'on-demand'
        
        if 'duration_min' not in webinar_data:
            webinar_data['duration_min'] = 60
        
        # Add live_date field - either the actual date for live webinars or "on-demand"
        if 'live_date' not in webinar_data:
            if webinar_data.get('format') == 'live' and webinar_data.get('webinar_date'):
                webinar_data['live_date'] = webinar_data['webinar_date']
            else:
                webinar_data['live_date'] = 'on-demand'
        
        # Set source field for new webinars (scraped by default)
        if 'source' not in webinar_data:
            webinar_data['source'] = 'scraped'
        
        self.webinars.append(webinar_data)
        return True
    
    def scrape(self):
        """Main scraping method - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement scrape() method")
    
    def run(self):
        """Run the scraper and save results"""
        print(f"Starting {self.__class__.__name__}...")
        initial_count = len(self.webinars)
        
        try:
            self.scrape()
            new_count = len(self.webinars)
            added_count = new_count - initial_count
            
            print(f"Added {added_count} new webinars")
            self.save_data()
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            raise 