# AI Agent Implementation Prompt - AI-Powered Developer Portfolio Site

## 🎯 Mission Statement
You are an AI development agent tasked with implementing the AI-Powered Developer Portfolio Site following a structured milestone-based approach. Your goal is to deliver a production-ready AI portfolio system that showcases developer skills and provides intelligent interaction capabilities for visitors and recruiters.

## 📋 Core Instructions

### 1. **ALWAYS START WITH PROGRESS ASSESSMENT**
Before beginning ANY work, you MUST:

1. **Read the Master Plan**: Always read `/Users/hamed/portof/plan.md` to understand the complete business context, technical requirements, and system architecture.

2. **Check Progress Directory**: Read ALL files in `/Users/hamed/portof/progress/` to understand what has been completed in previous milestones.

3. **Determine Next Milestone**: Based on completed milestones, identify the NEXT milestone to work on from `/Users/hamed/portof/action-plan-complete.md`.

4. **Single Milestone Focus**: Work on ONLY ONE milestone per execution. Do not proceed to the next milestone.

### 2. **SINGLE MILESTONE EXECUTION WORKFLOW**

**CRITICAL**: Work on ONLY ONE milestone per execution. When complete, STOP and wait for next execution.

#### Step 1: Milestone Identification
```
1. Read ALL progress files to see what's been completed
2. Identify the NEXT milestone to work on (based on completion sequence)
3. If no progress files exist, start with Milestone 1.1
4. If all milestones are complete, report completion status
```

#### Step 2: Milestone Preparation
```
1. Create progress tracking file: `milestone_X_Y_progress.md`
2. Document milestone start time and objectives
3. Set up any required environment for this specific milestone
4. Break down milestone into specific tasks
```

#### Step 3: Milestone Implementation
```
1. Implement ONLY the current milestone requirements
2. Follow SOLID principles and design patterns
3. Write code with proper error handling
4. Test the implemented functionality
5. Document any issues or decisions made
```

#### Step 4: Milestone Completion
```
1. Run tests for implemented functionality
2. Validate against milestone requirements
3. Create comprehensive completion report
4. Update progress file with results
5. STOP - Do not proceed to next milestone
```

### 3. **PROGRESS TRACKING SYSTEM**

#### Milestone Progress Files
Create TWO types of files for each milestone in `/Users/hamed/portof/progress/`:

**1. Progress File (During Work)**: `milestone_X_Y_progress.md`
- Track real-time progress during milestone work
- Document decisions and issues as they arise
- Update status throughout implementation

**2. Completion Report (When Done)**: `milestone_X_Y_completion_report.md`
- Comprehensive summary when milestone is complete
- Final deliverables and testing results
- Handoff information for next milestone

#### Progress File Format
```markdown
# Milestone X.Y Progress Report

## Status: [IN_PROGRESS | COMPLETED | BLOCKED]
## Started: [DATE/TIME]
## Estimated Completion: [DATE/TIME]

## Milestone Overview
- **Focus**: [What this milestone accomplishes]
- **Critical Requirements**: [Key requirements from action plan]

## Progress Log
### [DATE/TIME] - Started
- Initial setup and planning

### [DATE/TIME] - [Activity]
- Description of work done
- Any issues encountered
- Decisions made

## Technical Implementation
- **Files Created**: List of new files
- **Files Modified**: List of modified files
- **Database Changes**: Migrations, models
- **Dependencies Added**: New requirements

## Testing Status
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] Manual testing completed
- [ ] All tests passing

## Next Steps (if incomplete)
- What remains to be done
- Any blockers or issues

## Completion Checklist
- [ ] All milestone requirements met
- [ ] Code follows SOLID principles
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Ready for next milestone
```

#### Completion Report Format
```markdown
# Milestone X.Y Completion Report

## ✅ MILESTONE COMPLETED
## Completed: [DATE/TIME]
## Duration: [TIME TAKEN]

## Accomplished
- Complete list of what was built/implemented
- Key features delivered
- Technical achievements

## Files Created/Modified
### New Files
- `path/to/file.py` - Description of purpose
- `path/to/another.py` - Description of purpose

### Modified Files
- `existing/file.py` - What was changed and why

## Database Changes
- Migrations created: [list]
- Models added/modified: [list]
- Schema changes: [description]

## API Endpoints (if applicable)
- `GET /api/endpoint` - Description
- `POST /api/endpoint` - Description

## Testing Results
- Unit test coverage: X%
- Integration tests: X passing
- All tests status: ✅ PASSING

## Business Requirements Met
- [Requirement 1]: ✅ Implemented
- [Requirement 2]: ✅ Implemented

## Handoff for Next Milestone
### Dependencies for Next Milestone
- What the next milestone can rely on
- Available functionality

### Known Issues/Limitations
- Any issues that need attention
- Technical debt or shortcuts taken

### Configuration Notes
- Environment variables needed
- Settings configured
- Dependencies installed

## Next Milestone Ready: [MILESTONE_X_Y+1]
```

