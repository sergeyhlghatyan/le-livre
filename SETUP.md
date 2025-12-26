# Gold Stage Setup

## 1. Copy environment file
```bash
cp .env.example .env
```

Add your OpenAI API key to `.env`

## 2. Start databases
```bash
docker-compose up -d
```

This starts:
- PostgreSQL with pgvector on port 5432
- Neo4j on ports 7474 (HTTP) and 7687 (Bolt)

## 3. Verify databases
```bash
# Check Postgres
docker exec -it lelivre-postgres psql -U lelivre -d lelivre_gold -c "\dt"

# Check Neo4j (browser)
open http://localhost:7474
# Login: neo4j / lelivre123
```

## 4. Run Neo4j schema
```bash
# Via Neo4j Browser or:
docker exec -it lelivre-neo4j cypher-shell -u neo4j -p lelivre123 < data/schemas/neo4j.cypher
```

## 5. Install Python deps
```bash
pip install openai psycopg2-binary neo4j python-dotenv
```

## 6. Ready for Gold pipeline
```bash
python pipeline/gold/embed_provisions.py
python pipeline/gold/load_to_pgvector.py
python pipeline/gold/load_to_neo4j.py
```
