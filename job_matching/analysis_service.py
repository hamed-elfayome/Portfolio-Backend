from openai import OpenAI
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.core.cache import cache
from core.models import Profile
from .models import JobAnalysis, SkillsMatch, JobRecommendation
import PyPDF2
import logging
import time
import re
import json
import hashlib
from io import BytesIO

logger = logging.getLogger(__name__)


class JobAnalysisService:
    """Service for analyzing job requirements against profile data."""
    
    def __init__(self):
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
        self.model = "gpt-3.5-turbo"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.supported_file_types = ['.pdf', '.txt', '.docx']
    
    def analyze_job(self, job_text: str, uploaded_file=None, visitor_session=None) -> Dict[str, Any]:
        """Analyze job requirements against profile."""
        start_time = time.time()
        
        try:
            # Extract text from file if provided
            if uploaded_file:
                file_text = self._extract_text_from_file(uploaded_file)
                job_text = f"{job_text}\n\n{file_text}" if job_text else file_text
            
            # Get active profile
            profile = Profile.objects.filter(is_active=True).first()
            if not profile:
                raise ValueError("No active profile found")
            
            # Check cache first
            cache_key = self._get_cache_key(job_text, profile.profile_id)
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached job analysis result")
                return cached_result
            
            # Extract job details
            job_details = self._extract_job_details(job_text)
            
            # Analyze against profile
            analysis_result = self._analyze_against_profile(job_details, profile)
            
            # Calculate scores
            scores = self._calculate_match_scores(analysis_result, profile)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(analysis_result, scores)
            
            # Save to database
            job_analysis = JobAnalysis.objects.create(
                visitor_session=visitor_session,
                job_title=job_details.get('title', ''),
                company_name=job_details.get('company', ''),
                job_requirements=job_text,
                uploaded_file=uploaded_file,
                file_processed=bool(uploaded_file),
                overall_match_score=scores['overall'],
                skills_match_score=scores['skills'],
                experience_match_score=scores['experience'],
                education_match_score=scores['education'],
                matched_skills=analysis_result['matched_skills'],
                missing_skills=analysis_result['missing_skills'],
                skill_gaps=analysis_result['skill_gaps'],
                experience_analysis=analysis_result['experience_analysis'],
                education_analysis=analysis_result['education_analysis'],
                recommendations_data=recommendations,
                processing_time=time.time() - start_time
            )
            
            # Create related objects
            self._create_skills_matches(job_analysis, analysis_result)
            self._create_recommendations(job_analysis, recommendations)
            
            result = {
                'analysis_id': str(job_analysis.analysis_id),
                'job_details': job_details,
                'match_scores': scores,
                'analysis': analysis_result,
                'recommendations': recommendations,
                'match_level': job_analysis.get_match_level(),
                'match_level_display': job_analysis.get_match_level_display(),
                'processing_time': job_analysis.processing_time
            }
            
            # Cache result for 1 hour
            cache.set(cache_key, result, timeout=3600)
            
            return result
            
        except Exception as e:
            logger.error(f"Job analysis error: {str(e)}")
            raise
    
    def _extract_text_from_file(self, uploaded_file) -> str:
        """Extract text from uploaded file."""
        try:
            # Check file size
            if uploaded_file.size > self.max_file_size:
                raise ValueError(f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB")
            
            # Check file type
            file_extension = uploaded_file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in self.supported_file_types:
                raise ValueError(f"Unsupported file type. Supported: {', '.join(self.supported_file_types)}")
            
            if file_extension == 'pdf':
                return self._extract_pdf_text(uploaded_file)
            elif file_extension == 'txt':
                return uploaded_file.read().decode('utf-8')
            elif file_extension == 'docx':
                # For now, treat as text file
                return uploaded_file.read().decode('utf-8')
            else:
                return ""
                
        except Exception as e:
            logger.error(f"File extraction error: {str(e)}")
            raise ValueError(f"Error processing file: {str(e)}")
    
    def _extract_pdf_text(self, uploaded_file) -> str:
        """Extract text from PDF file."""
        try:
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Read PDF
            pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise ValueError(f"Error reading PDF file: {str(e)}")
    
    def _extract_job_details(self, job_text: str) -> Dict[str, Any]:
        """Extract structured information from job posting."""
        try:
            if not self.client:
                # Fallback without OpenAI
                return self._extract_job_details_fallback(job_text)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Extract key information from this job posting and return as JSON:
                        {
                            "title": "job title",
                            "company": "company name",
                            "required_skills": ["skill1", "skill2"],
                            "preferred_skills": ["skill1", "skill2"],
                            "experience_years": number,
                            "education_level": "degree level",
                            "responsibilities": ["resp1", "resp2"],
                            "benefits": ["benefit1", "benefit2"]
                        }"""
                    },
                    {"role": "user", "content": job_text}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Job details extraction error: {str(e)}")
            return self._extract_job_details_fallback(job_text)
    
    def _extract_job_details_fallback(self, job_text: str) -> Dict[str, Any]:
        """Fallback job details extraction without OpenAI."""
        # Simple keyword extraction
        text_lower = job_text.lower()
        
        # Extract title (look for common patterns)
        title = "Unknown Position"
        title_patterns = [
            r'position:\s*([^\n]+)',
            r'role:\s*([^\n]+)',
            r'job title:\s*([^\n]+)',
            r'we are looking for a\s+([^\n]+)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text_lower)
            if match:
                title = match.group(1).strip().title()
                break
        
        # Extract company
        company = "Unknown Company"
        company_patterns = [
            r'at\s+([^\n]+)',
            r'company:\s*([^\n]+)',
            r'about\s+([^\n]+)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text_lower)
            if match:
                company = match.group(1).strip().title()
                break
        
        # Extract skills (simple keyword matching)
        common_skills = [
            'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node.js',
            'django', 'flask', 'spring', 'sql', 'postgresql', 'mysql', 'mongodb',
            'aws', 'azure', 'docker', 'kubernetes', 'git', 'linux', 'agile',
            'scrum', 'machine learning', 'ai', 'data science', 'frontend',
            'backend', 'full stack', 'devops', 'ci/cd'
        ]
        
        found_skills = []
        for skill in common_skills:
            if skill in text_lower:
                # Capitalize properly
                if skill == 'node.js':
                    found_skills.append('Node.js')
                elif skill == 'ci/cd':
                    found_skills.append('CI/CD')
                elif skill == 'machine learning':
                    found_skills.append('Machine Learning')
                elif skill == 'data science':
                    found_skills.append('Data Science')
                elif skill == 'full stack':
                    found_skills.append('Full Stack')
                else:
                    found_skills.append(skill.title())
        
        # Extract experience years
        experience_years = 0
        exp_patterns = [
            r'(\d+)\+?\s*years?\s*experience',
            r'(\d+)\+?\s*years?\s*of\s*experience',
            r'experience:\s*(\d+)\+?',
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text_lower)
            if match:
                experience_years = int(match.group(1))
                break
        
        return {
            "title": title,
            "company": company,
            "required_skills": found_skills[:5],  # Top 5
            "preferred_skills": found_skills[5:10],  # Next 5
            "experience_years": experience_years,
            "education_level": "Bachelor's Degree",  # Default
            "responsibilities": [],
            "benefits": []
        }
    
    def _analyze_against_profile(self, job_details: Dict, profile: Profile) -> Dict[str, Any]:
        """Analyze job requirements against profile data."""
        profile_skills = profile.get_skills_list()
        required_skills = job_details.get('required_skills', [])
        preferred_skills = job_details.get('preferred_skills', [])
        
        # Skills analysis
        matched_skills = []
        missing_skills = []
        skill_gaps = []
        
        all_job_skills = required_skills + preferred_skills
        
        for job_skill in all_job_skills:
            skill_match = self._find_skill_match(job_skill, profile.skills)
            if skill_match:
                matched_skills.append({
                    'skill': job_skill,
                    'profile_skill': skill_match['name'],
                    'level': skill_match.get('level', 'unknown'),
                    'years': skill_match.get('years', 0),
                    'is_required': job_skill in required_skills
                })
            else:
                missing_skills.append({
                    'skill': job_skill,
                    'is_required': job_skill in required_skills,
                    'alternatives': self._find_related_skills(job_skill, profile_skills)
                })
        
        # Experience analysis
        required_years = job_details.get('experience_years', 0)
        profile_years = profile.get_experience_years()
        
        experience_analysis = {
            'required_years': required_years,
            'profile_years': profile_years,
            'meets_requirement': profile_years >= required_years,
            'experience_gap': max(0, required_years - profile_years)
        }
        
        # Education analysis
        education_analysis = {
            'required_level': job_details.get('education_level', ''),
            'profile_education': profile.education,
            'meets_requirement': self._check_education_match(
                job_details.get('education_level', ''),
                profile.education
            )
        }
        
        return {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'skill_gaps': skill_gaps,
            'experience_analysis': experience_analysis,
            'education_analysis': education_analysis
        }
    
    def _calculate_match_scores(self, analysis: Dict, profile: Profile) -> Dict[str, float]:
        """Calculate percentage match scores."""
        # Skills score
        total_skills = len(analysis['matched_skills']) + len(analysis['missing_skills'])
        skills_score = (len(analysis['matched_skills']) / total_skills * 100) if total_skills > 0 else 0
        
        # Experience score
        exp_analysis = analysis['experience_analysis']
        if exp_analysis['required_years'] == 0:
            experience_score = 100
        else:
            experience_score = min(100, (exp_analysis['profile_years'] / exp_analysis['required_years']) * 100)
        
        # Education score
        education_score = 100 if analysis['education_analysis']['meets_requirement'] else 70
        
        # Overall score (weighted average)
        overall_score = (skills_score * 0.5 + experience_score * 0.3 + education_score * 0.2)
        
        return {
            'overall': round(overall_score, 1),
            'skills': round(skills_score, 1),
            'experience': round(experience_score, 1),
            'education': round(education_score, 1)
        }
    
    def _generate_recommendations(self, analysis: Dict, scores: Dict) -> List[Dict[str, Any]]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Skills recommendations
        required_missing = [s for s in analysis['missing_skills'] if s['is_required']]
        if required_missing:
            recommendations.append({
                'type': 'skill',
                'priority': 'high',
                'title': 'Learn Required Skills',
                'description': f"Focus on learning: {', '.join([s['skill'] for s in required_missing[:3]])}",
                'skills': [s['skill'] for s in required_missing],
                'estimated_time': '3-6 months',
                'resources': []
            })
        
        # Experience recommendations
        exp_gap = analysis['experience_analysis']['experience_gap']
        if exp_gap > 0:
            recommendations.append({
                'type': 'experience',
                'priority': 'medium',
                'title': 'Gain More Experience',
                'description': f"Consider gaining {exp_gap} more years of relevant experience",
                'suggestion': "Look for similar roles with lower requirements or freelance projects",
                'estimated_time': f'{exp_gap} years',
                'resources': []
            })
        
        # Strengths to highlight
        strong_matches = [s for s in analysis['matched_skills'] if s.get('years', 0) >= 2]
        if strong_matches:
            recommendations.append({
                'type': 'project',
                'priority': 'low',
                'title': 'Highlight These Strengths',
                'description': f"Emphasize your experience with: {', '.join([s['skill'] for s in strong_matches[:3]])}",
                'skills': [s['skill'] for s in strong_matches],
                'estimated_time': 'Immediate',
                'resources': []
            })
        
        return recommendations
    
    def _create_skills_matches(self, job_analysis: JobAnalysis, analysis: Dict):
        """Create SkillsMatch objects for the analysis."""
        for match in analysis['matched_skills']:
            SkillsMatch.objects.create(
                job_analysis=job_analysis,
                job_skill=match['skill'],
                profile_skill=match['profile_skill'],
                match_type='exact' if match['skill'].lower() == match['profile_skill'].lower() else 'similar',
                confidence_score=0.8 if match['years'] >= 2 else 0.6,
                is_required=match['is_required'],
                years_experience=match.get('years', 0),
                proficiency_level=match.get('level', 'unknown')
            )
    
    def _create_recommendations(self, job_analysis: JobAnalysis, recommendations: List[Dict]):
        """Create JobRecommendation objects for the analysis."""
        for rec in recommendations:
            JobRecommendation.objects.create(
                job_analysis=job_analysis,
                recommendation_type=rec['type'],
                title=rec['title'],
                description=rec['description'],
                priority=rec['priority'],
                estimated_time=rec.get('estimated_time', ''),
                resources=rec.get('resources', []),
                skills_involved=rec.get('skills', [])
            )
    
    def _find_skill_match(self, job_skill: str, profile_skills: List) -> Optional[Dict]:
        """Find matching skill in profile."""
        job_skill_lower = job_skill.lower().strip()
        
        for skill in profile_skills:
            if isinstance(skill, dict):
                skill_name = skill.get('name', '').lower().strip()
                # Check for exact match or substring match
                if (job_skill_lower == skill_name or 
                    job_skill_lower in skill_name or 
                    skill_name in job_skill_lower):
                    return skill
            elif isinstance(skill, str):
                skill_name = skill.lower().strip()
                if (job_skill_lower == skill_name or 
                    job_skill_lower in skill_name or 
                    skill_name in job_skill_lower):
                    return {'name': skill}
        
        return None
    
    def _find_related_skills(self, job_skill: str, profile_skills: List) -> List[str]:
        """Find related/similar skills in profile."""
        related = []
        job_keywords = set(job_skill.lower().split())
        
        for skill in profile_skills:
            skill_name = skill if isinstance(skill, str) else str(skill)
            skill_keywords = set(skill_name.lower().split())
            
            if job_keywords.intersection(skill_keywords):
                related.append(skill_name)
        
        return related[:3]
    
    def _check_education_match(self, required: str, profile_education: List) -> bool:
        """Check if profile education meets job requirements."""
        if not required or not profile_education:
            return True
        
        # Simple education level matching
        education_levels = {
            'high school': 1,
            'associate': 2,
            'bachelor': 3,
            'master': 4,
            'phd': 5,
            'doctorate': 5
        }
        
        required_level = 0
        for level, value in education_levels.items():
            if level in required.lower():
                required_level = value
                break
        
        for education in profile_education:
            if isinstance(education, dict):
                degree = education.get('degree', '').lower()
                for level, value in education_levels.items():
                    if level in degree and value >= required_level:
                        return True
        
        return False
    
    def _get_cache_key(self, job_text: str, profile_id: str) -> str:
        """Generate cache key for job analysis."""
        content = f"{job_text}_{profile_id}"
        return f"job_analysis_{hashlib.md5(content.encode()).hexdigest()}"
