import json
import os
import re
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from slugify import slugify
import requests
from bs4 import BeautifulSoup


class BaseScraper:
    """Base class for all webinar scrapers"""
    
    def __init__(self, data_file: str = "../src/webinars.json"):
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
        """Add a webinar to the database if it doesn't exist"""
        # Check if webinar already exists
        existing_ids = [w['id'] for w in self.webinars]
        if webinar_data['id'] in existing_ids:
            return False
        
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


class LabrootsScraper(BaseScraper):
    """Scraper for Labroots webinars"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.labroots.com"
        self.api_url = "https://www.labroots.com/api/v1/events"
    
    def scrape(self):
        """Scrape Labroots webinars"""
        try:
            # Try the public events page instead of API
            events_url = "https://www.labroots.com/events"
            response = self.make_request(events_url)
            
            if not response:
                print("Failed to access Labroots events page")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for event links
            event_links = soup.find_all('a', href=re.compile(r'/event/'))
            
            for link in event_links:
                if self._is_relevant_event_link(link):
                    webinar_data = self._parse_event_link(link)
                    if webinar_data:
                        self.add_webinar(webinar_data)
        
        except Exception as e:
            print(f"Error scraping Labroots: {e}")
    
    def _is_relevant_event_link(self, link) -> bool:
        """Check if event link is relevant to our topics"""
        title = link.get_text(strip=True).lower()
        
        relevant_keywords = [
            'cell therapy', 'gene therapy', 'biotechnology', 'bioprocessing',
            'quality assurance', 'regulatory', 'manufacturing', 'clinical trials',
            'gmp', 'fda', 'compliance', 'validation', 'pharmaceutical',
            'biopharmaceutical', 'laboratory', 'research', 'development'
        ]
        
        return any(keyword in title for keyword in relevant_keywords)
    
    def _parse_event_link(self, link) -> Optional[Dict]:
        """Parse event link into webinar format"""
        try:
            title = link.get_text(strip=True)
            url = self.base_url + link.get('href', '') if link.get('href', '').startswith('/') else link.get('href', '')
            
            # Skip non-webinar content
            if not self._is_valid_webinar(title, url):
                return None
            
            # Check for certificate availability
            has_cert, process = self.check_certificate_availability(title)
            
            webinar_data = {
                'id': self.generate_id(title, 'Labroots'),
                'title': title,
                'provider': 'Labroots',
                'topics': self._extract_topics_from_title(title),
                'format': 'on-demand',
                'duration_min': 60,
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'url': url,
                'description': f"Labroots event: {title}"
            }
            
            return webinar_data
        
        except Exception as e:
            print(f"Error parsing event link: {e}")
            return None
    
    def _extract_topics_from_title(self, title: str) -> List[str]:
        """Extract topics from event title"""
        title_lower = title.lower()
        topics = []
        
        topic_keywords = {
            'cell therapy': 'cell-therapy',
            'gene therapy': 'gene-therapy',
            'biotechnology': 'biotech',
            'bioprocessing': 'bioprocess',
            'quality assurance': 'quality-assurance',
            'regulatory': 'regulatory',
            'manufacturing': 'manufacturing',
            'clinical trials': 'clinical-trials',
            'gmp': 'manufacturing',
            'fda': 'regulatory',
            'compliance': 'regulatory',
            'validation': 'validation',
            'pharmaceutical': 'pharmaceutical',
            'biopharmaceutical': 'biotech',
            'laboratory': 'laboratory',
            'research': 'research',
            'development': 'research'
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in title_lower:
                topics.append(topic)
        
        return topics
    
    def _is_relevant_event(self, event: Dict) -> bool:
        """Check if event is relevant to our topics"""
        relevant_keywords = [
            'cell therapy', 'gene therapy', 'biotechnology', 'bioprocessing',
            'quality assurance', 'regulatory', 'manufacturing', 'clinical trials',
            'gmp', 'fda', 'compliance', 'validation', 'pharmaceutical',
            'biopharmaceutical', 'laboratory', 'research', 'development'
        ]
        
        title = event.get('title', '').lower()
        description = event.get('description', '').lower()
        
        return any(keyword in title or keyword in description for keyword in relevant_keywords)
    
    def _parse_event(self, event: Dict) -> Optional[Dict]:
        """Parse event data into webinar format"""
        try:
            title = event.get('title', '')
            if not title:
                return None
            
            # Check for certificate availability
            description = event.get('description', '')
            has_cert, process = self.check_certificate_availability(description)
            
            # Include all webinars for now, even without certificates
            # TODO: Filter for certificates in production
            
            webinar_data = {
                'id': self.generate_id(title, 'Labroots'),
                'title': title,
                'provider': 'Labroots',
                'topics': self.normalize_topics(event.get('tags', [])),
                'format': 'on-demand' if event.get('is_on_demand') else 'live',
                'duration_min': self.extract_duration(description),
                'certificate_available': has_cert,
                'certificate_process': process,
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'url': f"{self.base_url}/event/{event.get('slug', '')}",
                'description': description[:200] + '...' if len(description) > 200 else description
            }
            
            return webinar_data
        
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None


class XtalksScraper(BaseScraper):
    """Scraper for Xtalks webinars"""
    
    def __init__(self):
        super().__init__(data_file="src/webinars.json")
        self.base_url = "https://xtalks.com"
        self.on_demand_url = "https://xtalks.com/?post_type=webinars&webinar-topics=&type=recorded-webinars&s="
        
        # Topic page keywords for filtering
        self.topic_page_keywords = [
            'host a webinar',
            'why host',
            'webinar topics',
            'webinar series',
            'webinar library',
            'webinar archive',
            'webinar catalog',
            'all webinars',
            'browse webinars',
            'find webinars',
            'search webinars'
        ]
    
    def scrape(self):
        """Scrape Xtalks on-demand webinars"""
        try:
            print("Scraping Xtalks on-demand webinars...")
            
            # Try multiple URLs to get more comprehensive results
            urls_to_scrape = [
                self.on_demand_url,  # Original URL
                "https://xtalks.com/?post_type=webinars&type=recorded-webinars",
                "https://xtalks.com/webinars/?type=recorded-webinars",
                "https://xtalks.com/webinars/"
            ]
            
            # Add pagination for the original URL
            for page in range(2, 6):  # Try pages 2-5
                urls_to_scrape.append(f"https://xtalks.com/?post_type=webinars&webinar-topics=&type=recorded-webinars&s=&paged={page}")
            
            total_webinars_found = 0
            
            for url in urls_to_scrape:
                print(f"Scraping: {url}")
                response = self.make_request(url)
                
                if not response:
                    print(f"Failed to access: {url}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for webinar date elements - these indicate individual webinar entries
                webinar_dates = soup.find_all(class_='webinar-date')
                print(f"Found {len(webinar_dates)} webinar date elements on this page")
                
                page_webinars = 0
                for date_elem in webinar_dates:
                    webinar_data = self._parse_webinar_from_date(date_elem)
                    if webinar_data:
                        self.add_webinar(webinar_data)
                        page_webinars += 1
                
                total_webinars_found += page_webinars
                print(f"Added {page_webinars} webinars from this page")
                
                # Also try to find direct webinar links as fallback
                webinar_links = soup.find_all('a', href=re.compile(r'/webinars/'))
                if webinar_links:
                    print(f"Found {len(webinar_links)} direct webinar links on this page")
                    
                    for link in webinar_links:
                        webinar_data = self._parse_webinar_link(link)
                        if webinar_data:
                            self.add_webinar(webinar_data)
            
            print(f"Total webinars found across all pages: {total_webinars_found}")
                    
        except Exception as e:
            print(f"Error scraping Xtalks: {e}")
    
    def _build_url(self, href: str) -> str:
        """Build full URL from href"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return 'https://xtalks.com' + href
        else:
            return 'https://xtalks.com/' + href
    
    def _clean_title(self, title: str) -> str:
        """Clean up webinar title"""
        if title.startswith('Webinar'):
            title = title[7:].strip()
        if 'On-Demand' in title:
            title = title.split('On-Demand')[0].strip()
        if 'This session' in title:
            title = title.split('This session')[0].strip()
        if 'In this webinar' in title:
            title = title.split('In this webinar')[0].strip()
        return title
    
    def _is_topic_page(self, title: str) -> bool:
        """Check if title represents a topic page"""
        title_lower = title.lower()
        
        # Check for topic page keywords
        if any(keyword in title_lower for keyword in self.topic_page_keywords):
            return True
        
        # Check for very short or generic titles
        if len(title) < 15 or title_lower in ['clinical trials', 'cell and gene therapy', 'pharma manufacturing']:
            return True
        
        return False
    
    def _parse_webinar_from_date(self, date_elem) -> Optional[Dict]:
        """Parse webinar information from a date element"""
        try:
            # Get the date from the date element
            date_text = date_elem.get_text(strip=True)
            
            # Parse the date (format: "June 30, 2025")
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(date_text, "%B %d, %Y")
                
                # Check if webinar is within last 6 months
                from datetime import timedelta
                six_months_ago = datetime.now() - timedelta(days=180)
                if parsed_date < six_months_ago:
                    return None  # Skip webinars older than 6 months
                    
            except ValueError:
                # If date parsing fails, skip this webinar
                return None
            
            # Find the parent element that contains both date and title
            parent = date_elem.parent
            
            # Look for the webinar title link
            title_link = parent.find('a')
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            href = title_link.get('href', '')
            
            # Build URL and clean title
            url = self._build_url(href)
            title = self._clean_title(title)
            
            # Apply filtering
            if not self._is_valid_webinar(title, url) or self._is_topic_page(title):
                return None
            
            # Only include actual individual webinars
            if not href or '/webinars/' not in href:
                return None
            
            # Extract description if available
            desc_elem = parent.find(['p', 'div'], class_=re.compile(r'description|summary|excerpt'))
            description = desc_elem.get_text(strip=True) if desc_elem else f"Xtalks on-demand webinar: {title}"
            
            # Check for certificate availability
            has_cert, process = self.check_certificate_availability(description)
            
            webinar_data = {
                'id': self.generate_id(title, 'Xtalks'),
                'title': title,
                'provider': 'Xtalks',
                'topics': self._extract_topics_from_title(title),
                'format': 'on-demand',
                'duration_min': 60,
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'webinar_date': parsed_date.strftime('%Y-%m-%d'),  # Add the actual webinar date
                'url': url,
                'description': description
            }
            
            return webinar_data
        
        except Exception as e:
            print(f"Error parsing webinar from date: {e}")
            return None
    
    def _parse_webinar_link(self, link) -> Optional[Dict]:
        """Parse individual webinar link"""
        try:
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            # Build URL and clean title
            url = self._build_url(href)
            title = self._clean_title(title)
            
            # Apply filtering
            if not self._is_valid_webinar(title, url) or self._is_topic_page(title):
                return None
            
            # For direct links, we don't have date info, so we'll include them
            # but mark them as needing date verification
            webinar_data = {
                'id': self.generate_id(title, 'Xtalks'),
                'title': title,
                'provider': 'Xtalks',
                'topics': self._extract_topics_from_title(title),
                'format': 'on-demand',
                'duration_min': 60,
                'certificate_available': False,  # Default for direct links
                'certificate_process': 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'webinar_date': 'Unknown',  # Mark as unknown for direct links
                'url': url,
                'description': f"Xtalks webinar: {title}"
            }
            
            return webinar_data
        
        except Exception as e:
            print(f"Error parsing webinar link: {e}")
            return None
    
    def _extract_topics_from_title(self, title: str) -> List[str]:
        """Extract topics from webinar title"""
        topics = []
        title_lower = title.lower()
        
        # Topic keywords mapping
        topic_keywords = {
            'clinical trial': 'clinical-trials',
            'clinical trials': 'clinical-trials',
            'clinical research': 'clinical-research',
            'drug discovery': 'drug-discovery',
            'drug development': 'drug-development',
            'pharmaceutical': 'pharmaceutical',
            'biotech': 'biotech',
            'biotechnology': 'biotech',
            'cell therapy': 'cell-therapy',
            'gene therapy': 'gene-therapy',
            'manufacturing': 'manufacturing',
            'quality': 'quality-assurance',
            'regulatory': 'regulatory',
            'fda': 'regulatory',
            'ema': 'regulatory',
            'compliance': 'compliance',
            'bioprocessing': 'bioprocess',
            'bioprocess': 'bioprocess',
            'laboratory': 'laboratory-management',
            'lab': 'laboratory-management',
            'research': 'research',
            'development': 'development',
            'life science': 'life-sciences',
            'life sciences': 'life-sciences',
            'oncology': 'oncology',
            'cancer': 'oncology',
            'cardiovascular': 'cardiovascular',
            'neuroscience': 'neuroscience',
            'rare disease': 'rare-disease',
            'rare diseases': 'rare-disease',
            'patient': 'patient-care',
            'diagnostic': 'diagnostic',
            'diagnostics': 'diagnostic',
            'biomarker': 'biomarker',
            'biomarkers': 'biomarker',
            'data': 'data-management',
            'analytics': 'data-management',
            'ai': 'artificial-intelligence',
            'artificial intelligence': 'artificial-intelligence',
            'machine learning': 'artificial-intelligence',
            'digital health': 'digital-health',
            'telemedicine': 'digital-health',
            'medical device': 'medical-device',
            'medical devices': 'medical-device'
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in title_lower and topic not in topics:
                topics.append(topic)
        
        return topics
    



class ISPEScraper(BaseScraper):
    """Scraper for ISPE webinars"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://ispe.org"
        self.webinars_url = "https://ispe.org/webinars"
    
    def scrape(self):
        """Scrape ISPE webinars"""
        try:
            response = self.make_request(self.webinars_url)
            
            if not response:
                print("Failed to access ISPE webinars page")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            webinar_links = soup.find_all('a', href=re.compile(r'webinar'))
            
            print(f"Found {len(webinar_links)} potential webinar links on ISPE")
            
            for link in webinar_links:
                webinar_data = self._parse_webinar_link(link)
                if webinar_data:
                    self.add_webinar(webinar_data)
                    
        except Exception as e:
            print(f"Error scraping ISPE: {e}")
    
    def _parse_webinar_link(self, link) -> Optional[Dict]:
        """Parse individual webinar link"""
        try:
            title = link.get_text(strip=True)
            url = self.base_url + link.get('href', '') if link.get('href', '').startswith('/') else link.get('href', '')
            
            # Skip non-webinar content
            if not self._is_valid_webinar(title, url):
                return None
            
            # Check for certificate availability
            has_cert, process = self.check_certificate_availability(title)
            webinar_data = {
                'id': self.generate_id(title, 'ISPE'),
                'title': title,
                'provider': 'ISPE',
                'topics': ['manufacturing', 'quality-assurance', 'regulatory'],
                'format': 'on-demand',
                'duration_min': 60,
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'url': url,
                'description': f"ISPE webinar: {title}"
            }
            
            return webinar_data
        
        except Exception as e:
            print(f"Error parsing webinar link: {e}")
            return None


class TechnologyNetworksScraper(BaseScraper):
    """Scraper for Technology Networks webinars"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.technologynetworks.com"
        self.webinars_url = "https://www.technologynetworks.com/tn/topic-hub/gene-and-cell-therapy/webinars-and-online-events"
    
    def scrape(self):
        """Scrape Technology Networks webinars"""
        try:
            response = self.make_request(self.webinars_url)
            
            if not response:
                print("Failed to access Technology Networks webinars page")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            webinar_links = soup.find_all('a', href=re.compile(r'webinar'))
            
            print(f"Found {len(webinar_links)} potential webinar links on Technology Networks")
            
            for link in webinar_links:
                webinar_data = self._parse_webinar_link(link)
                if webinar_data:
                    self.add_webinar(webinar_data)
                    
        except Exception as e:
            print(f"Error scraping Technology Networks: {e}")
    
    def _parse_webinar_link(self, link) -> Optional[Dict]:
        """Parse individual webinar link"""
        try:
            title = link.get_text(strip=True)
            url = self.base_url + link.get('href', '') if link.get('href', '').startswith('/') else link.get('href', '')
            
            # Skip non-webinar content
            if not self._is_valid_webinar(title, url):
                return None
            
            # Check for certificate availability
            has_cert, process = self.check_certificate_availability(title)
            webinar_data = {
                'id': self.generate_id(title, 'Technology Networks'),
                'title': title,
                'provider': 'Technology Networks',
                'topics': ['cell-therapy', 'gene-therapy', 'biotech'],
                'format': 'on-demand',
                'duration_min': 60,
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'url': url,
                'description': f"Technology Networks webinar: {title}"
            }
            
            return webinar_data
        
        except Exception as e:
            print(f"Error parsing webinar link: {e}")
            return None


class FDACDERScraper(BaseScraper):
    """Scraper for FDA CDER Drug Topics webinars"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.fda.gov"
        self.events_url = "https://www.fda.gov/drugs/news-events-human-drugs/fda-drug-topics"
    
    def scrape(self):
        """Scrape FDA CDER webinars"""
        try:
            response = requests.get(self.events_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            webinar_links = soup.find_all('a', href=re.compile(r'drug-topics.*webinar', re.I))
            
            for link in webinar_links:
                webinar_data = self._parse_webinar_link(link)
                if webinar_data:
                    self.add_webinar(webinar_data)
        
        except Exception as e:
            print(f"Error scraping FDA CDER: {e}")
    
    def _parse_webinar_link(self, link) -> Optional[Dict]:
        """Parse individual webinar link"""
        try:
            title = link.get_text(strip=True)
            url = self.base_url + link.get('href', '')
            
            # FDA Drug Topics typically provide certificates
            webinar_data = {
                'id': self.generate_id(title, 'FDA CDER'),
                'title': title,
                'provider': 'FDA CDER',
                'topics': ['regulatory', 'quality-assurance'],
                'format': 'on-demand',
                'duration_min': 90,  # FDA webinars are typically 90 minutes
                'certificate_available': True,
                'certificate_process': 'Certificate available after post-test and survey completion',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'url': url,
                'description': f"FDA Drug Topics webinar: {title}"
            }
            
            return webinar_data
        
        except Exception as e:
            print(f"Error parsing webinar link: {e}")
            return None


class SOCRAScraper(BaseScraper):
    """Scraper for SOCRA webinars"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.socra.org"
        self.webinars_url = "https://www.socra.org/conferences-and-education/live-webinars/"
    
    def scrape(self):
        """Scrape SOCRA webinars"""
        try:
            response = self.make_request(self.webinars_url)
            
            if not response:
                print("Failed to access SOCRA webinars page")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            webinar_links = soup.find_all('a', href=re.compile(r'webinar'))
            
            print(f"Found {len(webinar_links)} potential webinar links on SOCRA")
            
            for link in webinar_links:
                webinar_data = self._parse_webinar_link(link)
                if webinar_data:
                    self.add_webinar(webinar_data)
                    
        except Exception as e:
            print(f"Error scraping SOCRA: {e}")
    
    def _parse_webinar_link(self, link) -> Optional[Dict]:
        """Parse individual webinar link"""
        try:
            title = link.get_text(strip=True)
            url = self.base_url + link.get('href', '') if link.get('href', '').startswith('/') else link.get('href', '')
            
            # Skip non-webinar content
            if not self._is_valid_webinar(title, url):
                return None
            
            # Check for certificate availability
            has_cert, process = self.check_certificate_availability(title)
            webinar_data = {
                'id': self.generate_id(title, 'SOCRA'),
                'title': title,
                'provider': 'SOCRA',
                'topics': ['clinical-research', 'monitoring', 'project-management'],
                'format': 'live',
                'duration_min': 60,
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'url': url,
                'description': f"SOCRA webinar: {title}"
            }
            
            return webinar_data
        
        except Exception as e:
            print(f"Error parsing webinar link: {e}")
            return None


class PMIScraper(BaseScraper):
    """Scraper for PMI webinars"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.pmi.org"
        self.webinars_url = "https://www.pmi.org/learning/webinars"
    
    def scrape(self):
        """Scrape PMI webinars"""
        try:
            response = self.make_request(self.webinars_url)
            
            if not response:
                print("Failed to access PMI webinars page")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different patterns for finding webinar links
            webinar_links = soup.find_all('a', href=re.compile(r'webinar'))
            
            # If no webinar links found, try broader search
            if not webinar_links:
                webinar_links = soup.find_all('a', href=re.compile(r'learning'))
            
            # If still no links, try looking for any links with relevant text
            if not webinar_links:
                all_links = soup.find_all('a')
                webinar_links = [link for link in all_links if any(keyword in link.get_text(strip=True).lower() 
                    for keyword in ['webinar', 'learning', 'education', 'training'])]
            
            print(f"Found {len(webinar_links)} potential webinar links on PMI")
            
            for link in webinar_links:
                webinar_data = self._parse_webinar_link(link)
                if webinar_data:
                    self.add_webinar(webinar_data)
                    
        except Exception as e:
            print(f"Error scraping PMI: {e}")
    
    def _parse_webinar_link(self, link) -> Optional[Dict]:
        """Parse individual webinar link"""
        try:
            title = link.get_text(strip=True)
            url = self.base_url + link.get('href', '') if link.get('href', '').startswith('/') else link.get('href', '')
            
            webinar_data = {
                'id': self.generate_id(title, 'PMI'),
                'title': title,
                'provider': 'PMI',
                'topics': ['project-management'],
                'format': 'on-demand',
                'duration_min': 60,
                'certificate_available': True,
                'certificate_process': 'Certificate available upon completion',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'url': url,
                'description': f"PMI webinar: {title}"
            }
            
            return webinar_data
        
        except Exception as e:
            print(f"Error parsing webinar link: {e}")
            return None


if __name__ == "__main__":
    # Test all scrapers
    scrapers = [
        LabrootsScraper(),
        XtalksScraper(),
        ISPEScraper(),
        TechnologyNetworksScraper(),
        FDACDERScraper(),
        SOCRAScraper(),
        PMIScraper()
    ]
    
    for scraper in scrapers:
        try:
            scraper.run()
        except Exception as e:
            print(f"Failed to run {scraper.__class__.__name__}: {e}") 