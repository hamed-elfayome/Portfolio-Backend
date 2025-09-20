"""
Django management command for ingesting content into the RAG system.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from ai_services.content_processor import ContentProcessor
from core.models import Profile
from projects.models import Project
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ingest content from profiles and projects into the RAG system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--profile-id',
            type=str,
            help='Process specific profile by ID'
        )
        parser.add_argument(
            '--project-id',
            type=str,
            help='Process specific project by ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all profiles and projects'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing document chunks before processing'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show processing statistics'
        )
    
    def handle(self, *args, **options):
        processor = ContentProcessor()
        
        # Show statistics
        if options['stats']:
            self.show_stats(processor)
            return
        
        # Clear existing chunks if requested
        if options['clear_existing']:
            self.stdout.write('Clearing existing document chunks...')
            from ai_services.models import DocumentChunk
            count = DocumentChunk.objects.count()
            DocumentChunk.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Cleared {count} existing document chunks')
            )
        
        # Process specific profile
        if options['profile_id']:
            self.process_profile(processor, options['profile_id'])
        
        # Process specific project
        elif options['project_id']:
            self.process_project(processor, options['project_id'])
        
        # Process all content
        elif options['all']:
            self.process_all_content(processor)
        
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify --profile-id, --project-id, --all, or --stats'
                )
            )
    
    def process_profile(self, processor, profile_id):
        """Process a specific profile."""
        try:
            profile = Profile.objects.get(profile_id=profile_id)
            self.stdout.write(f'Processing profile: {profile.name}')
            
            result = processor.process_profile_content(profile)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed profile {profile.name}: '
                        f'{result["chunks_created"]} chunks created'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error processing profile: {result["error"]}')
                )
                
        except Profile.DoesNotExist:
            raise CommandError(f'Profile with ID {profile_id} does not exist')
        except Exception as e:
            raise CommandError(f'Error processing profile: {str(e)}')
    
    def process_project(self, processor, project_id):
        """Process a specific project."""
        try:
            project = Project.objects.get(project_id=project_id)
            self.stdout.write(f'Processing project: {project.title}')
            
            result = processor.process_project_content(project)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed project {project.title}: '
                        f'{result["chunks_created"]} chunks created'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error processing project: {result["error"]}')
                )
                
        except Project.DoesNotExist:
            raise CommandError(f'Project with ID {project_id} does not exist')
        except Exception as e:
            raise CommandError(f'Error processing project: {str(e)}')
    
    def process_all_content(self, processor):
        """Process all profiles and projects."""
        self.stdout.write('Processing all content...')
        
        result = processor.reprocess_all_content()
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed all content:\n'
                    f'  Total chunks: {result["total_chunks"]}\n'
                    f'  Profiles processed: {result["processed_profiles"]}\n'
                    f'  Projects processed: {result["processed_projects"]}'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'Error processing all content: {result["error"]}')
            )
    
    def show_stats(self, processor):
        """Show processing statistics."""
        self.stdout.write('Content Processing Statistics:')
        self.stdout.write('=' * 40)
        
        # Get processing stats
        stats = processor.get_processing_stats()
        
        self.stdout.write(f'Total document chunks: {stats.get("total_chunks", 0)}')
        self.stdout.write(f'Active document chunks: {stats.get("active_chunks", 0)}')
        
        self.stdout.write('\nChunks by source type:')
        for source_type, count in stats.get('chunks_by_source_type', {}).items():
            self.stdout.write(f'  {source_type}: {count}')
        
        self.stdout.write(f'\nRecent processing jobs (7 days): {stats.get("recent_processing_jobs", 0)}')
        
        # Get embedding stats
        embedding_stats = processor.embedding_service.get_embedding_stats()
        
        self.stdout.write('\nEmbedding Service Statistics:')
        self.stdout.write('=' * 40)
        self.stdout.write(f'Model used: {embedding_stats.get("model_used", "N/A")}')
        self.stdout.write(f'Total cached embeddings: {embedding_stats.get("total_cached_embeddings", 0)}')
        self.stdout.write(f'Recent embeddings (7 days): {embedding_stats.get("recent_embeddings_7_days", 0)}')
        self.stdout.write(f'Max tokens per chunk: {embedding_stats.get("max_tokens", 0)}')
        self.stdout.write(f'Default chunk size: {embedding_stats.get("chunk_size", 0)}')
        
        # Show recent processing jobs
        from ai_services.models import ContentProcessingJob
        recent_jobs = ContentProcessingJob.objects.order_by('-created_at')[:5]
        
        if recent_jobs:
            self.stdout.write('\nRecent Processing Jobs:')
            self.stdout.write('=' * 40)
            for job in recent_jobs:
                status_style = self.style.SUCCESS if job.status == 'completed' else self.style.ERROR
                self.stdout.write(
                    f'{job.job_type} - {job.source_type} - '
                    f'{status_style(job.status)} - '
                    f'{job.chunks_created or 0} chunks - '
                    f'{job.created_at.strftime("%Y-%m-%d %H:%M")}'
                )
