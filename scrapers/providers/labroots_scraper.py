import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from base_scraper import BaseScraper


class LabrootsScraper(BaseScraper):
    """Scraper for Labroots webinars"""
    
    def __init__(self):
        super().__init__(data_file="../src/webinars.json")
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