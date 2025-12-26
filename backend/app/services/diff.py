"""Diff service for comparing provision versions."""
from typing import Dict, Any, List, Optional, Tuple
import difflib
import openai
from collections import defaultdict
from ..database import get_postgres_conn
from ..config import get_settings

settings = get_settings()
openai.api_key = settings.openai_api_key


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


def generate_diff_summary(old_provision: Dict[str, Any], new_provision: Dict[str, Any], diff_lines: List[str]) -> str:
    """
    Generate LLM summary of changes between two provision versions.

    Args:
        old_provision: Old provision data
        new_provision: New provision data
        diff_lines: Unified diff lines

    Returns:
        LLM-generated summary of changes
    """
    diff_text = '\n'.join(diff_lines)

    messages = [
        {
            "role": "system",
            "content": "You are a legal analyst specializing in US firearms law. "
                      "Summarize changes between two versions of a legal provision. "
                      "Focus on substantive changes, new requirements, removed provisions, "
                      "and practical implications. Be concise and clear."
        },
        {
            "role": "user",
            "content": f"Provision: {old_provision['provision_id']}\n"
                      f"From: {old_provision['year']}\n"
                      f"To: {new_provision['year']}\n\n"
                      f"Unified Diff:\n{diff_text}\n\n"
                      f"Summarize the key changes:"
        }
    ]

    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        temperature=0.3,
        max_tokens=500
    )

    return response.choices[0].message.content


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

    # Generate summary if there are changes
    summary = None
    has_changes = len(diff_lines) > 2  # More than just headers

    if has_changes:
        summary = generate_diff_summary(old_provision, new_provision, diff_lines)
    else:
        summary = "No changes detected between these versions."

    return {
        "provision_id": provision_id,
        "year_old": year_old,
        "year_new": year_new,
        "old_provision": old_provision,
        "new_provision": new_provision,
        "diff": diff_lines,
        "has_changes": has_changes,
        "summary": summary
    }


# ============================================================
# Hierarchical Diff Functions
# ============================================================

def get_provision_hierarchy(provision_id: str, year: int) -> Optional[Dict[str, Any]]:
    """
    Get provision with all nested children from database.

    Builds a hierarchical tree structure of provisions.

    Args:
        provision_id: Provision ID (e.g., '/us/usc/t18/s922/a')
        year: Year

    Returns:
        Nested dict with provision and children, or None if not found
    """
    with get_postgres_conn() as conn:
        cur = conn.cursor()

        # Get the provision itself
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

        provision = {
            "provision_id": row[0],
            "section_num": row[1],
            "year": row[2],
            "provision_level": row[3],
            "provision_num": row[4],
            "text_content": row[5],
            "heading": row[6],
            "children": []
        }

        # Get all children (provisions starting with this ID + '/')
        cur.execute(
            """
            SELECT provision_id, section_num, year, provision_level,
                   provision_num, text_content, heading
            FROM provision_embeddings
            WHERE provision_id LIKE %s AND year = %s
            ORDER BY provision_id
            """,
            (provision_id + '/%', year)
        )

        all_provisions = [provision]
        for row in cur.fetchall():
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

        for prov in all_provisions[1:]:  # Skip root
            parent_id = '/'.join(prov["provision_id"].split('/')[:-1])
            if parent_id in provision_map:
                provision_map[parent_id]["children"].append(prov)

        return provision


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

        # Generate inline diff if changed
        inline_diff = None
        if text_changed:
            inline_diff = {
                "sentence": generate_inline_diff(
                    old_node["text_content"],
                    new_node["text_content"],
                    "sentence"
                ),
                "word": generate_inline_diff(
                    old_node["text_content"],
                    new_node["text_content"],
                    "word"
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

    # Generate summary
    summary = generate_hierarchical_summary(hierarchy_diff, provision_id, year_old, year_new)

    return {
        "provision_id": provision_id,
        "year_old": year_old,
        "year_new": year_new,
        "hierarchy_diff": hierarchy_diff,
        "summary": summary
    }


def generate_hierarchical_summary(
    hierarchy_diff: Dict[str, Any],
    provision_id: str,
    year_old: int,
    year_new: int
) -> str:
    """
    Generate LLM summary that understands hierarchical changes.

    Args:
        hierarchy_diff: Hierarchical diff structure
        provision_id: Provision ID
        year_old: Old year
        year_new: New year

    Returns:
        AI-generated summary referencing specific hierarchy levels
    """
    # Build a structured description of changes
    def describe_changes(node: Dict, path: str = "") -> List[str]:
        changes = []
        current_path = f"{path} {node['provision_num']}" if path else node['provision_num']

        if node['status'] == 'modified' and node['text_changed']:
            changes.append(f"- {node['provision_level'].capitalize()} {current_path}: Text modified")
        elif node['status'] == 'added':
            changes.append(f"- {node['provision_level'].capitalize()} {current_path}: Added")
        elif node['status'] == 'removed':
            changes.append(f"- {node['provision_level'].capitalize()} {current_path}: Removed")

        for child in node.get('children', []):
            changes.extend(describe_changes(child, current_path))

        return changes

    change_list = describe_changes(hierarchy_diff)
    changes_text = '\n'.join(change_list) if change_list else "No changes detected"

    messages = [
        {
            "role": "system",
            "content": "You are a legal analyst specializing in US firearms law. "
                      "Summarize changes between two versions of a legal provision. "
                      "Reference specific subsections, paragraphs, clauses as appropriate. "
                      "Focus on substantive changes and practical implications."
        },
        {
            "role": "user",
            "content": f"Provision: {provision_id}\n"
                      f"From: {year_old}\n"
                      f"To: {year_new}\n\n"
                      f"Hierarchical Changes:\n{changes_text}\n\n"
                      f"Provide a concise summary of the key changes:"
        }
    ]

    if not change_list:
        return "No changes detected between these versions."

    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        temperature=0.3,
        max_tokens=500
    )

    return response.choices[0].message.content
