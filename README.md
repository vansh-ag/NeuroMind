# NeuroMind — AI Learning Assistant

NeuroMind is an AI-powered learning assistant backend that generates personalized learning roadmaps, recommends practical projects, and answers roadmap-specific follow-up questions using Retrieval-Augmented Generation (RAG).

The application is built with FastAPI, PostgreSQL, Gemini, and Qdrant. It uses structured LLM outputs, Pydantic validation, retry handling, validation-driven response correction, semantic retrieval, and roadmap-isolated vector search.

## Features

### Personalized Learning Roadmap

Generate a structured learning roadmap based on:

* Career goal
* Experience level
* Existing skills
* Preferred learning style
* Weekly learning availability

The generated roadmap contains:

* Estimated total learning hours
* Recommended skills
* Ordered learning tasks
* Estimated hours for each task
* Actionable subtasks

### AI Project Recommendation

Generate a personalized project recommendation using either:

* An existing `roadmap_id`, or
* A goal title and list of skills

The recommendation includes:

* Project title
* Difficulty level
* Estimated completion time
* Recommended technology stack
* Core features
* Explanation of why the project is suitable

### Roadmap-Grounded AI Chat

Users can ask follow-up questions about their generated roadmap.

Example:

> Can I learn Docker before PostgreSQL?

The chat endpoint uses a complete RAG pipeline instead of passing the entire roadmap directly to the LLM.

The system:

1. Converts the user question into an embedding.
2. Searches Qdrant for semantically relevant roadmap chunks.
3. Filters retrieval results using the requested `roadmap_id`.
4. Retrieves the top relevant roadmap sections.
5. Sends only the retrieved context and user question to Gemini.
6. Returns a grounded answer with suggested follow-up questions.

### Structured AI Responses

Gemini responses are generated using structured JSON schemas and validated through Pydantic models before being returned by the API.

This reduces unreliable output formatting and prevents malformed LLM responses from reaching the application layer.

### Validation-Driven AI Response Correction

If a generated roadmap fails application-level Pydantic validation, NeuroMind:

1. Extracts the validation errors.
2. Builds a correction prompt containing the exact failed fields.
3. Sends the invalid response and validation feedback back to the model.
4. Regenerates the complete roadmap.
5. Validates the corrected response again.

This is particularly useful for enforcing constraints such as concise task titles and properly structured subtasks.

### Retry Mechanism

Temporary Gemini provider failures are retried using exponential backoff.

The retry strategy handles transient failures such as:

* Temporary service unavailability
* Model overload
* Provider-side server errors

Permanent application errors and invalid structured responses are handled separately.

---

## Tech Stack

### Backend

* Python 3.11
* FastAPI
* Pydantic v2
* SQLAlchemy 2.0 Async
* asyncpg
* Alembic
* Uvicorn

### AI

* Google Gemini
* Google GenAI Python SDK
* Gemini structured output
* Gemini text embeddings
* Prompt engineering
* Pydantic output validation

### Databases

* PostgreSQL for application and roadmap data
* Qdrant for vector embeddings and semantic retrieval

### Reliability and Tooling

* Tenacity for retry handling
* python-json-logger for structured application logs
* pydantic-settings for environment configuration
* uv for dependency and environment management

---

## Architecture Overview

```text
                        ┌─────────────────────┐
                        │       Client        │
                        │  Swagger / Frontend │
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │       FastAPI       │
                        │     API Routes      │
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │    Service Layer    │
                        │                     │
                        │ Roadmap Service     │
                        │ Project Service     │
                        │ Chat Service        │
                        └───────┬─────┬───────┘
                                │     │
                 ┌──────────────┘     └──────────────┐
                 ▼                                   ▼
        ┌─────────────────┐                 ┌─────────────────┐
        │   PostgreSQL    │                 │      Gemini     │
        │                 │                 │                 │
        │ Roadmaps        │                 │ Generation      │
        │ Tasks           │                 │ Embeddings      │
        │ Subtasks        │                 │ Chat Response   │
        └─────────────────┘                 └────────┬────────┘
                                                    │
                                                    ▼
                                           ┌─────────────────┐
                                           │   RAG Pipeline  │
                                           │                 │
                                           │ Document Builder│
                                           │ Embedding       │
                                           │ Retriever       │
                                           └────────┬────────┘
                                                    │
                                                    ▼
                                           ┌─────────────────┐
                                           │     Qdrant      │
                                           │                 │
                                           │ Vectors         │
                                           │ Chunk Content   │
                                           │ Metadata        │
                                           └─────────────────┘
```

