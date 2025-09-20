"""
Django management command for database optimization.
"""

from django.core.management.base import BaseCommand
from core.database_optimization import DatabaseOptimizationService


class Command(BaseCommand):
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
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )
    
    def handle(self, *args, **options):
        service = DatabaseOptimizationService()
        verbose = options['verbose']
        
        if options['stats_only']:
            self.stdout.write(self.style.SUCCESS("Database Statistics:"))
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
            self.stdout.write(self.style.SUCCESS("Analyzing database performance..."))
            stats = service.get_database_stats()
            self.stdout.write(f"Found {len(stats['indexes'])} indexes across {len(stats['tables'])} tables")
            
            if verbose:
                self.stdout.write("\nDetailed Statistics:")
                for table_name, table_info in stats['tables'].items():
                    self.stdout.write(f"  Table: {table_name}")
                    self.stdout.write(f"    Records: {table_info['count']}")
                
                self.stdout.write("\nIndexes:")
                for idx in stats['indexes']:
                    self.stdout.write(f"  - {idx['name']} on {idx['table']}")
            
            return
        
        # Run full optimization
        self.stdout.write(self.style.SUCCESS("Starting database optimization..."))
        
        # Add missing indexes
        self.stdout.write("Adding missing indexes...")
        index_results = service.add_missing_indexes()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(index_results['created'])} new indexes"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"Skipped {len(index_results['skipped'])} existing indexes"
            )
        )
        
        if index_results['created'] and verbose:
            self.stdout.write("New indexes created:")
            for idx_name in index_results['created']:
                self.stdout.write(f"  - {idx_name}")
        
        # Run database optimization
        self.stdout.write("Running database optimization...")
        optimizations = service.optimize_database()
        
        for optimization in optimizations:
            self.stdout.write(f"  - {optimization}")
        
        self.stdout.write(self.style.SUCCESS("Database optimization completed!"))
        
        # Show final statistics
        if verbose:
            self.stdout.write("\nFinal Database Statistics:")
            stats = service.get_database_stats()
            self.stdout.write(f"Total indexes: {len(stats['indexes'])}")
            if 'database_size_mb' in stats:
                self.stdout.write(f"Database size: {stats['database_size_mb']:.2f} MB")
