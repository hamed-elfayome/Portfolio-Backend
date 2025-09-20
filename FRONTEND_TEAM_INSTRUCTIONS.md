# Frontend Team Instructions - AI-Powered Developer Portfolio Site

## 🎯 Overview

This document provides comprehensive instructions for frontend developers to integrate with the AI-Powered Developer Portfolio Site backend. The backend is production-ready with a complete REST API, AI chat functionality, and job analysis capabilities.

---

## 🏗️ Backend Architecture Summary

### Technology Stack
- **Backend**: Django 4.2.7 with Django REST Framework
- **Database**: PostgreSQL with pgvector extension for AI embeddings
- **AI Services**: OpenAI GPT-4 and embedding models
- **Caching**: Redis for performance optimization
- **Deployment**: Docker containerization (production-ready)

### Key Features
- **Interactive AI Chat**: Real-time chat with RAG (Retrieval-Augmented Generation)
- **Job Analysis**: Upload job descriptions for automated skills matching
- **Project Showcase**: Dynamic project portfolio with AI-powered Q&A
- **Visitor Analytics**: Comprehensive visitor tracking and engagement metrics
- **Production Security**: SSL, rate limiting, input validation, monitoring

---

## 🔌 API Base Configuration

### Base URL
```
Production: https://your-domain.com/api/
Development: http://localhost:8000/api/
```

### Authentication
- **Type**: Session-based (no API keys required for public endpoints)
- **Rate Limiting**: 30 requests/hour for chat endpoints
- **CORS**: Configured for cross-origin requests

### Headers
```javascript
const defaultHeaders = {
  'Content-Type': 'application/json',
  'X-Requested-With': 'XMLHttpRequest',
  // Session cookie will be automatically included
};
```

---

## 📋 Core API Endpoints

### 1. Profile & Projects

#### Get Profile Information
```http
GET /api/profiles/
```
**Response:**
```json
{
  "profile_id": "uuid",
  "name": "Developer Name",
  "bio": "Professional bio",
  "email": "email@example.com",
  "skills": ["Python", "Django", "React"],
  "experience": [...],
  "skills_list": ["Python", "Django", "React"],
  "experience_years": 5,
  "primary_skills": ["Python", "Django"]
}
```

#### Get Projects List
```http
GET /api/projects/
```
**Query Parameters:**
- `featured=true` - Get only featured projects
- `status=completed` - Filter by project status
- `difficulty=intermediate` - Filter by difficulty level
- `search=react` - Search in title/description

**Response:**
```json
[
  {
    "project_id": "uuid",
    "title": "Project Title",
    "description": "Project description",
    "tech_stack_list": ["React", "Node.js", "MongoDB"],
    "is_featured": true,
    "difficulty_level": "intermediate",
    "primary_image": "https://example.com/image.jpg",
    "created_at": "2024-12-19T10:00:00Z"
  }
]
```

#### Get Project Details
```http
GET /api/projects/{project_id}/
```
**Response:**
```json
{
  "project_id": "uuid",
  "title": "Project Title",
  "description": "Detailed description",
  "detailed_description": "Comprehensive project details",
  "tech_stack": ["React", "Node.js", "MongoDB"],
  "github_url": "https://github.com/user/repo",
  "demo_url": "https://demo.example.com",
  "images": [
    {
      "image": "https://example.com/image1.jpg",
      "caption": "Project screenshot",
      "is_primary": true
    }
  ],
  "achievements": ["Performance optimization", "User engagement"],
  "challenges": ["Scalability issues", "Integration complexity"]
}
```

### 2. AI Chat System

#### Send Chat Message
```http
POST /api/chat/
```
**Request Body:**
```json
{
  "question": "Tell me about your React experience",
  "context_type": "general",
  "project_id": "uuid" // Optional for project-specific questions
}
```

**Context Types:**
- `general` - General experience and skills questions
- `project` - Project-specific questions
- `experience` - Work experience questions
- `skills` - Technical skills questions

**Response:**
```json
{
  "answer": "I have extensive experience with React...",
  "confidence": 0.95,
  "response_time": 2.3,
  "chunks_used": ["chunk1", "chunk2"],
  "tokens_used": 150
}
```