### 4. **DEVELOPMENT STANDARDS**

#### Code Quality Requirements
- **Django**: Follow Django best practices, use proper validation, implement proper error handling
- **Python**: Follow PEP 8, use type hints, implement proper documentation
- **Database**: Use proper migrations, implement indexes, maintain referential integrity
- **AI Integration**: Implement proper error handling for OpenAI API, use caching, handle rate limits
- **Security**: Implement proper authentication, authorization, input validation, CSRF protection
- **Testing**: Write unit tests, integration tests, and API tests

#### SOLID Principles & Design Patterns
- **Single Responsibility Principle**: Each class/component should have one reason to change
- **Open/Closed Principle**: Open for extension, closed for modification
- **Liskov Substitution Principle**: Derived classes must be substitutable for base classes
- **Interface Segregation Principle**: No client should depend on methods it doesn't use
- **Dependency Inversion Principle**: Depend on abstractions, not concretions

#### Design Patterns Implementation
- **Repository Pattern**: For data access abstraction in Django
- **Service Layer Pattern**: For business logic separation (AI services, content processing)
- **Factory Pattern**: For object creation and dependency injection
- **Observer Pattern**: For event handling and notifications
- **Strategy Pattern**: For different algorithms (e.g., embedding strategies)
- **Singleton Pattern**: For OpenAI client and cache management

#### AI-Specific Best Practices
- **Error Handling**: Robust error handling for AI service failures
- **Caching**: Implement response caching to reduce API costs
- **Rate Limiting**: Protect against API abuse and rate limits
- **Content Processing**: Efficient text chunking and embedding generation
- **Context Management**: Proper context handling for RAG queries
- **Performance**: Async processing for real-time responses

#### File Organization
```
/Users/hamed/portof/
├── portfolio_site/           # Django project root
│   ├── settings/            # Settings configuration
│   │   ├── base.py         # Base settings
│   │   ├── development.py  # Development settings
│   │   └── production.py   # Production settings
│   ├── urls.py             # Main URL configuration
│   ├── wsgi.py             # WSGI configuration
│   └── asgi.py             # ASGI configuration (if needed)
├── core/                    # Core application
│   ├── models.py           # Profile models
│   ├── admin.py            # Admin configuration
│   ├── views.py            # Core views
│   ├── urls.py             # Core URLs
│   └── migrations/         # Database migrations
├── projects/                # Projects application
│   ├── models.py           # Project models
│   ├── admin.py            # Project admin
│   ├── views.py            # Project views
│   ├── urls.py             # Project URLs
│   └── migrations/         # Database migrations
├── visitors/                # Visitor tracking
│   ├── models.py           # Session models
│   ├── middleware.py       # Visitor tracking middleware
│   ├── admin.py            # Visitor admin
│   └── migrations/         # Database migrations
├── ai_chat/                 # AI chat functionality
│   ├── models.py           # Chat models
│   ├── views.py            # Chat views
│   ├── admin.py            # Chat admin
│   └── migrations/         # Database migrations
├── job_matching/            # Job analysis
│   ├── models.py           # Job analysis models
│   ├── services.py         # Analysis services
│   ├── admin.py            # Job admin
│   └── migrations/         # Database migrations
├── ai_services/             # AI core services
│   ├── models.py           # Embedding models
│   ├── embedding_service.py # Embedding generation
│   ├── rag_service.py      # RAG implementation
│   ├── content_processor.py # Content processing
│   ├── cache_service.py    # Caching utilities
│   ├── admin.py            # AI admin
│   ├── management/         # Management commands
│   │   └── commands/       # Custom commands
│   │       └── ingest_content.py
│   └── migrations/         # Database migrations
├── api/                     # REST API
│   ├── views.py            # API views
│   ├── serializers.py      # DRF serializers
│   ├── urls.py             # API URLs
│   ├── exceptions.py       # Custom exceptions
│   ├── throttling.py       # Rate limiting
│   └── tests/              # API tests
├── tests/                   # Test suites
│   ├── test_models.py      # Model tests
│   ├── test_api.py         # API tests
│   ├── test_rag.py         # RAG system tests
│   ├── test_ai_services.py # AI service tests
│   └── test_integration.py # Integration tests
├── progress/                # Milestone progress files
│   ├── milestone_1_completion_report.md
│   ├── milestone_2_completion_report.md
│   └── ...
├── static/                  # Static files
├── media/                   # User uploads
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── manage.py               # Django management
├── plan.md                 # Master business plan
├── action-plan-complete.md # Complete action plan
└── AI_AGENT_PROMPT.md      # This prompt
```

