"""Configuration for pipeline (databases, API keys, etc.)"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# PostgreSQL
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'lelivre_gold')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'lelivre')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'lelivre123')

# Neo4j
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'lelivre123')

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
SILVER_SECTIONS_DIR = DATA_DIR / 'silver' / 'sections'
SILVER_REFS_DIR = DATA_DIR / 'silver' / 'references'
