#!/bin/bash
set -e

BACKUP_DIR="${1:-$HOME/backups}"
DATE=$(date +%Y%m%d_%H%M%S)

echo "=== Backing up Le Livre Databases ==="
echo "Backup directory: $BACKUP_DIR"
echo "Timestamp: $DATE"
echo ""

# Create backup directory
mkdir -p $BACKUP_DIR

# Source .env file to get database credentials
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec lelivre-postgres pg_dump -U ${POSTGRES_USER:-lelivre} ${POSTGRES_DB:-lelivre_gold} > $BACKUP_DIR/postgres_$DATE.sql
echo "✓ PostgreSQL backup: $BACKUP_DIR/postgres_$DATE.sql"

# Backup Neo4j
echo ""
echo "Backing up Neo4j..."
docker exec lelivre-neo4j neo4j-admin database dump neo4j --to-path=/tmp/
docker cp lelivre-neo4j:/tmp/neo4j.dump $BACKUP_DIR/neo4j_$DATE.dump
docker exec lelivre-neo4j rm /tmp/neo4j.dump
echo "✓ Neo4j backup: $BACKUP_DIR/neo4j_$DATE.dump"

# Compress backups
echo ""
echo "Compressing backups..."
tar -czf $BACKUP_DIR/lelivre_backup_$DATE.tar.gz -C $BACKUP_DIR postgres_$DATE.sql neo4j_$DATE.dump
rm $BACKUP_DIR/postgres_$DATE.sql $BACKUP_DIR/neo4j_$DATE.dump
echo "✓ Compressed backup: $BACKUP_DIR/lelivre_backup_$DATE.tar.gz"

# Get file size
BACKUP_SIZE=$(du -h $BACKUP_DIR/lelivre_backup_$DATE.tar.gz | cut -f1)

echo ""
echo "=== Backup Complete ==="
echo "File: $BACKUP_DIR/lelivre_backup_$DATE.tar.gz"
echo "Size: $BACKUP_SIZE"
echo ""

# Clean up old backups (keep last 7 days)
echo "Cleaning up old backups (keeping last 7 days)..."
find $BACKUP_DIR -name "lelivre_backup_*.tar.gz" -mtime +7 -delete
echo "✓ Cleanup complete"

echo ""
echo "To restore from this backup:"
echo "1. PostgreSQL:"
echo "   gunzip -c $BACKUP_DIR/lelivre_backup_$DATE.tar.gz | tar -xOf - postgres_$DATE.sql | docker exec -i lelivre-postgres psql -U lelivre -d lelivre_gold"
echo ""
echo "2. Neo4j:"
echo "   # Stop Neo4j container first"
echo "   gunzip -c $BACKUP_DIR/lelivre_backup_$DATE.tar.gz | tar -xOf - neo4j_$DATE.dump > /tmp/neo4j_restore.dump"
echo "   docker cp /tmp/neo4j_restore.dump lelivre-neo4j:/tmp/"
echo "   docker exec lelivre-neo4j neo4j-admin database load neo4j --from-path=/tmp/"
echo ""
echo "Backup files are stored in: $BACKUP_DIR"
