import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from base_scraper import BaseScraper


class PMIScraper(BaseScraper):
    """Scraper for PMI webinars"""
    
    def __init__(self):
        super().__init__(data_file="../webinars.json")
        self.base_url = "https://www.projectmanagement.com"
        self.webinars_url = "https://www.projectmanagement.com/webinars/webinarmainondemand.cfm"
    
    def scrape(self):
        """Add PMI on-demand webinars link"""
        try:
            print("Adding PMI on-demand webinars link...")
            
            # Add a single entry linking to the PMI on-demand webinars page
            # Check if PMI entry already exists to preserve original date_added
            existing_pmi = next((w for w in self.webinars if w['id'] == 'pmi-on-demand-webinars'), None)
            date_added = existing_pmi['date_added'] if existing_pmi else datetime.now().strftime('%Y-%m-%d')
            
            webinar_data = {
                'id': 'pmi-on-demand-webinars',
                'title': 'PMI On-Demand Webinars',
                'provider': 'PMI',
                'topics': ['project-management'],
                'format': 'on-demand',
                'duration_min': 'variable',
                'certificate_available': True,
                'certificate_process': 'PDUs available upon completion',
                'date_added': date_added,
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