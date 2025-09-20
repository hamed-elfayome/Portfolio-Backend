"""
Content Processing Service
Handles content ingestion, processing, and preparation for RAG system.
"""

import logging
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from .models import DocumentChunk, ContentProcessingJob
from .embedding_service import EmbeddingService
from core.models import Profile
from projects.models import Project
import json

logger = logging.getLogger(__name__)


class ContentProcessor:
    """Service for processing and ingesting content into the RAG system."""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    def process_profile_content(self, profile: Profile) -> Dict[str, Any]:
        """Process profile content and create document chunks."""
        try:
            job = ContentProcessingJob.objects.create(
                source_type='profile',
                source_id=str(profile.profile_id),
                source_title='Profile Content',
                content=profile.bio or '',
                status='processing'
            )
            
            chunks_created = 0
            
            # Process bio
            if profile.bio:
                chunks = self._process_text_content(
                    content=profile.bio,
                    source_type='profile',
                    source_id=str(profile.profile_id),
                    source_title='Bio',
                    metadata={'section': 'bio', 'profile_id': str(profile.profile_id)}
                )
                chunks_created += len(chunks)
            
            # Process skills
            if profile.skills:
                skills_text = self._format_skills_for_processing(profile.skills)
                chunks = self._process_text_content(
                    content=skills_text,
                    source_type='profile',
                    source_id=str(profile.profile_id),
                    source_title='Skills',
                    metadata={'section': 'skills', 'profile_id': str(profile.profile_id)}
                )
                chunks_created += len(chunks)
            
            # Process experience
            if profile.experience:
                experience_text = self._format_experience_for_processing(profile.experience)
                chunks = self._process_text_content(
                    content=experience_text,
                    source_type='profile',
                    source_id=str(profile.profile_id),
                    source_title='Experience',
                    metadata={'section': 'experience', 'profile_id': str(profile.profile_id)}
                )
                chunks_created += len(chunks)
            
            # Process education
            if profile.education:
                education_text = self._format_education_for_processing(profile.education)
                chunks = self._process_text_content(
                    content=education_text,
                    source_type='profile',
                    source_id=str(profile.profile_id),
                    source_title='Education',
                    metadata={'section': 'education', 'profile_id': str(profile.profile_id)}
                )
                chunks_created += len(chunks)
            
            # Update job status
            job.status = 'completed'
            job.chunks_created = chunks_created
            job.completed_at = timezone.now()
            job.save()
            
            logger.info(f"Processed profile {profile.name}: {chunks_created} chunks created")
            
            return {
                'success': True,
                'chunks_created': chunks_created,
                'job_id': str(job.job_id)
            }
            
        except Exception as e:
            logger.error(f"Error processing profile content: {str(e)}")
            if 'job' in locals():
                job.status = 'failed'
                job.error_message = str(e)
                job.save()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_project_content(self, project: Project) -> Dict[str, Any]:
        """Process project content and create document chunks."""
        try:
            job = ContentProcessingJob.objects.create(
                source_type='project',
                source_id=str(project.project_id),
                source_title=project.title,
                content=project.description or '',
                status='processing'
            )
            
            chunks_created = 0
            
            # Process project description
            if project.description:
                chunks = self._process_text_content(
                    content=project.description,
                    source_type='project',
                    source_id=str(project.project_id),
                    source_title=f'{project.title} - Description',
                    metadata={
                        'section': 'description',
                        'project_id': str(project.project_id),
                        'project_title': project.title
                    }
                )
                chunks_created += len(chunks)
            
            # Process detailed description
            if project.detailed_description:
                chunks = self._process_text_content(
                    content=project.detailed_description,
                    source_type='project',
                    source_id=str(project.project_id),
                    source_title=f'{project.title} - Detailed Description',
                    metadata={
                        'section': 'detailed_description',
                        'project_id': str(project.project_id),
                        'project_title': project.title
                    }
                )
                chunks_created += len(chunks)
            
            # Process tech stack
            if project.tech_stack:
                tech_text = self._format_tech_stack_for_processing(project.tech_stack)
                chunks = self._process_text_content(
                    content=tech_text,
                    source_type='project',
                    source_id=str(project.project_id),
                    source_title=f'{project.title} - Tech Stack',
                    metadata={
                        'section': 'tech_stack',
                        'project_id': str(project.project_id),
                        'project_title': project.title
                    }
                )
                chunks_created += len(chunks)
            
            # Process achievements
            if project.achievements:
                achievements_text = self._format_achievements_for_processing(project.achievements)
                chunks = self._process_text_content(
                    content=achievements_text,
                    source_type='project',
                    source_id=str(project.project_id),
                    source_title=f'{project.title} - Achievements',
                    metadata={
                        'section': 'achievements',
                        'project_id': str(project.project_id),
                        'project_title': project.title
                    }
                )
                chunks_created += len(chunks)
            
            # Process challenges
            if project.challenges:
                challenges_text = self._format_challenges_for_processing(project.challenges)
                chunks = self._process_text_content(
                    content=challenges_text,
                    source_type='project',
                    source_id=str(project.project_id),
                    source_title=f'{project.title} - Challenges',
                    metadata={
                        'section': 'challenges',
                        'project_id': str(project.project_id),
                        'project_title': project.title
                    }
                )
                chunks_created += len(chunks)
            
            # Process learnings
            if project.learnings:
                chunks = self._process_text_content(
                    content=project.learnings,
                    source_type='project',
                    source_id=str(project.project_id),
                    source_title=f'{project.title} - Learnings',
                    metadata={
                        'section': 'learnings',
                        'project_id': str(project.project_id),
                        'project_title': project.title
                    }
                )
                chunks_created += len(chunks)
            
            # Update job status
            job.status = 'completed'
            job.chunks_created = chunks_created
            job.completed_at = timezone.now()
            job.save()
            
            logger.info(f"Processed project {project.title}: {chunks_created} chunks created")
            
            return {
                'success': True,
                'chunks_created': chunks_created,
                'job_id': str(job.job_id)
            }
            
        except Exception as e:
            logger.error(f"Error processing project content: {str(e)}")
            if 'job' in locals():
                job.status = 'failed'
                job.error_message = str(e)
                job.save()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_text_content(self, content: str, source_type: str, source_id: str, 
                            source_title: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Process text content and create document chunks with embeddings."""
        try:
            # Chunk the text
            chunks_data = self.embedding_service.chunk_text(content)
            
            created_chunks = []
            
            with transaction.atomic():
                for chunk_data in chunks_data:
                    # Create embedding for the chunk
                    embedding = self.embedding_service.create_embedding(chunk_data['content'])
                    
                    # Create document chunk
                    chunk = DocumentChunk.objects.create(
                        content=chunk_data['content'],
                        embedding=embedding,
                        source_type=source_type,
                        source_id=source_id,
                        source_title=source_title,
                        metadata=metadata,
                        token_count=chunk_data['token_count'],
                        chunk_index=chunk_data['chunk_index']
                    )
                    
                    created_chunks.append(chunk)
            
            logger.info(f"Created {len(created_chunks)} document chunks for {source_title}")
            return created_chunks
            
        except Exception as e:
            logger.error(f"Error processing text content: {str(e)}")
            raise
    
    def _format_skills_for_processing(self, skills: List) -> str:
        """Format skills data for text processing."""
        if not skills:
            return ""
        
        formatted_skills = []
        for skill in skills:
            if isinstance(skill, dict):
                name = skill.get('name', '')
                level = skill.get('level', '')
                years = skill.get('years', 0)
                
                skill_text = f"{name}"
                if level:
                    skill_text += f" (Level: {level})"
                if years:
                    skill_text += f" - {years} years of experience"
                
                formatted_skills.append(skill_text)
            else:
                formatted_skills.append(str(skill))
        
        return "Skills: " + ", ".join(formatted_skills)
    
    def _format_experience_for_processing(self, experience: List) -> str:
        """Format experience data for text processing."""
        if not experience:
            return ""
        
        formatted_experience = []
        for exp in experience:
            if isinstance(exp, dict):
                title = exp.get('title', '')
                company = exp.get('company', '')
                duration = exp.get('duration_years', 0)
                description = exp.get('description', '')
                
                exp_text = f"Position: {title}"
                if company:
                    exp_text += f" at {company}"
                if duration:
                    exp_text += f" ({duration} years)"
                if description:
                    exp_text += f". {description}"
                
                formatted_experience.append(exp_text)
            else:
                formatted_experience.append(str(exp))
        
        return "Work Experience: " + ". ".join(formatted_experience)
    
    def _format_education_for_processing(self, education: List) -> str:
        """Format education data for text processing."""
        if not education:
            return ""
        
        formatted_education = []
        for edu in education:
            if isinstance(edu, dict):
                degree = edu.get('degree', '')
                institution = edu.get('institution', '')
                year = edu.get('year', '')
                
                edu_text = f"{degree}"
                if institution:
                    edu_text += f" from {institution}"
                if year:
                    edu_text += f" ({year})"
                
                formatted_education.append(edu_text)
            else:
                formatted_education.append(str(edu))
        
        return "Education: " + ". ".join(formatted_education)
    
    def _format_tech_stack_for_processing(self, tech_stack: List) -> str:
        """Format tech stack data for text processing."""
        if not tech_stack:
            return ""
        
        formatted_tech = []
        for tech in tech_stack:
            if isinstance(tech, dict):
                name = tech.get('name', '')
                category = tech.get('category', '')
                
                tech_text = name
                if category:
                    tech_text += f" ({category})"
                
                formatted_tech.append(tech_text)
            else:
                formatted_tech.append(str(tech))
        
        return "Technologies used: " + ", ".join(formatted_tech)
    
    def _format_achievements_for_processing(self, achievements: List) -> str:
        """Format achievements data for text processing."""
        if not achievements:
            return ""
        
        formatted_achievements = []
        for achievement in achievements:
            if isinstance(achievement, dict):
                title = achievement.get('title', '')
                description = achievement.get('description', '')
                
                achievement_text = title
                if description:
                    achievement_text += f": {description}"
                
                formatted_achievements.append(achievement_text)
            else:
                formatted_achievements.append(str(achievement))
        
        return "Project Achievements: " + ". ".join(formatted_achievements)
    
    def _format_challenges_for_processing(self, challenges: List) -> str:
        """Format challenges data for text processing."""
        if not challenges:
            return ""
        
        formatted_challenges = []
        for challenge in challenges:
            if isinstance(challenge, dict):
                title = challenge.get('title', '')
                description = challenge.get('description', '')
                solution = challenge.get('solution', '')
                
                challenge_text = f"Challenge: {title}"
                if description:
                    challenge_text += f" - {description}"
                if solution:
                    challenge_text += f" Solution: {solution}"
                
                formatted_challenges.append(challenge_text)
            else:
                formatted_challenges.append(str(challenge))
        
        return "Project Challenges: " + ". ".join(formatted_challenges)
    
    def reprocess_all_content(self) -> Dict[str, Any]:
        """Reprocess all profile and project content."""
        try:
            # Clear existing chunks
            DocumentChunk.objects.all().delete()
            
            total_chunks = 0
            processed_profiles = 0
            processed_projects = 0
            
            # Process all active profiles
            profiles = Profile.objects.filter(is_active=True)
            for profile in profiles:
                result = self.process_profile_content(profile)
                if result['success']:
                    total_chunks += result['chunks_created']
                    processed_profiles += 1
            
            # Process all projects
            projects = Project.objects.all()
            for project in projects:
                result = self.process_project_content(project)
                if result['success']:
                    total_chunks += result['chunks_created']
                    processed_projects += 1
            
            logger.info(f"Reprocessed all content: {total_chunks} chunks from {processed_profiles} profiles and {processed_projects} projects")
            
            return {
                'success': True,
                'total_chunks': total_chunks,
                'processed_profiles': processed_profiles,
                'processed_projects': processed_projects
            }
            
        except Exception as e:
            logger.error(f"Error reprocessing all content: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about content processing."""
        try:
            total_chunks = DocumentChunk.objects.count()
            active_chunks = DocumentChunk.objects.filter(is_active=True).count()
            
            chunks_by_source = {}
            for source_type in DocumentChunk.objects.values_list('source_type', flat=True).distinct():
                count = DocumentChunk.objects.filter(source_type=source_type).count()
                chunks_by_source[source_type] = count
            
            recent_jobs = ContentProcessingJob.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()
            
            return {
                'total_chunks': total_chunks,
                'active_chunks': active_chunks,
                'chunks_by_source_type': chunks_by_source,
                'recent_processing_jobs': recent_jobs
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {str(e)}")
            return {}
