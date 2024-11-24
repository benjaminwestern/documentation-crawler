import time
import shutil
import logging
from queue import Queue
from threading import Lock
from tqdm import tqdm

logger = logging.getLogger(__name__)

class UnifiedDisplay:
    """Manages all console output including logs, stats, and progress."""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.stats = {
            'processed': 0,
            'relevant': 0,
            'errors': 0,
            'current_url': '',
            'start_time': time.time()
        }
        self.lock = Lock()
        self.terminal_width = shutil.get_terminal_size().columns
        self.last_update = 0
        self.update_interval = 0.1
        self.progress_bar = None
        
        self.log_handler = self.create_log_handler()
        logger.setLevel(logging.INFO if not debug else logging.DEBUG)
        logger.handlers = []
        logger.addHandler(self.log_handler)
        
        self.message_queue = Queue()
        self.last_message = ""

    def create_log_handler(self):
        class ProgressBarHandler(logging.Handler):
            def __init__(self, display):
                super().__init__()
                self.display = display

            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.display.show_message(msg, level=record.levelname)
                except Exception:
                    self.handleError(record)

        handler = ProgressBarHandler(self)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        return handler

    def show_message(self, message: str, level: str = 'INFO') -> None:
        with self.lock:
            if self.progress_bar:
                self.progress_bar.clear()
                
                if level in ['ERROR', 'CRITICAL']:
                    print(f"\033[91m{message}\033[0m")
                elif level == 'WARNING':
                    print(f"\033[93m{message}\033[0m")
                else:
                    print(message)
                
                self.progress_bar.refresh()
            else:
                print(message)
            
            self.last_message = message

    def update_stats(self, **kwargs) -> None:
        with self.lock:
            for key, value in kwargs.items():
                if isinstance(value, (int, float)):
                    self.stats[key] = self.stats.get(key, 0) + value
                else:
                    self.stats[key] = value
            
            if self.progress_bar:
                self.progress_bar.set_description(self.get_status_line())

    def get_status_line(self) -> str:
        elapsed = time.time() - self.stats['start_time']
        rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
        return (f"Processed: {self.stats['processed']:,} | "
                f"Relevant: {self.stats['relevant']:,} | "
                f"Errors: {self.stats['errors']} | "
                f"Rate: {rate:.1f}/s")

    def create_progress_bar(self, total: int, desc: str = None) -> tqdm:
        self.progress_bar = tqdm(
            total=total,
            desc=desc or self.get_status_line(),
            position=0,
            leave=True,
            dynamic_ncols=True
        )
        return self.progress_bar