---

## Project Structure

```text
NeuroMind/
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── app/
│   ├── ai/
│   │   ├── prompts/
│   │   │   ├── roadmap_prompt.py
│   │   │   ├── project_prompt.py
│   │   │   └── chat_prompt.py
│   │   └── client.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── roadmap.py
│   │   │   ├── project.py
│   │   │   └── chat.py
│   │   └── router.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── models/
│   │   ├── roadmap.py
│   │   ├── roadmap_task.py
│   │   └── roadmap_subtask.py
│   │
│   ├── rag/
│   │   ├── document_builder.py
│   │   ├── embedding_service.py
│   │   ├── vector_store.py
│   │   ├── indexer.py
│   │   └── retriever.py
│   │
│   ├── repositories/
│   │   └── roadmap_repository.py
│   │
│   ├── schemas/
│   │   ├── roadmap.py
│   │   ├── project.py
│   │   └── chat.py
│   │
│   ├── services/
│   │   ├── roadmap_service.py
│   │   ├── project_service.py
│   │   └── chat_service.py
│   │
│   └── main.py
│
├── data/
│   └── qdrant/              # Local vector data, not committed
│
├── .env.example
├── .gitignore
├── alembic.ini
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## RAG Architecture

The `/chat` endpoint is implemented as a complete Retrieval-Augmented Generation pipeline.

### Why RAG Is Used

The generated roadmap is user-specific and is not part of the LLM's original knowledge.

A normal chat implementation could pass the complete roadmap into every prompt, but this approach becomes inefficient as the knowledge base grows and does not demonstrate actual retrieval.

NeuroMind instead stores roadmap knowledge in a vector database and retrieves only the most relevant roadmap sections for each question.

### Indexing Pipeline

```text
Generated Roadmap
        ↓
Save structured data to PostgreSQL
        ↓
Build semantic task-level documents
        ↓
Generate embeddings
        ↓
Store vectors and metadata in Qdrant
```

### Query Pipeline

```text
User Question
        ↓
Generate query embedding
        ↓
Semantic vector search
        ↓
Filter by roadmap_id
        ↓
Retrieve Top-K roadmap chunks
        ↓
Build grounded prompt
        ↓
Gemini structured generation
        ↓
Response + Follow-up Questions
```

---

## Chunking Strategy

NeuroMind uses structure-aware semantic chunking.

Each roadmap task becomes one retrievable document containing:

* Learning goal
* Experience level
* Learning style
* Weekly learning hours
* Task order
* Task title
* Task description
* Estimated hours
* Associated subtasks

Example:

```text
Learning Goal: Backend Developer

Task Order: 3
Task Title: Learn PostgreSQL

Task Description:
Understand relational database concepts and integrate PostgreSQL
with backend applications.

Estimated Task Hours:
15

Subtasks:
- Learn relational database concepts
- Practice SQL queries
- Understand indexing
- Connect PostgreSQL with FastAPI
```

This strategy was chosen instead of fixed character-based chunking because the roadmap already contains natural semantic boundaries.

Keeping a task and its subtasks together improves retrieval relevance and preserves the meaning of each learning stage.

---

## Embedding Strategy

Roadmap documents and user queries are converted into dense vector representations using Gemini embeddings.

The application uses separate semantic instructions for:

* Stored roadmap documents
* User retrieval queries

The vectors are stored in Qdrant using cosine similarity.

The embedding dimension is configurable through environment variables.

---

## Vector Storage and Retrieval

Qdrant is used as the vector database.

Each vector point stores:

```text
Vector
+
Payload:
    roadmap_id
    chunk_index
    task_title
    content
