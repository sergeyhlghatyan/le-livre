#!/bin/bash
set -e

echo "=== Initializing Databases ==="

# Source .env file to get passwords
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until docker exec lelivre-postgres pg_isready -U ${POSTGRES_USER:-lelivre} 2>/dev/null; do
  echo -n "."
  sleep 2
done
echo " Ready!"

# Run PostgreSQL schemas
echo ""
echo "Initializing PostgreSQL schemas..."

if [ -f "data/schemas/pgvector.sql" ]; then
    echo "- Running pgvector.sql..."
    docker exec -i lelivre-postgres psql -U ${POSTGRES_USER:-lelivre} -d ${POSTGRES_DB:-lelivre_gold} < data/schemas/pgvector.sql
fi

if [ -f "data/schemas/users.sql" ]; then
    echo "- Running users.sql..."
    docker exec -i lelivre-postgres psql -U ${POSTGRES_USER:-lelivre} -d ${POSTGRES_DB:-lelivre_gold} < data/schemas/users.sql
fi

echo "PostgreSQL initialization complete!"

# Wait for Neo4j to be ready
echo ""
echo "Waiting for Neo4j to be ready..."
until docker exec lelivre-neo4j cypher-shell -u ${NEO4J_USERNAME:-neo4j} -p ${NEO4J_PASSWORD} "RETURN 1" 2>/dev/null | grep -q "1"; do
  echo -n "."
  sleep 2
done
echo " Ready!"

# Run Neo4j schema (if exists)
if [ -f "data/schemas/neo4j.cypher" ]; then
    echo ""
    echo "Initializing Neo4j schema..."
    docker exec -i lelivre-neo4j cypher-shell -u ${NEO4J_USERNAME:-neo4j} -p ${NEO4J_PASSWORD} < data/schemas/neo4j.cypher
    echo "Neo4j initialization complete!"
fi

echo ""
echo "=== Database Initialization Complete ==="
echo ""
echo "IMPORTANT: You should now create an admin user."
echo ""
echo "To create an admin user, run:"
echo '  docker exec lelivre-backend python -c "'
echo '    import bcrypt'
echo '    import psycopg'
echo '    from app.config import get_settings'
echo '    settings = get_settings()'
echo '    hashed_pw = bcrypt.hashpw(b\"YOUR_PASSWORD\", bcrypt.gensalt()).decode()'
echo '    conn = psycopg.connect('
echo '        host=settings.postgres_host,'
echo '        port=settings.postgres_port,'
echo '        dbname=settings.postgres_db,'
echo '        user=settings.postgres_user,'
echo '        password=settings.postgres_password'
echo '    )'
echo '    cur = conn.cursor()'
echo '    cur.execute('
echo '        \"INSERT INTO users (email, hashed_password, is_superuser) VALUES (%s, %s, %s)\", '
echo '        (\"admin@lelivre.com\", hashed_pw, True)'
echo '    )'
echo '    conn.commit()'
echo '    print(\"Admin user created!\")'
echo '"'
echo ""
echo "Or manually run SQL:"
echo '  docker exec -it lelivre-postgres psql -U lelivre -d lelivre_gold'
echo '  INSERT INTO users (email, hashed_password, is_superuser) VALUES (...);'
