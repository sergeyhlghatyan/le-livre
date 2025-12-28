"""Diff service for comparing provision versions."""
from typing import Dict, Any, List, Optional, Tuple
import difflib
from collections import defaultdict
from ..database import get_postgres_conn
from ..config import get_settings

settings = get_settings()


def get_provision_text(provision_id: str, year: int) -> Dict[str, Any]:
    """
    Get provision text for a specific year.

    Args:
        provision_id: Provision ID
        year: Year

    Returns:
        Provision data or None if not found
    """
    with get_postgres_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT provision_id, section_num, year, provision_level,
                   provision_num, text_content, heading
            FROM provision_embeddings
            WHERE provision_id = %s AND year = %s
            """,
            (provision_id, year)
        )

        row = cur.fetchone()
        if not row:
            return None

        return {
            "provision_id": row[0],
            "section_num": row[1],
            "year": row[2],
            "provision_level": row[3],
            "provision_num": row[4],
            "text_content": row[5],
            "heading": row[6]
        }


def generate_text_diff(old_text: str, new_text: str) -> List[str]:
    """
    Generate unified diff between two texts.

    Args:
        old_text: Original text
        new_text: New text

    Returns:
        List of diff lines
    """
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        lineterm='',
        fromfile='old',
        tofile='new'
    )

    return list(diff)




def compare_provisions(provision_id: str, year_old: int, year_new: int) -> Dict[str, Any]:
    """
    Compare two versions of a provision.

    Args:
        provision_id: Provision ID to compare
        year_old: Old year
        year_new: New year

    Returns:
        Comparison result with diff and summary
    """
    old_provision = get_provision_text(provision_id, year_old)
    new_provision = get_provision_text(provision_id, year_new)

    if not old_provision:
        return {
            "error": f"Provision {provision_id} not found for year {year_old}",
            "provision_id": provision_id,
            "year_old": year_old,
            "year_new": year_new
        }

    if not new_provision:
        return {
            "error": f"Provision {provision_id} not found for year {year_new}",
            "provision_id": provision_id,
            "year_old": year_old,
            "year_new": year_new
        }

    # Generate diff
    diff_lines = generate_text_diff(
        old_provision["text_content"],
        new_provision["text_content"]
    )

    # Check if there are changes
    has_changes = len(diff_lines) > 2  # More than just headers

    return {
        "provision_id": provision_id,
        "year_old": year_old,
        "year_new": year_new,
        "old_provision": old_provision,
        "new_provision": new_provision,
        "diff": diff_lines,
        "has_changes": has_changes
    }


# ============================================================
# Hierarchical Diff Functions
# ============================================================

def get_provision_hierarchy(provision_id: str, year: int) -> Optional[Dict[str, Any]]:
    """
    Get provision with all nested children from database.

    Builds a hierarchical tree structure of provisions.
    Optimized to use a single query instead of N+1.

    Args:
        provision_id: Provision ID (e.g., '/us/usc/t18/s922/a')
        year: Year

    Returns:
        Nested dict with provision and children, or None if not found
    """
    with get_postgres_conn() as conn:
        cur = conn.cursor()

        # Single query: Get the provision AND all its children in one go
        cur.execute(
            """
            SELECT provision_id, section_num, year, provision_level,
                   provision_num, text_content, heading
            FROM provision_embeddings
            WHERE (provision_id = %s OR provision_id LIKE %s)
              AND year = %s
            ORDER BY provision_id
            """,
            (provision_id, provision_id + '/%', year)
        )

        rows = cur.fetchall()
        if not rows:
            return None

        # Convert rows to dict
        all_provisions = []
        for row in rows:
            all_provisions.append({
                "provision_id": row[0],
                "section_num": row[1],
                "year": row[2],
                "provision_level": row[3],
                "provision_num": row[4],
                "text_content": row[5],
                "heading": row[6],
                "children": []
            })

        # Build hierarchy by parent-child relationships
        provision_map = {p["provision_id"]: p for p in all_provisions}

        for prov in all_provisions[1:]:  # Skip root (first row is always root)
            parent_id = '/'.join(prov["provision_id"].split('/')[:-1])
            if parent_id in provision_map:
                provision_map[parent_id]["children"].append(prov)

        return all_provisions[0]  # Return root


def generate_inline_diff(
    old_text: str,
    new_text: str,
    granularity: str = "sentence"
) -> List[Dict[str, str]]:
    """
    Generate inline diff with word-level or sentence-level highlighting.

    Args:
        old_text: Original text
        new_text: New text
        granularity: "word" or "sentence"

    Returns:
        List of {type: 'unchanged'|'added'|'removed', text: '...'}
    """
    if granularity == "word":
        old_tokens = old_text.split()
        new_tokens = new_text.split()
    else:  # sentence
        import re
        # Simple sentence splitter
        old_tokens = re.split(r'([.!?]+\s+)', old_text)
        new_tokens = re.split(r'([.!?]+\s+)', new_text)

    matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens)

    diff_parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            text = ' '.join(old_tokens[i1:i2]) if granularity == "word" else ''.join(old_tokens[i1:i2])
            diff_parts.append({"type": "unchanged", "text": text})
        elif tag == 'delete':
            text = ' '.join(old_tokens[i1:i2]) if granularity == "word" else ''.join(old_tokens[i1:i2])
            diff_parts.append({"type": "removed", "text": text})
        elif tag == 'insert':
            text = ' '.join(new_tokens[j1:j2]) if granularity == "word" else ''.join(new_tokens[j1:j2])
            diff_parts.append({"type": "added", "text": text})
        elif tag == 'replace':
            old_text_part = ' '.join(old_tokens[i1:i2]) if granularity == "word" else ''.join(old_tokens[i1:i2])
            new_text_part = ' '.join(new_tokens[j1:j2]) if granularity == "word" else ''.join(new_tokens[j1:j2])
            diff_parts.append({"type": "removed", "text": old_text_part})
            diff_parts.append({"type": "added", "text": new_text_part})

    return diff_parts


def compare_hierarchical(
    provision_id: str,
    year_old: int,
    year_new: int,
    granularity: str = "sentence"
) -> Dict[str, Any]:
    """
    Compare provisions at all hierarchy levels.

    Recursively compares each level and tracks changes.

    Args:
        provision_id: Provision ID to compare
        year_old: Old year
        year_new: New year
        granularity: Diff granularity ("word" or "sentence")

    Returns:
        Structured hierarchical diff
    """
    old_hierarchy = get_provision_hierarchy(provision_id, year_old)
    new_hierarchy = get_provision_hierarchy(provision_id, year_new)

    if not old_hierarchy:
        return {
            "error": f"Provision {provision_id} not found for year {year_old}",
            "provision_id": provision_id,
            "year_old": year_old,
            "year_new": year_new
        }

    if not new_hierarchy:
        return {
            "error": f"Provision {provision_id} not found for year {year_new}",
            "provision_id": provision_id,
            "year_old": year_old,
            "year_new": year_new
        }

    def compare_node(old_node: Dict, new_node: Dict) -> Dict:
        """Compare a single node and its children."""
        # Check if text changed
        text_changed = old_node["text_content"] != new_node["text_content"]

        # Generate inline diff if changed - ONLY compute requested granularity
        inline_diff = None
        if text_changed:
            inline_diff = {
                granularity: generate_inline_diff(
                    old_node["text_content"],
                    new_node["text_content"],
                    granularity
                )
            }

        # Map children by ID for comparison
        old_children_map = {c["provision_id"]: c for c in old_node["children"]}
        new_children_map = {c["provision_id"]: c for c in new_node["children"]}

        all_child_ids = set(old_children_map.keys()) | set(new_children_map.keys())

        children_diff = []
        for child_id in sorted(all_child_ids):
            old_child = old_children_map.get(child_id)
            new_child = new_children_map.get(child_id)

            if old_child and new_child:
                # Child exists in both - recurse
                children_diff.append(compare_node(old_child, new_child))
            elif old_child:
                # Child removed
                children_diff.append({
                    "provision_id": child_id,
                    "provision_level": old_child["provision_level"],
                    "provision_num": old_child["provision_num"],
                    "status": "removed",
                    "old_text": old_child["text_content"],
                    "children": []
                })
            else:
                # Child added
                children_diff.append({
                    "provision_id": child_id,
                    "provision_level": new_child["provision_level"],
                    "provision_num": new_child["provision_num"],
                    "status": "added",
                    "new_text": new_child["text_content"],
                    "children": []
                })

        return {
            "provision_id": old_node["provision_id"],
            "provision_level": old_node["provision_level"],
            "provision_num": old_node["provision_num"],
            "heading": old_node["heading"] or new_node["heading"],
            "status": "modified" if text_changed else "unchanged",
            "text_changed": text_changed,
            "old_text": old_node["text_content"],
            "new_text": new_node["text_content"],
            "inline_diff": inline_diff,
            "children": children_diff
        }

    hierarchy_diff = compare_node(old_hierarchy, new_hierarchy)

    return {
        "provision_id": provision_id,
        "year_old": year_old,
        "year_new": year_new,
        "hierarchy_diff": hierarchy_diff
    }
