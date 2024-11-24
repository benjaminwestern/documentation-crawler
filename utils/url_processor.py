from typing import List, Optional
from urllib.parse import urljoin, urlparse, parse_qs
import xml.etree.ElementTree as ET
import requests
import logging
import re

logger = logging.getLogger(__name__)

class URLProcessor:
    """Handles URL processing, validation, and sitemap parsing."""
    
    def __init__(self, domain: str, base_path: str, headers: dict, timeout: int):
        self.domain = domain
        self.base_path = base_path
        self.headers = headers
        self.timeout = timeout

    def is_relevant_url(self, url: str, language: str) -> bool:
        """Check if URL is relevant based on domain, path, and language."""
        parsed_url = urlparse(url)
        if parsed_url.netloc != self.domain:
            return False
            
        if not parsed_url.path.startswith(self.base_path):
            return False

        query_params = parse_qs(parsed_url.query)
        url_language = query_params.get('hl', [None])[0]

        if language == 'en':
            return url_language is None
        
        return url_language == language

    def find_sitemap_url(self, base_url: str) -> Optional[str]:
        """Try to find sitemap URL from robots.txt or common locations."""
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            logger.info(f"Checking robots.txt at {robots_url}")
            response = requests.get(robots_url, headers=self.headers, timeout=self.timeout)
            
            sitemap_match = re.search(r'Sitemap: (.*)', response.text)
            if sitemap_match:
                return sitemap_match.group(1)

            # Try common sitemap locations
            common_paths = ['/sitemap.xml', '/sitemap_index.xml', '/sitemap/sitemap.xml']
            for path in common_paths:
                url = urljoin(base_url, path)
                try:
                    requests.get(url, headers=self.headers, timeout=self.timeout)
                    return url
                except requests.RequestException:
                    continue
                    
        except requests.RequestException as e:
            logger.error(f"Error finding sitemap: {e}")
        return None

    def parse_sitemap(self, sitemap_url: str) -> List[str]:
        """Parse XML sitemap and return list of URLs."""
        try:
            response = requests.get(sitemap_url, headers=self.headers, timeout=self.timeout)
            root = ET.fromstring(response.content)
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            return [loc.text for loc in root.findall('.//ns:loc', namespaces)]
            
        except Exception as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
            return []