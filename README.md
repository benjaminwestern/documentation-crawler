# Documentation Crawler

A robust Python tool for crawling documentation websites, downloading and then exporting them to a Markdown or Raw HTML format.

## ⚠️ Important Notice

This tool is intended for legitimate documentation retrieval with proper authorisation. Before using this tool:

1. Ensure you have permission to scrape the target website
2. Review the website's terms of service regarding automated access
3. The tool checks robots.txt, but you should verify your use case is allowed
4. Use rate limiting and don't overwhelm servers with requests

**Misuse of web scraping tools can result in IP blocks, legal issues, or service disruption for others. Use responsibly.**

## Features

* **Unified Console Display:** Single-threaded display system coordinates progress bars, statistics, and logging
* **Language-Aware Crawling:** 
  - Intelligent handling of language parameters in URLs
  - English content detection (URLs without language parameters)
  - Support for multiple languages (fr, de, es, ja, ko, etc.)
* **Smart Path Filtering:** Automatically detects and respects documentation base paths
* **Efficient Processing:**
  - Parallel processing of sitemaps using ThreadPoolExecutor
  - Configurable chunk sizes and worker threads
  - Rate-limited requests to respect server constraints
* **Interactive Page Selection:**
  - Paginated display of found documents
  - Multiple selection methods (individual, ranges, all)
  - Clean, non-scrolling interface
* **Robust Error Handling:**
  - Automatic retries with exponential backoff
  - Comprehensive error reporting and logging

## Requirements

### Development Environment
1. Install [Python](https://www.python.org/downloads/) (v3.10 or higher)
2. Install [Requirements](requirements.txt)
  - `pip install -r requirements.txt`

## Usage

```bash
python main.py
```

You'll be prompted to:
1. Choose whether to enable detailed statistics
2. Store URLs in the `selected_urls` directory
3. Store raw HTML files in the `downloaded_docs` directory
4. Store converted Markdown files in the `downloaded_docs` directory
5. Provide a list of URLs to crawl (e.g., `['https://example.com/system/docs', 'https://example.com/system/docs/page2']`)
   1. If no, Enter the documentation base URL (e.g., `https://example.com/system/docs`), providing this URL will crawl all pages of `https://example.com/system/`, adding `/docs/` to the end of the URL would crawl all pages of `https://example.com/system/docs/`
   2. Select your preferred language
6.  Select which pages to download
    1.  Select individual pages by entering the page number or range of pages (e.g., `1`, `1-5`)
    2.  Select all pages by entering `all`
    3.  Select no pages by entering `none`
    4.  Confirm your selection by entering `done`

## Configuration

The crawler can be configured through the `CrawlerConfig` dataclass, which is passed to the `Crawler` class.:

```python
config = CrawlerConfig(
    base_url="https://example.com/system/docs",   # Base URL of the documentation site to crawl
    language="en",                                # Default: English
    max_workers=5,                                # Parallel processing threads
    debug=False,                                  # Enable detailed statistics
    timeout=10,                                   # Request timeout in seconds
    max_retries=3,                                # Number of retry attempts
    retry_delay=1,                                # Delay between retries
    chunk_size=3,                                 # URLs per processing chunk
)
```

## Output

URLs are saved in the `selected_urls` directory, a single file containing all the selected URLs.
Downloaded documentation is saved in the `downloaded_docs` directory, with filenames based on the URL path structure. `html` and or `md` files are saved based on input configuration.

## Error Handling

The crawler includes comprehensive error handling:
- Connection timeouts
- Rate limiting responses
- Invalid URLs
- Malformed sitemaps
- HTML parsing errors

## Notes

- English documentation is detected by the absence of a language parameter
- Non-English documentation requires the appropriate language code in the URL
- The progress display is designed to be non-intrusive and informative
- All console output is coordinated through a single display system

## License

This repository is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

[Benjamin Western](https://benjaminwestern.io)