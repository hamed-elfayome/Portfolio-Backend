"""
Comprehensive exception handlers and custom exceptions for API responses.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404
from django.db import IntegrityError
import logging
import traceback
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PortfolioAPIException(Exception):
    """Base exception for portfolio API errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(PortfolioAPIException):
    """Custom validation error with detailed field information."""
    
    def __init__(self, message: str, field_errors: Dict[str, str] = None, error_code: str = "VALIDATION_ERROR"):
        self.field_errors = field_errors or {}
        super().__init__(message, error_code, {"field_errors": self.field_errors})


class AIServiceError(PortfolioAPIException):
    """Error related to AI service operations."""
    
    def __init__(self, message: str, service: str = None, error_code: str = "AI_SERVICE_ERROR"):
        details = {"service": service} if service else {}
        super().__init__(message, error_code, details)


class FileProcessingError(PortfolioAPIException):
    """Error related to file processing operations."""
    
    def __init__(self, message: str, file_type: str = None, error_code: str = "FILE_PROCESSING_ERROR"):
        details = {"file_type": file_type} if file_type else {}
        super().__init__(message, error_code, details)


class RateLimitExceededError(PortfolioAPIException):
    """Error when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, error_code: str = "RATE_LIMIT_EXCEEDED"):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, error_code, details)


class ResourceNotFoundError(PortfolioAPIException):
    """Error when a requested resource is not found."""
    
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None, error_code: str = "RESOURCE_NOT_FOUND"):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, error_code, details)


class DatabaseError(PortfolioAPIException):
    """Error related to database operations."""
    
    def __init__(self, message: str, operation: str = None, error_code: str = "DATABASE_ERROR"):
        details = {"operation": operation} if operation else {}
        super().__init__(message, error_code, details)


class ExternalServiceError(PortfolioAPIException):
    """Error related to external service calls."""
    
    def __init__(self, message: str, service: str = None, status_code: int = None, error_code: str = "EXTERNAL_SERVICE_ERROR"):
        details = {}
        if service:
            details["service"] = service
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, error_code, details)


def custom_exception_handler(exc, context):
    """Enhanced custom exception handler for API responses."""
    start_time = time.time()
    
    # Get the original response from DRF's exception handler
    response = exception_handler(exc, context)
    
    # Extract context information
    view = context.get('view', None)
    request = context.get('request', None)
    view_name = view.__class__.__name__ if view else 'Unknown'
    request_path = request.path if request else 'Unknown'
    request_method = request.method if request else 'Unknown'
    
    # Log the error with comprehensive context
    error_context = {
        'view': view_name,
        'path': request_path,
        'method': request_method,
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown') if request else 'Unknown',
        'ip_address': _get_client_ip(request) if request else 'Unknown',
        'timestamp': time.time(),
    }
    
    # Handle different types of exceptions
    if isinstance(exc, PortfolioAPIException):
        # Handle custom portfolio exceptions
        status_code = _get_status_code_for_exception(exc)
        error_data = _format_portfolio_exception(exc, error_context)
        
        logger.error(f"Portfolio API Error: {exc.error_code} - {exc.message}", 
                    extra=error_context)
        
    elif isinstance(exc, ValidationError):
        # Handle Django validation errors
        status_code = status.HTTP_400_BAD_REQUEST
        error_data = _format_validation_error(exc, error_context)
        
        logger.warning(f"Validation Error in {view_name}: {str(exc)}", 
                      extra=error_context)
        
    elif isinstance(exc, Http404):
        # Handle 404 errors
        status_code = status.HTTP_404_NOT_FOUND
        error_data = _format_404_error(exc, error_context)
        
        logger.warning(f"Resource Not Found: {request_path}", 
                      extra=error_context)
        
    elif isinstance(exc, IntegrityError):
        # Handle database integrity errors
        status_code = status.HTTP_409_CONFLICT
        error_data = _format_integrity_error(exc, error_context)
        
        logger.error(f"Database Integrity Error in {view_name}: {str(exc)}", 
                    extra=error_context)
        
    elif response is not None:
        # Handle DRF exceptions
        status_code = response.status_code
        error_data = _format_drf_exception(exc, response, error_context)
        
        logger.error(f"DRF Exception in {view_name}: {exc.__class__.__name__} - {str(exc)}", 
                    extra=error_context)
        
    else:
        # Handle unexpected exceptions
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_data = _format_unexpected_error(exc, error_context)
        
        logger.error(f"Unexpected Error in {view_name}: {exc.__class__.__name__} - {str(exc)}", 
                    extra=error_context, exc_info=True)
    
    # Add processing time
    processing_time = round((time.time() - start_time) * 1000, 2)
    error_data['processing_time_ms'] = processing_time
    
    # Create the response
    if response is None:
        response = Response(status=status_code)
    
    response.data = error_data
    response.status_code = status_code
    
    return response


def _get_client_ip(request):
    """Extract client IP address from request."""
    if not request:
        return 'Unknown'
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _get_status_code_for_exception(exc: PortfolioAPIException) -> int:
    """Get appropriate HTTP status code for custom exceptions."""
    status_mapping = {
        'VALIDATION_ERROR': status.HTTP_400_BAD_REQUEST,
        'AI_SERVICE_ERROR': status.HTTP_503_SERVICE_UNAVAILABLE,
        'FILE_PROCESSING_ERROR': status.HTTP_422_UNPROCESSABLE_ENTITY,
        'RATE_LIMIT_EXCEEDED': status.HTTP_429_TOO_MANY_REQUESTS,
        'RESOURCE_NOT_FOUND': status.HTTP_404_NOT_FOUND,
        'DATABASE_ERROR': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'EXTERNAL_SERVICE_ERROR': status.HTTP_502_BAD_GATEWAY,
    }
    return status_mapping.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


def _format_portfolio_exception(exc: PortfolioAPIException, context: Dict) -> Dict[str, Any]:
    """Format custom portfolio exception for API response."""
    return {
        'error': {
            'type': 'PortfolioAPIException',
            'code': exc.error_code,
            'message': exc.message,
            'details': exc.details,
            'timestamp': context['timestamp'],
            'request_id': _generate_request_id(context),
        },
        'success': False,
    }


def _format_validation_error(exc: ValidationError, context: Dict) -> Dict[str, Any]:
    """Format Django validation error for API response."""
    field_errors = {}
    if hasattr(exc, 'error_dict'):
        for field, errors in exc.error_dict.items():
            field_errors[field] = [str(error) for error in errors]
    elif hasattr(exc, 'error_list'):
        field_errors['non_field_errors'] = [str(error) for error in exc.error_list]
    
    return {
        'error': {
            'type': 'ValidationError',
            'code': 'VALIDATION_ERROR',
            'message': 'Validation failed',
            'field_errors': field_errors,
            'timestamp': context['timestamp'],
            'request_id': _generate_request_id(context),
        },
        'success': False,
    }


def _format_404_error(exc: Http404, context: Dict) -> Dict[str, Any]:
    """Format 404 error for API response."""
    return {
        'error': {
            'type': 'NotFoundError',
            'code': 'RESOURCE_NOT_FOUND',
            'message': str(exc) or 'The requested resource was not found',
            'timestamp': context['timestamp'],
            'request_id': _generate_request_id(context),
        },
        'success': False,
    }


def _format_integrity_error(exc: IntegrityError, context: Dict) -> Dict[str, Any]:
    """Format database integrity error for API response."""
    return {
        'error': {
            'type': 'IntegrityError',
            'code': 'DATABASE_INTEGRITY_ERROR',
            'message': 'A database integrity constraint was violated',
            'details': {
                'constraint': str(exc),
            },
            'timestamp': context['timestamp'],
            'request_id': _generate_request_id(context),
        },
        'success': False,
    }


def _format_drf_exception(exc, response, context: Dict) -> Dict[str, Any]:
    """Format DRF exception for API response."""
    return {
        'error': {
            'type': exc.__class__.__name__,
            'code': getattr(exc, 'default_code', 'DRF_ERROR'),
            'message': str(exc),
            'details': response.data if hasattr(response, 'data') else {},
            'timestamp': context['timestamp'],
            'request_id': _generate_request_id(context),
        },
        'success': False,
    }


def _format_unexpected_error(exc: Exception, context: Dict) -> Dict[str, Any]:
    """Format unexpected error for API response."""
    return {
        'error': {
            'type': 'UnexpectedError',
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An unexpected error occurred',
            'details': {
                'exception_type': exc.__class__.__name__,
                'traceback': traceback.format_exc() if context.get('debug', False) else None,
            },
            'timestamp': context['timestamp'],
            'request_id': _generate_request_id(context),
        },
        'success': False,
    }


def _generate_request_id(context: Dict) -> str:
    """Generate a unique request ID for tracking."""
    import hashlib
    import time
    
    request_string = f"{context['path']}_{context['method']}_{context['timestamp']}"
    return hashlib.md5(request_string.encode()).hexdigest()[:12]