#### Chat with Timeout
```http
POST /api/chat/timeout/
```
**Request Body:**
```json
{
  "question": "Complex question about architecture",
  "context_type": "project",
  "project_id": "uuid",
  "timeout": 15 // seconds (1-30)
}
```

**Timeout Response:**
```json
{
  "answer": "I'm taking a bit longer to process your question...",
  "confidence": 0.0,
  "response_time": 15.0,
  "timeout": true,
  "retry": true
}
```

#### Get Chat History
```http
GET /api/chat/history/
```
**Response:**
```json
[
  {
    "conversation_id": "uuid",
    "context_type": "general",
    "title": "General Chat",
    "message_count": 5,
    "messages": [
      {
        "message_id": "uuid",
        "content": "What's your experience with Python?",
        "is_user": true,
        "created_at": "2024-12-19T10:00:00Z"
      },
      {
        "message_id": "uuid",
        "content": "I have 5+ years of Python experience...",
        "is_user": false,
        "confidence_score": 0.95,
        "response_time": 2.1,
        "created_at": "2024-12-19T10:00:02Z"
      }
    ]
  }
]
```

#### Clear Chat History
```http
POST /api/chat/clear/
```
**Response:**
```json
{
  "message": "Cleared 3 conversations",
  "conversations_cleared": 3
}
```

### 3. Job Analysis System

#### Analyze Job Requirements
```http
POST /api/job-analysis/
```
**Request Body (Text):**
```json
{
  "job_requirements": "We are looking for a Senior Python Developer with Django experience..."
}
```

**Request Body (File Upload):**
```javascript
const formData = new FormData();
formData.append('job_file', file); // PDF, TXT, or DOCX file
```

**Response:**
```json
{
  "analysis_id": "uuid",
  "job_details": {
    "title": "Senior Python Developer",
    "company": "Tech Company",
    "location": "Remote"
  },
  "match_scores": {
    "overall": 85,
    "skills": 90,
    "experience": 80,
    "education": 75
  },
  "match_level": "excellent",
  "matched_skills": [
    {
      "skill": "Python",
      "match_type": "exact",
      "confidence": 0.95,
      "years_experience": 5
    }
  ],
  "missing_skills": [
    {
      "skill": "Kubernetes",
      "is_required": true,
      "priority": "high"
    }
  ],
  "recommendations": [
    {
      "type": "skill_development",
      "title": "Learn Kubernetes",
      "description": "Consider taking a Kubernetes course...",
      "priority": "high"
    }
  ],
  "response_time": 3.2
}
```

#### Get Job Analysis History
```http
GET /api/job-analysis/history/
```
**Response:**
```json
[
  {
    "analysis_id": "uuid",
    "job_title": "Senior Python Developer",
    "company_name": "Tech Company",
    "overall_match_score": 85,
    "match_level": "excellent",
    "processing_time": 3.2,
    "created_at": "2024-12-19T10:00:00Z"
  }
]
```

#### Get Job Analysis Details
```http
GET /api/job-analysis/{analysis_id}/
```
**Response:** Full analysis details with skills matches and recommendations

### 4. Search & Analytics

#### Global Search
```http
GET /api/search/?q=react
```
**Response:**
```json
{
  "projects": [
    {
      "project_id": "uuid",
      "title": "React Dashboard",
      "description": "Modern React dashboard...",
      "tech_stack_list": ["React", "TypeScript"]
    }
  ],
  "profiles": [
    {
      "profile_id": "uuid",
      "name": "Developer Name",
      "bio": "React expert with 5+ years..."
    }
  ]
}
```

#### API Statistics
```http
GET /api/stats/
```
**Response:**
```json
{
  "profiles": 1,
  "projects": 15,
  "conversations": 150,
  "job_analyses": 25,
  "document_chunks": 500,
  "visitor_sessions": 1000
}
```

---

## 🎨 Frontend Implementation Guide

### 1. Project Setup

#### Recommended Tech Stack
- **Framework**: React, Vue.js, or Angular
- **State Management**: Redux, Vuex, or NgRx
- **HTTP Client**: Axios, Fetch API, or HttpClient
- **UI Framework**: Material-UI, Ant Design, or Tailwind CSS
- **Real-time**: WebSocket for live chat updates

