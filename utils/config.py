from dataclasses import dataclass

@dataclass
class CrawlerConfig:
    """Configuration settings for the DocCrawler."""
    base_url: str
    language: str = 'en'
    max_workers: int = 10
    debug: bool = False
    timeout: int = 10
    max_retries: int = 3
    retry_delay: float = 1
    chunk_size: int = 10
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    def __post_init__(self):
        if not self.base_url.startswith("http"):
            raise ValueError("Invalid URL format. Please include the protocol (http/https).")

        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1.")

        if self.timeout < 1:
            raise ValueError("timeout must be at least 1.")

        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative.")

        if self.retry_delay < 0:
            raise ValueError("retry_delay cannot be negative.")

        if self.chunk_size < 1:
            raise ValueError("chunk_size must be at least 1.")

        if not self.user_agent:
            raise ValueError("user_agent cannot be empty.")