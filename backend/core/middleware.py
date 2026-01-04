"""
Request/Response logging middleware for IGNISYL backend.
Provides comprehensive HTTP request logging with timing and status codes.
"""

import logging
import time
import sys
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure console handler with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m',      # Reset
    }

    def format(self, record):
        # Add color based on level
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format the message
        formatted = super().format(record)
        return f"{color}{formatted}{reset}"


def setup_logging():
    """Configure logging for the application"""
    # Create formatter
    formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from other libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return logging.getLogger("ignisyl")


# Create module-level logger
logger = setup_logging()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    Shows method, path, status code, and response time.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("ignisyl.http")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for static files and health checks (reduce noise)
        path = request.url.path
        if path.startswith("/static") or path == "/favicon.ico":
            return await call_next(request)

        # Start timing
        start_time = time.perf_counter()

        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            status_code = response.status_code

            # Determine log level and emoji based on status
            if status_code < 300:
                emoji = "[OK]"
                log_func = self.logger.info
            elif status_code < 400:
                emoji = "[->]"
                log_func = self.logger.info
            elif status_code == 401:
                emoji = "[!!]"
                log_func = self.logger.warning
            elif status_code == 403:
                emoji = "[NO]"
                log_func = self.logger.warning
            elif status_code == 404:
                emoji = "[??]"
                log_func = self.logger.warning
            elif status_code < 500:
                emoji = "[!!]"
                log_func = self.logger.warning
            else:
                emoji = "[XX]"
                log_func = self.logger.error

            # Log the request/response
            log_func(
                f"{emoji} {method:6} {path:40} -> {status_code} ({duration_ms:7.2f}ms) [{client_ip}]"
            )

            return response

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error(
                f"[XX] {method:6} {path:40} -> EXCEPTION ({duration_ms:7.2f}ms) [{client_ip}] - {str(e)}"
            )
            raise


def log_startup_banner():
    """Print startup banner to console"""
    banner = """
============================================================
     IGNISYL - AI-Powered Insider Threat Detection
============================================================
    """
    print(banner)


def log_component_status(component: str, status: str = "OK"):
    """Log component initialization status"""
    if status == "OK":
        logger.info(f"[OK] {component}")
    elif status == "WARN":
        logger.warning(f"[!!] {component}")
    else:
        logger.error(f"[XX] {component}")


def log_ready():
    """Log server ready message"""
    logger.info("=" * 60)
    logger.info("[READY] IGNISYL Server is running and monitoring threats")
    logger.info("=" * 60)
