# Historical Statute Database - Research & Progress

## Project Goal

Build a system to retrieve, parse, and store historical versions of 18 USC 922 (and potentially other statutes) with:
- Full legislative history tracking
- Cross-reference extraction and mapping
- Multi-version comparison capabilities
- Structured data output (JSON)

## Key Decisions

### Data Source: uscode.house.gov (NOT GovInfo)

**Initial Assumption (WRONG)**: GovInfo provides USLM XML for U.S. Code
- Investigated GovInfo API - returns HTML only
- Downloaded 232MB GovInfo ZIP package for Title 18
- Found: Only HTML files, PDF files, and metadata XML
- **No USLM XML content in GovInfo**

**Correct Source (CONFIRMED)**: uscode.house.gov (U.S. House of Representatives)
- Official source for U.S. Code in USLM XML format
- Historical archives available (1994-2024)
- No API authentication required
- Direct file downloads

### Data Format: USLM XML

**United States Legislative Markup (USLM)**
- Based on Akoma Ntoso XML standard
- Semantic markup with hierarchical structure
- Built-in cross-reference tags: `<ref idref="/us/usc/t18/s923">`
- Legislative history via `<notes>` elements
- Dublin Core metadata
- XPath-queryable structure

**Why USLM XML vs HTML**:
- HTML requires regex parsing (unreliable)
- USLM has semantic `<ref>` tags for cross-references
- Structured hierarchy (section → subsection → paragraph → subparagraph → clause)
- Legislative history embedded in `<notes>` elements
- Consistent schema across all versions

## Research Findings

### Access Method

**No API Key Required**
- uscode.house.gov provides direct downloads
- No authentication needed
- Simple HTTP downloads

**URL Pattern** (from unitedstates/uscode GitHub repo):
```
http://uscode.house.gov/zip/[version]/
```

Where `[version]` can be:
- `uscprelim` - Current/preliminary version
- `2024`, `2023`, `2011`, etc. - Specific historical years

**Download Script Example** (from unitedstates/uscode):
```bash
#!/bin/bash
# Download all uscode files for a year
DIR=`pwd`"/data"
DEST="$DIR/uscode.house.gov/zip/$1/"
mkdir -P $DIR
wget -m -l1 -P $DIR http://uscode.house.gov/zip/$1
cd $DEST
for filename in `ls`; do unzip $filename; done
find . -type f -name "*zip" -delete
cd $DIR
```

### USLM XML Structure

**Hierarchy**:
```xml
<section identifier="922">
  <num>922</num>
  <heading>Unlawful acts</heading>
  <subsection identifier="(a)">
    <num>(a)</num>
    <paragraph identifier="(1)">
      <num>(1)</num>
      <subparagraph identifier="(A)">
        <num>(A)</num>
        <p>Text content here...</p>
      </subparagraph>
    </paragraph>
  </subsection>
</section>
```

**Cross-References**:
```xml
<ref idref="/us/usc/t18/s923">section 923</ref>
<ref idref="/us/usc/t18/s921/a/3">section 921(a)(3)</ref>
```

**Legislative History**:
```xml
<notes>
  <note role="source-credit">
    <p>Added Pub. L. 90-351, title IV, §902, June 19, 1968, 82 Stat. 226</p>
  </note>
  <note role="amendment-note">
    <heading>2021 Amendment</heading>
    <p>Subsec. (d)(9). Pub. L. 117-103 added par. (9).</p>
  </note>
</notes>
```

**Metadata**:
```xml
<meta>
  <dc:identifier>usc/t18/s922</dc:identifier>
  <dc:date>2024-12-02</dc:date>
</meta>
```

### Historical Coverage

**Available Versions**: 1994-2025
- Current version: Through Public Law 119-46 (Dec 2, 2025)
- Annual Historical Archives page has older versions
- Prior Release Points page has specific PL milestones

### Key Resources

