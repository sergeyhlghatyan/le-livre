"""
Pydantic models for Silver stage (parsed and validated USC sections).

These models define the schema for validated legal statute data, ensuring
data quality before it flows into Gold stage (vector + graph databases).
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, computed_field
from typing import List, Optional, Literal
from datetime import datetime
import re


class Reference(BaseModel):
    """
    A cross-reference from one provision to another USC provision.

    Example:
        {
            "target": "/us/usc/t18/s1715",
            "text": "section 1715 of this title"
        }
    """
    target: str = Field(
        ...,
        description="Target USC path (e.g., '/us/usc/t18/s923')"
    )
    text: str = Field(
        ...,
        description="Display text for the reference (e.g., 'section 923')"
    )

    @field_validator('target')
    @classmethod
    def validate_legal_path(cls, v: str) -> str:
        """
        Validate that target is a valid legal reference path.
        Accepts USC, Public Law, Statutes, and HTML anchors (from XHTML format).
        """
        valid_prefixes = [
            '/us/usc/',   # United States Code
            '/us/pl/',    # Public Law
            '/us/stat/',  # Statutes at Large
            '#',          # HTML anchor (XHTML internal references)
        ]
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(
                f"Invalid legal reference path: {v} "
                f"(must start with one of: {', '.join(valid_prefixes)})"
            )
        return v

    @field_validator('text')
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure reference text is not empty."""
        if not v.strip():
            raise ValueError("Reference text cannot be empty")
        return v


class Provision(BaseModel):
    """
    A single provision within a section (subsection, paragraph, subparagraph, clause, or subclause).

    Provisions are hierarchical:
    - Section contains subsections
    - Subsection contains paragraphs
    - Paragraph contains subparagraphs
    - Subparagraph contains clauses
    - Clause contains subclauses

    Example:
        {
            "id": "/us/usc/t18/s922/a/1",
            "tag": "paragraph",
            "num": "(1)",
            "text": "It shall be unlawful...",
            "subparagraphs": [...]
        }
    """
    id: str = Field(
        ...,
        description="Full hierarchical ID (e.g., '/us/usc/t18/s922/a/1')"
    )
    tag: Literal['section', 'subsection', 'paragraph', 'subparagraph', 'clause', 'subclause'] = Field(
        ...,
        description="Provision type"
    )
    num: str = Field(
        ...,
        description="Display number (e.g., '(a)', '(1)', '(A)', '(i)', '(I)')"
    )
    text: Optional[str] = Field(
        default="",
        description="Full text content of this provision (may be empty for structural provisions)"
    )
    heading: Optional[str] = Field(
        default=None,
        description="Optional heading for this provision"
    )

    # References in this provision
    refs: List[Reference] = Field(
        default_factory=list,
        description="Cross-references found in this provision's text"
    )

    # Child provisions (recursive structure)
    subsections: List[Provision] = Field(
        default_factory=list,
        description="Child subsections (only for section-level)"
    )
    paragraphs: List[Provision] = Field(
        default_factory=list,
        description="Child paragraphs (only for subsection-level)"
    )
    subparagraphs: List[Provision] = Field(
        default_factory=list,
        description="Child subparagraphs (only for paragraph-level)"
    )
    clauses: List[Provision] = Field(
        default_factory=list,
        description="Child clauses (only for subparagraph-level)"
    )
    subclauses: List[Provision] = Field(
        default_factory=list,
        description="Child subclauses (only for clause-level)"
    )

    @field_validator('text')
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """
        Allow empty text for structural provisions.
        Some provisions only have child provisions, no direct text.
        """
        # Just return the text as-is, even if empty
        # This is common in complex hierarchies
        return v

    @computed_field
    @property
    def total_children(self) -> int:
        """Count total number of child provisions at all levels."""
        return (
            len(self.subsections) +
            len(self.paragraphs) +
            len(self.subparagraphs) +
            len(self.clauses) +
            len(self.subclauses)
        )

    def get_all_provisions(self) -> List[Provision]:
        """
        Recursively get all provisions in this tree (including self).
        Used for counting total provisions and extracting references.
        """
        provisions = [self]
        for child_list in [
            self.subsections,
            self.paragraphs,
            self.subparagraphs,
            self.clauses,
            self.subclauses
        ]:
            for child in child_list:
                provisions.extend(child.get_all_provisions())
        return provisions

    def get_all_references(self) -> List[Reference]:
        """
        Recursively get all references in this provision tree.
        """
        all_refs = list(self.refs)
        for child_list in [
            self.subsections,
            self.paragraphs,
            self.subparagraphs,
            self.clauses,
            self.subclauses
        ]:
            for child in child_list:
                all_refs.extend(child.get_all_references())
        return all_refs


