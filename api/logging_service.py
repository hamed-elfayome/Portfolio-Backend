"""
Comprehensive logging service for the portfolio API.
"""
import logging
import logging.handlers
import json
import time
import traceback
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
import threading

logger = logging.getLogger(__name__)


class APILogger:
    """Enhanced API logging service with structured logging and monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger('portfolio_api')
        self.performance_logger = logging.getLogger('portfolio_performance')
        self.security_logger = logging.getLogger('portfolio_security')
        self.ai_logger = logging.getLogger('portfolio_ai')
        self.error_logger = logging.getLogger('portfolio_errors')
        
        # Thread-local storage for request context
        self._local = threading.local()
        
        # Performance metrics
        self._performance_metrics = {}
        
        # Security monitoring
        self._security_events = []
        
        # AI service monitoring
        self._ai_metrics = {}
    
    def set_request_context(self, request_id: str, user_id: str = None, 
                          ip_address: str = None, user_agent: str = None):
        """Set request context for logging."""
        self._local.request_id = request_id
        self._local.user_id = user_id
        self._local.ip_address = ip_address
        self._local.user_agent = user_agent
        self._local.start_time = time.time()
    
    def get_request_context(self) -> Dict[str, Any]:
        """Get current request context."""
        return {
            'request_id': getattr(self._local, 'request_id', None),
            'user_id': getattr(self._local, 'user_id', None),
            'ip_address': getattr(self._local, 'ip_address', None),
            'user_agent': getattr(self._local, 'user_agent', None),
            'start_time': getattr(self._local, 'start_time', None),
        }
    
    def log_api_request(self, method: str, path: str, status_code: int, 
                       response_time: float, user_id: str = None, 
                       additional_data: Dict[str, Any] = None):
        """Log API request with comprehensive metrics."""
        context = self.get_request_context()
        
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'type': 'api_request',
            'method': method,
            'path': path,
            'status_code': status_code,
            'response_time_ms': round(response_time * 1000, 2),
            'user_id': user_id,
            'request_id': context.get('request_id'),
            'ip_address': context.get('ip_address'),
            'user_agent': context.get('user_agent'),
        }
        
        if additional_data:
            log_data.update(additional_data)
        
        # Log based on status code
        if status_code >= 500:
            self.error_logger.error(f"API Error: {method} {path}", extra=log_data)
        elif status_code >= 400:
            self.logger.warning(f"API Warning: {method} {path}", extra=log_data)
        else:
            self.logger.info(f"API Request: {method} {path}", extra=log_data)
        
        # Update performance metrics
        self._update_performance_metrics(method, path, status_code, response_time)
    
    def log_ai_service_call(self, service: str, operation: str, 
                           success: bool, response_time: float,
                           tokens_used: int = None, cost: float = None,
                           error_message: str = None):
        """Log AI service calls with detailed metrics."""
        context = self.get_request_context()
        
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'type': 'ai_service_call',
            'service': service,
            'operation': operation,
            'success': success,
            'response_time_ms': round(response_time * 1000, 2),
            'tokens_used': tokens_used,
            'cost': cost,
            'error_message': error_message,
            'request_id': context.get('request_id'),
        }
        
        if success:
            self.ai_logger.info(f"AI Service: {service}.{operation}", extra=log_data)
        else:
            self.ai_logger.error(f"AI Service Error: {service}.{operation}", extra=log_data)
        
        # Update AI metrics
        self._update_ai_metrics(service, operation, success, response_time, tokens_used, cost)
    
    def log_security_event(self, event_type: str, severity: str, 
                          description: str, ip_address: str = None,
                          user_id: str = None, additional_data: Dict[str, Any] = None):
        """Log security events with appropriate severity."""
        context = self.get_request_context()
        
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'type': 'security_event',
            'event_type': event_type,
            'severity': severity,
            'description': description,
            'ip_address': ip_address or context.get('ip_address'),
            'user_id': user_id or context.get('user_id'),
            'request_id': context.get('request_id'),
        }
        
        if additional_data:
            log_data.update(additional_data)
        
        # Log based on severity
        if severity == 'critical':
            self.security_logger.critical(f"Security Critical: {event_type}", extra=log_data)
        elif severity == 'high':
            self.security_logger.error(f"Security High: {event_type}", extra=log_data)
        elif severity == 'medium':
            self.security_logger.warning(f"Security Medium: {event_type}", extra=log_data)
        else:
            self.security_logger.info(f"Security Low: {event_type}", extra=log_data)
        
        # Store security event for monitoring
        self._store_security_event(log_data)
    
    def log_database_operation(self, operation: str, table: str, 
                              success: bool, execution_time: float,
                              rows_affected: int = None, error_message: str = None):
        """Log database operations with performance metrics."""
        context = self.get_request_context()
        
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'type': 'database_operation',
            'operation': operation,
            'table': table,
            'success': success,
            'execution_time_ms': round(execution_time * 1000, 2),
            'rows_affected': rows_affected,
            'error_message': error_message,
            'request_id': context.get('request_id'),
        }
        
        if success:
            self.performance_logger.info(f"DB Operation: {operation} on {table}", extra=log_data)
        else:
            self.error_logger.error(f"DB Error: {operation} on {table}", extra=log_data)
    
    def log_cache_operation(self, operation: str, key: str, 
                           success: bool, hit: bool = None,
                           response_time: float = None):
        """Log cache operations with hit/miss metrics."""
        context = self.get_request_context()
        
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'type': 'cache_operation',
            'operation': operation,
            'key': key,
            'success': success,
            'hit': hit,
            'response_time_ms': round(response_time * 1000, 2) if response_time else None,
            'request_id': context.get('request_id'),
        }
        
        if success:
            self.performance_logger.info(f"Cache {operation}: {key}", extra=log_data)
        else:
            self.error_logger.warning(f"Cache Error: {operation} {key}", extra=log_data)
    
    def log_file_operation(self, operation: str, filename: str, 
                          file_size: int, success: bool,
                          error_message: str = None):
        """Log file operations with size and success metrics."""
        context = self.get_request_context()
        
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'type': 'file_operation',
            'operation': operation,
            'filename': filename,
            'file_size_bytes': file_size,
            'success': success,
            'error_message': error_message,
            'request_id': context.get('request_id'),
        }
        
        if success:
            self.logger.info(f"File {operation}: {filename}", extra=log_data)
        else:
            self.error_logger.error(f"File Error: {operation} {filename}", extra=log_data)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log errors with full context and stack trace."""
        request_context = self.get_request_context()
        
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'type': 'error',
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'request_id': request_context.get('request_id'),
        }
        
        if context:
            log_data.update(context)
        
        self.error_logger.error(f"Error: {error.__class__.__name__}", extra=log_data)
    
    def log_performance_metric(self, metric_name: str, value: float, 
                              unit: str = 'ms', tags: Dict[str, str] = None):
        """Log custom performance metrics."""
        context = self.get_request_context()
        
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'type': 'performance_metric',
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'tags': tags or {},
            'request_id': context.get('request_id'),
        }
        
        self.performance_logger.info(f"Metric: {metric_name}={value}{unit}", extra=log_data)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self._performance_metrics.copy()
    
    def get_ai_metrics(self) -> Dict[str, Any]:
        """Get current AI service metrics."""
        return self._ai_metrics.copy()
    
    def get_security_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent security events."""
        return self._security_events[-limit:] if self._security_events else []
    
    def _update_performance_metrics(self, method: str, path: str, 
                                  status_code: int, response_time: float):
        """Update performance metrics."""
        key = f"{method}_{path}"
        
        if key not in self._performance_metrics:
            self._performance_metrics[key] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'status_codes': {},
                'last_updated': time.time()
            }
        
        metrics = self._performance_metrics[key]
        metrics['count'] += 1
        metrics['total_time'] += response_time
        metrics['avg_time'] = metrics['total_time'] / metrics['count']
        metrics['min_time'] = min(metrics['min_time'], response_time)
        metrics['max_time'] = max(metrics['max_time'], response_time)
        metrics['status_codes'][status_code] = metrics['status_codes'].get(status_code, 0) + 1
        metrics['last_updated'] = time.time()
    
    def _update_ai_metrics(self, service: str, operation: str, 
                          success: bool, response_time: float,
                          tokens_used: int = None, cost: float = None):
        """Update AI service metrics."""
        key = f"{service}_{operation}"
        
        if key not in self._ai_metrics:
            self._ai_metrics[key] = {
                'count': 0,
                'success_count': 0,
                'failure_count': 0,
                'total_time': 0,
                'avg_time': 0,
                'total_tokens': 0,
                'total_cost': 0,
                'last_updated': time.time()
            }
        
        metrics = self._ai_metrics[key]
        metrics['count'] += 1
        metrics['total_time'] += response_time
        metrics['avg_time'] = metrics['total_time'] / metrics['count']
        
        if success:
            metrics['success_count'] += 1
        else:
            metrics['failure_count'] += 1
        
        if tokens_used:
            metrics['total_tokens'] += tokens_used
        
        if cost:
            metrics['total_cost'] += cost
        
        metrics['last_updated'] = time.time()
    
    def _store_security_event(self, event_data: Dict[str, Any]):
        """Store security event for monitoring."""
        self._security_events.append(event_data)
        
        # Keep only last 1000 events
        if len(self._security_events) > 1000:
            self._security_events = self._security_events[-1000:]


class LoggingMiddleware:
    """Middleware for automatic request/response logging."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_logger = APILogger()
    
    def __call__(self, request):
        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())[:12]
        
        # Set request context
        self.api_logger.set_request_context(
            request_id=request_id,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Add request ID to request
        request.request_id = request_id
        
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log API request
        self.api_logger.log_api_request(
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            response_time=response_time
        )
        
        # Add request ID to response headers
        response['X-Request-ID'] = request_id
        
        return response
    
    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Global logger instance
api_logger = APILogger()