```

Retrieval uses:

```text
Semantic Similarity
+
roadmap_id Metadata Filter
+
Top-K Selection
```

The `roadmap_id` filter prevents chunks belonging to another user's roadmap from entering the retrieved context.

For the assignment implementation, Qdrant runs in local persistent mode. This avoids requiring an additional external vector database service during local setup while maintaining a real vector retrieval pipeline.

---

## Database Design

PostgreSQL stores the structured roadmap data.

The primary entities are:

### Roadmap

Stores:

* Goal title
* Experience level
* Known skills
* Learning style
* Weekly available hours
* Estimated total hours
* Recommended skills

### Roadmap Task

Stores:

* Task title
* Description
* Estimated hours
* Sequence order
* Parent roadmap relationship

### Roadmap Subtask

Stores:

* Subtask title
* Sequence order
* Parent task relationship

Database schema changes are managed using Alembic migrations.

---

## API Endpoints

### Health Check

```http
GET /api/v1/health
```

### Generate Learning Roadmap

```http
POST /api/v1/roadmaps
```

Example request:

```json
{
  "goal_title": "Backend Developer",
  "experience": "Less than 1 year",
  "known_skills": [
    "Python",
    "SQL"
  ],
  "learning_style": "Project Based",
  "weekly_hours": 15
}
```

Example response structure:

```json
{
  "roadmap_id": "uuid",
  "estimated_hours": 120,
  "skills": [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Docker"
  ],
  "tasks": [
    {
      "title": "Learn FastAPI",
      "description": "Learn API development with FastAPI.",
      "estimated_hours": 12,
      "subtasks": [
        {
          "title": "Learn routing"
        }
      ]
    }
  ]
}
```

### Get Roadmap

```http
GET /api/v1/roadmaps/{roadmap_id}
```

### Recommend Project

```http
POST /api/v1/projects
```

Using an existing roadmap:

```json
{
  "roadmap_id": "uuid"
}
```

Or using direct input:

```json
{
  "goal_title": "Backend Developer",
  "skills": [
    "Python",
    "FastAPI",
    "SQL"
  ]
}
```

### Roadmap-Grounded Chat

```http
POST /api/v1/chat
```

Example request:

```json
{
  "roadmap_id": "uuid",
  "message": "Can I learn Docker before PostgreSQL?"
}
```

Example response:

```json
{
  "response": "You can learn Docker fundamentals before PostgreSQL, but understanding databases first can make containerizing a complete backend application more practical.",
  "follow_up_questions": [
    "Would you like a revised learning order?",
    "Which Docker concepts should you learn first?",
    "Would you like a project combining FastAPI, PostgreSQL, and Docker?"
  ]
}
```

---

## Setup Instructions

### Prerequisites

Make sure the following are installed:

* Python 3.11+
* PostgreSQL
* uv
* Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd NeuroMind
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
APP_NAME=NeuroMind
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/neuromind

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=768

QDRANT_PATH=./data/qdrant
QDRANT_COLLECTION_NAME=roadmap_chunks

RAG_TOP_K=3
```

Do not commit the `.env` file.

### 4. Create PostgreSQL Database

Create a PostgreSQL database named:

```text
neuromind
```

Update the `DATABASE_URL` in `.env` with the correct PostgreSQL username and password.

### 5. Run Database Migrations

```bash
uv run alembic upgrade head
```

### 6. Start the Application

