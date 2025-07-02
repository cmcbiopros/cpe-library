import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from base_scraper import BaseScraper


class XtalksScraper(BaseScraper):
    """Scraper for Xtalks webinars"""
    
    def __init__(self):
        super().__init__(data_file="../src/webinars.json")
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