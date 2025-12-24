"""
Routes for viewing USC sections.
"""

from flask import Blueprint, render_template, abort
from services.data_loader import SectionDataLoader
from pathlib import Path

bp = Blueprint('sections', __name__)

# Initialize data loader (points to ../data/ directory)
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
loader = SectionDataLoader(DATA_DIR)


@bp.route('/')
def index():
    """Homepage - list all sections."""
    sections = loader.list_all_sections()
    return render_template('index.html', sections=sections)


@bp.route('/section/<section_num>')
def view_section(section_num):
    """View a specific section (latest version by default)."""
    versions = loader.get_section_versions(section_num)

    if not versions:
        abort(404, description=f"Section {section_num} not found")

    latest_year = max(versions.keys())
    latest_data = versions[latest_year]

    return render_template('section_view.html',
                          section_num=section_num,
                          heading=latest_data.get('heading', 'Unknown'),
                          current_year=latest_year,
                          data=latest_data,
                          versions=versions,
                          available_years=sorted(versions.keys(), reverse=True))


@bp.route('/section/<section_num>/<int:year>')
def view_section_year(section_num, year):
    """View a specific section at a specific year."""
    data = loader.get_section(section_num, year)

    if not data:
        abort(404, description=f"Section {section_num} ({year}) not found")

    versions = loader.get_section_versions(section_num)

    return render_template('section_view.html',
                          section_num=section_num,
                          heading=data.get('heading', 'Unknown'),
                          current_year=year,
                          data=data,
                          versions=versions,
                          available_years=sorted(versions.keys(), reverse=True))
