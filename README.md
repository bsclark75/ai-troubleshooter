AI Troubleshooter

OVERVIEW

AI Troubleshooter is an AI-powered incident analysis platform for Nagios environments. The application continuously monitors Nagios log files, detects host and service failures, stores incidents in a local database, and uses a locally hosted Large Language Model (LLM) through Ollama to generate troubleshooting recommendations.

The platform is designed to help system administrators reduce troubleshooting time by automatically analyzing monitoring events, correlating historical incidents, and identifying likely root causes.

Unlike cloud-based AI solutions, AI Troubleshooter operates entirely within your environment using local models hosted by Ollama.

WHY THIS PROJECT EXISTS

Traditional monitoring systems such as Nagios are excellent at detecting failures but provide limited guidance for troubleshooting them.

AI Troubleshooter bridges that gap by combining monitoring data, historical incidents, and local Large Language Models to automatically generate diagnostic recommendations.

The project was built to explore practical AI Operations (AIOps) techniques while maintaining complete control of infrastructure data through locally hosted models.

FEATURES

* Continuous Nagios log monitoring
* Automated incident ingestion
* AI-powered troubleshooting analysis
* Local LLM support through Ollama
* Historical incident storage
* Similar incident retrieval
* Knowledge base integration
* Queue-based processing pipeline
* Incident severity classification
* Incident trend analysis
* Host-level incident views
* Dashboard reporting
* Batch log analysis
* Retry handling for failed AI requests
* Log rotation awareness
* Docker deployment support

PREREQUISITES

- Docker
- Docker Compose
- Nagios
- Python 3.12+
- Ollama

INSTALLATION (DOCKER)

The application is designed to run as a multi-container stack.

Containers

1. ai-troubleshooter
   Main application container.

2. ollama
   Local LLM serving platform.

3. ollama-init
   One-time initialization container used to automatically download the required model.

Default Model

qwen2.5:1.5b

Starting the Application

docker compose up -d

Viewing Logs

docker compose logs -f

Stopping the Application

docker compose down

Environment Variables

OLLAMA_URL
Default:
http://ollama:11434/api/chat

NAGIOSLOGFILE
Default:
/logs/nagios.log

VOLUME MOUNTS

Nagios Logs

Host:
/usr/local/nagios/var

Container:
/logs

Ollama Data

Persistent volume:
ollama

INSTALLATION WITHOUT DOCKER

1. Clone the repository

   git clone <repository-url>

2. Create a virtual environment

   python3 -m venv venv

3. Activate the environment

   source venv/bin/activate

4. Install dependencies

   pip install -r requirements.txt

5. Configure environment variables

   export OLLAMA_URL=http://localhost:11434/api/chat

   export NAGIOSLOGFILE=/usr/local/nagios/var/nagios.log

6. Start Ollama

   ollama serve

7. Download the model

   ollama pull qwen2.5:1.5b

8. Start the application

   uvicorn main:app --host 0.0.0.0 --port 8000

9. Access the dashboard

   http://localhost:8000/dashboard

TECHNOLOGY STACK

Backend Framework

* FastAPI 0.136
* Uvicorn ASGI Server
* Starlette

AI Layer

* Ollama
* qwen2.5:1.5b (default model)

Data Storage

* SQLite

Frontend

* Jinja2 Templates
* HTML Dashboard Views

Networking

* HTTPX
* Requests

Configuration

* Python Dotenv

Containerization

* Docker
* Docker Compose

Language

* Python 3.12+

ARCHITECTURE

The platform consists of five major components:

1. Log Monitoring Layer

   log_watcher.py continuously monitors Nagios logs and detects new events.

2. Processing Pipeline

   Incidents are parsed, normalized, classified, and placed into a processing queue.

3. AI Analysis Layer

   The AI service submits incident context and log data to Ollama for analysis.

4. Knowledge Layer

   Historical incidents and known issues are used to provide additional context for AI analysis.

