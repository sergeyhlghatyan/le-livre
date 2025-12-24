#!/usr/bin/env python3
"""
Re-extract all sections from XHTML years with new hierarchical parser.
"""

from pathlib import Path
import subprocess
import sys

def main():
    sections_dir = Path('data/sections')

    # Get all section numbers
    sections = sorted([d.name for d in sections_dir.iterdir() if d.is_dir()],
                     key=lambda x: int(x) if x.isdigit() else 0)

    print(f"Re-extracting {len(sections)} sections from XHTML years...")
    print(f"Years: 1994, 2000, 2006, 2013, 2018")
    print()

    # Process in batches to show progress
    batch_size = 50
    for i in range(0, len(sections), batch_size):
        batch = sections[i:i+batch_size]
        print(f"Processing sections {i+1}-{min(i+batch_size, len(sections))}...")

        cmd = ['python3', 'scripts/extract_sections.py', '--sections'] + batch
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)

    print(f"\n✓ Re-extracted all {len(sections)} sections")

if __name__ == '__main__':
    main()
