# United States Code (USC) Complete Hierarchical Structure

## Full Hierarchy (9 Levels)

The complete USC structure has **9 hierarchical levels** from Title down to Subclause:

```
Title → Part → Chapter → Section → Subsection → Paragraph → Subparagraph → Clause → Subclause
```

**Example path for 18 U.S.C. § 922(a)(1)(A):**
```
Title 18 (Crimes and Criminal Procedure)
  └─ Part I (Crimes)
      └─ Chapter 44 (Firearms)
          └─ Section 922 (Unlawful acts)
              └─ Subsection (a)
                  └─ Paragraph (1)
                      └─ Subparagraph (A)
                          └─ Clause (i)
                              └─ Subclause (I)
```

---

## Level Definitions

### Level 1: Title
**Example**: Title 18 - CRIMES AND CRIMINAL PROCEDURE

**XML (USLM):**
```xml
<title identifier="/us/usc/t18">
  <num value="18">Title 18—</num>
  <heading>CRIMES AND CRIMINAL PROCEDURE</heading>
</title>
```

**XHTML**: Title appears in document metadata and page headers

**Identifier pattern**: `/us/usc/t18`

---

### Level 2: Part
**Numbering**: Roman numerals - I, II, III, IV, V

**Example**: Part I - CRIMES

**XML (USLM):**
```xml
<part identifier="/us/usc/t18/ptI">
  <num value="I">PART I—</num>
  <heading>CRIMES</heading>
</part>
```

**XHTML**: Appears as section headers

**Identifier pattern**: `/us/usc/t18/ptI`

---

### Level 3: Chapter
**Numbering**: Numbers - 1, 2, 3, ... 44, ...

**Example**: Chapter 44 - FIREARMS

**XML (USLM):**
```xml
<chapter identifier="/us/usc/t18/ptI/ch44">
  <num value="44">CHAPTER 44—</num>
  <heading>FIREARMS</heading>
</chapter>
```

**XHTML**: Chapter headers in document

**Identifier pattern**: `/us/usc/t18/ptI/ch44`

---

### Level 4: Section
**Numbering**: Numbers - § 1, § 2, § 922, § 933, ...

**Example**: § 922 - Unlawful acts

**XML (USLM):**
```xml
<section identifier="/us/usc/t18/s922">
  <num value="922">§ 922.</num>
  <heading> Unlawful acts</heading>
</section>
```

**XHTML**: Section headers
```html
<h3 class="section-head">&sect;922. Unlawful acts</h3>
```

**Identifier pattern**: `/us/usc/t18/s922`

**Note**: Our extracted JSON files start at this level - they contain one section with all its subdivisions.

---

## Subdivision Levels Within a Section

The following 5 levels are **subdivisions within a section**. These are what we extract and compare in the diff tool.

### Level 5: Subsection
**Numbering**: Lowercase letters - (a), (b), (c), (d), ...

**XML (USLM):**
- Tag: `<subsection>`
- Identifier: `/us/usc/t18/s922/a`

**XHTML:**
- CSS class: `statutory-body`
- Pattern: `<p class="statutory-body">(a) It shall be unlawful—</p>`

**Example**: `(a) It shall be unlawful—`

---

### Level 6: Paragraph
**Numbering**: Numbers - (1), (2), (3), ...

**XML (USLM):**
- Tag: `<paragraph>`
- Identifier: `/us/usc/t18/s922/a/1`

**XHTML:**
- CSS class: `statutory-body-1em`
- Pattern: `<p class="statutory-body-1em">(1) for any person—</p>`
- Indentation: 1em

**Example**: `(1) for any person—`

---

### Level 7: Subparagraph
**Numbering**: Uppercase letters - (A), (B), (C), ...

**XML (USLM):**
- Tag: `<subparagraph>`
- Identifier: `/us/usc/t18/s922/a/1/A`

**XHTML:**
- CSS class: `statutory-body-2em`
- Pattern: `<p class="statutory-body-2em">(A) except a licensed importer...</p>`
- Indentation: 2em

**Example**: `(A) except a licensed importer...`

---

### Level 8: Clause
**Numbering**: Lowercase Roman numerals - (i), (ii), (iii), ...

**XML (USLM):**
- Tag: `<clause>`
- Identifier: `/us/usc/t18/s922/a/1/A/i`

**XHTML:**
- CSS class: `statutory-body-3em`
- Pattern: `<p class="statutory-body-3em">(i) first clause...</p>`
- Indentation: 3em

**Example**: `(i) constructed of...`

---

### Level 9: Subclause
**Numbering**: Uppercase Roman numerals - (I), (II), (III), ...

**XML (USLM):**
- Tag: `<subclause>`
- Identifier: `/us/usc/t18/s922/a/1/A/i/I`

**XHTML:**
- CSS class: `statutory-body-4em`
- Pattern: `<p class="statutory-body-4em">(I) text...</p>`
- Indentation: 4em

**Example**: `(I) deepest subdivision...`

---

## Summary Tables

### Complete 9-Level Hierarchy