#### Environment Configuration
```javascript
// config.js
const config = {
  development: {
    apiBaseUrl: 'http://localhost:8000/api/',
    wsUrl: 'ws://localhost:8000/ws/'
  },
  production: {
    apiBaseUrl: 'https://your-domain.com/api/',
    wsUrl: 'wss://your-domain.com/ws/'
  }
};
```

### 2. API Client Setup

#### Axios Configuration
```javascript
// api/client.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
  },
  withCredentials: true // For session cookies
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add any auth headers if needed
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      // Handle rate limiting
      console.warn('Rate limit exceeded. Please wait before making more requests.');
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 3. Chat Component Implementation

#### React Chat Component Example
```jsx
// components/Chat.jsx
import React, { useState, useEffect, useRef } from 'react';
import apiClient from '../api/client';

const Chat = ({ projectId = null, contextType = 'general' }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      content: inputMessage,
      is_user: true,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post('/chat/', {
        question: inputMessage,
        context_type: contextType,
        project_id: projectId
      });

      const aiMessage = {
        content: response.data.answer,
        is_user: false,
        confidence: response.data.confidence,
        response_time: response.data.response_time,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.is_user ? 'user' : 'ai'}`}>
            <div className="message-content">
              {message.content}
            </div>
            {!message.is_user && (
              <div className="message-meta">
                <span className="confidence">
                  Confidence: {Math.round(message.confidence * 100)}%
                </span>
                <span className="response-time">
                  {message.response_time}s
                </span>
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="message ai loading">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="input-container">
        <textarea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me anything about my experience or projects..."
          disabled={isLoading}
          rows={2}
        />
        <button
          onClick={sendMessage}
          disabled={!inputMessage.trim() || isLoading}
          className="send-button"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default Chat;
```

### 4. Job Analysis Component

#### React Job Analysis Component
```jsx
// components/JobAnalysis.jsx
import React, { useState } from 'react';
import apiClient from '../api/client';

const JobAnalysis = () => {
  const [jobText, setJobText] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!allowedTypes.includes(file.type)) {
        setError('Please upload a PDF, TXT, or DOCX file.');
        return;
      }
      
      // Validate file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB.');
        return;
      }
      
      setUploadedFile(file);
      setError(null);
    }
  };

  const analyzeJob = async () => {
    if (!jobText.trim() && !uploadedFile) {
      setError('Please provide job requirements or upload a file.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      
      if (uploadedFile) {
        formData.append('job_file', uploadedFile);
      } else {
        formData.append('job_requirements', jobText);
      }

      const response = await apiClient.post('/job-analysis/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setAnalysis(response.data);
    } catch (err) {
      setError('Failed to analyze job requirements. Please try again.');
      console.error('Job analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getMatchLevelColor = (level) => {
    switch (level) {
      case 'excellent': return '#4CAF50';
      case 'good': return '#8BC34A';
      case 'fair': return '#FF9800';
      case 'poor': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  return (
    <div className="job-analysis-container">
      <h2>Job Requirements Analysis</h2>
      
      <div className="input-section">
        <div className="text-input">
          <label>Job Requirements Text:</label>
          <textarea
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            placeholder="Paste job requirements here..."
            rows={6}
            disabled={isLoading}
          />
        </div>
        
        <div className="file-upload">
          <label>Or Upload File:</label>
          <input
            type="file"
            accept=".pdf,.txt,.docx"
            onChange={handleFileUpload}
            disabled={isLoading}
          />
          {uploadedFile && (
            <p className="file-info">
              Selected: {uploadedFile.name} ({(uploadedFile.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>
        
        <button
          onClick={analyzeJob}
          disabled={isLoading || (!jobText.trim() && !uploadedFile)}
          className="analyze-button"
        >
          {isLoading ? 'Analyzing...' : 'Analyze Job'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {analysis && (
        <div className="analysis-results">
          <div className="job-details">
            <h3>{analysis.job_details.title}</h3>
            <p><strong>Company:</strong> {analysis.job_details.company}</p>
            <p><strong>Location:</strong> {analysis.job_details.location}</p>
          </div>

          <div className="match-scores">
            <h3>Match Scores</h3>
            <div className="scores-grid">
              <div className="score-item">
                <span className="score-label">Overall</span>
                <div className="score-bar">
                  <div 
                    className="score-fill"
                    style={{ 
                      width: `${analysis.match_scores.overall}%`,
                      backgroundColor: getMatchLevelColor(analysis.match_level)
                    }}
                  ></div>
                </div>
                <span className="score-value">{analysis.match_scores.overall}%</span>
              </div>
              <div className="score-item">
                <span className="score-label">Skills</span>
                <div className="score-bar">
                  <div 
                    className="score-fill"
                    style={{ width: `${analysis.match_scores.skills}%` }}
                  ></div>
                </div>
                <span className="score-value">{analysis.match_scores.skills}%</span>
              </div>
              <div className="score-item">
                <span className="score-label">Experience</span>
                <div className="score-bar">
                  <div 
                    className="score-fill"
                    style={{ width: `${analysis.match_scores.experience}%` }}
                  ></div>
                </div>
                <span className="score-value">{analysis.match_scores.experience}%</span>
              </div>
            </div>
          </div>

          <div className="matched-skills">
            <h3>Matched Skills</h3>
            {analysis.matched_skills.map((skill, index) => (
              <div key={index} className="skill-item">
                <span className="skill-name">{skill.skill}</span>
                <span className="skill-confidence">
                  {Math.round(skill.confidence * 100)}% match
                </span>
                <span className="skill-experience">
                  {skill.years_experience} years
                </span>
              </div>
            ))}
          </div>

          {analysis.missing_skills.length > 0 && (
            <div className="missing-skills">
              <h3>Missing Skills</h3>
              {analysis.missing_skills.map((skill, index) => (
                <div key={index} className="skill-item missing">
                  <span className="skill-name">{skill.skill}</span>
                  <span className="skill-priority">
                    {skill.priority} priority
                  </span>
                </div>
              ))}
            </div>
          )}

          <div className="recommendations">
            <h3>Recommendations</h3>
            {analysis.recommendations.map((rec, index) => (
              <div key={index} className="recommendation-item">
                <h4>{rec.title}</h4>
                <p>{rec.description}</p>
                <span className="recommendation-priority">
                  {rec.priority} priority
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default JobAnalysis;
```

### 5. Project Showcase Component

#### React Project Showcase
```jsx
// components/ProjectShowcase.jsx
import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import Chat from './Chat';

const ProjectShowcase = () => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await apiClient.get('/projects/');
      setProjects(response.data);
      if (response.data.length > 0) {
        setSelectedProject(response.data[0]);
      }
    } catch (err) {
      setError('Failed to load projects.');
      console.error('Projects fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchProjectDetails = async (projectId) => {
    try {
      const response = await apiClient.get(`/projects/${projectId}/`);
      setSelectedProject(response.data);
    } catch (err) {
      setError('Failed to load project details.');
      console.error('Project details error:', err);
    }
  };

  if (isLoading) {
    return <div className="loading">Loading projects...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="project-showcase">
      <div className="projects-sidebar">
        <h3>Projects</h3>
        {projects.map((project) => (
          <div
            key={project.project_id}
            className={`project-item ${selectedProject?.project_id === project.project_id ? 'active' : ''}`}
            onClick={() => fetchProjectDetails(project.project_id)}
          >
            <div className="project-image">
              {project.primary_image && (
                <img src={project.primary_image} alt={project.title} />
              )}
            </div>
            <div className="project-info">
              <h4>{project.title}</h4>
              <p>{project.description}</p>
              <div className="tech-stack">
                {project.tech_stack_list.map((tech, index) => (
                  <span key={index} className="tech-tag">{tech}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="project-details">
        {selectedProject && (
          <>
            <div className="project-header">
              <h1>{selectedProject.title}</h1>
              <div className="project-meta">
                <span className="difficulty">{selectedProject.difficulty_level}</span>
                <span className="status">{selectedProject.status}</span>
              </div>
            </div>

            <div className="project-content">
              <div className="project-description">
                <h2>Description</h2>
                <p>{selectedProject.detailed_description}</p>
              </div>

              <div className="project-tech-stack">
                <h2>Technology Stack</h2>
                <div className="tech-list">
                  {selectedProject.tech_stack_list.map((tech, index) => (
                    <span key={index} className="tech-item">{tech}</span>
                  ))}
                </div>
              </div>

              {selectedProject.achievements && selectedProject.achievements.length > 0 && (
                <div className="project-achievements">
                  <h2>Achievements</h2>
                  <ul>
                    {selectedProject.achievements.map((achievement, index) => (
                      <li key={index}>{achievement}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedProject.challenges && selectedProject.challenges.length > 0 && (
                <div className="project-challenges">
                  <h2>Challenges</h2>
                  <ul>
                    {selectedProject.challenges.map((challenge, index) => (
                      <li key={index}>{challenge}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="project-links">
                {selectedProject.github_url && (
                  <a href={selectedProject.github_url} target="_blank" rel="noopener noreferrer">
                    View on GitHub
                  </a>
                )}
                {selectedProject.demo_url && (
                  <a href={selectedProject.demo_url} target="_blank" rel="noopener noreferrer">
                    Live Demo
                  </a>
                )}
              </div>
            </div>

            <div className="project-chat">
              <h2>Ask About This Project</h2>
              <Chat 
                projectId={selectedProject.project_id}
                contextType="project"
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ProjectShowcase;
```

---

## 🎨 UI/UX Guidelines

### 1. Design Principles
- **Clean & Modern**: Minimalist design with focus on content
- **Responsive**: Mobile-first approach with breakpoints
- **Accessible**: WCAG 2.1 AA compliance
- **Performance**: Optimized loading and smooth interactions

### 2. Color Scheme
```css
:root {
  --primary-color: #2563eb;
  --secondary-color: #64748b;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
  --background-color: #ffffff;
  --surface-color: #f8fafc;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --border-color: #e2e8f0;
}
```

### 3. Typography
```css
/* Headings */
h1 { font-size: 2.5rem; font-weight: 700; line-height: 1.2; }
h2 { font-size: 2rem; font-weight: 600; line-height: 1.3; }
h3 { font-size: 1.5rem; font-weight: 600; line-height: 1.4; }

/* Body text */
body { font-size: 1rem; font-weight: 400; line-height: 1.6; }

/* Code */
code { font-family: 'Fira Code', monospace; font-size: 0.875rem; }
```

### 4. Component Styling

#### Chat Component Styles
```css
.chat-container {
  display: flex;
  flex-direction: column;
  height: 500px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background-color: var(--surface-color);
}

.message {
  margin-bottom: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  max-width: 80%;
}

.message.user {
  background-color: var(--primary-color);
  color: white;
  margin-left: auto;
}

.message.ai {
  background-color: white;
  border: 1px solid var(--border-color);
}

.message-meta {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.input-container {
  display: flex;
  padding: 1rem;
  background-color: white;
  border-top: 1px solid var(--border-color);
}

.input-container textarea {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  resize: none;
  font-family: inherit;
}

.send-button {
  margin-left: 0.5rem;
  padding: 0.75rem 1.5rem;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.send-button:disabled {
  background-color: var(--secondary-color);
  cursor: not-allowed;
}
```

#### Job Analysis Styles
```css
.job-analysis-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.input-section {
  background-color: var(--surface-color);
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.score-bar {
  width: 100%;
  height: 8px;
  background-color: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  margin: 0.5rem 0;
}

.score-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.skill-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background-color: white;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.skill-item.missing {
  border-left: 4px solid var(--error-color);
}
```

---

## 🔧 Error Handling & Loading States

### 1. Error Handling Strategy
```javascript
// utils/errorHandler.js
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return `Bad Request: ${data.error || 'Invalid input'}`;
      case 404:
        return 'Resource not found';
      case 429:
        return 'Rate limit exceeded. Please wait before making more requests.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return `Error ${status}: ${data.error || 'Unknown error'}`;
    }
  } else if (error.request) {
    // Network error
    return 'Network error. Please check your connection.';
  } else {
    // Other error
    return 'An unexpected error occurred.';
  }
};
```

### 2. Loading States
```jsx
// components/LoadingSpinner.jsx
const LoadingSpinner = ({ size = 'medium', text = 'Loading...' }) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12'
  };

  return (
    <div className="loading-spinner">
      <div className={`spinner ${sizeClasses[size]}`}></div>
      {text && <p className="loading-text">{text}</p>}
    </div>
  );
};

// CSS for spinner
.spinner {
  border: 2px solid var(--border-color);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

### 3. Retry Logic
```javascript
// utils/retry.js
export const retryRequest = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
    }
  }
};
```

---

## 📱 Responsive Design

### 1. Breakpoints
```css
/* Mobile First Approach */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
```

### 2. Mobile Chat Interface
```css
@media (max-width: 768px) {
  .chat-container {
    height: 100vh;
    border-radius: 0;
  }
  
  .project-showcase {
    flex-direction: column;
  }
  
  .projects-sidebar {
    order: 2;
    max-height: 200px;
    overflow-y: auto;
  }
  
  .project-details {
    order: 1;
  }
}
```

---

## 🚀 Performance Optimization

### 1. Code Splitting
```javascript
// Lazy load components
const Chat = React.lazy(() => import('./components/Chat'));
const JobAnalysis = React.lazy(() => import('./components/JobAnalysis'));

