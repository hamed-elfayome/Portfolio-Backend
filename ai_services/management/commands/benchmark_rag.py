"""
Management command to benchmark RAG service performance.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import time
import statistics
from ai_services.rag_service import RAGService
from ai_services.optimized_rag_service import OptimizedRAGService


class Command(BaseCommand):
    help = 'Benchmark RAG service performance and compare optimized vs standard implementation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queries',
            type=int,
            default=5,
            help='Number of test queries to run (default: 5)'
        )
        parser.add_argument(
            '--warmup',
            type=int,
            default=2,
            help='Number of warmup queries to run (default: 2)'
        )

    def handle(self, *args, **options):
        num_queries = options['queries']
        num_warmup = options['warmup']
        
        self.stdout.write(self.style.SUCCESS('Starting RAG Performance Benchmark...'))
        
        # Test queries
        test_queries = [
            "What programming languages does the developer know?",
            "Tell me about the developer's experience with web development",
            "What projects has the developer worked on?",
            "What are the developer's key skills and expertise?",
            "Describe the developer's educational background",
            "What technologies does the developer use?",
            "Tell me about the developer's work experience",
            "What are the developer's achievements?",
            "What kind of projects does the developer build?",
            "What is the developer's experience with databases?"
        ]
        
        # Initialize services
        standard_rag = RAGService()
        optimized_rag = OptimizedRAGService()
        
        self.stdout.write(f'Running {num_warmup} warmup queries...')
        
        # Warmup queries
        for i in range(num_warmup):
            query = test_queries[i % len(test_queries)]
            self.stdout.write(f'Warmup {i+1}: {query[:50]}...')
            
            # Standard RAG warmup
            try:
                standard_rag.query(query)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Standard RAG warmup failed: {e}'))
            
            # Optimized RAG warmup
            try:
                optimized_rag.query(query)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Optimized RAG warmup failed: {e}'))
        
        self.stdout.write('\nRunning performance tests...')
        
        # Performance tests
        standard_times = []
        optimized_times = []
        standard_confidences = []
        optimized_confidences = []
        
        for i in range(num_queries):
            query = test_queries[i % len(test_queries)]
            self.stdout.write(f'Test {i+1}: {query[:50]}...')
            
            # Test standard RAG
            start_time = time.time()
            try:
                standard_result = standard_rag.query(query)
                standard_time = time.time() - start_time
                standard_times.append(standard_time)
                standard_confidences.append(standard_result.get('confidence', 0))
                self.stdout.write(f'  Standard: {standard_time:.3f}s, confidence: {standard_result.get("confidence", 0):.2f}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Standard RAG failed: {e}'))
                standard_times.append(float('inf'))
                standard_confidences.append(0)
            
            # Test optimized RAG
            start_time = time.time()
            try:
                optimized_result = optimized_rag.query(query)
                optimized_time = time.time() - start_time
                optimized_times.append(optimized_time)
                optimized_confidences.append(optimized_result.get('confidence', 0))
                self.stdout.write(f'  Optimized: {optimized_time:.3f}s, confidence: {optimized_result.get("confidence", 0):.2f}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Optimized RAG failed: {e}'))
                optimized_times.append(float('inf'))
                optimized_confidences.append(0)
        
        # Calculate statistics
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('PERFORMANCE BENCHMARK RESULTS'))
        self.stdout.write('='*60)
        
        # Filter out infinite times for statistics
        valid_standard_times = [t for t in standard_times if t != float('inf')]
        valid_optimized_times = [t for t in optimized_times if t != float('inf')]
        
        if valid_standard_times:
            self.stdout.write(f'\nStandard RAG Service:')
            self.stdout.write(f'  Average time: {statistics.mean(valid_standard_times):.3f}s')
            self.stdout.write(f'  Median time: {statistics.median(valid_standard_times):.3f}s')
            self.stdout.write(f'  Min time: {min(valid_standard_times):.3f}s')
            self.stdout.write(f'  Max time: {max(valid_standard_times):.3f}s')
            self.stdout.write(f'  Average confidence: {statistics.mean(standard_confidences):.3f}')
            self.stdout.write(f'  Success rate: {len(valid_standard_times)}/{num_queries} ({len(valid_standard_times)/num_queries*100:.1f}%)')
        
        if valid_optimized_times:
            self.stdout.write(f'\nOptimized RAG Service:')
            self.stdout.write(f'  Average time: {statistics.mean(valid_optimized_times):.3f}s')
            self.stdout.write(f'  Median time: {statistics.median(valid_optimized_times):.3f}s')
            self.stdout.write(f'  Min time: {min(valid_optimized_times):.3f}s')
            self.stdout.write(f'  Max time: {max(valid_optimized_times):.3f}s')
            self.stdout.write(f'  Average confidence: {statistics.mean(optimized_confidences):.3f}')
            self.stdout.write(f'  Success rate: {len(valid_optimized_times)}/{num_queries} ({len(valid_optimized_times)/num_queries*100:.1f}%)')
        
        # Performance comparison
        if valid_standard_times and valid_optimized_times:
            avg_standard = statistics.mean(valid_standard_times)
            avg_optimized = statistics.mean(valid_optimized_times)
            improvement = ((avg_standard - avg_optimized) / avg_standard) * 100
            
            self.stdout.write(f'\nPerformance Improvement:')
            if improvement > 0:
                self.stdout.write(self.style.SUCCESS(f'  Optimized RAG is {improvement:.1f}% faster'))
            else:
                self.stdout.write(self.style.WARNING(f'  Optimized RAG is {abs(improvement):.1f}% slower'))
            
            # Confidence comparison
            avg_standard_conf = statistics.mean(standard_confidences)
            avg_optimized_conf = statistics.mean(optimized_confidences)
            conf_diff = avg_optimized_conf - avg_standard_conf
            
            self.stdout.write(f'  Confidence difference: {conf_diff:+.3f}')
        
        # Get performance stats
        self.stdout.write(f'\nOptimized RAG Performance Stats:')
        try:
            stats = optimized_rag.get_performance_stats()
            for key, value in stats.items():
                self.stdout.write(f'  {key}: {value}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error getting stats: {e}'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Benchmark completed!'))