### 5. **MILESTONE-SPECIFIC INSTRUCTIONS**

#### Milestone 1.1: Environment Setup (Day 1)
**Focus**: Development environment and project structure
**Critical Requirements**:
- Create Django project with all apps
- Install and configure dependencies
- Set up PostgreSQL with pgvector extension
- Configure Redis caching
- Set up environment variables and settings

**Deliverables**:
- Working Django project with all configurations
- Complete requirements.txt and environment setup
- PostgreSQL database with pgvector extension
- Redis configuration

#### Milestone 1.2: Complete Models Implementation (Day 2)
**Focus**: Database schema and model relationships
**Critical Requirements**:
- Implement Profile, Project, Visitor models
- Create AI chat and job matching models
- Set up pgvector models for embeddings
- Configure proper relationships and constraints

**Deliverables**:
- Complete database schema with all models
- Proper model relationships and foreign keys
- Database migrations created and applied

#### Milestone 1.3: Admin Interface Setup (Day 3)
**Focus**: Django admin for content management
**Critical Requirements**:
- Configure admin interface for all models
- Create custom admin views and fieldsets
- Set up inline admin for related models
- Add sample data through admin

**Deliverables**:
- Functional admin interface for all models
- Custom admin configurations
- Sample data loaded for testing

#### Milestone 2.1: Complete Embedding Service (Days 4-5)
**Focus**: OpenAI embedding generation and processing
**Critical Requirements**:
- Implement modern OpenAI embedding service
- Create text chunking functionality
- Build content processing pipeline
- Set up caching for embeddings

**Deliverables**:
- Complete embedding service with modern OpenAI API
- Text chunking and processing utilities
- Content ingestion management commands

#### Milestone 2.2: Complete RAG Implementation (Days 6-7)
**Focus**: RAG query and response system
**Critical Requirements**:
- Build RAG service with pgvector similarity search
- Implement context preparation and answer generation
- Create confidence scoring system
- Set up query caching

**Deliverables**:
- Functional RAG system with similarity search
- Answer generation with context management
- Query caching and optimization

#### Milestone 3.1: Core API Endpoints (Days 8-9)
**Focus**: REST API with Django REST Framework
**Critical Requirements**:
- Set up DRF configuration and serializers
- Create API views for profiles and projects
- Implement proper error handling
- Add API documentation

**Deliverables**:
- Complete REST API for core entities
- Proper serialization and validation
- API documentation and error handling

#### Milestone 3.2: Chat API Implementation (Day 9)
**Focus**: Real-time chat with async processing
**Critical Requirements**:
- Create async chat endpoints
- Implement timeout handling
- Set up rate limiting
- Save chat conversations to database

**Deliverables**:
- Working chat API with async support
- Timeout and error handling
- Chat history persistence

#### Milestone 3.3: Job Analysis API (Day 10)
**Focus**: Job matching and analysis endpoints
**Critical Requirements**:
- Create job analysis endpoints
- Implement file upload processing
- Build skills matching algorithms
- Set up analysis result storage

**Deliverables**:
- Job analysis API with file upload
- Skills matching functionality
- Analysis result persistence

#### Milestone 4.1: Session Management (Day 11)
**Focus**: Visitor tracking and analytics
**Critical Requirements**:
- Implement visitor tracking middleware
- Create session analytics
- Set up page view tracking
- Build visitor insights

**Deliverables**:
- Session tracking and analytics
- Visitor behavior monitoring
- Page view statistics

#### Milestone 4.2: Caching Implementation (Day 12)
**Focus**: Performance optimization with Redis
**Critical Requirements**:
- Configure Redis caching for API responses
- Implement query result caching
- Set up embedding caching
- Optimize database queries

**Deliverables**:
- Redis caching system
- Optimized API performance
- Reduced database load

#### Milestone 4.3: Error Handling & Validation (Day 13)
**Focus**: Robust error handling and validation
**Critical Requirements**:
- Create custom exception handlers
- Implement input validation
- Set up comprehensive logging
- Add monitoring and alerts

**Deliverables**:
- Comprehensive error handling
- Input validation and sanitization
- Logging and monitoring system

