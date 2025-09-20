"""
Enhanced visitor tracking middleware for comprehensive analytics and session management.
"""
import uuid
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
import logging
import re
from urllib.parse import urlparse

from .models import VisitorSession, PageView, VisitorInteraction

logger = logging.getLogger(__name__)

class VisitorTrackingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request: HttpRequest):
        try:
            # Skip for admin, static files, and health checks
            if self._should_skip_tracking(request):
                return None

            # Get or create visitor session
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            # Get or create visitor session in database
            visitor_session = self._get_or_create_visitor_session(request, session_key)
            
            # Store visitor session info in request for views to use
            request.visitor_session = visitor_session
            request.visitor_session_id = session_key
            request.visitor_ip = self._get_client_ip(request)
            request.visitor_user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

            # Track session start time for time-on-page calculation
            request.session_start_time = timezone.now()

        except Exception as e:
            logger.error(f"Error in visitor tracking middleware: {str(e)}")
            request.visitor_session = None
            request.visitor_session_id = None
            request.visitor_ip = None
            request.visitor_user_agent = None

        return None

    def process_response(self, request, response):
        try:
            # Track page view and interactions if visitor session exists
            if hasattr(request, 'visitor_session') and request.visitor_session:
                self._track_page_view(request, response)
                self._track_interactions(request, response)
                self._update_session_activity(request)

        except Exception as e:
            logger.error(f"Error tracking page view: {str(e)}")

        return response

    def _should_skip_tracking(self, request):
        """Determine if tracking should be skipped for this request."""
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/health/',
            '/favicon.ico',
            '/robots.txt',
            '/sitemap.xml'
        ]
        
        path = request.path
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _get_or_create_visitor_session(self, request, session_key):
        """Get or create visitor session in database."""
        try:
            # Try to get existing session
            visitor_session = VisitorSession.objects.get(session_key=session_key)
            
            # Update last activity
            visitor_session.last_activity = timezone.now()
            visitor_session.save(update_fields=['last_activity'])
            
            return visitor_session
            
        except VisitorSession.DoesNotExist:
            # Create new visitor session
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            referrer = request.META.get('HTTP_REFERER', '')[:500]
            
            # Detect device and browser
            device_type = self._detect_device_type(request)
            browser = self._detect_browser(request)
            
            # Detect if it's a bot
            is_bot = self._detect_bot(user_agent)
            
            # Detect if it's likely a recruiter
            is_recruiter = self._detect_recruiter(request, user_agent, referrer)
            
            visitor_session = VisitorSession.objects.create(
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
                device_type=device_type,
                browser=browser,
                is_bot=is_bot,
                is_recruiter=is_recruiter
            )
            
            logger.info(f"Created new visitor session: {visitor_session.session_id}")
            return visitor_session

    def _track_page_view(self, request, response):
        """Track page view for analytics."""
        try:
            # Skip API endpoints for page view tracking
            if request.path.startswith('/api/'):
                return

            # Calculate time on page if we have session start time
            time_on_page = None
            if hasattr(request, 'session_start_time'):
                time_on_page = timezone.now() - request.session_start_time

            # Get page title from response or request
            page_title = self._extract_page_title(request, response)
            
            # Create page view record
            page_view = PageView.objects.create(
                visitor_session=request.visitor_session,
                page_url=request.build_absolute_uri(),
                page_title=page_title,
                referrer=request.META.get('HTTP_REFERER', '')[:500],
                time_on_page=time_on_page
            )
            
            # Update page views count
            request.visitor_session.page_views_count += 1
            request.visitor_session.save(update_fields=['page_views_count'])
            
            logger.debug(f"Tracked page view: {page_view.page_url}")
            
        except Exception as e:
            logger.error(f"Error tracking page view: {str(e)}")

    def _track_interactions(self, request, response):
        """Track visitor interactions based on request patterns."""
        try:
            interactions = []
            
            # Track chat interactions
            if request.path.startswith('/api/v1/chat/'):
                interactions.append({
                    'type': 'chat_start' if request.method == 'POST' else 'chat_message',
                    'details': {
                        'endpoint': request.path,
                        'method': request.method,
                        'response_status': response.status_code
                    }
                })
            
            # Track job analysis interactions
            elif request.path.startswith('/api/v1/job-analysis/'):
                interactions.append({
                    'type': 'job_analysis',
                    'details': {
                        'endpoint': request.path,
                        'method': request.method,
                        'response_status': response.status_code
                    }
                })
            
            # Track project views
            elif '/projects/' in request.path and request.method == 'GET':
                interactions.append({
                    'type': 'project_view',
                    'details': {
                        'path': request.path,
                        'response_status': response.status_code
                    }
                })
            
            # Create interaction records
            for interaction_data in interactions:
                VisitorInteraction.objects.create(
                    visitor_session=request.visitor_session,
                    interaction_type=interaction_data['type'],
                    details=interaction_data['details']
                )
                
        except Exception as e:
            logger.error(f"Error tracking interactions: {str(e)}")

    def _update_session_activity(self, request):
        """Update session activity and time spent."""
        try:
            if hasattr(request, 'session_start_time'):
                time_spent = timezone.now() - request.session_start_time
                
                # Update total time spent
                if request.visitor_session.time_spent:
                    request.visitor_session.time_spent += time_spent
                else:
                    request.visitor_session.time_spent = time_spent
                
                request.visitor_session.save(update_fields=['time_spent'])
                
        except Exception as e:
            logger.error(f"Error updating session activity: {str(e)}")

    def _extract_page_title(self, request, response):
        """Extract page title from response or infer from URL."""
        try:
            # Try to extract from response content
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8', errors='ignore')
                title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE)
                if title_match:
                    return title_match.group(1).strip()[:200]
            
            # Infer from URL path
            path = request.path
            if path == '/':
                return 'Home'
            elif path.startswith('/projects/'):
                return 'Projects'
            elif path.startswith('/api/'):
                return 'API'
            else:
                return path.replace('/', ' ').strip().title()[:200]
                
        except Exception:
            return 'Unknown Page'

    def _detect_bot(self, user_agent):
        """Detect if the request is from a bot/crawler."""
        bot_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'crawling',
            'googlebot', 'bingbot', 'slurp', 'duckduckbot',
            'baiduspider', 'yandexbot', 'facebookexternalhit',
            'twitterbot', 'linkedinbot', 'whatsapp', 'telegram'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in bot_patterns)

    def _detect_recruiter(self, request, user_agent, referrer):
        """Detect if the visitor is likely a recruiter."""
        # Check referrer for job sites
        job_sites = [
            'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
            'ziprecruiter.com', 'dice.com', 'careerbuilder.com', 'angel.co',
            'wellfound.com', 'stackoverflow.com/jobs', 'github.com'
        ]
        
        if referrer:
            referrer_domain = urlparse(referrer).netloc.lower()
            if any(job_site in referrer_domain for job_site in job_sites):
                return True
        
        # Check user agent for recruiting tools
        recruiter_patterns = [
            'recruiter', 'talent', 'hiring', 'hr-', 'ats-'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in recruiter_patterns)

    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _detect_device_type(self, request):
        """Detect device type from user agent."""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        return 'desktop'

    def _detect_browser(self, request):
        """Detect browser from user agent."""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'chrome' in user_agent:
            return 'chrome'
        elif 'firefox' in user_agent:
            return 'firefox'
        elif 'safari' in user_agent:
            return 'safari'
        elif 'edge' in user_agent:
            return 'edge'
        return 'unknown'