| Level | Name | Example Numbering | XML Tag | Identifier Example |
|-------|------|-------------------|---------|-------------------|
| 1 | Title | 18 | `<title>` | `/us/usc/t18` |
| 2 | Part | I, II, III | `<part>` | `/us/usc/t18/ptI` |
| 3 | Chapter | 44 | `<chapter>` | `/us/usc/t18/ptI/ch44` |
| 4 | Section | § 922 | `<section>` | `/us/usc/t18/s922` |
| 5 | Subsection | (a), (b) | `<subsection>` | `/us/usc/t18/s922/a` |
| 6 | Paragraph | (1), (2) | `<paragraph>` | `/us/usc/t18/s922/a/1` |
| 7 | Subparagraph | (A), (B) | `<subparagraph>` | `/us/usc/t18/s922/a/1/A` |
| 8 | Clause | (i), (ii) | `<clause>` | `/us/usc/t18/s922/a/1/A/i` |
| 9 | Subclause | (I), (II) | `<subclause>` | `/us/usc/t18/s922/a/1/A/i/I` |

### Subdivision Levels (What We Extract)

Our JSON extractions contain **levels 4-9** (Section and its subdivisions):

| Level | Name | Numbering | XML Tag | XHTML Class | Full Path Example |
|-------|------|-----------|---------|-------------|-------------------|
| 4 | Section | § 922 | `<section>` | `section-head` | `922` |
| 5 | Subsection | (a) | `<subsection>` | `statutory-body` | `a` |
| 6 | Paragraph | (1) | `<paragraph>` | `statutory-body-1em` | `a/1` |
| 7 | Subparagraph | (A) | `<subparagraph>` | `statutory-body-2em` | `a/1/A` |
| 8 | Clause | (i) | `<clause>` | `statutory-body-3em` | `a/1/A/i` |
| 9 | Subclause | (I) | `<subclause>` | `statutory-body-4em` | `a/1/A/i/I` |

---

## Identifier Patterns

### XML Identifier Extraction

From identifier to subdivision path:
```python
identifier = "/us/usc/t18/s922/a/1/A/i/I"

# Split and find section
parts = identifier.split('/')
# parts = ['', 'us', 'usc', 't18', 's922', 'a', '1', 'A', 'i', 'I']

# Find index of section (starts with 's')
section_idx = next(i for i, p in enumerate(parts) if p.startswith('s'))
# section_idx = 4

# Extract subdivision path after section
path = '/'.join(parts[section_idx + 1:])
# path = 'a/1/A/i/I'
```

### XHTML Class to Level Mapping

```python
class_to_level = {
    'statutory-body': 5,        # Subsection
    'statutory-body-1em': 6,    # Paragraph
    'statutory-body-2em': 7,    # Subparagraph
    'statutory-body-3em': 8,    # Clause
    'statutory-body-4em': 9,    # Subclause
}

level_to_name = {
    5: 'subsection',
    6: 'paragraph',
    7: 'subparagraph',
    8: 'clause',
    9: 'subclause',
}
```

---

## Special XHTML Classes

### Block Elements (Non-numbered)

These appear after enumerated lists:

| Class | Meaning |
|-------|---------|
| `statutory-body-block` | Block text at subsection level |
| `statutory-body-block-1em` | Block text at paragraph level |
| `statutory-body-block-2em` | Block text at subparagraph level |

Example:
```html
<p class="statutory-body-block">This subsection shall not apply...</p>
```

---

## Real Example from § 922

### Full path example:
```
Title 18 (CRIMES AND CRIMINAL PROCEDURE)
  Part I (CRIMES)
    Chapter 44 (FIREARMS)
      § 922 (Unlawful acts)
        (a) It shall be unlawful—
          (1) for any person—
            (A) except a licensed importer, licensed manufacturer...
            (B) except a licensed importer or licensed manufacturer...
          (2) for any importer, manufacturer...
            (A) this paragraph and subsection (b)(3)...
            (B) this paragraph shall not be held...
            (C) nothing in this paragraph...
```

### XML representation:
```xml
<title identifier="/us/usc/t18">
  <part identifier="/us/usc/t18/ptI">
    <chapter identifier="/us/usc/t18/ptI/ch44">
      <section identifier="/us/usc/t18/s922">
        <subsection identifier="/us/usc/t18/s922/a">
          <paragraph identifier="/us/usc/t18/s922/a/1">
            <subparagraph identifier="/us/usc/t18/s922/a/1/A">
              ...
            </subparagraph>
          </paragraph>
        </subsection>
      </section>
    </chapter>
  </part>
</title>
```

---

## For Diff Tool Implementation

**Scope**: We compare **levels 5-9** (Subsection through Subclause)

**Input**: Section JSON files containing one section with all subdivisions

**Output**: Hierarchical diff showing changes at each subdivision level

**Key considerations**:
1. Section (level 4) is the container - we don't diff this
2. We recursively diff subsections (level 5) and all their children
3. Preserve full path for context: `(a)(1)(A)` not just `(A)`
4. Handle missing levels gracefully (e.g., paragraph without subparagraphs)
5. Show hierarchy visually with indentation in HTML output