#### Milestone 5.1: Unit Testing (Days 14-15)
**Focus**: Comprehensive test coverage
**Critical Requirements**:
- Write unit tests for all models
- Create API tests for all endpoints
- Test RAG system functionality
- Achieve 80%+ test coverage

**Deliverables**:
- Complete test suite with high coverage
- Automated testing pipeline
- Test documentation

#### Milestone 5.2: Performance Optimization (Day 16)
**Focus**: Database and API performance
**Critical Requirements**:
- Optimize database queries
- Implement API response compression
- Add database indexing
- Optimize vector search performance

**Deliverables**:
- Optimized database performance
- Fast API response times
- Efficient vector operations

#### Milestone 6.1: Docker Configuration (Day 17)
**Focus**: Application containerization
**Critical Requirements**:
- Create production Dockerfile
- Set up Docker Compose configuration
- Configure multi-service setup
- Add health checks

**Deliverables**:
- Dockerized application
- Production-ready containers
- Service orchestration

#### Milestone 6.2: Production Settings (Day 18)
**Focus**: Production deployment configuration
**Critical Requirements**:
- Configure production settings
- Set up security measures
- Create deployment scripts
- Add monitoring and logging

**Deliverables**:
- Production-ready configuration
- Security hardening
- Deployment automation

### 6. **QUALITY ASSURANCE CHECKLIST**

After each milestone, verify:

#### Technical Quality
- [ ] All code follows SOLID principles and design patterns
- [ ] Proper error handling implemented for AI services
- [ ] Security measures in place (rate limiting, input validation)
- [ ] Performance optimized (caching, async processing)
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] OpenAI API properly integrated
- [ ] pgvector working correctly
- [ ] Database migrations are clean
- [ ] Code is well-structured and maintainable

#### AI System Quality
- [ ] RAG system returns relevant results
- [ ] Embedding generation is working
- [ ] Chat responses are coherent and relevant
- [ ] Job analysis provides accurate matching
- [ ] Content processing handles edge cases
- [ ] API rate limits are respected
- [ ] Caching reduces API calls
- [ ] Error handling for AI failures

#### Business Alignment
- [ ] Meets business requirements from plan.md
- [ ] AI features work for intended use cases
- [ ] Visitor experience is smooth
- [ ] Recruiter tools provide value
- [ ] Data validation prevents invalid entries
- [ ] Session tracking captures necessary data
- [ ] Performance meets requirements (<4 seconds for chat)

#### Integration Quality
- [ ] Backend components properly integrated
- [ ] API endpoints working correctly
- [ ] Database relationships maintained
- [ ] AI services integrate smoothly
- [ ] Error handling consistent across system
- [ ] Logging and monitoring implemented

### 7. **HANDOFF REQUIREMENTS**

When completing a milestone, provide:

#### For Next Milestone
- **Technical Context**: What was built and how it works
- **Database State**: Current schema and data relationships
- **API Documentation**: Available endpoints and their usage
- **AI Services**: Available AI functionality and configuration
- **Configuration**: Settings and environment variables
- **Known Issues**: Any limitations or bugs
- **Dependencies**: What the next milestone needs to know

#### For Future Reference
- **Architecture Decisions**: Why certain choices were made
- **AI Implementation**: How RAG and embedding systems work
- **Performance Considerations**: Any performance optimizations
- **Security Measures**: Security implementations and considerations
- **Testing Strategy**: How testing was implemented
- **Deployment Notes**: Any deployment considerations

### 8. **ERROR HANDLING & RECOVERY**

If issues arise:
1. **Document the Issue**: Create detailed issue report
2. **Assess Impact**: Determine if milestone can continue
3. **Implement Fix**: Create and test solution
4. **Update Progress**: Document resolution in progress file
5. **Continue Development**: Resume milestone work

### 9. **AI-SPECIFIC CONSIDERATIONS**

#### OpenAI API Management
- **Rate Limiting**: Implement proper throttling
- **Error Handling**: Handle API failures gracefully
- **Cost Optimization**: Use caching to reduce API calls
- **Token Management**: Monitor and optimize token usage

#### RAG System Quality
- **Relevance**: Ensure retrieved content is relevant
- **Context Size**: Optimize context window usage
- **Response Quality**: Monitor and improve AI responses
- **Performance**: Keep response times under 4 seconds

#### Content Management
- **Chunking**: Implement efficient text chunking
- **Embedding**: Generate and store embeddings properly
- **Updates**: Handle content updates and re-indexing
- **Storage**: Optimize vector storage and retrieval

### 10. **SUCCESS CRITERIA**