5. Web Interface

   A web dashboard provides visibility into incidents, processing status, trends, and AI-generated recommendations.

WORKFLOW

1. Nagios writes events to nagios.log
2. Log Watcher detects new entries
3. Events are parsed into incidents
4. Incident severity is determined
5. Incident is stored in SQLite
6. Incident enters processing queue
7. Historical incidents are searched
8. Known issues are searched
9. Context is sent to Ollama
10. AI generates analysis and recommendations
11. Results are stored
12. Dashboard displays incident status and analysis

CORE SERVICES

ai_service.py
    Interfaces with Ollama.

ingestion_service.py
    Accepts and normalizes incident data.

incident_processor.py
    Coordinates incident analysis workflows.

retrieval_service.py
    Searches historical incidents.

knowledge_service.py
    Searches known issues.

queue_service.py
    Manages asynchronous processing.

worker_service.py
    Executes background analysis tasks.

trend_service.py
    Generates incident trend metrics.

severity_service.py
    Determines incident severity levels.

metrics_service.py
    Provides operational statistics.


CONFIGURATION

API ENDPOINTS

General

GET /
Application landing endpoint.

GET /health
Health check endpoint.

Analysis

GET /analyze
Analyze a single incident or log sample.

POST /analyze/batch
Analyze multiple incidents in a batch operation.

Incidents

GET /incidents
List all incidents.

GET /incident/{incident_id}
Retrieve a specific incident.

GET /incident/{incident_id}/ui
Incident detail page.

Hosts

GET /host/{host}
Retrieve incidents for a host.

GET /host/{host}/ui
Host dashboard view.

Monitoring

GET /queue
Current processing queue.

GET /processing
Incidents currently being processed.

GET /failures
Failed processing attempts.

Metrics

GET /stats
System statistics and metrics.

Dashboard

GET /dashboard
Main operational dashboard.

DATABASE

The application uses SQLite for persistent storage.

Incident Table

CREATE TABLE incidents (
id TEXT PRIMARY KEY,
host TEXT,
logs TEXT,
service TEXT,
severity TEXT,
analysis TEXT,
status TEXT,
retry_count INTEGER,
created_at TEXT,
next_retry_at TEXT,
updated_at TEXT
);

Field Descriptions

id
Unique incident identifier.

host
Host generating the alert.

logs
Raw log content associated with the incident.

service
Service associated with the alert.

severity
Classified severity level.

analysis
AI-generated troubleshooting analysis.

status
Current processing status.

retry_count
Number of retry attempts.

created_at
Initial incident timestamp.

next_retry_at
Scheduled retry time.

updated_at
Last modification timestamp.

KNOWLEDGE BASE

The application includes a knowledge repository located in:

knowledge/common_issues.json

Known issues can be added to improve AI recommendations by supplying:

* Common symptoms
* Root causes
* Recommended fixes
* Troubleshooting procedures

DESIGN GOALS

* Keep all AI processing local
* Minimize operational complexity
* Reduce alert investigation time
* Preserve incident history
* Enable future RAG implementations
* Support containerized deployment
* Remain lightweight enough for home labs and small enterprises

FUTURE ROADMAP

* Additional monitoring platform integrations
* Root cause confidence scoring
* RAG-based troubleshooting knowledge base
* Automated remediation workflows
* Alert correlation engine
* Multi-model AI analysis
* Data center monitoring integrations
* Trend forecasting
* Grafana integration
* Foreman and Bitcoin mining infrastructure support

USE CASES

* Infrastructure monitoring
* Linux server administration
* Network operations centers
* Home labs
* Small and medium businesses
* Managed service providers
* Data center operations
* Bitcoin mining operations

AUTHOR

Brian Clark

PROJECT STATUS

Active Development

Current focus areas include:
- Retrieval Augmented Generation (RAG)
- Incident correlation
- Trend analysis
- Automated remediation workflows
- Integration with additional monitoring platforms

LICENSE

This project is provided for educational and operational use. Review all AI-generated recommendations before applying changes to production systems.

