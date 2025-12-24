"""
USC Parsing Rules - Post-processing fixes for known edge cases.

This module provides section-specific overrides to correct parsing issues
that are difficult to handle generically in the parser.
"""


# Section-specific parsing fixes
SECTION_OVERRIDES = {
    '922': {
        'remove_provisions': [
            # Remove duplicate (v) from repealed provision [(v), (w) Repealed...]
            # Keep only the (v) with actual content
            {
                'id_pattern': '/us/usc/t18/s922/v',
                'text_contains': 'Repealed',
                'reason': 'Duplicate (v) from repealed provision marker'
            }
        ],
        'relocate_provisions': [
            # Fix (C) that appears at root level but should be nested
            # This is a formatting quirk in the XHTML
            {
                'wrong_id': '/us/usc/t18/s922/C',
                'text_starts_with': 'If a chief law enforcement officer',
                'reason': 'Uppercase (C) incorrectly parsed as root subsection'
                # Note: Correct location would need deeper investigation
                # For now, just remove from root level
            }
        ]
    }
}


def apply_post_parse_fixes(parsed_section: dict, section_num: str) -> dict:
    """
    Apply section-specific fixes to parsed output.

    Args:
        parsed_section: Parsed section data
        section_num: Section number (e.g., "922")

    Returns:
        Fixed parsed section data
    """
    if section_num not in SECTION_OVERRIDES:
        return parsed_section

    overrides = SECTION_OVERRIDES[section_num]

    # Apply removals
    if 'remove_provisions' in overrides:
        for rule in overrides['remove_provisions']:
            parsed_section = _remove_matching_provision(parsed_section, rule)

    # Apply relocations
    if 'relocate_provisions' in overrides:
        for rule in overrides['relocate_provisions']:
            parsed_section = _remove_matching_provision(parsed_section, {
                'id_pattern': rule['wrong_id'],
                'text_starts_with': rule.get('text_starts_with'),
                'reason': rule['reason']
            })

    return parsed_section


def _remove_matching_provision(parsed_section: dict, rule: dict) -> dict:
    """Remove provision matching the rule from subsections."""
    if 'subsections' not in parsed_section:
        return parsed_section

    filtered_subsections = []

    for subsection in parsed_section['subsections']:
        # Check if this provision matches the removal rule
        should_remove = False

        # Check ID pattern
        if 'id_pattern' in rule and subsection['id'] == rule['id_pattern']:
            # Additional text checks
            if 'text_contains' in rule:
                if rule['text_contains'] in subsection.get('text', ''):
                    should_remove = True
            elif 'text_starts_with' in rule:
                if subsection.get('text', '').startswith(rule['text_starts_with']):
                    should_remove = True
            else:
                # ID match alone is sufficient
                should_remove = True

        if not should_remove:
            filtered_subsections.append(subsection)

    parsed_section['subsections'] = filtered_subsections
    return parsed_section