```bash
uv run python -m uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Prompt Design Decisions

The application uses separate prompts for each AI capability.

### Roadmap Prompt

The roadmap prompt provides:

* Learner goal
* Experience level
* Known skills
* Learning preference
* Weekly availability
* Output constraints

The prompt instructs the model to avoid unnecessarily repeating skills the learner already knows and to generate a practical progression based on prerequisites.

### Project Recommendation Prompt

The project prompt focuses on practical skill application.

The model receives:

* Target role
* Relevant skills

It is instructed to recommend a project with appropriate difficulty, realistic scope, practical features, and a technology stack aligned with the learner's goal.

### Chat Prompt

The chat prompt separates:

* System instructions
* Retrieved roadmap context
* Current user question

The model is instructed to use retrieved roadmap context as its primary source and avoid inventing roadmap-specific details that are not supported by the retrieved context.

The response also includes one to three follow-up questions intended to anticipate likely next questions from the learner.

---

## AI Reliability Strategy

LLM outputs are nondeterministic, so NeuroMind uses multiple reliability layers.

### Structured Generation

Gemini is instructed to return JSON matching predefined schemas.

### Pydantic Validation

All structured outputs are validated before entering the application layer.

### Validation Correction

Invalid roadmap outputs are corrected using validation feedback and regenerated.

### Transient Retry

Temporary Gemini server failures are retried with exponential backoff.

### Error Separation

The application distinguishes between:

* Temporary provider failures
* Empty AI responses
* Invalid structured responses
* Missing roadmaps
* Request validation failures

This prevents unrelated failure types from being handled identically.

---

## Additional Product Improvement

The additional product improvement implemented in NeuroMind is a combined AI reliability mechanism consisting of:

* Retry handling for temporary AI provider failures
* Exponential backoff
* Structured response validation
* Validation-driven roadmap correction and regeneration

This improves the user experience by reducing failures caused by temporary provider overload or malformed LLM output.

Instead of immediately returning an error when a roadmap violates the application schema, the system gives the model targeted validation feedback and attempts to generate a corrected response.

---

## Logging

NeuroMind uses structured logging for important application events.

Examples include:

```text
application_starting
roadmap_generation_started
roadmap_generation_completed
roadmap_response_validation_failed
project_generation_started
project_generation_completed
roadmap_vectors_upserted
roadmap_indexing_completed
rag_retrieval_started
rag_retrieval_completed
chat_generation_started
chat_generation_completed
```

Structured logs make debugging the AI and RAG pipelines easier and provide visibility into each stage of the application workflow.

---

## Assumptions

The following assumptions were made:

1. A roadmap is relatively small and can be indexed synchronously after generation.
2. Each roadmap task represents a meaningful semantic retrieval unit.
3. The top three retrieved chunks provide sufficient context for typical roadmap questions.
4. PostgreSQL is responsible for relational application data.
5. Qdrant is responsible only for semantic retrieval data.
6. Qdrant local persistent mode is sufficient for assignment demonstration and local development.
7. A production deployment could move vector indexing to a background worker.
8. Authentication and multi-user account management are outside the assignment scope.
9. The LLM can provide general educational guidance, but roadmap-specific claims should be grounded in retrieved roadmap context.

---

## Current Limitations and Production Improvements

For a production deployment, the following improvements could be added:

* Background job processing for roadmap indexing
* Indexing status tracking
* Conversation history
* User authentication and authorization
* Redis caching
* Streaming chat responses
* Hybrid keyword and vector retrieval
* Retrieval relevance thresholds
* Reranking
* Managed Qdrant deployment
* Rate limiting
* Automated unit and integration tests
* Distributed tracing and monitoring

---

## Approximate Time Spent

Approximate development time: **10–14 hours**

This includes:

* Architecture planning
* FastAPI API design
* Database modeling
* Alembic migration setup
* Gemini integration
* Prompt engineering
* Structured output validation
* Retry and correction handling
* RAG architecture
* Qdrant integration
* Retrieval testing
* End-to-end API testing
* Documentation

---

## Use of AI Development Tools

AI-assisted development tools were used during the development of NeuroMind to support learning, implementation, debugging, and code quality improvement. These tools were used as development assistants, while the project architecture, technology choices, integration decisions, testing, and final implementation decisions were evaluated and validated manually.

### ChatGPT

ChatGPT was primarily used as a development and learning assistant throughout the project.

It was used for:

* Understanding and designing the overall backend architecture.
* Breaking the assignment requirements into manageable development phases.
* Understanding RAG concepts such as chunking strategies, embeddings, vector storage, semantic retrieval, and grounded generation.
* Evaluating technology choices, including PostgreSQL for relational data and Qdrant for vector retrieval.
* Understanding FastAPI, SQLAlchemy async patterns, Alembic migrations, and Pydantic structured validation.
* Debugging integration issues involving Gemini, PostgreSQL, Alembic, Qdrant, and asynchronous Python code.
* Analyzing error traces and identifying possible causes and fixes.
* Improving prompt design for roadmap generation, project recommendations, and RAG-based chat.
* Reviewing implementation approaches and identifying edge cases and architectural improvements.
* Assisting with technical documentation and explaining architectural decisions.

ChatGPT was also used during debugging to understand runtime errors, validation failures, database configuration issues, and AI provider errors. Suggested solutions were reviewed and tested against the actual application before being retained.

### GitHub Copilot

GitHub Copilot was used as an in-editor coding assistant during implementation.

It was primarily used for:

* Code completion and boilerplate generation.
* Suggesting repetitive implementation patterns.
* Assisting with FastAPI route and schema development.
* Supporting SQLAlchemy model and repository implementation.
* Suggesting small refactoring improvements.
* Helping identify and resolve straightforward coding errors.
* Accelerating repetitive code while maintaining the existing project architecture and coding patterns.

Copilot-generated suggestions were reviewed and modified where necessary before being included in the final codebase.

### OpenAI Codex

OpenAI Codex was used selectively for coding assistance and implementation support.

It was used for:

* Assisting with selected code implementation tasks.
* Reviewing and improving code structure.
* Supporting error resolution and debugging.
* Suggesting fixes for implementation-level issues.
* Helping refine existing code while preserving the intended architecture.
* Assisting with repetitive or mechanical coding tasks.

Codex suggestions were treated as implementation assistance rather than automatically accepted output. Changes were reviewed, tested, and integrated only when they matched the project requirements and architecture.

### AI-Assisted Development Approach

The development process followed an AI-assisted engineering workflow:

```text
Assignment Requirements
        ↓
