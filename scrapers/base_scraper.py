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
        """Add or update a webinar in the database by id"""
        # Check if webinar already exists
        existing_ids = [w['id'] for w in self.webinars]
        if webinar_data['id'] in existing_ids:
            # Replace the old entry with the new one
            idx = existing_ids.index(webinar_data['id'])
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
        super().__init__(data_file="src/webinars.json")
        self.base_url = "https://www.labroots.com"
        self.api_url = "https://www.labroots.com/api/v1/events"
    
    def scrape(self):
        """Scrape Labroots webinars"""
        try:
            # Scrape both upcoming and on-demand events
            urls_to_scrape = [
                ("https://www.labroots.com/virtual-events/all/filter/upcoming/page", "live"),
                ("https://www.labroots.com/virtual-events/all/filter/ondemand/page", "on-demand")
            ]
            
            for url, format_type in urls_to_scrape:
                print(f"Scraping {format_type} events from {url}")
                response = self.make_request(url)
                
                if not response:
                    print(f"Failed to access {format_type} events page")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for event links - try multiple patterns
                event_links = soup.find_all('a', href=re.compile(r'/event/'))
                
                # If no event links found, try looking for other patterns
                if not event_links:
                    # Look for any links that might contain event information
                    all_links = soup.find_all('a', href=True)
                    event_links = [link for link in all_links if any(keyword in link.get('href', '').lower() for keyword in ['event', 'webinar', 'conference'])]
                
                print(f"Found {len(event_links)} potential {format_type} event links")
                
                for link in event_links:
                    if self._is_relevant_event_link(link):
                        webinar_data = self._parse_event_link(link, format_type)
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
    
    def _parse_event_link(self, link, format_type="on-demand") -> Optional[Dict]:
        """Parse event link into webinar format"""
        try:
            title = link.get_text(strip=True)
            url = self.base_url + link.get('href', '') if link.get('href', '').startswith('/') else link.get('href', '')
            
            # Skip non-webinar content
            if not self._is_valid_webinar(title, url):
                return None
            
            # Get the actual event date from the event page
            webinar_date = self._get_event_date_from_page(url)
            
            # Check for certificate availability
            has_cert, process = self.check_certificate_availability(title)
            
            webinar_data = {
                'id': self.generate_id(title, 'Labroots'),
                'title': title,
                'provider': 'Labroots',
                'topics': self._extract_topics_from_title(title),
                'format': format_type,
                'duration_min': 'unknown',
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'webinar_date': webinar_date,
                'live_date': webinar_date if format_type == 'live' and webinar_date else 'on-demand',
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
    
    def _extract_date_from_title(self, title: str) -> str:
        """Extract date from event title"""
        # Look for year patterns like "2025", "2026"
        year_match = re.search(r'20\d{2}', title)
        if year_match:
            year = year_match.group(0)
            # For now, just return the year as YYYY-01-01
            # In the future, we could look for month patterns too
            return f"{year}-01-01"
        
        # If no year found, return "Unknown"
        return "Unknown"
    
    def _get_event_date_from_page(self, event_url: str) -> str:
        """Get the actual event date from the event page"""
        try:
            response = self.make_request(event_url)
            if not response:
                return "Unknown"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            all_text = soup.get_text()
            
            # Look for date patterns: "OCT 15, 2025" or "October 15th, 2025"
            date_patterns = [
                r'([A-Z]{3})\s+(\d{1,2}),\s+(\d{4})',  # OCT 15, 2025
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?,\s+(\d{4})'  # October 15th, 2025
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, all_text)
                if matches:
                    # Take the first match (usually the main event date)
                    match = matches[0]
                    if len(match) == 3:
                        month, day, year = match
                        # Convert abbreviated month to number
                        month_map = {
                            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12',
                            'January': '01', 'February': '02', 'March': '03', 'April': '04',
                            'May': '05', 'June': '06', 'July': '07', 'August': '08',
                            'September': '09', 'October': '10', 'November': '11', 'December': '12'
                        }
                        month_num = month_map.get(month.upper(), '01')
                        return f"{year}-{month_num}-{day.zfill(2)}"
            
            return "Unknown"
            
        except Exception as e:
            print(f"Error getting date from event page: {e}")
            return "Unknown"
    
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
                parsed_date = datetime.strptime(date_text, "%B %d, %Y")
                
                # Check if webinar is within last 6 months
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
                'duration_min': 'unknown',
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'webinar_date': parsed_date.strftime('%Y-%m-%d'),  # Add the actual webinar date
                'live_date': 'on-demand',  # Xtalks webinars are on-demand
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
                'duration_min': 'unknown',
                'certificate_available': False,  # Default for direct links
                'certificate_process': 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'webinar_date': 'Unknown',  # Mark as unknown for direct links
                'live_date': 'on-demand',  # Xtalks webinars are on-demand
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
        super().__init__(data_file="src/webinars.json")
        self.base_url = "https://ispe.org"
        self.upcoming_url = "https://ispe.org/webinars"
        self.past_url = "https://ispe.org/webinars/past/videos/recordings-past-webinars"
    
    def scrape(self):
        """Scrape ISPE webinars from both upcoming and past pages"""
        try:
            # Scrape upcoming (live) webinars
            print("Scraping ISPE upcoming webinars...")
            self._scrape_upcoming_webinars()
            
            # Scrape past (on-demand) webinars
            print("Scraping ISPE past webinars...")
            self._scrape_past_webinars()
                    
        except Exception as e:
            print(f"Error scraping ISPE: {e}")
    
    def _scrape_upcoming_webinars(self):
        """Scrape upcoming webinars from the main webinars page"""
        try:
            response = self.make_request(self.upcoming_url)
            
            if not response:
                print("Failed to access ISPE upcoming webinars page")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for webinar blocks - ISPE uses column column-block structure
            webinar_blocks = soup.find_all('div', class_='column column-block')
            
            print(f"Found {len(webinar_blocks)} webinar blocks")
            
            for block in webinar_blocks:
                webinar_data = self._parse_upcoming_webinar(block)
                if webinar_data:
                    self.add_webinar(webinar_data)
                    
        except Exception as e:
            print(f"Error scraping upcoming webinars: {e}")
    
    def _scrape_past_webinars(self):
        """Scrape past webinars from the recordings page"""
        try:
            response = self.make_request(self.past_url)
            
            if not response:
                print("Failed to access ISPE past webinars page")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for past webinar entries - they might be in a different structure
            # Try to find webinar links or entries
            webinar_links = soup.find_all('a', href=re.compile(r'/webinars/'))
            
            print(f"Found {len(webinar_links)} potential past webinar links")
            
            for link in webinar_links:
                webinar_data = self._parse_past_webinar_link(link)
                if webinar_data:
                    self.add_webinar(webinar_data)
                    
        except Exception as e:
            print(f"Error scraping past webinars: {e}")
    
    def _parse_upcoming_webinar(self, block) -> Optional[Dict]:
        """Parse upcoming webinar from a column block"""
        try:
            # Extract title from h5 element
            title_elem = block.find('h5')
            if not title_elem:
                return None
            
            title_link = title_elem.find('a')
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            href = title_link.get('href', '')
            
            # For ISPE, be more permissive - if it's in the webinar blocks, it's likely valid
            # Skip only obvious non-webinar content
            if any(skip in title.lower() for skip in ['webinar library', 'visit', 'call for proposals', 'submit']):
                return None
            
            # Extract date from paragraph after the title - improved method
            date_text = ""
            p_elements = block.find_all('p')
            for p_elem in p_elements:
                p_text = p_elem.get_text(strip=True)
                if re.search(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', p_text):
                    date_text = p_text
                    break
            
            # Build URL
            url = self.base_url + href if href.startswith('/') else href
            
            # Parse date
            webinar_date = self._parse_ispe_date(date_text)
            
            # Check for certificate availability
            has_cert, process = self.check_certificate_availability(title)
            
            webinar_data = {
                'id': self.generate_id(title, 'ISPE'),
                'title': title,
                'provider': 'ISPE',
                'topics': self._extract_topics_from_title(title),
                'format': 'live',
                'duration_min': 60,
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'webinar_date': webinar_date,
                'live_date': webinar_date if webinar_date and webinar_date != "Unknown" else 'on-demand',
                'url': url,
                'description': f"ISPE upcoming webinar: {title}"
            }
            
            return webinar_data
            
        except Exception as e:
            print(f"Error parsing upcoming webinar: {e}")
            return None
    
    def _parse_past_webinar_link(self, link) -> Optional[Dict]:
        """Parse past webinar from a link"""
        try:
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            # Skip if not a valid webinar title
            if not self._is_valid_webinar(title, href):
                return None
            
            # Skip navigation and non-webinar links
            if any(skip in title.lower() for skip in ['visit', 'library', 'past', 'recordings', 'webinar library']):
                return None
            
            # Build URL
            url = self.base_url + href if href.startswith('/') else href
            
            # For past webinars, we might not have exact dates, so use a placeholder
            webinar_date = "Unknown"
            
            # Check for certificate availability
            has_cert, process = self.check_certificate_availability(title)
            
            webinar_data = {
                'id': self.generate_id(title, 'ISPE'),
                'title': title,
                'provider': 'ISPE',
                'topics': self._extract_topics_from_title(title),
                'format': 'on-demand',
                'duration_min': 60,
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'webinar_date': webinar_date,
                'live_date': 'on-demand',  # ISPE past webinars are on-demand
                'url': url,
                'description': f"ISPE past webinar: {title}"
            }
            
            return webinar_data
            
        except Exception as e:
            print(f"Error parsing past webinar link: {e}")
            return None
    
    def _parse_ispe_date(self, date_text: str) -> str:
        """Parse ISPE date format"""
        if not date_text:
            return "Unknown"
        
        try:
            # Handle ISPE date format: "Tuesday, 1 July 2025" or "Wednesday, 9 July 2025" or "Thursday, 4 Sep 2025"
            # More flexible pattern to handle abbreviated months
            date_pattern = r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})'
            
            match = re.search(date_pattern, date_text)
            if match:
                day, month, year = match.groups()
                
                # Convert month name to number (handle both full and abbreviated names)
                month_map = {
                    'january': '01', 'jan': '01',
                    'february': '02', 'feb': '02',
                    'march': '03', 'mar': '03',
                    'april': '04', 'apr': '04',
                    'may': '05',
                    'june': '06', 'jun': '06',
                    'july': '07', 'jul': '07',
                    'august': '08', 'aug': '08',
                    'september': '09', 'sep': '09',
                    'october': '10', 'oct': '10',
                    'november': '11', 'nov': '11',
                    'december': '12', 'dec': '12'
                }
                
                month_num = month_map.get(month.lower(), '01')
                day_num = day.zfill(2)
                
                return f"{year}-{month_num}-{day_num}"
            
            return "Unknown"
            
        except Exception as e:
            print(f"Error parsing date '{date_text}': {e}")
            return "Unknown"
    
    def _extract_topics_from_title(self, title: str) -> List[str]:
        """Extract topics from ISPE webinar title"""
        title_lower = title.lower()
        topics = []
        
        topic_keywords = {
            'process validation': 'validation',
            'validation': 'validation',
            'quality': 'quality-assurance',
            'quality assurance': 'quality-assurance',
            'manufacturing': 'manufacturing',
            'regulatory': 'regulatory',
            'compliance': 'regulatory',
            'gmp': 'manufacturing',
            'bioprocess': 'bioprocess',
            'biotechnology': 'biotech',
            'clinical': 'clinical-trials',
            'clinical trials': 'clinical-trials',
            'supply chain': 'supply-chain',
            'facility': 'facility',
            'equipment': 'equipment',
            'information systems': 'information-systems',
            'data': 'data-management',
            'documentation': 'documentation',
            'audit': 'quality-assurance',
            'investigation': 'quality-assurance',
            'error': 'quality-assurance',
            'human error': 'quality-assurance',
            'c&q': 'validation',
            'commissioning': 'validation',
            'qualification': 'validation',
            'sterilizing': 'manufacturing',
            'filter': 'manufacturing',
            'autoclave': 'manufacturing',
            'parts washer': 'manufacturing',
            'productivity': 'manufacturing',
            'cogs': 'manufacturing',
            'pat': 'manufacturing',
            'capacitance': 'manufacturing'
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in title_lower:
                topics.append(topic)
        
        # Default topics for ISPE webinars
        if not topics:
            topics = ['manufacturing', 'quality-assurance']
        
        return topics


class TechnologyNetworksScraper(BaseScraper):
    """Scraper for Technology Networks webinars"""
    
    def __init__(self):
        super().__init__(data_file="src/webinars.json")
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
            
            # Technology Networks-specific: skip navigation/general pages
            title_lower = title.lower().strip()
            general_titles = [
                'webinars & online events', 'next', 'last', 'previous', 'first'
            ]
            if title_lower in general_titles:
                return None
            if title_lower.isdigit():
                return None
            
            # Skip non-webinar content
            if not self._is_valid_webinar(title, url):
                return None

            # Fetch the webinar page to extract date and determine format
            format_type = 'on-demand'  # default
            webinar_date = None
            
            try:
                page_response = self.make_request(url)
                if page_response:
                    page_soup = BeautifulSoup(page_response.content, 'html.parser')
                    
                    # Extract date from page content
                    page_text = page_soup.get_text()
                    
                    # Date patterns to look for on the page
                    date_patterns = [
                        r'(\d{1,2} [A-Za-z]+ \d{4})',         # 16 July 2025
                        r'([A-Za-z]+ \d{1,2}, \d{4})',         # July 16, 2025
                        r'(\d{1,2}/\d{1,2}/\d{4})',           # 16/07/2025 or 07/16/2025
                        r'(\d{4}-\d{2}-\d{2})'                # 2025-07-16
                    ]
                    
                    now = datetime.now()
                    for pattern in date_patterns:
                        match = re.search(pattern, page_text)
                        if match:
                            date_str = match.group(1)
                            for fmt in ["%d %B %Y", "%B %d, %Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"]:
                                try:
                                    dt = datetime.strptime(date_str, fmt)
                                    if dt > now:
                                        format_type = 'live'
                                        webinar_date = dt
                                        break
                                except ValueError:
                                    continue
                            if webinar_date:
                                break
                    
                    # If no future date found, check for on-demand indicators
                    if not webinar_date:
                        page_text_lower = page_text.lower()
                        if 'on-demand' in page_text_lower or 'on demand' in page_text_lower:
                            format_type = 'on-demand'
                        elif re.search(r'\b(live|upcoming|register)\b', page_text_lower):
                            format_type = 'live'
                        else:
                            format_type = 'on-demand'
                            
            except Exception as e:
                print(f"Error fetching webinar page {url}: {e}")
                # Fallback to title-based logic
                if 'on-demand' in title_lower or 'on demand' in title_lower:
                    format_type = 'on-demand'
                elif re.search(r'\b(live|upcoming|register)\b', title_lower):
                    format_type = 'live'
                else:
                    format_type = 'on-demand'

            # Check for certificate availability
            has_cert, process = self.check_certificate_availability(title)
            webinar_data = {
                'id': self.generate_id(title, 'Technology Networks'),
                'title': title,
                'provider': 'Technology Networks',
                'topics': ['cell-therapy', 'gene-therapy', 'biotech'],
                'format': format_type,
                'duration_min': 60,
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'No certificate information available',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'url': url,
                'description': f"Technology Networks webinar: {title}"
            }
            if webinar_date:
                webinar_data['webinar_date'] = webinar_date.strftime('%Y-%m-%d')
                webinar_data['live_date'] = webinar_date.strftime('%Y-%m-%d') if format_type == 'live' else 'on-demand'
            else:
                webinar_data['live_date'] = 'on-demand'
            return webinar_data
        except Exception as e:
            print(f"Error parsing webinar link: {e}")
            return None


class FDACDERScraper(BaseScraper):
    """Scraper for FDA CDER training courses and webinars"""
    
    def __init__(self):
        super().__init__(data_file="src/webinars.json")
        self.base_url = "https://www.fda.gov"
        self.cderlearn_url = "https://www.fda.gov/training-and-continuing-education/cderlearn"
    
    def scrape(self):
        """Scrape FDA CDER training courses and webinars"""
        try:
            print("Scraping FDA CDER training courses and webinars...")
            
            response = self.make_request(self.cderlearn_url)
            
            if not response:
                print("Failed to access FDA CDER Learn page")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the table with training courses
            table = soup.find('table', class_='table')
            if not table:
                print("No training table found on FDA CDER Learn page")
                return
            
            # Parse table rows
            rows = table.find_all('tr')
            print(f"Found {len(rows)} rows in FDA training table")
            
            for row in rows[1:]:  # Skip header row
                course_data = self._parse_course_row(row)
                if course_data:
                    self.add_webinar(course_data)
        
        except Exception as e:
            print(f"Error scraping FDA CDER: {e}")
    
    def _parse_course_row(self, row) -> Optional[Dict]:
        """Parse a course row from the FDA training table"""
        try:
            cells = row.find_all('td')
            if len(cells) < 4:
                return None
            
            # Extract data from cells
            title_cell = cells[0]
            topic_cell = cells[1]
            ce_cell = cells[2]
            credits_cell = cells[3]
            
            # Extract title and URL
            title_link = title_cell.find('a')
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            href = title_link.get('href', '')
            
            # Build full URL
            if href.startswith('http'):
                url = href
            elif href.startswith('/'):
                url = self.base_url + href
            else:
                url = self.base_url + '/' + href
            
            # Extract topics
            topics_text = topic_cell.get_text(strip=True)
            topics = self._extract_topics_from_text(topics_text)
            
            # Check CE availability
            ce_text = ce_cell.get_text(strip=True).lower()
            has_ce = ce_text == 'yes'
            
            # Extract credits
            credits_text = credits_cell.get_text(strip=True)
            try:
                credits = float(credits_text) if credits_text != '0' else 0
            except:
                credits = 0
            
            # Determine format based on title and URL
            format_type = self._determine_format(title, url)
            
            # Determine duration based on credits (rough estimate)
            duration_min = self._estimate_duration(credits)
            
            # Create course data
            course_data = {
                'id': self.generate_id(title, 'FDA CDER'),
                'title': title,
                'provider': 'FDA CDER',
                'topics': topics,
                'format': format_type,
                'duration_min': duration_min,
                'certificate_available': has_ce,
                'certificate_process': f'CE credits available: {credits} credits' if has_ce else 'No CE credits available',
                'ce_credits': credits if has_ce else 0,
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'live_date': 'on-demand' if format_type == 'on-demand' else 'Unknown',  # Set based on format
                'url': url,
                'description': f"FDA CDER training: {title}. Topics: {topics_text}"
            }
            
            return course_data
        
        except Exception as e:
            print(f"Error parsing course row: {e}")
            return None
    
    def _extract_topics_from_text(self, topics_text: str) -> List[str]:
        """Extract topics from the topics cell text"""
        topics = []
        
        # Split by semicolon and clean up
        topic_list = [t.strip() for t in topics_text.split(';')]
        
        # Map FDA topics to our topic categories
        topic_mapping = {
            'drug development': 'drug-development',
            'drug regulatory process': 'regulatory',
            'drug safety': 'drug-safety',
            'cancer drugs': 'cancer',
            'biosimilars': 'biosimilars',
            'generic drugs': 'generic-drugs',
            'compounding': 'compounding',
            'covid-19': 'covid-19',
            'opioids': 'opioids',
            'women\'s health': 'womens-health',
            'rare diseases': 'rare-diseases',
            'artificial intelligence': 'artificial-intelligence',
            'medwatch': 'medwatch',
            'ind/expanded access': 'expanded-access',
            'otc drug regulations': 'otc-drugs',
            'health fraud': 'health-fraud',
            'case study': 'case-study',
            'minority health': 'minority-health',
            'español': 'spanish',
            'cannabidiol': 'cannabis',
            'sunscreen': 'sunscreen',
            'biotechnology': 'biotechnology',
            'clinical trials': 'clinical-trials',
            'pharmacovigilance': 'pharmacovigilance',
            'quality assurance': 'quality-assurance',
            'manufacturing': 'manufacturing',
            'validation': 'validation',
            'laboratory': 'laboratory'
        }
        
        for topic in topic_list:
            topic_lower = topic.lower()
            for fda_topic, our_topic in topic_mapping.items():
                if fda_topic in topic_lower:
                    topics.append(our_topic)
        
        # Default topics if none found
        if not topics:
            topics = ['regulatory', 'drug-development']
        
        return topics
    
    def _determine_format(self, title: str, url: str) -> str:
        """Determine the format of the training"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        if any(keyword in title_lower for keyword in ['webinar', 'live', 'virtual']):
            return 'live'
        elif any(keyword in url_lower for keyword in ['youtube', 'video']):
            return 'on-demand'
        elif any(keyword in title_lower for keyword in ['course', 'training', 'seminar']):
            return 'on-demand'
        else:
            return 'on-demand'
    
    def _estimate_duration(self, credits: float) -> int:
        """Estimate duration in minutes based on CE credits"""
        if credits == 0:
            return 60  # Default for non-CE content
        else:
            # Rough estimate: 1 CE credit = 60 minutes
            return int(credits * 60)





class PMIScraper(BaseScraper):
    """Scraper for PMI webinars"""
    
    def __init__(self):
        super().__init__(data_file="src/webinars.json")
        self.base_url = "https://www.projectmanagement.com"
        self.webinars_url = "https://www.projectmanagement.com/webinars/webinarmainondemand.cfm"
    
    def scrape(self):
        """Add PMI on-demand webinars link"""
        try:
            print("Adding PMI on-demand webinars link...")
            
            # Add a single entry linking to the PMI on-demand webinars page
            webinar_data = {
                'id': 'pmi-on-demand-webinars',
                'title': 'PMI On-Demand Webinars',
                'provider': 'PMI',
                'topics': ['project-management'],
                'format': 'on-demand',
                'duration_min': 'variable',
                'certificate_available': True,
                'certificate_process': 'PDUs available upon completion',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'live_date': 'on-demand',  # PMI webinars are on-demand
                'url': 'https://www.projectmanagement.com/webinars/webinarmainondemand.cfm',
                'description': 'Access to PMI on-demand webinars. Free webinars available within the last 6 months. PDUs available upon completion.'
            }
            
            self.add_webinar(webinar_data)
            print("Added PMI on-demand webinars link")
                    
        except Exception as e:
            print(f"Error adding PMI link: {e}")
    
    def _find_webinar_entries(self, soup):
        """Find webinar entries in the page"""
        entries = []
        
        # Try multiple patterns to find webinar entries
        # Look for table rows that might contain webinar info
        table_rows = soup.find_all('tr')
        for row in table_rows:
            if self._looks_like_webinar_row(row):
                entries.append(row)
        
        # Look for div containers that might contain webinar info
        div_containers = soup.find_all('div', class_=re.compile(r'webinar|event|session'))
        entries.extend(div_containers)
        
        # Look for any elements containing webinar-like content
        all_elements = soup.find_all(['div', 'article', 'section'])
        for element in all_elements:
            text = element.get_text()
            if any(keyword in text.lower() for keyword in ['webinar', 'pdu', 'project management', 'free']):
                entries.append(element)
        
        return entries
    
    def _looks_like_webinar_row(self, row):
        """Check if a table row looks like it contains webinar information"""
        text = row.get_text().lower()
        return any(keyword in text for keyword in ['webinar', 'pdu', 'project management', 'free'])
    
    def _parse_webinar_entry(self, entry) -> Optional[Dict]:
        """Parse webinar from an entry element"""
        try:
            # Extract title
            title_elem = entry.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'])
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Skip navigation and non-webinar content
            if any(skip in title.lower() for skip in ['webinar library', 'view all', 'opens in a new tab', 'navigation']):
                return None
            
            # Extract URL
            link_elem = entry.find('a', href=True)
            url = ""
            if link_elem:
                href = link_elem.get('href', '')
                url = self.base_url + href if href.startswith('/') else href
            
            # Extract date if available
            date_text = ""
            date_elem = entry.find(text=re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'))
            if date_elem:
                date_text = date_elem.strip()
            
            # Parse date
            webinar_date = self._parse_pmi_date(date_text)
            
            # Check if it's within last 6 months
            if webinar_date != "Unknown":
                try:
                    from datetime import datetime, timedelta
                    parsed_date = datetime.strptime(webinar_date, '%Y-%m-%d')
                    six_months_ago = datetime.now() - timedelta(days=180)
                    if parsed_date < six_months_ago:
                        return None  # Skip webinars older than 6 months
                except:
                    pass
            
            # Check for certificate availability (PMI typically provides PDUs)
            has_cert, process = self.check_certificate_availability(title)
            
            webinar_data = {
                'id': self.generate_id(title, 'PMI'),
                'title': title,
                'provider': 'PMI',
                'topics': self._extract_topics_from_title(title),
                'format': 'on-demand',
                'duration_min': 60,
                'certificate_available': has_cert,
                'certificate_process': process if has_cert else 'PDUs available upon completion',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'webinar_date': webinar_date,
                'live_date': 'on-demand',  # PMI webinars are on-demand
                'url': url,
                'description': f"PMI on-demand webinar: {title}"
            }
            
            return webinar_data
            
        except Exception as e:
            print(f"Error parsing webinar entry: {e}")
            return None
    
    def _parse_pmi_date(self, date_text: str) -> str:
        """Parse PMI date format"""
        if not date_text:
            return "Unknown"
        
        try:
            # Handle various PMI date formats
            date_patterns = [
                r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',  # "July 1, 2025" or "July 1 2025"
                r'(\d{1,2})\s+(\w+)\s+(\d{4})',    # "1 July 2025"
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_text)
                if match:
                    if len(match.groups()) == 3:
                        if match.group(1).isdigit():
                            # Format: "1 July 2025"
                            day, month, year = match.groups()
                        else:
                            # Format: "July 1, 2025"
                            month, day, year = match.groups()
                        
                        # Convert month name to number
                        month_map = {
                            'january': '01', 'february': '02', 'march': '03', 'april': '04',
                            'may': '05', 'june': '06', 'july': '07', 'august': '08',
                            'september': '09', 'october': '10', 'november': '11', 'december': '12'
                        }
                        
                        month_num = month_map.get(month.lower(), '01')
                        day_num = day.zfill(2)
                        
                        return f"{year}-{month_num}-{day_num}"
            
            return "Unknown"
            
        except Exception as e:
            print(f"Error parsing date '{date_text}': {e}")
            return "Unknown"
    
    def _extract_topics_from_title(self, title: str) -> List[str]:
        """Extract topics from PMI webinar title"""
        title_lower = title.lower()
        topics = []
        
        topic_keywords = {
            'project management': 'project-management',
            'agile': 'project-management',
            'scrum': 'project-management',
            'kanban': 'project-management',
            'leadership': 'leadership',
            'team management': 'team-management',
            'risk management': 'risk-management',
            'stakeholder': 'stakeholder-management',
            'communication': 'communication',
            'planning': 'planning',
            'scheduling': 'planning',
            'budget': 'budget-management',
            'quality': 'quality-management',
            'procurement': 'procurement',
            'integration': 'integration',
            'scope': 'scope-management',
            'time management': 'time-management',
            'cost management': 'cost-management',
            'human resources': 'human-resources',
            'pmp': 'project-management',
            'pdu': 'project-management'
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in title_lower:
                topics.append(topic)
        
        # Default topic for PMI webinars
        if not topics:
            topics = ['project-management']
        
        return topics


if __name__ == "__main__":
    # Test all scrapers
    scrapers = [
        LabrootsScraper(),
        XtalksScraper(),
        ISPEScraper(),
        TechnologyNetworksScraper(),
        FDACDERScraper(),
        PMIScraper()
    ]
    
    for scraper in scrapers:
        try:
            scraper.run()
        except Exception as e:
            print(f"Failed to run {scraper.__class__.__name__}: {e}") 