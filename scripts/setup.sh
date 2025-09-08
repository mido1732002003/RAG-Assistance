#!/bin/bash
set -e

echo "🚀 Setting up Local RAG Assistant..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ is required. Current version: $python_version"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p data var/index var/logs snapshots

# Download models
echo "🤖 Downloading models..."
python scripts/download_models.py

# Initialize database
echo "💾 Initializing database..."
python scripts/migrate_db.py

echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  make dev"