import os
import concurrent.futures
import logging
import shutil
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse
from threading import Lock
from xml.etree import ElementTree as ET
import requests
import time

from utils.config import CrawlerConfig
from utils.display import UnifiedDisplay
from utils.url_processor import URLProcessor
from converters.html_to_md import HTMLToMarkdownConverter

logger = logging.getLogger(__name__)

class DocCrawler:
    """Main crawler class that orchestrates the documentation crawling process."""
    
    def __init__(self, config: CrawlerConfig):
        self.config = config
        parsed_url = urlparse(config.base_url)
        self.domain = parsed_url.netloc
        
        # Initialize display
        self.display = UnifiedDisplay(debug=config.debug)
        
        # Extract base path for filtering
        path_parts = parsed_url.path.rstrip('/').split('/')
        if path_parts[-1] in ['overview', 'introduction', 'docs']:
            path_parts.pop()
        self.base_path = '/'.join(path_parts)
        
        # Initialize components
        self.url_processor = URLProcessor(
            domain=self.domain,
            base_path=self.base_path,
            headers={'User-Agent': config.user_agent},
            timeout=config.timeout
        )
        
        self.converter = HTMLToMarkdownConverter()
        
        # State management
        self.visited_urls = set()
        self.sitemap = {}
        self.sitemap_lock = Lock()
        
        logger.info(f"Initializing crawler for domain: {self.domain}")
        logger.info(f"Base path filter: {self.base_path}")
        logger.info(f"Language filter: {config.language}")

    def make_request(self, url: str, method: str = 'get') -> requests.Response:
        """Make HTTP request with retry logic."""
        headers = {'User-Agent': self.config.user_agent}
        
        for attempt in range(self.config.max_retries):
            try:
                if method == 'get':
                    response = requests.get(
                        url,
                        headers=headers,
                        timeout=self.config.timeout
                    )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt + 1 < self.config.max_retries:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise

    def process_sitemap_url(self, url: str) -> List[Tuple[str, str]]:
        """Process a single sitemap URL."""
        try:
            if url.endswith('.xml'):
                response = self.make_request(url)
                root = ET.fromstring(response.content)
                namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                urls = root.findall('.//ns:loc', namespaces)
                
                results = []
                for loc in urls:
                    page_url = loc.text
                    self.display.update_stats(
                        processed=1,
                        current_url=url
                    )
                    
                    if not page_url.endswith('.xml') and self.url_processor.is_relevant_url(page_url, self.config.language):
                        self.display.update_stats(relevant=1)
                        title = self.get_page_title(page_url)
                        results.append((page_url, title))
                
                return results
                
            elif self.url_processor.is_relevant_url(url, self.config.language):
                self.display.update_stats(
                    processed=1,
                    relevant=1,
                    current_url=url
                )
                return [(url, self.get_page_title(url))]
            
            self.display.update_stats(processed=1)
            return []
            
        except Exception as e:
            self.display.update_stats(errors=1)
            logger.error(f"Error processing URL {url}: {e}")
            return []

    def get_page_title(self, url: str) -> str:
        """Extract and clean page title from URL."""
        try:
            response = self.make_request(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else url
            return self.converter.clean_title(title, url)
        except Exception as e:
            logger.debug(f"Could not get title for {url}: {e}")
            return url

    def process_sitemap_chunk(self, urls: List[str]) -> List[Tuple[str, str]]:
        """Process a chunk of sitemap URLs."""
        results = []
        for url in urls:
            try:
                chunk_results = self.process_sitemap_url(url)
                results.extend(chunk_results)
            except Exception as e:
                self.stats_display.update(errors=1)
                logger.error(f"Error processing URL chunk: {e}")
        return results

    def parallel_sitemap_processing(self, sitemap_urls: List[str]) -> None:
        """Process sitemap URLs in parallel with unified display."""
        url_chunks = [
            sitemap_urls[i:i + self.config.chunk_size] 
            for i in range(0, len(sitemap_urls), self.config.chunk_size)
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_chunk = {
                executor.submit(self.process_sitemap_chunk, chunk): chunk 
                for chunk in url_chunks
            }
            
            with self.display.create_progress_bar(len(sitemap_urls)) as pbar:
                for future in concurrent.futures.as_completed(future_to_chunk):
                    try:
                        results = future.result()
                        with self.sitemap_lock:
                            for url, title in results:
                                self.sitemap[url] = title
                        pbar.update(len(future_to_chunk[future]))
                        
                    except Exception as e:
                        self.display.update_stats(errors=1)
                        logger.error(f"Error processing chunk: {e}")

    def parse_sitemap(self, sitemap_url: Optional[str] = None) -> None:
        """Parse XML sitemap and collect URLs."""
        if not sitemap_url:
            sitemap_url = self.url_processor.find_sitemap_url(self.config.base_url)
            if not sitemap_url:
                logger.error("No sitemap found!")
                return

        try:
            logger.info(f"Parsing main sitemap: {sitemap_url}")
            sitemap_urls = self.url_processor.parse_sitemap(sitemap_url)
            logger.info(f"Found {len(sitemap_urls)} potential sitemaps/URLs")
            
            self.parallel_sitemap_processing(sitemap_urls)
            
        except Exception as e:
            logger.error(f"Error parsing sitemap: {e}")

    def select_pages(self) -> List[str]:
        """Interactive page selection interface."""
        # Clear terminal first
        os.system('cls' if os.name == 'nt' else 'clear')
        
        logger.info("Preparing page selection interface...")
        
        # Create a list of tuples with index, url, and truncated title
        pages = []
        for i, (url, title) in enumerate(self.sitemap.items(), 1):
            # Truncate title if too long
            display_title = f"{title[:60]}..." if len(title) > 60 else title
            pages.append((i, url, display_title))

        # Create pages in groups of 10 for easier viewing
        page_groups = [pages[i:i + 10] for i in range(0, len(pages), 10)]
        current_group = 0
        selected_indices = set()

        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nSelected pages:", len(selected_indices))
            print("\nCurrent pages (showing 10 at a time):")
            print("─" * shutil.get_terminal_size().columns)
            
            # Display current group of pages
            for i, url, title in page_groups[current_group]:
                selected = "✓" if i in selected_indices else " "
                print(f"{i:3d}. [{selected}] {title}")
            
            print("─" * shutil.get_terminal_size().columns)
            print("\nControls:")
            print("- Enter page numbers (e.g., '1 3 5' or '1-5')")
            print("- 'n' for next page")
            print("- 'p' for previous page")
            print("- 'done' to finish selection")
            print("- 'all' to select all pages")
            print(f"\nPage {current_group + 1}/{len(page_groups)}")

            choice = input("\nEnter selection: ").strip().lower()

            if choice == 'done':
                break
            elif choice == 'n' and current_group < len(page_groups) - 1:
                current_group += 1
            elif choice == 'p' and current_group > 0:
                current_group -= 1
            elif choice == 'all':
                selected_indices = set(i for i, _, _ in pages)
            else:
                try:
                    for part in choice.split():
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            for num in range(start, end + 1):
                                if num in selected_indices:
                                    selected_indices.remove(num)
                                else:
                                    selected_indices.add(num)
                        else:
                            num = int(part)
                            if num in selected_indices:
                                selected_indices.remove(num)
                            else:
                                selected_indices.add(num)
                except ValueError:
                    print("Invalid input. Please try again.")
                    time.sleep(1)

        # Convert selected indices back to URLs
        selected_urls = [url for i, url, _ in pages if i in selected_indices]
        logger.info(f"Selected {len(selected_urls)} pages")
        return selected_urls

    def process_selected_pages(self, selected_urls: List[str], store_raw_html: bool, store_markdown: bool) -> None:
        """Download, convert, and save selected pages."""
        output_dir = Path('downloaded_urls')
        output_dir.mkdir(exist_ok=True)
        
        with self.display.create_progress_bar(len(selected_urls)) as pbar:
            for i in range(len(selected_urls)):
                url = selected_urls[i]
                try:
                    response = self.make_request(url)

                    urlpath = urlparse(url).path.strip('/')

                    # Save markdown content if needed
                    if store_markdown:
                        markdown_content = self.converter.convert(response.text)
                        markdown_filename = Path(urlpath).with_suffix('.md')
                        filepath = output_dir / markdown_filename
                        filepath.parent.mkdir(parents=True, exist_ok=True)
                        filepath.write_text(markdown_content, encoding='utf-8')
                    
                    # Save raw HTML content if needed
                    if store_raw_html:
                        html_filename = Path(urlpath).with_suffix('.html')
                        html_filepath = output_dir / html_filename
                        html_filepath.parent.mkdir(parents=True, exist_ok=True)
                        html_filepath.write_text(response.text, encoding='utf-8')

                    # Update display stats and progress bar
                    self.display.update_stats(processed=1)
                    pbar.update(1)
                    
                except Exception as e:
                    self.display.update_stats(errors=1)
                    logger.error(f"Error processing {url}: {e}")

    def store_urls(self, selected_urls: List[str]) -> None:
        """Store captured URLs in a text file."""
        output_dir = Path('selected_urls')
        output_dir.mkdir(exist_ok=True)
        if not selected_urls:
            return
        first_url = selected_urls[0]
        rootpath = urlparse(first_url).path.split('/')

        if len(rootpath) > 1:
            rootpath = rootpath[1]
        else:
            rootpath = 'default'

        filepath = output_dir / rootpath / 'selected_urls.txt'
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with filepath.open('w', encoding='utf-8') as f:
            for url in self.sitemap:
                f.write(f"{url}\n")
        
        logger.info(f"Stored captured URLs in: {filepath}")