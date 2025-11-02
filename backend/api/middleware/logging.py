"""Logging middleware for API requests."""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        # Start timer
        start_time = time.time()
        
        # Get request details
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log successful request
            logger.info(
                "API request",
                method=method,
                url=url,
                status_code=response.status_code,
                duration_ms=f"{duration * 1000:.2f}",
                client_ip=client_ip
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = f"{duration:.4f}"
            
            return response
        
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "API request failed",
                method=method,
                url=url,
                error=str(e),
                duration_ms=f"{duration * 1000:.2f}",
                client_ip=client_ip,
                exc_info=True
            )
            
            raise


