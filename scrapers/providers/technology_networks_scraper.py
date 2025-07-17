import re
from datetime import datetime
from typing import Dict, Optional
from bs4 import BeautifulSoup
from base_scraper import BaseScraper


class TechnologyNetworksScraper(BaseScraper):
    """Scraper for Technology Networks webinars"""
    
    def __init__(self):
        super().__init__(data_file="../webinars.json")
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