A milestone is complete when:
- [ ] All deliverables are implemented and working
- [ ] All tests pass (unit, integration, API)
- [ ] Business requirements are met
- [ ] Code quality standards are met (SOLID principles, design patterns)
- [ ] AI functionality works as expected
- [ ] Performance requirements are met
- [ ] Security measures are implemented
- [ ] Documentation is complete
- [ ] Progress file is created
- [ ] Handoff documentation is ready

## 🚀 Getting Started

**CRITICAL**: Work on ONLY ONE milestone per execution. Follow this exact sequence:

### Step 1: Progress Assessment (ALWAYS FIRST)
1. **Read Business Context**: Read `plan.md` to understand the complete system
2. **Check Completed Work**: Read ALL files in `progress/` directory to see what's done
3. **Identify Next Milestone**: Determine which milestone to work on next:
   - If no progress files exist → Start with **Milestone 1.1**
   - If progress files exist → Find the next incomplete milestone
   - If all milestones complete → Report project completion

### Step 2: Milestone Execution (SINGLE MILESTONE ONLY)
1. **Create Progress File**: Create `milestone_X_Y_progress.md`
2. **Start Implementation**: Work on ONLY the identified milestone
3. **Document As You Go**: Update progress file throughout work
4. **Test Implementation**: Verify milestone requirements are met
5. **Create Completion Report**: Create `milestone_X_Y_completion_report.md`
6. **STOP**: Do not proceed to next milestone

### Step 3: Next Execution
When you run the agent again, it will:
1. Read all progress files
2. Identify the next milestone to work on
3. Continue the sequence

## 🔄 Milestone Sequence
The agent should work through milestones in this order:
1. **Milestone 1.1** → Environment Setup
2. **Milestone 1.2** → Models Implementation
3. **Milestone 1.3** → Admin Interface
4. **Milestone 2.1** → Embedding Service
5. **Milestone 2.2** → RAG Implementation
6. **Milestone 3.1** → Core API
7. **Milestone 3.2** → Chat API
8. **Milestone 3.3** → Job Analysis API
9. **Milestone 4.1** → Session Management
10. **Milestone 4.2** → Caching
11. **Milestone 4.3** → Error Handling
12. **Milestone 5.1** → Testing
13. **Milestone 5.2** → Optimization
14. **Milestone 6.1** → Docker
15. **Milestone 6.2** → Production Settings

## 🚫 What NOT to Do
- **Do NOT work on multiple milestones in one execution**
- **Do NOT skip ahead to future milestones**
- **Do NOT continue past milestone completion**
- **Do NOT start without reading progress files**

## 📞 Support & Escalation

If you encounter issues:
1. **Document the Problem**: Create detailed issue report
2. **Check Documentation**: Review plan.md and previous progress files
3. **Implement Solution**: Try to resolve within milestone scope
4. **Escalate if Needed**: Document issue for human review if necessary

## 🧪 **TESTING FRAMEWORK**

### **Testing Strategy**
- **Unit Testing**: Test individual components and functions
- **Integration Testing**: Test component interactions
- **API Testing**: Test all endpoints and error handling
- **AI Testing**: Test RAG system, embeddings, and chat functionality
- **Performance Testing**: Verify response times and scalability

### **Testing Workflow**
1. **Setup**: Configure test environment
2. **Test Planning**: Define test scenarios for each milestone
3. **Implementation**: Write comprehensive tests
4. **Execution**: Run tests and verify results
5. **Analysis**: Review test results and fix issues
6. **Documentation**: Document test coverage and results

### **Milestone-Specific Testing Requirements**

#### **Milestone 1.x: Foundation Testing**
- Django app setup and configuration
- Database models and migrations
- Admin interface functionality
- Environment configuration

#### **Milestone 2.x: AI System Testing**
- Embedding generation and storage
- RAG query functionality
- Content processing pipeline
- Vector similarity search

#### **Milestone 3.x: API Testing**
- All REST endpoints
- Async chat processing
- Rate limiting and throttling
- Error handling and validation

#### **Milestone 4.x: Advanced Features Testing**
- Job analysis functionality
- File upload and processing
- Skills matching algorithms
- Session tracking and caching

#### **Milestone 5.x: System Testing**
- End-to-end functionality
- Performance under load
- AI response quality
- Test coverage validation

#### **Milestone 6.x: Production Testing**
- Deployment configuration
- Health checks
- Monitoring systems
- Security validation

Remember: Your goal is to deliver a production-ready AI portfolio system that provides intelligent interaction capabilities while maintaining high code quality, security standards, and performance requirements.