**Downloaded**:
- ✅ USLM User Guide PDF from xml.house.gov

**URLs**:
- Main download page: http://uscode.house.gov/download/download.shtml
- XML schema: http://xml.house.gov/schemas/uslm/1.0/USLM-1.0.xsd
- User guide: http://xml.house.gov/schemas/uslm/1.0/USLM-User-Guide.pdf
- GitHub reference: https://github.com/unitedstates/uscode

## Current Status

### Completed
1. ✅ Created project directory structure
2. ✅ Updated requirements.txt (requests, lxml, beautifulsoup4)
3. ✅ Researched and verified correct data source
4. ✅ Found URL patterns for downloads
5. ✅ Downloaded USLM User Guide
6. ✅ Understood USLM XML structure
7. ✅ Confirmed no API key needed
8. ✅ Created implementation plan

### Current Issue

**uscode.house.gov Connectivity Problems**:
- All direct access attempts timeout
- curl/wget commands fail to connect
- WebFetch tool times out
- Site may be:
  - Temporarily down
  - Very slow to respond
  - Blocking automated requests
  - Having network routing issues

**What Works**:
- ✅ xml.house.gov (downloaded User Guide successfully)
- ✅ GitHub repos (accessed unitedstates/uscode)
- ✅ Web search results

**What Doesn't Work**:
- ❌ uscode.house.gov/download/download.shtml
- ❌ uscode.house.gov/zip/uscprelim/
- ❌ uscode.house.gov/download/releasepoints/...

### Next Steps

**Option 1**: Create download script with known URL patterns, test later
- Use: `http://uscode.house.gov/zip/uscprelim/` for current
- Use: `http://uscode.house.gov/zip/2024/`, `/2018/`, etc. for historical
- Implement retry logic and better error handling
- Test when site becomes accessible

**Option 2**: Manual download
- User visits download page
- Downloads Title 18 ZIP manually
- Provides file to continue with parsing scripts

**Option 3**: Alternative data source
- Use GovInfo API (requires free API key from api.data.gov)
- Would get HTML instead of USLM XML
- Would require different parsing approach (regex vs XPath)
- **Not recommended** - loses semantic markup benefits

## Implementation Plan

### Planned Scripts

1. **download_usc_xml.py**
   - Download Title 18 USLM XML for multiple versions
   - Target years: [2024, 2018, 2012, 2006, 2000, 1994]
   - Output: `data/raw/uslm/title18-[year].xml`

2. **extract_section.py**
   - Extract section 922 from full Title 18 XML
   - Use XPath: `//section[@identifier="922"]`
   - Output: `data/sections/usc-18-922-[year].xml`

3. **parse_uslm_structure.py**
   - Parse hierarchical structure to JSON
   - Extract all levels (section → subsection → paragraph → subparagraph → clause)
   - Output: `data/parsed/usc-18-922-[year]-structure.json`

4. **extract_references.py**
   - Extract all `<ref>` tags with `@idref` attributes
   - Parse target statute info (title, section, subsection)
   - Track reference location and context
   - Output: `data/references/usc-18-922-[year]-refs.json`

5. **extract_legislative_history.py**
   - Parse `<notes>` elements by role
   - Extract Public Law citations
   - Build chronological amendment timeline
   - Output: `data/history/usc-18-922-[year]-history.json`

6. **consolidate_data.py**
   - Merge all parsed data
   - Compute version differences
   - Generate cross-reference graph
   - Output: `data/consolidated/usc-18-922-complete.json`

### Directory Structure

```
lelivre/
├── scripts/
│   ├── download_usc_xml.py
│   ├── extract_section.py
│   ├── parse_uslm_structure.py
│   ├── extract_references.py
│   ├── extract_legislative_history.py
│   └── consolidate_data.py
├── data/
│   ├── raw/
│   │   ├── uslm/              # Full Title 18 XML files
│   │   └── USLM-User-Guide.pdf
│   ├── sections/              # Extracted section 922 XML
│   ├── parsed/                # Structure JSON
│   ├── references/            # Reference JSON
│   ├── history/               # Legislative history JSON
│   └── consolidated/          # Final unified database
├── requirements.txt
├── RESEARCH.md               # This file
└── README.md
```

