"""Logging configuration with PII safety."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import re


class PIIRedactingFormatter(logging.Formatter):
    """Formatter that redacts potential PII from logs."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Patterns for PII detection
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        self.ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
        self.credit_card_pattern = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
    
    def format(self, record):
        msg = super().format(record)
        
        # Redact potential PII
        msg = self.email_pattern.sub('[EMAIL_REDACTED]', msg)
        msg = self.phone_pattern.sub('[PHONE_REDACTED]', msg)
        msg = self.ssn_pattern.sub('[SSN_REDACTED]', msg)
        msg = self.credit_card_pattern.sub('[CC_REDACTED]', msg)
        
        return msg


def setup_logging(level: str = "INFO", log_file: Path = None):
    """Setup application logging with PII safety."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = PIIRedactingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)