// Use with Suspense
<Suspense fallback={<LoadingSpinner />}>
  <Chat />
</Suspense>
```

### 2. Image Optimization
```jsx
// Optimized image component
const OptimizedImage = ({ src, alt, ...props }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  return (
    <div className="image-container">
      {!isLoaded && !hasError && (
        <div className="image-placeholder">
          <LoadingSpinner size="small" />
        </div>
      )}
      <img
        src={src}
        alt={alt}
        onLoad={() => setIsLoaded(true)}
        onError={() => setHasError(true)}
        style={{ display: isLoaded ? 'block' : 'none' }}
        {...props}
      />
    </div>
  );
};
```

### 3. API Caching
```javascript
// Simple in-memory cache
const cache = new Map();

export const cachedApiCall = async (key, apiCall, ttl = 300000) => { // 5 minutes
  const cached = cache.get(key);
  
  if (cached && Date.now() - cached.timestamp < ttl) {
    return cached.data;
  }
  
  const data = await apiCall();
  cache.set(key, { data, timestamp: Date.now() });
  return data;
};
```

---

## 🧪 Testing Guidelines

### 1. Unit Testing
```javascript
// tests/Chat.test.js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Chat from '../components/Chat';
import apiClient from '../api/client';

jest.mock('../api/client');

