from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from base_scraper import BaseScraper


class FDACDERScraper(BaseScraper):
    """Scraper for FDA CDER training courses and webinars"""
    
    def __init__(self):
        super().__init__(data_file="../src/webinars.json")
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
                if course_data and course_data.get('ce_credits', 0) > 0:
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