import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from base_scraper import BaseScraper


class ISPEScraper(BaseScraper):
    """Scraper for ISPE webinars"""
    
    def __init__(self):
        super().__init__(data_file="../webinars.json")
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