describe('Chat Component', () => {
  beforeEach(() => {
    apiClient.post.mockClear();
  });

  test('sends message and displays response', async () => {
    const mockResponse = {
      data: {
        answer: 'Test response',
        confidence: 0.95,
        response_time: 2.1
      }
    };
    
    apiClient.post.mockResolvedValue(mockResponse);
    
    render(<Chat />);
    
    const input = screen.getByPlaceholderText(/ask me anything/i);
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('Test response')).toBeInTheDocument();
    });
    
    expect(apiClient.post).toHaveBeenCalledWith('/chat/', {
      question: 'Test question',
      context_type: 'general',
      project_id: null
    });
  });
});
```

### 2. Integration Testing
```javascript
// tests/JobAnalysis.test.js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import JobAnalysis from '../components/JobAnalysis';

describe('Job Analysis Integration', () => {
  test('analyzes job requirements and displays results', async () => {
    render(<JobAnalysis />);
    
    const textarea = screen.getByPlaceholderText(/paste job requirements/i);
    const analyzeButton = screen.getByText('Analyze Job');
    
    fireEvent.change(textarea, {
      target: { value: 'Looking for a Python developer with Django experience' }
    });
    
    fireEvent.click(analyzeButton);
    
    await waitFor(() => {
      expect(screen.getByText(/match scores/i)).toBeInTheDocument();
    });
  });
});
```

---

## 🔒 Security Considerations

### 1. Input Sanitization
```javascript
// utils/sanitize.js
export const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;
  
  // Remove potentially dangerous characters
  return input
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+\s*=/gi, '')
    .trim();
};
```

### 2. File Upload Security
```javascript
// utils/fileValidation.js
export const validateFile = (file) => {
  const allowedTypes = [
    'application/pdf',
    'text/plain',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ];
  
  const maxSize = 10 * 1024 * 1024; // 10MB
  
  if (!allowedTypes.includes(file.type)) {
    throw new Error('Invalid file type');
  }
  
  if (file.size > maxSize) {
    throw new Error('File too large');
  }
  
  return true;
};
```

---

## 📊 Analytics Integration

### 1. Visitor Tracking
```javascript
// utils/analytics.js
export const trackEvent = (eventName, properties = {}) => {
  // Track user interactions
  if (typeof gtag !== 'undefined') {
    gtag('event', eventName, properties);
  }
  
  // Track API calls
  apiClient.interceptors.response.use(
    (response) => {
      trackEvent('api_success', {
        endpoint: response.config.url,
        status: response.status,
        response_time: response.headers['x-response-time']
      });
      return response;
    },
    (error) => {
      trackEvent('api_error', {
        endpoint: error.config?.url,
        status: error.response?.status,
        error: error.message
      });
      return Promise.reject(error);
    }
  );
};
```

### 2. Performance Monitoring
```javascript
// utils/performance.js
export const measurePerformance = (name, fn) => {
  const start = performance.now();
  const result = fn();
  const end = performance.now();
  
  console.log(`${name} took ${end - start} milliseconds`);
  
  // Send to analytics
  trackEvent('performance_measurement', {
    name,
    duration: end - start
  });
  
  return result;
};
```

---

## 🚀 Deployment Checklist

### 1. Pre-deployment
- [ ] All API endpoints tested
- [ ] Error handling implemented
- [ ] Loading states added
- [ ] Responsive design verified
- [ ] Performance optimized
- [ ] Security measures in place
- [ ] Analytics tracking configured

### 2. Environment Configuration
```javascript
// config/environment.js
const environments = {
  development: {
    apiBaseUrl: 'http://localhost:8000/api/',
    debug: true
  },
  staging: {
    apiBaseUrl: 'https://staging-api.yourdomain.com/api/',
    debug: true
  },
  production: {
    apiBaseUrl: 'https://api.yourdomain.com/api/',
    debug: false
  }
};

