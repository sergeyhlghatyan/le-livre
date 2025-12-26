"""Provisions API router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from ..database import get_postgres_conn
from ..services.diff import compare_provisions, compare_hierarchical

router = APIRouter(prefix="/provisions", tags=["provisions"])


class ProvisionResponse(BaseModel):
    """Provision response model."""
    provision_id: str
    section_num: str
    year: int
    provision_level: str
    provision_num: str
    text_content: str
    heading: Optional[str] = None


class TimelineResponse(BaseModel):
    """Timeline response model."""
    section_num: str
    years: List[int]


class CompareRequest(BaseModel):
    """Compare request model."""
    provision_id: str
    year_old: int
    year_new: int


class CompareHierarchicalRequest(BaseModel):
    """Hierarchical compare request model."""
    provision_id: str
    year_old: int
    year_new: int
    granularity: str = "sentence"  # "word" or "sentence"


# NOTE: More specific routes must come first!
@router.get("/timeline/{section}", response_model=TimelineResponse)
async def get_timeline(section: str):
    """
    Get available years for a section.

    Args:
        section: Section number (e.g., '922')
    """
    try:
        with get_postgres_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT DISTINCT year
                FROM provision_embeddings
                WHERE section_num = %s
                ORDER BY year
                """,
                (section,)
            )

            years = [row[0] for row in cur.fetchall()]

            return TimelineResponse(
                section_num=section,
                years=years
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{section}/{year}", response_model=List[ProvisionResponse])
async def get_provisions_by_year(section: str, year: int):
    """
    Get all provisions for a section and year.

    Args:
        section: Section number (e.g., '922')
        year: Year (e.g., 2024)
    """
    try:
        with get_postgres_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT provision_id, section_num, year, provision_level,
                       provision_num, text_content, heading
                FROM provision_embeddings
                WHERE section_num = %s AND year = %s
                ORDER BY provision_num
                """,
                (section, year)
            )

            results = []
            for row in cur.fetchall():
                results.append(ProvisionResponse(
                    provision_id=row[0],
                    section_num=row[1],
                    year=row[2],
                    provision_level=row[3],
                    provision_num=row[4],
                    text_content=row[5],
                    heading=row[6]
                ))

            return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare(request: CompareRequest):
    """
    Compare two versions of a provision.

    Returns diff and LLM-generated summary of changes.
    """
    try:
        result = compare_provisions(
            provision_id=request.provision_id,
            year_old=request.year_old,
            year_new=request.year_new
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare/hierarchical")
async def compare_hierarchical_endpoint(request: CompareHierarchicalRequest):
    """
    Compare provisions hierarchically at all levels.

    Returns structured hierarchical diff with inline highlighting,
    recursively showing changes at subsection, paragraph, clause,
    subclause levels.
    """
    try:
        result = compare_hierarchical(
            provision_id=request.provision_id,
            year_old=request.year_old,
            year_new=request.year_new,
            granularity=request.granularity
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
