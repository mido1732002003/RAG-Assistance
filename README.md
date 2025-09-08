# Local RAG Assistant

A privacy-first, local knowledge management system with RAG (Retrieval-Augmented Generation) capabilities.

## Features

- 🔒 **Privacy-First**: Runs completely offline by default
- 📁 **Auto-Indexing**: Watches folders and automatically indexes documents
- 🔍 **Hybrid Search**: Combines vector similarity and BM25 for better results
- 💬 **Flexible Generation**: Works offline or with LLM APIs (OpenAI, Mistral, Anthropic)
- 📚 **Multi-Format Support**: PDF, DOCX, TXT, MD, CSV
- 🌍 **Multi-Language**: Automatic language detection and appropriate handling
- 🎯 **Smart Citations**: Always provides sources for answers

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd local-rag-assistant

# Run setup
make setup

# Start the server
make dev
## SETUP
# 1. Activate venv (already done)
.venv\Scripts\activate

# 2. Upgrade pip
python -m pip install --upgrade pip

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
copy .env.example .env

# 5. Create necessary directories
mkdir data, var\index, var\logs, snapshots -Force

# 6. Now run the scripts (after dependencies are installed)
python scripts/download_models.py
python scripts/migrate_db.py

# 7. Start the server
uvicorn app.main:app --reload