Requirement Analysis and Architecture Design
        ↓
Implementation with AI-Assisted Development Tools
        ↓
Manual Review and Integration
        ↓
Local Testing
        ↓
Error Analysis and Debugging
        ↓
End-to-End Validation
```

AI tools helped accelerate development and improve understanding, but the application was tested through direct API calls, database migration verification, embedding tests, Qdrant storage tests, semantic retrieval tests, roadmap isolation tests, and complete end-to-end RAG chat testing.

The final technology choices, including FastAPI, PostgreSQL, Gemini, structure-aware roadmap chunking, Qdrant vector storage, cosine similarity retrieval, and roadmap-specific metadata filtering, were selected based on the requirements and validated through implementation and testing.


## Demonstration Flow

The recommended demonstration sequence is:

1. Start the FastAPI application.
2. Open Swagger documentation.
3. Generate a Backend Developer learning roadmap.
4. Show the generated tasks, skills, and estimated hours.
5. Generate a project recommendation using the returned `roadmap_id`.
6. Ask a roadmap-specific question through the chat endpoint.
7. Show retrieval and generation logs in the terminal.
8. Explain task-level chunking, embeddings, Qdrant retrieval, and `roadmap_id` filtering.
9. Show the structured chat response and follow-up questions.

---

## Author

**Vansh Agarwal**

AI/ML Engineer and Full-Stack Developer

Built as part of the AI Engineering Intern Assignment.
