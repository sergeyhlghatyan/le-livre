"""Gold stage: Vector embeddings + Graph database loading."""

from .embed_provisions import embed_subsections_from_silver
from .load_to_pgvector import load_embeddings_to_postgres
from .load_to_neo4j import load_sections_to_graph

__all__ = [
    'embed_subsections_from_silver',
    'load_embeddings_to_postgres',
    'load_sections_to_graph',
]