export default environments[process.env.NODE_ENV || 'development'];
```

### 3. Build Optimization
```javascript
// webpack.config.js or vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          api: ['axios'],
          ui: ['@mui/material', '@mui/icons-material']
        }
      }
    }
  }
};
```

---

## 📞 Support & Resources

### 1. API Documentation
- **Swagger UI**: Available at `/api/docs/` (if enabled)
- **Postman Collection**: Available for testing endpoints
- **Rate Limits**: 30 requests/hour for chat endpoints

### 2. Common Issues & Solutions

#### Rate Limiting
```javascript
// Handle rate limiting gracefully
if (error.response?.status === 429) {
  const retryAfter = error.response.headers['retry-after'];
  showNotification(`Rate limit exceeded. Please wait ${retryAfter} seconds.`);
}
```

#### Network Timeouts
```javascript
// Implement timeout handling
const timeoutPromise = new Promise((_, reject) => {
  setTimeout(() => reject(new Error('Request timeout')), 30000);
});

const response = await Promise.race([
  apiClient.post('/chat/', data),
  timeoutPromise
]);
```

#### File Upload Issues
```javascript
// Handle file upload progress
const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('job_file', file);
  
  try {
    const response = await apiClient.post('/job-analysis/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        setUploadProgress(percentCompleted);
      }
    });
    return response.data;
  } catch (error) {
    throw new Error('File upload failed');
  }
};
```

### 3. Contact Information
- **Technical Support**: Available through project repository
- **API Issues**: Check health endpoint at `/api/health/`
- **Performance Issues**: Monitor response times and error rates

---

**🎉 The backend is production-ready and fully documented. Frontend teams can start integration immediately with these comprehensive instructions and examples.**
