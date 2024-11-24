from bs4 import BeautifulSoup
from markdownify import MarkdownConverter
import logging
import re

logger = logging.getLogger(__name__)

class HTMLToMarkdownConverter:
    """Converts HTML content to Markdown format."""
    
    @staticmethod
    def convert(html_content: str) -> str:
        """Convert HTML content to markdown."""
        if html_content is None or html_content == '':
            return ''
        
        # Parse HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        for element in soup.find_all(['picture', 'header', 'footer', 'nav', 'script', 'style', 'button']):
            element.decompose()

        # Convert to markdown
        markdown_content = MarkdownConverter().convert_soup(soup)
        
        return markdown_content

    @staticmethod
    def clean_title(title: str, url: str) -> str:
        """Clean and format page title."""
        if title is None or title == '':
            return url
        
        # Remove common suffixes
        title = re.sub(r'\s*\|\s*Google Cloud$', '', title)

        return title.strip()