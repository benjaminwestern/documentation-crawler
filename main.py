import sys
import inquirer
from typing import List
import logging
from utils.config import CrawlerConfig
from crawler.crawler import DocCrawler
from utils.logging import setup_logging

logger = logging.getLogger(__name__)

def select_language() -> str:
    """Language selection interface."""
    languages = [
        ('English', 'en'),
        ('French (Français)', 'fr'),
        ('German (Deutsch)', 'de'),
        ('Spanish (Español)', 'es'),
        ('Portuguese (Português)', 'pt-BR'),
        ('Japanese (日本語)', 'ja'),
        ('Korean (한국어)', 'ko'),
        ('Chinese (中文)', 'zh-CN'),
        ('Italian (Italiano)', 'it'),
        ('Indonesian (Bahasa Indonesia)', 'id'),
        ('Spanish - Latin America (Español)', 'es-419')
    ]

    questions = [
        inquirer.List('language',
                     message="Select documentation language:",
                     choices=languages,
                     default='en')
    ]

    answers = inquirer.prompt(questions)
    return answers['language'] if answers else 'en'

def main():
    """Main execution function."""
    selected_urls = []
    urls = []
    setup_logging()
    
    try:        
        questions = [
            inquirer.Confirm('debug',
                            message="Enable detailed statistics?",
                            default=False),
            inquirer.Confirm('store_urls', 
                            message="Store URLs in a file?",
                            default=True),
            inquirer.Confirm('store_raw_html', 
                            message="Store raw HTML content?",
                            default=False),
            inquirer.Confirm('store_markdown',
                            message="Store markdown content?",
                            default=True),
            inquirer.Confirm('store_text',
                            message="Store as plain text content?",
                            default=False),
            inquirer.Confirm('provide_url_list',
                            message="Provide a list of URLs to export?",
                            default=False),
            inquirer.Confirm('multiple_urls',
                            message="Crawl multiple paths?",
                            default=False)
        ]
        answers = inquirer.prompt(questions)

        debug_mode = answers['debug'] if answers else False
        store_urls = answers['store_urls'] if answers else False
        store_raw_html = answers['store_raw_html'] if answers else False
        store_markdown = answers['store_markdown'] if answers else False
        store_text = answers['store_text'] if answers else False
        provide_url_list = answers['provide_url_list'] if answers else False
        multiple_urls = answers['multiple_urls'] if answers else False

        if not store_raw_html and not store_markdown and not store_text:
            logger.warning("No content will be stored. Exiting...")
            logger.warning("Please enable at least one content storage option.")
            return
        
        config = CrawlerConfig(
            base_url="",
            debug=debug_mode
        )
        
        if multiple_urls:
            print("Enter the base URLs to crawl (one per line, 'done' to finish):")
            while True:
                url = input().strip()
                if url.lower() == 'done':
                    break
                urls.append(url)
                
            if not urls:
                logger.warning("No URLs provided. Exiting...")
                return
            
            language = select_language()
            config.language = language
            try:
              crawler = DocCrawler(config, urls)
            except ValueError as e:
              logger.error(e)
              return
                
            print("Building sitemap...")
            crawler.parse_sitemap(urls)
            
            if not crawler.sitemap:
                logger.error("No pages found!")
                return
            
            print(f"\nFound {len(crawler.sitemap)} relevant pages.")
            selected_urls = crawler.select_pages()
            
            if not selected_urls:
                logger.warning("No pages selected.")
                return
        
        elif provide_url_list:
            url_file = input("Enter the path to the URL list: ")
            with open(url_file, 'r') as f:
                urls = f.readlines()
                urls = [url.strip() for url in urls if url.strip()]
                if not urls:
                    logger.warning("No URLs found in the file. Exiting...")
                    return
                for url in urls:
                    if not url.startswith("http"): # TODO: Improve URL validation
                        logger.warning(f"Invalid URL found: {url}")
                        return
                selected_urls = urls
                
            
            
            language = select_language()
            config.language = language
            
            if urls:
              config.base_url = urls[0]
            else:
              config.base_url = ""
            crawler = DocCrawler(config, urls)

        else:
            url = input("Enter the base URL to crawl: ")
            language = select_language()
            config.language = language
            config.base_url = url
            crawler = DocCrawler(config, [url])

            print("Building sitemap...")
            crawler.parse_sitemap([url])
            
            if not crawler.sitemap:
                logger.error("No pages found!")
                return
            
            print(f"\nFound {len(crawler.sitemap)} relevant pages.")
            selected_urls = crawler.select_pages()
            
            if not selected_urls:
                logger.warning("No pages selected.")
                return
        
        if store_urls:
            crawler.store_urls(selected_urls)
        
        crawler.process_selected_pages(selected_urls, store_raw_html, store_markdown, store_text)
        logger.info("Processing complete!")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()