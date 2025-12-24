"""
Routes for comparing USC section versions.
"""

from flask import Blueprint, render_template, request, abort
from services.data_loader import SectionDataLoader
from services.diff_engine import compare_versions, get_diff_stats
from pathlib import Path

bp = Blueprint('comparison', __name__)

# Initialize data loader
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
loader = SectionDataLoader(DATA_DIR)


@bp.route('/compare/<section_num>')
def compare(section_num):
    """
    Compare two versions of a section.

    Query params:
        year1: First year to compare
        year2: Second year to compare
    """
    year1 = request.args.get('year1', type=int)
    year2 = request.args.get('year2', type=int)

    if not year1 or not year2:
        # Show selection page if years not provided
        versions = loader.get_section_versions(section_num)
        if not versions:
            abort(404, description=f"Section {section_num} not found")

        available_years = sorted(versions.keys())
        return render_template('select_comparison.html',
                              section_num=section_num,
                              available_years=available_years)

    # Load the two versions
    version1 = loader.get_section(section_num, year1)
    version2 = loader.get_section(section_num, year2)

    if not version1 or not version2:
        abort(404, description=f"One or both versions not found")

    # Compare versions
    diffs = compare_versions(version1, version2)
    stats = get_diff_stats(diffs)

    return render_template('comparison.html',
                          section_num=section_num,
                          year1=year1,
                          year2=year2,
                          heading1=version1.get('heading', 'Unknown'),
                          heading2=version2.get('heading', 'Unknown'),
                          diffs=diffs,
                          stats=stats)
