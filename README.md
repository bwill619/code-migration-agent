# Autonomous Code Migration & Refactoring Agent (Multi-Agent RAG)

An autonomous, self-correcting multi-agent system powered by **LangGraph** and **Qdrant** designed to automate complex codebase migrations. This implementation focuses on refactoring legacy, synchronous code (e.g., Flask APIs or older Python syntax) into high-performance, asynchronous architectures (e.g., FastAPI / Python 3.12+ type hints), validating execution safety via a closed-loop testing environment.

---

## 🏗️ System Architecture

Unlike typical text-based chat systems, this application uses a state-machine topology to handle cyclic multi-agent loops, state isolation, and automated self-correction based on runtime exceptions.

Legacy Codebase) ───► (AST Parser Agent)│▼┌───────────────────► (Retriever Agent) ◄─── (Vector Search) ───► (Qdrant DB) (FastAPI Docs)│                           ││                           ▼│                     (Refactorer Agent)│                           ││                           ▼└─ (Tests Failed) ◄─── (Validator Agent) ───► (Tests Passed) ───► (Upgraded Production Code)
### The Multi-Agent Workflow
1. **The Code Parser Agent:** Analyzes the target legacy source code using Python's native Abstract Syntax Tree (AST) module. It tokenizes functions and classes, identifying specific architectural anti-patterns (e.g., blocking `time.sleep()`, synchronous database sessions).
2. **The Documentation Retriever Agent:** Performs dense vector semantic search against a **Qdrant** vector store containing the target framework documentation and migration guides to map legacy syntax to updated patterns.
3. **The Refactorer Agent:** Synthesizes the extracted AST metadata and retrieved RAG context using advanced LLM tool-calling to generate code diffs.
4. **The Validator Agent (Closed Loop):** Writes the updated code into an isolated directory and executes a local test harness via **pytest**. If tests fail or syntax errors occur, the stack trace is fed back into the *Retriever Agent* as context for an autonomous second-pass attempt.

---

## ⚡ Tech Stack & Core Technologies

- **Orchestration:** LangGraph (State Graph Engine)
- **Vector Database:** Qdrant (Hybrid search optimization)
- **AI Core:** OpenAI GPT-4o / Anthropic Claude 3.5 Sonnet
- **Static Analysis:** Python `ast` library
- **Validation Engine:** Pytest / Subprocess Execution
- **Deployment & Infra:** Docker, Docker-Compose

---

## 🚀 Getting Started

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+
- An OpenAI or Anthropic API Key

### 2. Installation & Environment Setup
Clone the repository and set up a virtual environment:
```bash
git clone https://github.com[Your-Username]/code-migration-agent.git
cd code-migration-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure your environmental variables:
```bash
cp .env.example .env
# Open .env and insert your API keys and local settings
```

### 3. Spin Up Infrastructure
Launch the local Qdrant vector database container:
```bash
docker-compose up -d
```

### 4. Run a Code Migration
To execute the multi-agent pipeline over a target legacy script or directory, run:
```bash
python run_pipeline.py --input ./data/legacy_codebase/app.py --output ./data/upgraded_codebase/
```

---

## 📊 Evaluation & Production Metrics

To ensure enterprise-level code reliability, this system implements automated evaluation pipelines checking two major benchmarks:

- **Compilation & Test Pass Rate:** Tracks the percentage of files that pass the `validator_agent` testing loop without requiring manual engineer intervention (Targeting >88%).
- **Ragas Framework Evaluation:** Uses the **Ragas** Python library to score pipeline precision:
  - *Context Precision:* Measures if the Retriever is pulling the exact framework migration snippets needed.
  - *Faithfulness:* Ensures the generated code diff aligns entirely with the retrieved documentation rather than hallucinating deprecated methods.

---

## 🛠️ Feature Roadmap & Next Steps
- [ ] Implement multi-file structural dependency mapping via Neo4j GraphRAG.
- [ ] Integrate Role-Based Access Control (RBAC) tool-gating for production CI/CD execution.
- [ ] Support for multi-language AST translation (e.g., Java Spring Boot configuration upgrades).

---