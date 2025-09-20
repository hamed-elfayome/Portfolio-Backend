# Technical Architecture Overview - AI-Powered Developer Portfolio Site

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services   │
│   (React/Vue)   │◄──►│   (Django)      │◄──►│   (OpenAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Database      │
                       │ (PostgreSQL +   │
                       │  pgvector)      │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Cache         │
                       │   (Redis)       │
                       └─────────────────┘
```

### Technology Stack
- **Backend Framework**: Django 4.2.7 with Django REST Framework
- **Database**: PostgreSQL 15 with pgvector extension
- **AI Services**: OpenAI GPT-4 and text-embedding-ada-002
- **Caching**: Redis 7 for sessions and response caching
- **Containerization**: Docker with Docker Compose
- **Web Server**: Nginx (production) / Django dev server (development)
- **Deployment**: Production-ready with health checks and monitoring

---

## 🗄️ Database Architecture

### Core Models & Relationships

#### 1. Profile Management (`core` app)
```python
class Profile(models.Model):
    profile_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    bio = models.TextField()
    email = models.EmailField()
    skills = models.JSONField(default=list)
    experience = models.JSONField(default=list)
    education = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    resume_versions = models.JSONField(default=dict)
    ai_personality_prompt = models.TextField()
    is_active = models.BooleanField(default=True)
```

#### 2. Project Showcase (`projects` app)
```python
class Project(models.Model):
    project_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    detailed_description = models.TextField()
    tech_stack = models.JSONField(default=list)
    github_url = models.URLField(blank=True)
    demo_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    complexity_score = models.FloatField(null=True, blank=True)
    achievements = models.JSONField(default=list)
    challenges = models.JSONField(default=list)
    learnings = models.JSONField(default=list)
```

#### 3. Visitor Analytics (`visitors` app)
```python
class VisitorSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session_key = models.CharField(max_length=50, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.URLField(blank=True)
    device_type = models.CharField(max_length=20)
    browser = models.CharField(max_length=50)
    is_recruiter = models.BooleanField(default=False)
    is_bot = models.BooleanField(default=False)
    page_views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
```

#### 4. AI Chat System (`ai_chat` app)
```python
class Conversation(models.Model):
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    visitor_session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL)
    context_type = models.CharField(max_length=50, choices=CONTEXT_CHOICES)
    title = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    message_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    content = models.TextField()
    is_user = models.BooleanField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    response_time = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    context_chunks_used = models.JSONField(default=list)
    feedback_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 5. Job Analysis (`job_matching` app)
```python
class JobAnalysis(models.Model):
    analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    visitor_session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True)
    job_requirements = models.TextField()
    uploaded_file = models.FileField(upload_to='job_docs/', null=True, blank=True)
    file_processed = models.BooleanField(default=False)
    overall_match_score = models.FloatField()
    skills_match_score = models.FloatField()
    experience_match_score = models.FloatField()
    education_match_score = models.FloatField()
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    skill_gaps = models.JSONField(default=list)
    experience_analysis = models.JSONField(default=dict)
    education_analysis = models.JSONField(default=dict)
    recommendations = models.JSONField(default=list)
    processing_time = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 6. AI Services & RAG System (`ai_services` app)
```python
class DocumentChunk(models.Model):
    chunk_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    content = models.TextField()
    embedding = VectorField(dimensions=1536)  # OpenAI embedding size
    source_type = models.CharField(max_length=50)  # 'project', 'resume', 'experience'
    source_id = models.CharField(max_length=100)
    source_title = models.CharField(max_length=200)
    chunk_index = models.PositiveIntegerField()
    token_count = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class EmbeddingCache(models.Model):
    cache_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    text_hash = models.CharField(max_length=64, unique=True)
    embedding = VectorField(dimensions=1536)
    model_name = models.CharField(max_length=50)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class RAGQuery(models.Model):
    query_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    query_text = models.TextField()
    context_type = models.CharField(max_length=50)
    source_id = models.CharField(max_length=100, null=True, blank=True)
    chunks_retrieved = models.JSONField(default=list)
    chunks_used = models.JSONField(default=list)
    response_time = models.FloatField()
    confidence_score = models.FloatField()
    tokens_used = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
```

### Database Indexes & Optimization
```python
# Optimized indexes for performance
class Meta:
    indexes = [
        models.Index(fields=['source_type']),
        models.Index(fields=['source_id']),
        models.Index(fields=['is_active']),
        models.Index(fields=['created_at']),
        # Vector similarity search index
        models.Index(fields=['embedding'], name='embedding_idx', opclasses=['vector_cosine_ops']),
    ]
```

---

## 🤖 AI Integration Architecture

### RAG (Retrieval-Augmented Generation) System

#### 1. Embedding Generation Service
```python
class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-ada-002"
        self.dimensions = 1536
    
    def create_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise
```

#### 2. Content Processing Pipeline
```python
class ContentProcessor:
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks for embedding."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = text.rfind('.', start, end)
                if last_period > start + self.chunk_size // 2:
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
        
        return chunks
    
    def process_project_content(self, project: Project) -> List[DocumentChunk]:
        """Process project content into chunks with embeddings."""
        chunks = []
        
        # Combine project content
        content = f"""
        Title: {project.title}
        Description: {project.description}
        Detailed Description: {project.detailed_description}
        Tech Stack: {', '.join(project.tech_stack)}
        Achievements: {', '.join(project.achievements)}
        Challenges: {', '.join(project.challenges)}
        Learnings: {', '.join(project.learnings)}
        """
        
        # Chunk the content
        text_chunks = self.chunk_text(content)
        
        # Generate embeddings
        embeddings = self.embedding_service.create_embeddings_batch(text_chunks)
        
        # Create DocumentChunk objects
        for i, (chunk_text, embedding) in enumerate(zip(text_chunks, embeddings)):
            chunk = DocumentChunk.objects.create(
                content=chunk_text,
                embedding=embedding,
                source_type='project',
                source_id=str(project.project_id),
                source_title=project.title,
                chunk_index=i,
                token_count=len(chunk_text.split())
            )
            chunks.append(chunk)
        
        return chunks
```

#### 3. RAG Query Service
```python
class RAGService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_service = EmbeddingService()
        self.similarity_threshold = 0.7
        self.max_chunks = 5
    
    def similarity_search(self, query: str, context_type: str = None, 
                         source_id: str = None, limit: int = 5) -> List[DocumentChunk]:
        """Find similar content chunks using vector similarity search."""
        # Generate query embedding
        query_embedding = self.embedding_service.create_embedding(query)
        
        # Build queryset
        queryset = DocumentChunk.objects.filter(is_active=True)
        
        if context_type:
            queryset = queryset.filter(source_type=context_type)
        
        if source_id:
            queryset = queryset.filter(source_id=source_id)
        
        # Vector similarity search using pgvector
        similar_chunks = queryset.annotate(
            similarity=1 - CosineDistance('embedding', query_embedding)
        ).filter(
            similarity__gte=self.similarity_threshold
        ).order_by('-similarity')[:limit]
        
        return list(similar_chunks)
    
    def generate_answer(self, question: str, context_chunks: List[DocumentChunk]) -> str:
        """Generate answer using GPT-4 with retrieved context."""
        # Prepare context
        context = "\n\n".join([chunk.content for chunk in context_chunks])
        
        # Create system prompt
        system_prompt = f"""
        You are an AI assistant helping visitors learn about a developer's experience and projects.
        Answer the question based on the provided context. Be helpful, accurate, and concise.
        
        Context:
        {context}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GPT-4 response generation failed: {str(e)}")
            raise
    
    def query(self, question: str, context_type: str = None, 
              source_id: str = None) -> Dict:
        """Complete RAG query with similarity search and answer generation."""
        start_time = time.time()
        
        try:
            # Retrieve relevant chunks
            chunks = self.similarity_search(question, context_type, source_id)
            
            if not chunks:
                return {
                    'answer': 'I apologize, but I couldn\'t find relevant information to answer your question.',
                    'confidence': 0.0,
                    'chunks_used': [],
                    'tokens_used': 0
                }
            
            # Generate answer
            answer = self.generate_answer(question, chunks)
            
            # Calculate confidence based on similarity scores
            confidence = sum(chunk.similarity for chunk in chunks) / len(chunks)
            
            # Log query for analytics
            RAGQuery.objects.create(
                query_text=question,
                context_type=context_type or 'general',
                source_id=source_id,
                chunks_retrieved=[str(chunk.chunk_id) for chunk in chunks],
                chunks_used=[str(chunk.chunk_id) for chunk in chunks],
                response_time=time.time() - start_time,
                confidence_score=confidence,
                tokens_used=len(answer.split())
            )
            
            return {
                'answer': answer,
                'confidence': confidence,
                'chunks_used': [str(chunk.chunk_id) for chunk in chunks],
                'tokens_used': len(answer.split())
            }
            
        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            return {
                'answer': 'I apologize, but I encountered an error processing your question.',
                'confidence': 0.0,
                'chunks_used': [],
                'tokens_used': 0,
                'error': str(e)
            }
```

### Job Analysis Service
```python
class JobAnalysisService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_service = EmbeddingService()
    
    def extract_job_details(self, job_text: str) -> Dict:
        """Extract structured job information from text."""
        prompt = f"""
        Extract the following information from this job description:
        1. Job title
        2. Company name
        3. Location
        4. Required skills (list)
        5. Preferred skills (list)
        6. Experience requirements
        7. Education requirements
        
        Job description:
        {job_text}
        
        Return as JSON format.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Job details extraction failed: {str(e)}")
            raise
    
    def analyze_skills_match(self, job_skills: List[str], profile_skills: List[str]) -> Dict:
        """Analyze skills matching between job requirements and profile."""
        matched_skills = []
        missing_skills = []
        
        for skill in job_skills:
            # Check for exact match
            if skill.lower() in [s.lower() for s in profile_skills]:
                matched_skills.append({
                    'skill': skill,
                    'match_type': 'exact',
                    'confidence': 1.0
                })
            else:
                # Check for partial match
                partial_matches = [s for s in profile_skills if skill.lower() in s.lower() or s.lower() in skill.lower()]
                if partial_matches:
                    matched_skills.append({
                        'skill': skill,
                        'match_type': 'partial',
                        'confidence': 0.7,
                        'matched_with': partial_matches[0]
                    })
                else:
                    missing_skills.append({
                        'skill': skill,
                        'is_required': True,
                        'priority': 'high'
                    })
        
        return {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills
        }
    
    def generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """Generate improvement recommendations based on analysis."""
        recommendations = []
        
        # Skills development recommendations
        for missing_skill in analysis['missing_skills']:
            recommendations.append({
                'type': 'skill_development',
                'title': f'Learn {missing_skill["skill"]}',
                'description': f'Consider taking a course or project in {missing_skill["skill"]} to improve your match for this role.',
                'priority': missing_skill['priority'],
                'estimated_effort': '2-4 weeks'
            })
        
        # Experience recommendations
        if analysis['experience_gap'] > 0:
            recommendations.append({
                'type': 'experience_building',
                'title': 'Gain Relevant Experience',
                'description': f'Consider taking on projects or roles that provide {analysis["experience_gap"]} more years of relevant experience.',
                'priority': 'medium',
                'estimated_effort': '6-12 months'
            })
        
        return recommendations
    
    def analyze_job(self, job_text: str, uploaded_file=None, visitor_session=None) -> Dict:
        """Complete job analysis pipeline."""
        start_time = time.time()
        
        try:
            # Process uploaded file if provided
            if uploaded_file:
                job_text = self.process_uploaded_file(uploaded_file)
            
            # Extract job details
            job_details = self.extract_job_details(job_text)
            
            # Get profile data
            profile = Profile.objects.filter(is_active=True).first()
            if not profile:
                raise ValueError("No active profile found")
            
            # Analyze skills match
            skills_analysis = self.analyze_skills_match(
                job_details.get('required_skills', []),
                profile.skills
            )
            
            # Calculate match scores
            total_skills = len(job_details.get('required_skills', []))
            matched_skills_count = len(skills_analysis['matched_skills'])
            skills_score = (matched_skills_count / total_skills * 100) if total_skills > 0 else 0
            
            # Calculate overall match score
            overall_score = (skills_score * 0.6) + (80 * 0.4)  # Weighted average
            
            # Generate recommendations
            recommendations = self.generate_recommendations({
                'missing_skills': skills_analysis['missing_skills'],
                'experience_gap': 0  # Simplified for this example
            })
            
            # Create job analysis record
            analysis = JobAnalysis.objects.create(
                visitor_session=visitor_session,
                job_title=job_details.get('title', ''),
                company_name=job_details.get('company', ''),
                job_requirements=job_text,
                uploaded_file=uploaded_file,
                file_processed=bool(uploaded_file),
                overall_match_score=overall_score,
                skills_match_score=skills_score,
                experience_match_score=80,  # Simplified
                education_match_score=75,   # Simplified
                matched_skills=skills_analysis['matched_skills'],
                missing_skills=skills_analysis['missing_skills'],
                recommendations=recommendations,
                processing_time=time.time() - start_time
            )
            
            return {
                'analysis_id': str(analysis.analysis_id),
                'job_details': job_details,
                'match_scores': {
                    'overall': overall_score,
                    'skills': skills_score,
                    'experience': 80,
                    'education': 75
                },
                'match_level': self.get_match_level(overall_score),
                'matched_skills': skills_analysis['matched_skills'],
                'missing_skills': skills_analysis['missing_skills'],
                'recommendations': recommendations,
                'response_time': time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Job analysis failed: {str(e)}")
            raise
    
    def get_match_level(self, score: float) -> str:
        """Determine match level based on score."""
        if score >= 90:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 50:
            return 'fair'
        else:
            return 'poor'
```

---

## 🚀 API Architecture

### REST API Design

#### 1. URL Structure
```
/api/
├── profiles/                    # Profile management
├── projects/                    # Project showcase
├── visitor-sessions/           # Visitor analytics
├── conversations/              # Chat conversations
├── job-analyses/              # Job analysis results
├── document-chunks/           # AI content chunks
├── chat/                      # Chat endpoints
├── job-analysis/              # Job analysis endpoints
├── search/                    # Global search
├── stats/                     # API statistics
├── health/                    # Health checks
└── cache/                     # Cache management
```

#### 2. ViewSet Architecture
```python
class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Project model with filtering and search."""
    serializer_class = ProjectSerializer
    lookup_field = 'project_id'
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return projects with optimized queries and filtering."""
        queryset = query_optimizer.get_optimized_projects()
        
        # Apply filters
        featured = self.request.query_params.get('featured')
        if featured is not None:
            queryset = queryset.filter(is_featured=featured.lower() == 'true')
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get all featured projects."""
        featured_projects = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(featured_projects, many=True)
        return Response(serializer.data)
```

#### 3. Custom API Endpoints
```python
@api_view(['POST'])
@throttle_classes([ChatRateThrottle])
def chat_endpoint(request):
    """Real-time chat endpoint with RAG integration."""
    try:
        question = request.data.get('question', '').strip()
        context_type = request.data.get('context_type', 'general')
        project_id = request.data.get('project_id', None)
        
        # Validate input
        if not question:
            return Response(
                {'error': 'Question is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process with RAG service
        rag_service = RAGService()
        start_time = time.time()
        
        result = rag_service.query(
            question, 
            context_type=context_type, 
            source_id=project_id
        )
        
        result['response_time'] = round(time.time() - start_time, 2)
        
        # Save conversation
        if hasattr(request, 'visitor_session') and request.visitor_session:
            save_chat_message(request.visitor_session, question, result, context_type)
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### Serialization & Validation
```python
class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model with related images."""
    images = ProjectImageSerializer(many=True, read_only=True)
    tech_stack_list = serializers.ReadOnlyField(source='get_tech_stack_list')
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'project_id', 'title', 'description', 'tech_stack',
            'github_url', 'demo_url', 'is_featured', 'images',
            'primary_image', 'created_at'
        ]
        read_only_fields = ['project_id', 'created_at']
    
    def get_primary_image(self, obj):
        """Get the primary image URL for the project."""
        primary_image = obj.get_primary_image()
        return primary_image.image.url if primary_image else None
```

---

## ⚡ Performance Optimization

### 1. Database Optimization

#### Query Optimization
```python
class QueryOptimizer:
    @staticmethod
    def get_optimized_projects():
        """Get projects with optimized queries."""
        return Project.objects.select_related('profile').prefetch_related(
            'images', 'conversations'
        ).filter(is_active=True)
    
    @staticmethod
    def get_optimized_profiles(active_only=True):
        """Get profiles with optimized queries."""
        queryset = Profile.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.prefetch_related('projects')
```

#### Database Indexes
```python
# Optimized indexes for performance
class DocumentChunk(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['source_type']),
            models.Index(fields=['source_id']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
            # Vector similarity search index
            models.Index(fields=['embedding'], name='embedding_idx', opclasses=['vector_cosine_ops']),
        ]
```

### 2. Caching Strategy

#### Redis Caching
```python
class APICacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB
        )
        self.default_ttl = 300  # 5 minutes
    
    def get_cache_stats(self):
        """Get comprehensive cache statistics."""
        info = self.redis_client.info()
        return {
            'total_keys': info['db0']['keys'],
            'memory_usage': info['used_memory_human'],
            'hit_rate': info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses']),
            'connected_clients': info['connected_clients']
        }
    
    def cache_api_response(self, key: str, data: Any, ttl: int = None):
        """Cache API response data."""
        ttl = ttl or self.default_ttl
        self.redis_client.setex(
            f"api:{key}",
            ttl,
            json.dumps(data, default=str)
        )
    
    def get_cached_response(self, key: str) -> Any:
        """Get cached API response."""
        cached = self.redis_client.get(f"api:{key}")
        if cached:
            return json.loads(cached)
        return None
