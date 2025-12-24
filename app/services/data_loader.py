"""
Data loader service - Parses USC sections on-the-fly from source XML/XHTML files.
"""

from pathlib import Path
from typing import Dict, List, Optional
from .usc_parser import parse_xml_section, parse_xhtml_section


class SectionDataLoader:
    """
    Loads section data by parsing source XML/XHTML files on-the-fly.

    This avoids data quality issues from pre-extracted JSON files.
    """

    # Years configuration - maps year to source file info
    YEARS_CONFIG = {
        2024: {'format': 'xml', 'file': '2024/usc18.xml'},
        2022: {'format': 'xml', 'file': '2022/usc18.xml'},
        2018: {'format': 'xhtml', 'file': '2018/2018/2018usc18.htm'},
        2013: {'format': 'xhtml', 'file': '2013/2013/2013usc18.htm'},
        2006: {'format': 'xhtml', 'file': '2006/2006/2006usc18.htm'},
        2000: {'format': 'xhtml', 'file': '2000/2000/2000usc18.htm'},
        1994: {'format': 'xhtml', 'file': '1994/1994/1994usc18.htm'},
    }

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.raw_dir = data_dir / 'raw' / 'uslm'

        # Cache for parsed sections: "section_num:year" -> parsed_data
        self._cache = {}

        # Cache section numbers per year (fast lookup for availability)
        self._section_index = {}
        print("Building section index...")
        self._build_section_index()
        print(f"Section index built: {sum(len(v) for v in self._section_index.values())} section-year pairs")

    def get_section(self, section_num: str, year: int) -> Optional[dict]:
        """
        Load a specific version of a section by parsing on-the-fly.

        Args:
            section_num: Section number (e.g., '922', '933')
            year: Year

        Returns:
            Parsed section data or None if not found
        """
        # Check cache first
        cache_key = f"{section_num}:{year}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Get file info for this year
        config = self.YEARS_CONFIG.get(year)
        if not config:
            return None

        # Build file path
        source_file = self.raw_dir / config['file']
        if not source_file.exists():
            print(f"Source file not found: {source_file}")
            return None

        # Parse based on format
        try:
            if config['format'] == 'xml':
                data = parse_xml_section(source_file, section_num, year)
            else:  # xhtml
                data = parse_xhtml_section(source_file, section_num, year)

            # Cache the result
            if data:
                self._cache[cache_key] = data

            return data

        except Exception as e:
            print(f"Error parsing {source_file} section {section_num}: {e}")
            return None

    def get_section_versions(self, section_num: str) -> Dict[int, dict]:
        """
        Load all versions of a section.

        Args:
            section_num: Section number (e.g., '922', '933')

        Returns:
            Dictionary mapping year -> section data
        """
        versions = {}

        for year in self.YEARS_CONFIG.keys():
            data = self.get_section(section_num, year)
            if data:
                versions[year] = data

        return versions

    def get_available_years(self) -> List[int]:
        """
        Get list of all available years.

        Returns:
            Sorted list of years (descending order, newest first)
        """
        return sorted(self.YEARS_CONFIG.keys(), reverse=True)

    def _build_section_index(self):
        """
        Build fast index of which sections exist in each year.

        This parses each year's file ONCE to extract section numbers only,
        avoiding the N×M bottleneck of parsing 9,100+ times.
        """
        import re

        for year, config in self.YEARS_CONFIG.items():
            source_file = self.raw_dir / config['file']
            if not source_file.exists():
                print(f"  Warning: {year} source file not found")
                self._section_index[year] = set()
                continue

            try:
                if config['format'] == 'xml':
                    # Quick extract of section numbers from XML
                    from lxml import etree
                    tree = etree.parse(source_file)
                    ns = {'uslm': 'http://xml.house.gov/schemas/uslm/1.0'}
                    section_elems = tree.xpath('//uslm:section', namespaces=ns)

                    section_nums = set()
                    for elem in section_elems:
                        identifier = elem.get('identifier', '')
                        match = re.search(r'/s(\d+[a-z]?)', identifier)
                        if match:
                            section_nums.add(match.group(1))

                    self._section_index[year] = section_nums
                    print(f"  {year}: {len(section_nums)} sections (XML)")

                else:  # xhtml
                    # Quick extract of section numbers from XHTML
                    from bs4 import BeautifulSoup
                    with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')

                    section_headers = soup.find_all('h3', class_='section-head')
                    section_nums = set()

                    for header in section_headers:
                        text = header.get_text()
                        match = re.search(r'§(\d+[a-z]?)', text)
                        if match:
                            section_nums.add(match.group(1))

                    self._section_index[year] = section_nums
                    print(f"  {year}: {len(section_nums)} sections (XHTML)")

            except Exception as e:
                print(f"  Error indexing {year}: {e}")
                self._section_index[year] = set()

    def list_all_sections(self) -> List[dict]:
        """
        Get list of all sections with metadata.

        This method scans the latest year (2024) to find all sections,
        then checks which years each section is available in.

        Returns:
            List of dicts with section_num, heading, and available years
        """
        sections = []
        latest_year = max(self.YEARS_CONFIG.keys())

        # Parse latest year file to get all sections
        latest_config = self.YEARS_CONFIG[latest_year]
        latest_file = self.raw_dir / latest_config['file']

        if not latest_file.exists():
            print(f"Latest file not found: {latest_file}")
            return []

        # For XML files, we can extract all section identifiers
        if latest_config['format'] == 'xml':
            try:
                from lxml import etree
                tree = etree.parse(latest_file)
                ns = {'uslm': 'http://xml.house.gov/schemas/uslm/1.0'}

                section_elems = tree.xpath('//uslm:section', namespaces=ns)

                for section_elem in section_elems:
                    identifier = section_elem.get('identifier', '')

                    # Extract section number from identifier
                    import re
                    match = re.search(r'/s(\d+[a-z]?)', identifier)
                    if not match:
                        continue

                    section_num = match.group(1)

                    # Get heading
                    heading_elem = section_elem.find('.//{http://xml.house.gov/schemas/uslm/1.0}heading')
                    heading = heading_elem.text if heading_elem is not None else 'Unknown'

                    # Fast lookup using pre-built index instead of parsing 7 times per section
                    available_years = [
                        y for y in sorted(self.YEARS_CONFIG.keys())
                        if section_num in self._section_index.get(y, set())
                    ]

                    if available_years:
                        sections.append({
                            'num': section_num,
                            'heading': heading,
                            'years': available_years,
                            'year_range': f"{available_years[0]}-{available_years[-1]}" if len(available_years) > 1 else str(available_years[0])
                        })

            except Exception as e:
                print(f"Error scanning sections: {e}")
                return []

        # Sort by section number
        sections.sort(key=lambda x: int(x['num']) if x['num'].isdigit() else 0)

        return sections

    def clear_cache(self):
        """Clear the parsing cache."""
        self._cache.clear()
