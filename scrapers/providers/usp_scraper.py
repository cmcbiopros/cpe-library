from datetime import datetime
from typing import List, Dict
from base_scraper import BaseScraper


class USPScraper(BaseScraper):
    """Scraper for USP trainings"""
    
    def __init__(self):
        super().__init__(data_file="../webinars.json")
        self.base_url = "https://uspharmacopeia.csod.com"
        self.trainings_url = "https://uspharmacopeia.csod.com/catalog/CustomPage.aspx?id=221000396&tab_page_id=221000396"
    
    def scrape(self):
        """Add USP trainings link"""
        try:
            print("Adding USP trainings link...")
            
            # Add a single entry linking to the USP trainings page
            webinar_data = {
                'id': 'usp-trainings',
                'title': 'USP Training Programs',
                'provider': 'USP',
                'topics': ['regulatory', 'quality-assurance', 'pharmaceutical', 'compliance'],
                'format': 'on-demand',
                'duration_min': 'variable',
                'certificate_available': True,
                'certificate_process': 'Certificate available upon completion',
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'live_date': 'on-demand',  # USP trainings are typically on-demand
                'url': 'https://uspharmacopeia.csod.com/catalog/CustomPage.aspx?id=221000396&tab_page_id=221000396',
                'description': 'Access to USP training programs and courses. Registration/login required to access training content. USP provides training on pharmaceutical standards, quality assurance, and regulatory compliance.'
            }
            
            self.add_webinar(webinar_data)
            print("Added USP trainings link")
                    
        except Exception as e:
            print(f"Error adding USP link: {e}")
    
    def _extract_topics_from_title(self, title: str) -> List[str]:
        """Extract topics from USP training title"""
        title_lower = title.lower()
        topics = []
        
        topic_keywords = {
            'pharmaceutical': 'pharmaceutical',
            'pharmacopeia': 'pharmaceutical',
            'usp': 'pharmaceutical',
            'quality assurance': 'quality-assurance',
            'quality control': 'quality-control',
            'regulatory': 'regulatory',
            'compliance': 'compliance',
            'gmp': 'gmp',
            'good manufacturing practice': 'gmp',
            'validation': 'validation',
            'analytical': 'analytical',
            'microbiology': 'microbiology',
            'chemistry': 'chemistry',
            'reference standards': 'reference-standards',
            'monographs': 'monographs',
            'general chapters': 'general-chapters',
            'drug substance': 'drug-substance',
            'drug product': 'drug-product',
            'excipients': 'excipients',
            'biologics': 'biologics',
            'biotechnology': 'biotech',
            'sterilization': 'sterilization',
            'packaging': 'packaging',
            'stability': 'stability',
            'impurities': 'impurities',
            'dissolution': 'dissolution',
            'bioavailability': 'bioavailability',
            'bioequivalence': 'bioequivalence'
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in title_lower:
                topics.append(topic)
        
        # Default topics if none found
        if not topics:
            topics = ['pharmaceutical', 'regulatory']
        
        return topics 