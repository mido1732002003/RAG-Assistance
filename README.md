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