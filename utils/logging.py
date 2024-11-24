import logging
import sys
from typing import Optional

def setup_logging(level: int = logging.INFO, 
                 log_file: Optional[str] = None) -> None:
    """Configure logging for the application."""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optionally add file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Quiet down some chatty libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)