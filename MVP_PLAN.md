# Le Livre MVP - Implementation Plan

## Backend (FastAPI)

### Setup
- [ ] Create `backend/` folder structure
- [ ] FastAPI app with CORS
- [ ] Connect to PostgreSQL + Neo4j
- [ ] Environment variables (.env)

### API Endpoints
- [ ] `GET /provisions/{section}/{year}` - Get provision by year
- [ ] `GET /provisions/timeline/{section}` - Get available years
- [ ] `POST /provisions/compare` - Compare two versions
- [ ] `POST /chat` - Chat with RAG

### RAG Implementation
- [ ] Semantic search (embeddings)
- [ ] Graph search (Neo4j relationships)
- [ ] Hybrid search (combine both)
- [ ] LLM answer generation

### Diff Engine
- [ ] Generate text diffs
- [ ] LLM change summary

---

## Frontend (SvelteKit)

### Setup
- [ ] Create `frontend/` with SvelteKit
- [ ] Tailwind CSS
- [ ] API client
- [ ] Layout + navigation

### Components
- [ ] Timeline slider
- [ ] Provision viewer
- [ ] Diff view (side-by-side)
- [ ] Chat interface
- [ ] Message list with sources

### Pages
- [ ] `/` - Home with chat
- [ ] `/timeline` - Timeline view
- [ ] `/compare` - Diff view

---

## Integration

- [ ] Connect frontend to backend APIs
- [ ] Error handling
- [ ] Loading states
- [ ] Update docker-compose.yml

---

## Success Criteria

- [ ] Chat works: Ask question → Get answer with sources
- [ ] Timeline works: Select year → See provision text
- [ ] Diff works: Compare years → See changes + summary
- [ ] RAG works: Semantic + graph search both working
