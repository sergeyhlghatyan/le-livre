"""Chat API router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.rag import hybrid_search, generate_rag_response

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""
    query: str
    year: Optional[int] = None
    limit: int = 10


class ChatResponse(BaseModel):
    """Chat response model."""
    query: str
    answer: str
    sources: list
    semantic_count: int
    graph_count: int
    year_used: int  # Year used for the search


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint with RAG.

    Performs hybrid search (semantic + graph) and generates an answer.
    Defaults to year 2024 if not specified.
    """
    try:
        # Default to latest year (2024) if not specified
        search_year = request.year if request.year is not None else 2024

        # Perform hybrid search
        search_results = hybrid_search(
            query=request.query,
            limit=request.limit,
            year=search_year
        )

        # Generate answer
        answer = generate_rag_response(
            query=request.query,
            context_results=search_results["results"]
        )

        return ChatResponse(
            query=request.query,
            answer=answer,
            sources=search_results["results"],
            semantic_count=search_results["semantic_count"],
            graph_count=search_results["graph_count"],
            year_used=search_year
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
