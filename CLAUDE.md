# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Le Livre** is a legislative version tracking and comparison system focused on US firearms law (18 USC 922). It provides semantic search, timeline browsing, hierarchical diff comparison, and AI-powered chat using RAG (Retrieval Augmented Generation).

**Tech Stack:**
- Backend: FastAPI (Python) with PostgreSQL (pgvector) + Neo4j
- Frontend: SvelteKit 2.0 with Svelte 5, TypeScript, Tailwind CSS
- AI: OpenAI (text-embedding-3-small, GPT-4-Turbo)
- Data: Multi-stage ETL pipeline (Bronze → Silver → Gold)

## Development Commands

### Starting/Stopping Services

```bash
# Start all services (backend + frontend)
./start.sh

# Stop all services
./stop.sh

# Start databases only
docker-compose up -d

# Stop databases
docker-compose down
```

**Service URLs:**
- Frontend: http://localhost:5174
- Backend API: http://localhost:8000
- Neo4j Browser: http://localhost:7474 (neo4j/lelivre123)
- PostgreSQL: localhost:5432 (lelivre/lelivre123, database: lelivre_gold)

### Backend Development

```bash
cd backend

# Run backend with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest

# Install dependencies
pip install -r requirements.txt
```

### Frontend Development

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Install dependencies
npm install
```

### Data Pipeline

```bash
# Bronze layer (download raw USLM XML)
python scripts/download_usc_xml.py

# Silver layer (parse and extract)
python scripts/extract_sections.py
python pipeline/silver/parser.py
python pipeline/silver/reference_extractor.py

