# DevOps Repository Auditing Agent

An autonomous, AI-powered DevOps auditing agent built for MLOps & Production AI Engineering. It inspects public GitHub repositories, identifies best-practice violations using an explicit Python agent loop, and generates a structured, evidence-based JSON report.

## Architecture & Design

* **No Frameworks**: Built in plain Python without heavy agent orchestration platforms (e.g., LangChain, LangGraph, or n8n).
* **Agent Loop**: Follows an autonomous **Observe $\to$ Reason $\to$ Select Tool $\to$ Execute Tool $\to$ Interpret Results $\to$ Report** cycle using the official Google GenAI SDK (`google-genai`).
* **Model**: Powered by Google Gemini (`gemini-3.8-flash`) with native function calling and strict JSON response schema enforcement.

## Project Structure

```text
A2/
├── .github/
│   └── workflows/
│       ├── ci.yml            # CI workflow for automated pytest execution
│       └── cd.yml            # CD workflow for building and pushing to GHCR
├── tests/
│   ├── __init__.py
│   ├── test_tools.py         # Unit tests for inspection tools & security checks
│   └── test_agent.py         # Integration tests for agent lifecycle & mocking
├── agent.py                  # CLI entry point
├── agent_core.py             # Core agent loop, Gemini integration, and function declarations
├── tools.py                  # Inspection tool implementations (list_files, read_file, search_code, git_log)
├── requirements.txt          # Project dependencies
├── Dockerfile                # Containerization setup
├── .dockerignore             # Optimization & security filter for docker builds
├── .env.example              # Environment variable template
└── sample_report.json        # Authentic example JSON report output```

## Prerequisites & Installation
Clone the repository and navigate to the project directory:

```Bash
cd A2
```

Create and activate a virtual environment:
```Bash
python -m venv .venv
.venv\Scripts\activate  # On Windows PowerShell
# source .venv/bin/activate  # On macOS/Linux
```

Install dependencies:

```Bash
pip install -r requirements.txt
```

Configure your API Key:
Copy .env.example to .env and add your Google AI Studio API key:

```Bash
cp .env.example .env
```

Open .env and set your key:

```
GEMINI_API_KEY=AQ.YourActualAPIKeyHere
```

## Execution
Run the agent unattended via the command line using the required signature:

```Bash
python agent.py --repo [https://github.com/octocat/Spoon-Knife](https://github.com/octocat/Spoon-Knife) --output report.json
```

## Inspection Tools
The agent dynamically selects from the following local inspection tools:

- list_files(): Discovers repository structure and files.
- read_file(path): Safely inspects configuration or source code files.
- search_code(pattern): Searches for suspicious patterns or strings across the codebase.
- git_log(max_count): Inspects recent commit history for anti-patterns.

# Containerization (Docker)
You can build and run the agent in an isolated, reproducible container environment using Docker.

## Build the Docker image:

```Bash
docker build -t devops-agent .
```

## Run the containerized agent:
Pass your runtime .env file securely using the environment file flag:

```Bash
docker run --rm --env-file .env devops-agent --repo [https://github.com/octocat/Spoon-Knife](https://github.com/octocat/Spoon-Knife) --output report.json
```

# CI/CD Automation
The repository utilizes decoupled GitHub Actions workflows for production-grade MLOps automation:

- CI (ci.yml): Automatically triggers on pushes and pull requests to run the complete pytest suite and ensure code health.

- CD (cd.yml): Automatically triggers on pushes to main, verifying code integrity before building and pushing the container image to the GitHub Container Registry (GHCR).