```

#### Cache Decorators
```python
def cache_api_response(cache_key: str, ttl: int = 300):
    """Decorator to cache API responses."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_service = APICacheService()
            cached = cache_service.get_cached_response(cache_key)
            
            if cached:
                return Response(cached)
            
            response = func(*args, **kwargs)
            if hasattr(response, 'data'):
                cache_service.cache_api_response(cache_key, response.data, ttl)
            
            return response
        return wrapper
    return decorator
```

### 3. Async Processing

#### Async Chat Processing
```python
@api_view(['POST'])
@throttle_classes([ChatRateThrottle])
def chat_with_timeout(request):
    """Chat endpoint with timeout handling."""
    try:
        question = request.data.get('question', '').strip()
        timeout = request.data.get('timeout', 10)
        
        # Create async task with timeout
        async def process_chat():
            return await sync_to_async(rag_service.query)(
                question, 
                context_type=context_type, 
                source_id=project_id
            )
        
        # Run with timeout
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                asyncio.wait_for(process_chat(), timeout=timeout)
            )
        finally:
            loop.close()
        
        return Response(result)
        
    except asyncio.TimeoutError:
        return Response({
            'answer': 'I\'m taking a bit longer to process your question...',
            'timeout': True,
            'retry': True
        }, status=status.HTTP_408_REQUEST_TIMEOUT)
```

---

## 🛡️ Security Architecture

### 1. Authentication & Authorization
```python
# Session-based authentication
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF protection
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ['https://yourdomain.com']
```

### 2. Rate Limiting
```python
class ChatRateThrottle(AnonRateThrottle):
    """Custom rate throttle for chat endpoints."""
    rate = '30/hour'

class JobAnalysisRateThrottle(AnonRateThrottle):
    """Rate throttle for job analysis endpoints."""
    rate = '10/hour'
```

### 3. Input Validation & Sanitization
```python
class InputValidator:
    @staticmethod
    def validate_chat_input(data):
        """Validate chat input data."""
        question = data.get('question', '').strip()
        
        if not question:
            raise ValidationError('Question is required')
        
        if len(question) > 1000:
            raise ValidationError('Question too long (max 1000 characters)')
        
        # Sanitize input
        question = html.escape(question)
        
        return {
            'question': question,
            'context_type': data.get('context_type', 'general'),
            'project_id': data.get('project_id')
        }
    
    @staticmethod
    def validate_file_upload(file):
        """Validate uploaded file."""
        allowed_types = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        max_size = 10 * 1024 * 1024  # 10MB
        
        if file.content_type not in allowed_types:
            raise ValidationError('Invalid file type')
        
        if file.size > max_size:
            raise ValidationError('File too large')
        
        return True
```

### 4. Security Headers
```python
# Security middleware configuration
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
```

---

## 📊 Monitoring & Logging

### 1. Health Checks
```python
@api_view(['GET'])
def health_check(request):
    """Comprehensive health check endpoint."""
    checks = {
        'database': check_database_connection(),
        'redis': check_redis_connection(),
        'openai': check_openai_connection(),
        'disk_space': check_disk_space(),
        'memory': check_memory_usage()
    }
    
    overall_status = 'healthy' if all(checks.values()) else 'unhealthy'
    
    return Response({
        'status': overall_status,
        'timestamp': timezone.now().isoformat(),
        'checks': checks
    })

def check_database_connection():
    """Check database connectivity."""
    try:
        from django.db import connection
        connection.cursor()
        return True
    except Exception:
        return False

def check_redis_connection():
    """Check Redis connectivity."""
    try:
        redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        redis_client.ping()
        return True
    except Exception:
        return False
```

### 2. Performance Monitoring
```python
class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        process_time = time.time() - start_time
        
        # Log slow requests
        if process_time > 2.0:
            logger.warning(f"Slow request: {request.path} took {process_time:.2f}s")
        
        # Add performance headers
        response['X-Process-Time'] = str(process_time)
        
        return response
```

### 3. Structured Logging
```python
# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/application.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/errors.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'ai_services': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## 🐳 Deployment Architecture

### 1. Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "portfolio_site.wsgi:application"]
```

### 2. Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:password@db:5432/portfolio_db
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      - ./media:/app/media
    restart: unless-stopped

  db:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_DB=portfolio_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 3. Production Settings
```python
# settings/production.py
import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'portfolio_db'),
        'USER': os.environ.get('DB_USER', 'user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Redis
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Logging
LOGGING['handlers']['file']['filename'] = '/app/logs/application.log'
LOGGING['handlers']['error_file']['filename'] = '/app/logs/errors.log'
```

---

## 🔧 Development Workflow

### 1. Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd portfolio-site

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py loaddata fixtures/sample_data.json

# Start development server
python manage.py runserver
```

### 2. Testing Strategy
```python
# tests/test_rag_service.py
class RAGServiceTestCase(TestCase):
    def setUp(self):
        self.rag_service = RAGService()
        self.test_project = Project.objects.create(
            title="Test Project",
            description="Test description",
            tech_stack=["Python", "Django"]
        )
    
    def test_similarity_search(self):
        """Test vector similarity search."""
        chunks = self.rag_service.similarity_search(
            "Python Django project",
            context_type="project"
        )
        self.assertGreater(len(chunks), 0)
    
    def test_generate_answer(self):
        """Test answer generation."""
        chunks = DocumentChunk.objects.filter(source_type="project")[:3]
        answer = self.rag_service.generate_answer(
            "What technologies were used?",
            chunks
        )
        self.assertIsInstance(answer, str)
        self.assertGreater(len(answer), 0)
```

### 3. API Testing
```python
# tests/test_api.py
class ChatAPITestCase(APITestCase):
    def test_chat_endpoint(self):
        """Test chat API endpoint."""
        response = self.client.post('/api/chat/', {
            'question': 'Tell me about your Python experience',
            'context_type': 'general'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('answer', response.data)
        self.assertIn('confidence', response.data)
    
    def test_job_analysis_endpoint(self):
        """Test job analysis API endpoint."""
        response = self.client.post('/api/job-analysis/', {
            'job_requirements': 'Looking for a Python developer with Django experience'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('match_scores', response.data)
        self.assertIn('recommendations', response.data)
```

---

## 📈 Scalability Considerations

### 1. Horizontal Scaling
- **Load Balancer**: Nginx or AWS ALB for traffic distribution
- **Multiple Instances**: Docker containers behind load balancer
- **Database**: Read replicas for read-heavy operations
- **Cache**: Redis cluster for distributed caching

### 2. Performance Optimization
- **Connection Pooling**: Database connection pooling
- **Query Optimization**: Efficient database queries with proper indexing
- **Caching Strategy**: Multi-level caching (Redis, CDN, browser)
- **Async Processing**: Background tasks for heavy operations

### 3. Monitoring & Alerting
- **Health Checks**: Comprehensive health monitoring
- **Performance Metrics**: Response time and throughput monitoring
- **Error Tracking**: Centralized error logging and alerting
- **Resource Monitoring**: CPU, memory, and disk usage tracking

---

**🎉 This technical architecture provides a robust, scalable, and maintainable foundation for the AI-Powered Developer Portfolio Site, with comprehensive AI integration, security measures, and production-ready deployment capabilities.**
