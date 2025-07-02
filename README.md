# AI Agent Project

This project is a comprehensive, full-stack AI Agent application designed as a learning tool to master modern AI Agent development and deployment practices.

## Overview

The project includes:
- A React.js frontend for user interaction.
- A Python/FastAPI backend API.
- A Python-based AI Agent service utilizing OpenAI and pgvector for semantic search.
- PostgreSQL for relational data storage and vector embeddings.
- Redis for caching and short-term chat session memory.
- Nginx as a reverse proxy gateway.
- Docker for containerization (local development and production).
- Deployment scripts and documentation for AWS.

## Project Structure

```
ai-agent-project/
├── frontend/                 # React frontend
├── backend/                  # FastAPI backend
├── ai-agent/                 # AI Agent service
├── nginx/                    # Nginx configuration (gateway and prod frontend)
├── aws/                      # AWS deployment scripts and configuration
├── docs/                     # Project documentation (architecture, detailed guides)
├── .env.example              # Environment variables template
├── docker-compose.yml        # Local development environment
├── docker-compose.prod.yml   # Production environment configuration
└── README.md                 # This file
```

## Core Features
- **Intelligent Chat**: AI-powered conversations using OpenAI models.
- **Semantic Search**: pgvector integration for finding relevant information from past conversations (RAG).
- **Memory Management**: Short-term context in Redis, long-term storage in PostgreSQL.
- **User Authentication**: JWT-based authentication for users.
- **Streaming Responses**: Real-time message streaming from AI to the frontend.
- **Containerized Deployment**: Fully containerized using Docker for consistent environments.

## Technology Stack

### Service Components
- **Frontend**: React.js (with React Router, Axios)
- **Backend API**: Python, FastAPI, SQLAlchemy
- **AI Agent Service**: Python, FastAPI, OpenAI API, pgvector
- **Relational & Vector Database**: PostgreSQL with pgvector extension
- **Cache**: Redis
- **Gateway Proxy**: Nginx

### AWS Deployment (Example)
- **Compute**: EC2 (for Docker containers)
- **Database**: RDS for PostgreSQL
- **Cache**: ElastiCache for Redis
- **Container Registry**: ECR
- **Networking**: VPC, ALB, Route 53, Security Groups
- **SSL**: AWS Certificate Manager (ACM)

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js and npm (for local frontend development/dependency management)
- Python (for local backend/AI agent development if not using Docker exclusively)
- Git

### Local Development Setup
1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd ai-agent-project
    ```
2.  **Environment Variables:**
    *   Copy `.env.example` to `.env` in the project root: `cp .env.example .env`
    *   Fill in the required values in `.env`, especially:
        *   `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
        *   `SECRET_KEY` (generate a strong random string)
        *   `OPENAI_API_KEY`
        *   Other variables as needed (defaults are generally fine for local dev).
3.  **Build and Run with Docker Compose:**
    ```bash
    docker compose up --build -d
    ```
    *   This will build all service images and start the containers.
    *   The `-d` flag runs them in detached mode.
    *   Services:
        *   Frontend (React Dev Server): `http://localhost:3000` (proxied by Nginx Gateway to `http://localhost/`)
        *   Nginx Gateway: `http://localhost/` (or `http://localhost:80/`)
        *   Backend API: Accessible via Nginx gateway at `http://localhost/api/v1/backend/`
        *   AI Agent Service: Accessible via Nginx gateway at `http://localhost/api/v1/agent/`
        *   PostgreSQL: Port `5432` (exposed for direct access if needed, but services use Docker network)
        *   Redis: Port `6379` (exposed for direct access if needed)
4.  **Install Frontend Dependencies (Optional, for IDE integration/local scripts):**
    If your IDE needs local `node_modules` or you want to run `npm` scripts directly in `frontend/`:
    ```bash
    cd frontend
    npm install
    cd ..
    ```
5.  **Accessing the Application:**
    Open your browser and navigate to `http://localhost/`. (The Nginx gateway listens on port 80).

### Stopping Local Development
```bash
docker compose down -v # -v removes named volumes (like DB data)
```

## Production Deployment

For deploying this project to AWS, please refer to the detailed guide:
[AWS Deployment Guide](./aws/README.md)

This guide covers setting up the necessary AWS infrastructure (VPC, EC2, RDS, ElastiCache, ECR, ALB, Route53) and deploying the application using the `docker-compose.prod.yml` configuration.

## Further Documentation
- Detailed architecture diagrams and component descriptions can be found in the `docs/` directory (to be added).
- Specific service configurations and API documentation will also be added to `docs/`.
