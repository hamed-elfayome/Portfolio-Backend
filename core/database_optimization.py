"""
Database optimization service for performance improvements.
Adds missing indexes, optimizes queries, and provides performance monitoring.
"""

from django.db import models, connection
from django.core.management.base import BaseCommand
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)


class DatabaseOptimizationService:
    """Service for database optimization and performance monitoring."""
    
    def __init__(self):
        self.connection = connection
    
    def add_missing_indexes(self):
        """Add missing database indexes for better performance."""
        indexes_to_add = [
            # Profile model indexes
            {
                'table': 'core_profile',
                'name': 'idx_profile_is_active',
                'columns': ['is_active'],
                'description': 'Index for filtering active profiles'
            },
            {
                'table': 'core_profile',
                'name': 'idx_profile_created_at',
                'columns': ['created_at'],
                'description': 'Index for ordering profiles by creation date'
            },
            
            # Project model indexes
            {
                'table': 'projects_project',
                'name': 'idx_project_difficulty_level',
                'columns': ['difficulty_level'],
                'description': 'Index for filtering by difficulty level'
            },
            {
                'table': 'projects_project',
                'name': 'idx_project_order',
                'columns': ['"order"'],
                'description': 'Index for ordering projects'
            },
            {
                'table': 'projects_project',
                'name': 'idx_project_composite_featured_order',
                'columns': ['is_featured', '"order"', 'created_at'],
                'description': 'Composite index for project ordering'
            },
            
            # ProjectImage model indexes
            {
                'table': 'projects_image',
                'name': 'idx_projectimage_is_primary',
                'columns': ['is_primary'],
                'description': 'Index for filtering primary images'
            },
            
            # VisitorSession model indexes
            {
                'table': 'visitors_session',
                'name': 'idx_visitorsession_created_at',
                'columns': ['created_at'],
                'description': 'Index for ordering sessions by creation date'
            },
            {
                'table': 'visitors_session',
                'name': 'idx_visitorsession_is_bot',
                'columns': ['is_bot'],
                'description': 'Index for filtering bot sessions'
            },
            {
                'table': 'visitors_session',
                'name': 'idx_visitorsession_is_recruiter',
                'columns': ['is_recruiter'],
                'description': 'Index for filtering recruiter sessions'
            },
            
            # PageView model indexes
            {
                'table': 'visitors_pageview',
                'name': 'idx_pageview_created_at',
                'columns': ['created_at'],
                'description': 'Index for ordering page views by date'
            },
            
            # Conversation model indexes
            {
                'table': 'ai_chat_conversation',
                'name': 'idx_conversation_context_type',
                'columns': ['context_type'],
                'description': 'Index for filtering by context type'
            },
            {
                'table': 'ai_chat_conversation',
                'name': 'idx_conversation_is_active',
                'columns': ['is_active'],
                'description': 'Index for filtering active conversations'
            },
            
            # Message model indexes
            {
                'table': 'ai_chat_message',
                'name': 'idx_message_is_user',
                'columns': ['is_user'],
                'description': 'Index for filtering user vs AI messages'
            },
            {
                'table': 'ai_chat_message',
                'name': 'idx_message_created_at',
                'columns': ['created_at'],
                'description': 'Index for ordering messages by creation time'
            },
            
            # JobAnalysis model indexes
            {
                'table': 'job_matching_analysis',
                'name': 'idx_jobanalysis_overall_match_score',
                'columns': ['overall_match_score'],
                'description': 'Index for filtering by match score'
            },
            {
                'table': 'job_matching_analysis',
                'name': 'idx_jobanalysis_created_at',
                'columns': ['created_at'],
                'description': 'Index for ordering analyses by date'
            },
            
            # DocumentChunk model indexes (for vector operations)
            {
                'table': 'ai_services_documentchunk',
                'name': 'idx_documentchunk_source_type_id',
                'columns': ['source_type', 'source_id'],
                'description': 'Composite index for source filtering'
            },
            {
                'table': 'ai_services_documentchunk',
                'name': 'idx_documentchunk_chunk_index',
                'columns': ['chunk_index'],
                'description': 'Index for ordering chunks'
            },
            
            # EmbeddingCache model indexes
            {
                'table': 'ai_services_embeddingcache',
                'name': 'idx_embeddingcache_expires_at',
                'columns': ['expires_at'],
                'description': 'Index for cache expiration cleanup'
            },
            
            # RAGQuery model indexes
            {
                'table': 'ai_services_ragquery',
                'name': 'idx_ragquery_created_at',
                'columns': ['created_at'],
                'description': 'Index for ordering queries by date'
            },
            {
                'table': 'ai_services_ragquery',
                'name': 'idx_ragquery_processing_time',
                'columns': ['processing_time'],
                'description': 'Index for performance analysis'
            },
        ]
        
        created_indexes = []
        skipped_indexes = []
        
        with self.connection.cursor() as cursor:
            for index_info in indexes_to_add:
                try:
                    # Check if index already exists
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='index' AND name=%s AND tbl_name=%s",
                        [index_info['name'], index_info['table']]
                    )
                    
                    if cursor.fetchone():
                        skipped_indexes.append(index_info['name'])
                        continue
                    
                    # Create the index
                    columns_str = ', '.join(index_info['columns'])
                    create_sql = f"CREATE INDEX {index_info['name']} ON {index_info['table']} ({columns_str})"
                    
                    cursor.execute(create_sql)
                    created_indexes.append(index_info['name'])
                    logger.info(f"Created index: {index_info['name']} on {index_info['table']}")
                    
                except Exception as e:
                    logger.error(f"Failed to create index {index_info['name']}: {str(e)}")
        
        return {
            'created': created_indexes,
            'skipped': skipped_indexes,
            'total_processed': len(indexes_to_add)
        }
    
    def analyze_query_performance(self, query, params=None):
        """Analyze the performance of a database query."""
        start_time = time.time()
        
        with self.connection.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            execution_time = time.time() - start_time
            
            # Get query plan (SQLite specific)
            if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                cursor.execute(f"EXPLAIN QUERY PLAN {query}", params or [])
                query_plan = cursor.fetchall()
            else:
                query_plan = []
            
            return {
                'execution_time': execution_time,
                'row_count': len(results),
                'query_plan': query_plan,
                'results': results
            }
    
    def get_database_stats(self):
        """Get database statistics and performance metrics."""
        stats = {}
        
        with self.connection.cursor() as cursor:
            # Get table sizes
            cursor.execute("""
                SELECT name, 
                       (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as table_count
                FROM sqlite_master m 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            tables = cursor.fetchall()
            stats['tables'] = {table[0]: {'count': table[1]} for table in tables}
            
            # Get index information
            cursor.execute("""
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            
            indexes = cursor.fetchall()
            stats['indexes'] = [
                {'name': idx[0], 'table': idx[1], 'sql': idx[2]} 
                for idx in indexes
            ]
            
            # Get database file size (SQLite specific)
            if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                db_path = settings.DATABASES['default']['NAME']
                try:
                    import os
                    stats['database_size_mb'] = os.path.getsize(db_path) / (1024 * 1024)
                except:
                    stats['database_size_mb'] = 0
            
        return stats
    
    def optimize_database(self):
        """Run database optimization commands."""
        optimizations = []
        
        with self.connection.cursor() as cursor:
            try:
                # SQLite specific optimizations
                if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                    # Analyze tables for better query planning
                    cursor.execute("ANALYZE")
                    optimizations.append("ANALYZE - Updated table statistics")
                    
                    # Vacuum to reclaim space and optimize
                    cursor.execute("VACUUM")
                    optimizations.append("VACUUM - Reclaimed space and optimized database")
                
                # PostgreSQL specific optimizations would go here
                elif 'postgresql' in settings.DATABASES['default']['ENGINE']:
                    # VACUUM ANALYZE for PostgreSQL
                    cursor.execute("VACUUM ANALYZE")
                    optimizations.append("VACUUM ANALYZE - Updated statistics and reclaimed space")
                
            except Exception as e:
                logger.error(f"Database optimization failed: {str(e)}")
                optimizations.append(f"Optimization failed: {str(e)}")
        
        return optimizations
    
    def get_slow_queries(self, threshold_seconds=1.0):
        """Identify potentially slow queries (placeholder for production monitoring)."""
        # In a production environment, this would integrate with query logging
        # For now, return a placeholder
        return {
            'message': 'Slow query monitoring requires production query logging setup',
            'threshold_seconds': threshold_seconds,
            'recommendations': [
                'Enable query logging in production',
                'Use database monitoring tools',
                'Implement query performance tracking'
            ]
        }


class DatabaseOptimizationCommand(BaseCommand):
    """Django management command for database optimization."""
    
    help = 'Optimize database performance by adding indexes and running optimizations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='Only analyze database without making changes',
        )
        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='Only show database statistics',
        )
    
    def handle(self, *args, **options):
        service = DatabaseOptimizationService()
        
        if options['stats_only']:
            self.stdout.write("Database Statistics:")
            stats = service.get_database_stats()
            
            self.stdout.write(f"Tables: {len(stats['tables'])}")
            for table_name, table_info in stats['tables'].items():
                self.stdout.write(f"  - {table_name}: {table_info['count']} records")
            
            self.stdout.write(f"Indexes: {len(stats['indexes'])}")
            for idx in stats['indexes']:
                self.stdout.write(f"  - {idx['name']} on {idx['table']}")
            
            if 'database_size_mb' in stats:
                self.stdout.write(f"Database size: {stats['database_size_mb']:.2f} MB")
            
            return
        
        if options['analyze_only']:
            self.stdout.write("Analyzing database performance...")
            stats = service.get_database_stats()
            self.stdout.write(f"Found {len(stats['indexes'])} indexes across {len(stats['tables'])} tables")
            return
        
        # Run full optimization
        self.stdout.write("Starting database optimization...")
        
        # Add missing indexes
        self.stdout.write("Adding missing indexes...")
        index_results = service.add_missing_indexes()
        
        self.stdout.write(f"Created {len(index_results['created'])} new indexes")
        self.stdout.write(f"Skipped {len(index_results['skipped'])} existing indexes")
        
        if index_results['created']:
            self.stdout.write("New indexes created:")
            for idx_name in index_results['created']:
                self.stdout.write(f"  - {idx_name}")
        
        # Run database optimization
        self.stdout.write("Running database optimization...")
        optimizations = service.optimize_database()
        
        for optimization in optimizations:
            self.stdout.write(f"  - {optimization}")
        
        self.stdout.write("Database optimization completed!")