# Gold layer (embeddings and loading)
python pipeline/gold/embed_provisions.py
python pipeline/gold/load_to_pgvector.py
python pipeline/gold/load_to_neo4j.py
```

**Note:** Ensure `.env` file exists with `OPENAI_API_KEY` before running gold layer scripts.

## Architecture Overview

### Dual Database Strategy

The application uses **two databases simultaneously** for complementary capabilities:

1. **PostgreSQL with pgvector** (`lelivre_gold` database)
   - Stores provision text with embeddings (3072-dim vectors)
   - Table: `provision_embeddings`
   - Used for: Semantic similarity search via cosine distance
   - Schema: `data/schemas/pgvector.sql`

2. **Neo4j Graph Database**
   - Stores provision nodes and relationships
   - Relationships: `PARENT_OF` (hierarchy), `REFERENCES` (cross-references)
   - Used for: Graph traversal, relationship discovery, hierarchical queries
   - Schema: `data/schemas/neo4j.cypher`

**Why both?** Vector search finds semantically similar provisions; graph search finds related provisions via structure and references. Combined = richer context for RAG.

### Backend Architecture (backend/app/)

**Request Flow:**
```
Router → Service → Database(s) → OpenAI API → Response
```

**Key Files:**
- `main.py`: FastAPI app initialization, CORS, route registration
- `config.py`: Pydantic Settings for configuration (DB URLs, API keys)
- `database.py`: Connection managers (PostgreSQL + Neo4j drivers)

**Routers:**
- `routers/chat.py`: RAG endpoint (`POST /chat`) - hybrid search + LLM answer
- `routers/provisions.py`: Timeline, provision retrieval, comparison, graph endpoints

**Services:**
- `services/rag.py`: Hybrid search implementation
  - `semantic_search()`: pgvector similarity search
  - `graph_search()`: Neo4j relationship traversal (bidirectional)
  - `hybrid_search()`: Combines both, deduplicates results
  - `generate_rag_response()`: OpenAI GPT-4-Turbo answer generation
- `services/diff.py`: Version comparison
  - `compare_hierarchical()`: Recursive tree diffing with inline changes
  - `generate_inline_diff()`: Word/sentence-level granularity
  - Optimized hierarchy fetching (single query with LIKE wildcard, avoids N+1)

### Frontend Architecture (frontend/src/)

**Framework:** SvelteKit 2.0 with Svelte 5 (uses new runes API for state)

**Routing (file-based):**
- `/` → `routes/+page.svelte` (Chat interface)
- `/timeline` → `routes/timeline/+page.svelte` (Timeline view)
- `/compare` → `routes/compare/+page.svelte` (Diff view)
- `/graph` → `routes/graph/+page.svelte` (Cytoscape graph)
- `/provision/[id]` → `routes/provision/[id]/+page.svelte` (Details)

**State Management (Svelte 5 Runes):**
- `lib/stores/chat.svelte.ts`: Chat messages (persisted to localStorage)
- `lib/stores/theme.svelte.ts`: Dark/light mode toggle
- `lib/stores/toast.svelte.ts`: Toast notifications

**Pattern:** Class-based stores with `$state` runes, NOT traditional Svelte stores.

**Components:**
- `lib/components/chat/`: MessageBubble, SourceGroup, SourceCard
- `lib/components/ui/`: Reusable UI primitives (Button, Input, Card, Modal, Toast)
- `lib/components/HierarchyTree.svelte`: Tree navigation for hierarchical diffs
- `lib/components/InlineDiff.svelte`: Word/sentence-level diff visualization

**API Client:**
- `lib/api.ts`: Fetch-based client (no axios)
- Hierarchical comparison has 60-second timeout with AbortController

### Data Pipeline (Medallion Architecture)

**Bronze Layer** (`pipeline/bronze/`):
- Raw USLM XML files from uscode.house.gov
- Stored in `data/raw/`

**Silver Layer** (`pipeline/silver/`):
- `parser.py`: Parses USLM XML → JSON structures
- `reference_extractor.py`: Extracts cross-references between provisions
- Output: `data/silver/sections/`, `data/silver/references/`

**Gold Layer** (`pipeline/gold/`):
- `embed_provisions.py`: Generate OpenAI embeddings
- `load_to_pgvector.py`: Load provisions + embeddings into PostgreSQL
- `load_to_neo4j.py`: Load provisions + relationships into Neo4j
- Output: Ready-to-query databases

**Data Flow:**
```
USLM XML → Parser → JSON + References → Embeddings → PostgreSQL + Neo4j
```

### Hybrid RAG Implementation

**Query Flow** (`services/rag.py`):
1. User query → Generate embedding (OpenAI)
2. Semantic search in pgvector (top N by cosine similarity)
3. Use top semantic results as entry points for graph traversal (Neo4j)
4. Combine and deduplicate results (semantic first, then graph-only)
5. Generate answer with GPT-4-Turbo using combined context
6. Return answer + sources (tagged as 'semantic', 'graph', or both)

**Key Insight:** Semantic search finds conceptually similar provisions; graph search expands to related provisions (parent/child/references). This provides both relevance and structural context.

### Hierarchical Diff Pattern

**Challenge:** Comparing nested provision structures across years.

**Solution** (`services/diff.py: compare_hierarchical()`):
1. Fetch entire hierarchy in single query (uses `LIKE provision_id/%`)
2. Build tree structure in Python
3. Recursively compare trees:
   - Match provisions by ID
   - Detect: modified, unchanged, added, removed
   - Generate inline diff (word or sentence granularity)
4. Return nested structure with status + changes

**Optimization:** Single database query instead of recursive queries (N+1 problem avoided).

## Important Patterns

### Backend Patterns

1. **Exponential Backoff for OpenAI**
   - `rag.py` includes retry logic for embeddings and LLM calls
   - Initial 1s delay, doubles on each retry

2. **Bidirectional Graph Search**
   - Single Cypher query handles: children, parents, siblings, references (both directions)
   - Uses `OPTIONAL MATCH` for flexibility

3. **Result Deduplication**
   - Hybrid search tracks `(provision_id, year)` tuples
   - Preserves semantic ordering, appends graph-only results

4. **Database Connection Management**
   - PostgreSQL: psycopg connection pool
   - Neo4j: Singleton driver pattern with context managers

### Frontend Patterns

1. **Svelte 5 Runes for State**
   - Use `$state` for reactive state (not `writable` stores)
   - Class-based pattern: `class ChatStore { messages = $state([]) }`
   - Browser-only initialization (`browser` check from `$app/environment`)

2. **localStorage Persistence**
   - Chat history auto-saves to localStorage
   - Theme preference persisted
   - Pattern: Load on init, save on change

3. **Component Communication**
   - Direct prop passing (no event bus)
   - Store references for global state
   - Toast notifications via store methods

4. **Error Handling**
   - Try/catch in component handlers
   - Toast notifications for user feedback
   - Graceful degradation (optional data with `?`)

## Code Conventions

### Backend

- **Router → Service → Database** separation
- Pydantic models for request/response validation
- Dependency injection for database connections
- Type hints throughout
- Docstrings for public functions

### Frontend

- TypeScript strict mode enabled
- Components use `<script lang="ts">`
- Tailwind for styling (custom theme in `tailwind.config.js`)
- File-based routing (SvelteKit convention)
- Component files in `lib/components/`, pages in `routes/`

## Environment Variables

Required in `.env` (backend and pipeline):
```
OPENAI_API_KEY=sk-...

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=lelivre_gold
POSTGRES_USER=lelivre
POSTGRES_PASSWORD=lelivre123

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=lelivre123
```

## Testing

### Backend Tests

```bash
cd backend
pytest
```

Test files located in `backend/tests/` (if present) or inline with `test_*.py` pattern.

### Frontend Tests

Currently no test suite configured. To add:
```bash
npm install -D vitest @testing-library/svelte
```

## Common Gotchas

1. **Neo4j APOC Plugin**: Required for graph operations, enabled in docker-compose.yml
2. **pgvector Extension**: Must be enabled in PostgreSQL (auto-initialized via schema)
3. **Port Conflicts**: Ensure ports 5432, 7474, 7687, 8000, 5174 are available
4. **OpenAI Rate Limits**: Embedding pipeline may hit rate limits on large datasets
5. **Hierarchical Diff Timeout**: 60s timeout on frontend, may need adjustment for large trees
6. **Svelte 5 Migration**: Uses new runes API, not compatible with Svelte 4 store patterns

## Database Schemas

### PostgreSQL Table Structure
```sql
provision_embeddings (
  provision_id TEXT,
  section_num TEXT,
  year INTEGER,
  provision_level TEXT,
  provision_num TEXT,
  text_content TEXT,
  heading TEXT,
  embedding vector(3072)
)
```

### Neo4j Node/Relationship Structure
```cypher
(:Provision {id, year, section_num, level, num, text, heading})
(:Section {section_num, year})

(:Provision)-[:PARENT_OF]->(:Provision)
(:Provision)-[:REFERENCES]->(:Provision)
(:Section)-[:CONTAINS]->(:Provision)
```

## Adding New Features

### Adding a Backend Endpoint
1. Create route function in appropriate router (`routers/*.py`)
2. Add service function in `services/*.py` for business logic
3. Update API client in `frontend/src/lib/api.ts`
4. Add TypeScript types for request/response

### Adding a Frontend Page
1. Create `routes/{page-name}/+page.svelte`
2. Add navigation link in `routes/+layout.svelte`
3. Create API client function if needed
4. Add page-specific components in `lib/components/`

### Modifying RAG Behavior
- Edit `backend/app/services/rag.py`
- Key functions: `semantic_search()`, `graph_search()`, `hybrid_search()`
- Adjust search parameters, relationship types, or LLM prompts

### Changing Diff Granularity
- Edit `backend/app/services/diff.py: generate_inline_diff()`
- Options: 'word' or 'sentence' level tokenization
- Frontend controls in `routes/compare/+page.svelte`