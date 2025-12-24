"""
Diff engine for comparing USC section versions.

Key improvement: Uses full provision IDs from JSON instead of partial paths.
This fixes alignment issues caused by string sorting and missing context.
"""

from typing import Dict, List


def build_provision_tree(data: dict) -> Dict[str, dict]:
    """
    Build a flat tree of all provisions using dynamically constructed IDs.

    This function builds unique IDs from the hierarchical structure,
    handling both old format (duplicate IDs) and new format (proper IDs).

    Args:
        data: Section JSON data

    Returns:
        Dictionary mapping provision_id -> provision data

    Example keys:
        /us/usc/t18/s922/a
        /us/usc/t18/s922/a/1
        /us/usc/t18/s922/a/1/A
    """
    tree = {}

    # Extract section base from root ID
    section_base = data.get('id', '')  # e.g., '/us/usc/t18/s922'

    def traverse(node, parent_path=''):
        """
        Recursively traverse and build unique IDs from hierarchy.

        Args:
            node: Current provision node
            parent_path: Path built from parent provisions
        """
        # Use ID from parser if it exists (preferred)
        provision_id = node.get('id', '')
        parser_had_id = bool(provision_id)

        # Fallback: rebuild ID if parser didn't provide one
        if not provision_id:
            # Extract the provision number, stripping parentheses
            num = node.get('num', '').strip()

            # Clean the number: remove parentheses and periods
            # "(a)" -> "a", "(1)" -> "1", "§ 922." -> ""
            clean_num = num.strip('()§. \xa0\u202f')

            # Build unique ID from hierarchy path
            if clean_num and parent_path:
                # Child provision: append to parent path
                provision_id = f"{parent_path}/{clean_num}"
            elif clean_num:
                # Top-level provision: use section base
                provision_id = f"{section_base}/{clean_num}"
            else:
                # No number: use parent path or section base
                provision_id = parent_path if parent_path else section_base

        # Skip if no valid ID (shouldn't happen)
        if not provision_id:
            return

        # Store provision data with dynamically built ID
        tree[provision_id] = {
            'id': provision_id,
            'num': node.get('num', ''),
            'text': node.get('text', ''),
            'tag': node.get('tag', ''),
            'refs': node.get('refs', [])
        }

        # Recursively process all child types
        # Pass provision_id (from parser or rebuilt) as parent for children
        for child_type in ['subsections', 'paragraphs', 'subparagraphs',
                          'clauses', 'subclauses']:
            children = node.get(child_type, [])
            for child in children:
                traverse(child, provision_id)

    # Start traversal from subsections
    for subsection in data.get('subsections', []):
        traverse(subsection)

    return tree


def compare_versions(version1: dict, version2: dict) -> List[dict]:
    """
    Compare two versions and return aligned diffs.

    Args:
        version1: First version JSON data
        version2: Second version JSON data

    Returns:
        List of diff objects with type (added/deleted/modified/unchanged)
        and provision data

    The diffs are sorted by provision ID, which maintains hierarchical order.
    """
    tree1 = build_provision_tree(version1)
    tree2 = build_provision_tree(version2)

    # Get all unique provision IDs from both versions
    all_ids = sorted(set(tree1.keys()) | set(tree2.keys()))

    diffs = []

    for provision_id in all_ids:
        node1 = tree1.get(provision_id)
        node2 = tree2.get(provision_id)

        if not node1:
            # Provision added in version 2
            diffs.append({
                'type': 'added',
                'id': provision_id,
                'old': None,
                'new': node2
            })
        elif not node2:
            # Provision deleted (exists in version 1 but not 2)
            diffs.append({
                'type': 'deleted',
                'id': provision_id,
                'old': node1,
                'new': None
            })
        else:
            # Compare text
            text1 = node1['text'].strip()
            text2 = node2['text'].strip()

            text_changed = text1 != text2
            structure_changed = False

            # For provisions with empty text, check if structure changed
            if not text1 and not text2:
                # Get child keys (paragraphs, subparagraphs, etc.)
                child_keys1 = set(k for k in node1.keys() if k.endswith('s') and k != 'refs')
                child_keys2 = set(k for k in node2.keys() if k.endswith('s') and k != 'refs')

                # Check if child types changed
                if child_keys1 != child_keys2:
                    structure_changed = True
                else:
                    # Check if child counts changed
                    for key in child_keys1:
                        if len(node1.get(key, [])) != len(node2.get(key, [])):
                            structure_changed = True
                            break

            if text_changed or structure_changed:
                # Provision modified
                diffs.append({
                    'type': 'modified',
                    'id': provision_id,
                    'old': node1,
                    'new': node2
                })
            else:
                # Provision unchanged
                diffs.append({
                    'type': 'unchanged',
                    'id': provision_id,
                    'old': node1,
                    'new': node2
                })

    return diffs


def get_diff_stats(diffs: List[dict]) -> dict:
    """
    Calculate diff statistics.

    Args:
        diffs: List of diff objects

    Returns:
        Dictionary with counts of each diff type
    """
    stats = {
        'added': 0,
        'deleted': 0,
        'modified': 0,
        'unchanged': 0,
        'total': len(diffs)
    }

    for diff in diffs:
        diff_type = diff.get('type', 'unchanged')
        if diff_type in stats:
            stats[diff_type] += 1

    return stats


def highlight_word_changes(text1: str, text2: str) -> tuple:
    """
    Simple word-level diff highlighting.

    Args:
        text1: Original text
        text2: Modified text

    Returns:
        Tuple of (highlighted_text1, highlighted_text2)
    """
    words1 = text1.split()
    words2 = text2.split()

    # Find changed words
    highlighted1 = []
    highlighted2 = []

    max_len = max(len(words1), len(words2))

    for i in range(max_len):
        word1 = words1[i] if i < len(words1) else None
        word2 = words2[i] if i < len(words2) else None

        if word1 and word2:
            if word1 != word2:
                highlighted1.append(f'<mark>{word1}</mark>')
                highlighted2.append(f'<mark>{word2}</mark>')
            else:
                highlighted1.append(word1)
                highlighted2.append(word2)
        elif word1:
            highlighted1.append(f'<mark>{word1}</mark>')
        elif word2:
            highlighted2.append(f'<mark>{word2}</mark>')

    return ' '.join(highlighted1), ' '.join(highlighted2)
