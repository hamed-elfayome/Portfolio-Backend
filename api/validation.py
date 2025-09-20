"""
Comprehensive input validation utilities for the portfolio API.
"""
import re
import json
import logging
from typing import Dict, List, Any, Optional, Union
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email, URLValidator
from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers
from .exceptions import ValidationError, FileProcessingError

logger = logging.getLogger(__name__)


class InputValidator:
    """Comprehensive input validation service."""
    
    # Common validation patterns
    PATTERNS = {
        'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE),
        'slug': re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$'),
        'phone': re.compile(r'^\+?1?-?\.?\s?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$'),
        'github_username': re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$'),
        'linkedin_username': re.compile(r'^[a-zA-Z0-9-]{3,100}$'),
        'safe_string': re.compile(r'^[a-zA-Z0-9\s\-_.,!?@#$%^&*()+=\[\]{}|\\:";\'<>?/~`]*$'),
    }
    
    # File type validation
    ALLOWED_FILE_TYPES = {
        'pdf': ['application/pdf'],
        'text': ['text/plain', 'text/csv'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    }
    
    MAX_FILE_SIZES = {
        'pdf': 10 * 1024 * 1024,  # 10MB
        'text': 5 * 1024 * 1024,   # 5MB
        'docx': 10 * 1024 * 1024,  # 10MB
        'image': 5 * 1024 * 1024,  # 5MB
    }
    
    def __init__(self):
        self.url_validator = URLValidator()
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that all required fields are present."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                field_errors={field: "This field is required" for field in missing_fields}
            )
    
    def validate_string_field(self, value: Any, field_name: str, 
                            min_length: int = None, max_length: int = None,
                            pattern: str = None, allow_empty: bool = False) -> str:
        """Validate string field with various constraints."""
        if value is None:
            if allow_empty:
                return ""
            raise ValidationError(f"{field_name} is required", {field_name: "This field is required"})
        
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string", {field_name: "Must be a string"})
        
        value = value.strip()
        
        if not value and not allow_empty:
            raise ValidationError(f"{field_name} cannot be empty", {field_name: "Cannot be empty"})
        
        if min_length and len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters long",
                {field_name: f"Must be at least {min_length} characters"}
            )
        
        if max_length and len(value) > max_length:
            raise ValidationError(
                f"{field_name} must be no more than {max_length} characters long",
                {field_name: f"Must be no more than {max_length} characters"}
            )
        
        if pattern and pattern in self.PATTERNS:
            if not self.PATTERNS[pattern].match(value):
                raise ValidationError(
                    f"{field_name} format is invalid",
                    {field_name: f"Invalid {pattern} format"}
                )
        
        return value
    
    def validate_email_field(self, value: Any, field_name: str = "email") -> str:
        """Validate email field."""
        if not value:
            raise ValidationError(f"{field_name} is required", {field_name: "This field is required"})
        
        try:
            validate_email(value)
            return value.lower().strip()
        except DjangoValidationError:
            raise ValidationError(f"Invalid {field_name} format", {field_name: "Invalid email format"})
    
    def validate_url_field(self, value: Any, field_name: str, allow_empty: bool = True) -> Optional[str]:
        """Validate URL field."""
        if not value:
            if allow_empty:
                return None
            raise ValidationError(f"{field_name} is required", {field_name: "This field is required"})
        
        try:
            self.url_validator(value)
            return value.strip()
        except DjangoValidationError:
            raise ValidationError(f"Invalid {field_name} format", {field_name: "Invalid URL format"})
    
    def validate_uuid_field(self, value: Any, field_name: str) -> str:
        """Validate UUID field."""
        if not value:
            raise ValidationError(f"{field_name} is required", {field_name: "This field is required"})
        
        value = str(value).strip()
        if not self.PATTERNS['uuid'].match(value):
            raise ValidationError(f"Invalid {field_name} format", {field_name: "Invalid UUID format"})
        
        return value
    
    def validate_json_field(self, value: Any, field_name: str, 
                          expected_type: type = None, allow_empty: bool = True) -> Any:
        """Validate JSON field."""
        if not value:
            if allow_empty:
                return None if expected_type != list else []
            raise ValidationError(f"{field_name} is required", {field_name: "This field is required"})
        
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(f"Invalid {field_name} JSON format", {field_name: "Invalid JSON format"})
        
        if expected_type and not isinstance(value, expected_type):
            raise ValidationError(
                f"{field_name} must be of type {expected_type.__name__}",
                {field_name: f"Must be of type {expected_type.__name__}"}
            )
        
        return value
    
    def validate_list_field(self, value: Any, field_name: str, 
                          item_validator: callable = None, min_items: int = None,
                          max_items: int = None, allow_empty: bool = True) -> List[Any]:
        """Validate list field."""
        if not value:
            if allow_empty:
                return []
            raise ValidationError(f"{field_name} is required", {field_name: "This field is required"})
        
        if not isinstance(value, list):
            raise ValidationError(f"{field_name} must be a list", {field_name: "Must be a list"})
        
        if min_items and len(value) < min_items:
            raise ValidationError(
                f"{field_name} must have at least {min_items} items",
                {field_name: f"Must have at least {min_items} items"}
            )
        
        if max_items and len(value) > max_items:
            raise ValidationError(
                f"{field_name} must have no more than {max_items} items",
                {field_name: f"Must have no more than {max_items} items"}
            )
        
        if item_validator:
            for i, item in enumerate(value):
                try:
                    item_validator(item)
                except Exception as e:
                    raise ValidationError(
                        f"Invalid item at index {i} in {field_name}: {str(e)}",
                        {field_name: f"Invalid item at index {i}"}
                    )
        
        return value
    
    def validate_file_upload(self, file: UploadedFile, allowed_types: List[str] = None,
                           max_size: int = None, field_name: str = "file") -> UploadedFile:
        """Validate file upload."""
        if not file:
            raise ValidationError(f"{field_name} is required", {field_name: "This field is required"})
        
        if not isinstance(file, UploadedFile):
            raise ValidationError(f"{field_name} must be a file", {field_name: "Must be a file"})
        
        # Check file size
        if max_size and file.size > max_size:
            size_mb = max_size / (1024 * 1024)
            raise ValidationError(
                f"{field_name} size exceeds {size_mb:.1f}MB limit",
                {field_name: f"File size must be less than {size_mb:.1f}MB"}
            )
        
        # Check file type
        if allowed_types:
            file_type = self._get_file_type(file.content_type)
            if file_type not in allowed_types:
                raise ValidationError(
                    f"{field_name} type not allowed. Allowed types: {', '.join(allowed_types)}",
                    {field_name: f"File type must be one of: {', '.join(allowed_types)}"}
                )
        
        return file
    
    def validate_chat_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate chat input data."""
        self.validate_required_fields(data, ['question'])
        
        question = self.validate_string_field(
            data.get('question'), 
            'question', 
            min_length=1, 
            max_length=1000
        )
        
        context_type = self.validate_string_field(
            data.get('context_type', 'general'),
            'context_type',
            max_length=50
        )
        
        valid_context_types = ['general', 'project', 'experience', 'skills']
        if context_type not in valid_context_types:
            raise ValidationError(
                f"Invalid context_type. Must be one of: {', '.join(valid_context_types)}",
                {'context_type': f"Must be one of: {', '.join(valid_context_types)}"}
            )
        
        project_id = data.get('project_id')
        if project_id:
            project_id = self.validate_uuid_field(project_id, 'project_id')
        
        return {
            'question': question,
            'context_type': context_type,
            'project_id': project_id
        }
    
    def validate_job_analysis_input(self, data: Dict[str, Any], files: Dict[str, UploadedFile]) -> Dict[str, Any]:
        """Validate job analysis input data."""
        job_text = data.get('job_requirements', '').strip()
        uploaded_file = files.get('job_file')
        
        if not job_text and not uploaded_file:
            raise ValidationError(
                "Either job_requirements text or job_file must be provided",
                {'job_requirements': 'Required if no file uploaded', 'job_file': 'Required if no text provided'}
            )
        
        validated_data = {}
        
        if job_text:
            validated_data['job_requirements'] = self.validate_string_field(
                job_text, 'job_requirements', min_length=10, max_length=50000
            )
        
        if uploaded_file:
            validated_data['job_file'] = self.validate_file_upload(
                uploaded_file, 
                allowed_types=['pdf', 'text', 'docx'],
                max_size=10 * 1024 * 1024,  # 10MB
                field_name='job_file'
            )
        
        return validated_data
    
    def validate_project_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate project data."""
        self.validate_required_fields(data, ['title', 'description'])
        
        validated_data = {}
        
        validated_data['title'] = self.validate_string_field(
            data.get('title'), 'title', min_length=1, max_length=200
        )
        
        validated_data['description'] = self.validate_string_field(
            data.get('description'), 'description', min_length=10, max_length=5000
        )
        
        if 'tech_stack' in data:
            validated_data['tech_stack'] = self.validate_list_field(
                data.get('tech_stack'), 'tech_stack', max_items=50
            )
        
        if 'github_url' in data:
            validated_data['github_url'] = self.validate_url_field(
                data.get('github_url'), 'github_url'
            )
        
        if 'demo_url' in data:
            validated_data['demo_url'] = self.validate_url_field(
                data.get('demo_url'), 'demo_url'
            )
        
        return validated_data
    
    def validate_profile_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate profile data."""
        self.validate_required_fields(data, ['name', 'email'])
        
        validated_data = {}
        
        validated_data['name'] = self.validate_string_field(
            data.get('name'), 'name', min_length=1, max_length=100
        )
        
        validated_data['email'] = self.validate_email_field(data.get('email'))
        
        if 'bio' in data:
            validated_data['bio'] = self.validate_string_field(
                data.get('bio'), 'bio', max_length=2000, allow_empty=True
            )
        
        if 'skills' in data:
            validated_data['skills'] = self.validate_list_field(
                data.get('skills'), 'skills', max_items=100
            )
        
        if 'experience' in data:
            validated_data['experience'] = self.validate_list_field(
                data.get('experience'), 'experience', max_items=50
            )
        
        return validated_data
    
    def sanitize_input(self, value: str, field_name: str = None) -> str:
        """Sanitize input string to prevent XSS and other attacks."""
        if not isinstance(value, str):
            return value
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r', '\n']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        # Limit length to prevent DoS
        if len(value) > 10000:
            value = value[:10000]
            if field_name:
                logger.warning(f"Input truncated for {field_name} due to length")
        
        return value.strip()
    
    def _get_file_type(self, content_type: str) -> str:
        """Get file type category from content type."""
        for file_type, mime_types in self.ALLOWED_FILE_TYPES.items():
            if content_type in mime_types:
                return file_type
        return 'unknown'


class APIRequestValidator:
    """Validator for API request parameters and headers."""
    
    def __init__(self):
        self.input_validator = InputValidator()
    
    def validate_request_headers(self, request) -> Dict[str, str]:
        """Validate and sanitize request headers."""
        headers = {}
        
        # Validate Content-Type
        content_type = request.META.get('CONTENT_TYPE', '')
        if content_type and not content_type.startswith(('application/json', 'multipart/form-data', 'application/x-www-form-urlencoded')):
            logger.warning(f"Unexpected Content-Type: {content_type}")
        
        # Validate User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if user_agent:
            headers['user_agent'] = self.input_validator.sanitize_input(user_agent)
        
        # Validate Accept header
        accept = request.META.get('HTTP_ACCEPT', '')
        if accept:
            headers['accept'] = self.input_validator.sanitize_input(accept)
        
        return headers
    
    def validate_query_parameters(self, request, allowed_params: List[str] = None) -> Dict[str, Any]:
        """Validate and sanitize query parameters."""
        params = {}
        
        for key, value in request.GET.items():
            if allowed_params and key not in allowed_params:
                continue
            
            # Sanitize parameter values
            if isinstance(value, str):
                params[key] = self.input_validator.sanitize_input(value, f"query_param_{key}")
            else:
                params[key] = value
        
        return params
    
    def validate_pagination_params(self, request) -> Dict[str, int]:
        """Validate pagination parameters."""
        params = {}
        
        page = request.GET.get('page', '1')
        page_size = request.GET.get('page_size', '20')
        
        try:
            params['page'] = max(1, int(page))
        except (ValueError, TypeError):
            raise ValidationError("Invalid page parameter", {'page': 'Must be a positive integer'})
        
        try:
            params['page_size'] = min(100, max(1, int(page_size)))
        except (ValueError, TypeError):
            raise ValidationError("Invalid page_size parameter", {'page_size': 'Must be between 1 and 100'})
        
        return params


# Global validator instances
input_validator = InputValidator()
api_request_validator = APIRequestValidator()