class SectionVersion(BaseModel):
    """
    A complete section of the USC for a specific year/version.

    This represents the top-level validated data structure for a single
    section-year pair (e.g., § 922 as of 2024).

    Example:
        {
            "id": "/us/usc/t18/s922",
            "section_num": "922",
            "title_num": 18,
            "year": 2024,
            "heading": "Unlawful acts",
            "subsections": [...]
        }
    """
    # Identity
    id: str = Field(
        ...,
        description="Section ID (e.g., '/us/usc/t18/s922')"
    )
    section_num: str = Field(
        ...,
        description="Section number only (e.g., '922', '923')"
    )
    title_num: int = Field(
        18,
        description="USC Title number (currently always 18)"
    )

    # Required section-level fields
    tag: Literal['section'] = Field(
        default='section',
        description="Must be 'section' for top level"
    )
    num: str = Field(
        ...,
        description="Section number with symbol (e.g., '§ 922.')"
    )
    heading: str = Field(
        ...,
        description="Section heading (e.g., 'Unlawful acts')"
    )

    # Optional section-level text (some sections have intro text)
    text: Optional[str] = Field(
        default=None,
        description="Section-level text (if any)"
    )

    # Child provisions
    subsections: List[Provision] = Field(
        ...,
        description="List of subsections in this section"
    )

    # Metadata (for tracking and quality)
    year: int = Field(
        ...,
        ge=1994,
        le=2030,
        description="Year of this version"
    )
    effective_date: Optional[datetime] = Field(
        default=None,
        description="Effective date of this version (future enhancement)"
    )
    public_law: Optional[str] = Field(
        default=None,
        description="Public Law citation (future enhancement)"
    )

    # Source provenance
    source_file: str = Field(
        ...,
        description="Source file path (e.g., 'data/raw/uslm/2024/usc18.xml')"
    )
    source_format: Literal['xml', 'xhtml'] = Field(
        ...,
        description="Source file format"
    )
    parsed_at: datetime = Field(
        default_factory=datetime.now,
        description="When this section was parsed"
    )
    parser_version: str = Field(
        default="1.0",
        description="Parser version for reproducibility"
    )

    # Computed quality metrics
    @computed_field
    @property
    def provision_count(self) -> int:
        """Total number of provisions in this section (all levels)."""
        count = 0
        for subsection in self.subsections:
            count += len(subsection.get_all_provisions())
        return count

    @computed_field
    @property
    def reference_count(self) -> int:
        """Total number of cross-references in this section."""
        count = 0
        for subsection in self.subsections:
            count += len(subsection.get_all_references())
        return count

    @computed_field
    @property
    def max_depth(self) -> int:
        """Maximum nesting depth of provisions in this section."""
        def get_depth(provision: Provision, current_depth: int = 0) -> int:
            max_child_depth = current_depth
            for child_list in [
                provision.subsections,
                provision.paragraphs,
                provision.subparagraphs,
                provision.clauses,
                provision.subclauses
            ]:
                for child in child_list:
                    child_depth = get_depth(child, current_depth + 1)
                    max_child_depth = max(max_child_depth, child_depth)
            return max_child_depth

        max_d = 0
        for subsection in self.subsections:
            max_d = max(max_d, get_depth(subsection, 1))
        return max_d

    @field_validator('subsections')
    @classmethod
    def validate_has_subsections(cls, v: List[Provision]) -> List[Provision]:
        """Ensure section has at least one subsection."""
        if not v:
            raise ValueError("Section must have at least one subsection")
        return v

    @field_validator('section_num')
    @classmethod
    def validate_section_num(cls, v: str) -> str:
        """Validate section number format."""
        # Section numbers should be numeric or numeric with letter suffix (e.g., "922", "922a")
        if not re.match(r'^\d+[a-z]?$', v):
            raise ValueError(f"Invalid section number format: {v}")
        return v


class ReferenceRecord(BaseModel):
    """
    A flat reference record for graph database ingestion.

    This is extracted from the hierarchical SectionVersion structure
    to create a flat list of all references for easy loading into Neo4j.

    Example:
        {
            "id": "922:2024:ref0",
            "year": 2024,
            "source_section": "922",
            "source_provision_id": "/us/usc/t18/s922/a/2/B",
            "target_section": "1715",
            "target_provision_id": "/us/usc/t18/s1715",
            "target_title": 18,
            "display_text": "section 1715 of this title",
            "ref_type": "internal"
        }
    """
    id: str = Field(
        ...,
        description="Unique reference ID (e.g., '922:2024:ref0')"
    )
    year: int = Field(
        ...,
        description="Year this reference appears in"
    )

    # Source (where the reference appears)
    source_section: str = Field(
        ...,
        description="Source section number (e.g., '922')"
    )
    source_provision_id: str = Field(
        ...,
        description="Full source provision path (e.g., '/us/usc/t18/s922/a/2/B')"
    )

    # Target (what the reference points to)
    target_section: Optional[str] = Field(
        None,
        description="Target section number if within Title 18 (e.g., '923')"
    )
    target_provision_id: str = Field(
        ...,
        description="Full target provision path (e.g., '/us/usc/t18/s1715')"
    )
    target_title: Optional[int] = Field(
        None,
        description="Target title number (e.g., 18, 21, 26)"
    )

    # Display
    display_text: str = Field(
        ...,
        description="How the reference is displayed (e.g., 'section 923')"
    )

    # Classification
    ref_type: Literal['internal', 'cross_title'] = Field(
        ...,
        description="internal = within Title 18, cross_title = to other titles"
    )

    @field_validator('ref_type')
    @classmethod
    def validate_ref_type_consistency(cls, v: str, info) -> str:
        """Ensure ref_type is consistent with target_title."""
        # Access other field values through info.data
        target_title = info.data.get('target_title')

        if v == 'internal' and target_title is not None and target_title != 18:
            raise ValueError(f"ref_type is 'internal' but target_title is {target_title} (should be 18)")
        if v == 'cross_title' and target_title == 18:
            raise ValueError(f"ref_type is 'cross_title' but target_title is 18 (should be 'internal')")

        return v


# Version info for tracking
SILVER_SCHEMA_VERSION = "1.0.0"