## Technical Stack

**Language**: Python 3.x

**Dependencies**:
- `requests>=2.31.0` - HTTP downloads
- `lxml>=4.9.0` - XML parsing with XPath
- `beautifulsoup4>=4.12.0` - Alternative XML parser

**Key Technologies**:
- XPath for XML navigation
- USLM schema for structured parsing
- JSON for output format
- Git for version control

## Lessons Learned

1. **Always verify data source assumptions**
   - GovInfo was assumed to have USLM XML (incorrect)
   - Downloaded and inspected actual files to confirm
   - Found correct source through research

2. **Semantic markup is superior to text parsing**
   - USLM XML has `<ref>` tags vs regex on HTML
   - Structured hierarchy vs text patterns
   - Legislative history embedded vs external lookups

3. **Government websites can be unreliable**
   - Timeouts and connectivity issues
   - Need robust retry logic
   - Consider manual download fallback

4. **Open source repos are valuable**
   - unitedstates/uscode provided URL patterns
   - Confirmed no authentication needed
   - Working script examples

## References

### Official Sources
- **House Office of Law Revision Counsel**: http://uscode.house.gov
- **XML Schemas and Documentation**: http://xml.house.gov
- **USLM Schema**: http://xml.house.gov/schemas/uslm/1.0/USLM-1.0.xsd
- **USLM User Guide**: http://xml.house.gov/schemas/uslm/1.0/USLM-User-Guide.pdf

### Alternative Sources
- **GovInfo**: https://www.govinfo.gov (HTML/PDF only, no USLM XML for organized code)
- **GovInfo API**: https://www.govinfo.gov/features/api (requires API ZemaHAlYY7KH6SlkVjuL5PgdcrZt4ReLsobTGNXJ)
- **Congress.gov API**: https://www.loc.gov/apis/additional-apis/congress-dot-gov-api/

### GitHub Repositories
- **unitedstates/uscode**: https://github.com/unitedstates/uscode (archived)
- **unitedstates/congress**: https://github.com/unitedstates/congress
- **usgpo/uslm**: https://github.com/usgpo/uslm (schema discussions)

### Documentation
- **Library of Congress Blog**: https://blogs.loc.gov/law/2013/11/the-united-states-code-online-downloadable-xml-files-and-more/
- **USLM on GovInfo**: https://www.govinfo.gov/features/beta-uslm-xml
- **Statute Compilations**: https://www.govinfo.gov/features/statute-compilations-uslm-xml

## Open Questions

1. **Exact file names**: What is Title 18 ZIP file named? (e.g., `title18.zip`, `usc18.zip`)
2. **Directory listing**: Can we get directory listing from `/zip/uscprelim/`?
3. **Historical consistency**: Are all years 1994-2024 in same USLM format?
4. **Site accessibility**: When will uscode.house.gov be accessible for downloads?
5. **Rate limiting**: Are there any rate limits or download restrictions?

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Dec 14, 2025 | Use uscode.house.gov instead of GovInfo | GovInfo only has HTML/PDF, not USLM XML |
| Dec 14, 2025 | Use USLM XML format | Semantic markup for references and structure |
| Dec 14, 2025 | Start with 18 USC 922 only | Focused scope for proof of concept |
| Dec 14, 2025 | Target 6 historical versions | 2024, 2018, 2012, 2006, 2000, 1994 |
| Dec 14, 2025 | Use Python with lxml | XPath support for XML parsing |
| Dec 14, 2025 | Delete old HTML-based scripts | Reset to USLM XML approach |

---

**Last Updated**: December 14, 2025
**Status**: Research complete, awaiting site access for download testing