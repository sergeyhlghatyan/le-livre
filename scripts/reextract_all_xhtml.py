#!/usr/bin/env python3
"""
Re-extract all sections from XHTML years (1994, 2000, 2006, 2013, 2018).
Enhanced with multiprocessing for speed and tqdm progress bars.
"""

from pathlib import Path
import json
import sys
from collections import defaultdict
import multiprocessing as mp
from functools import partial

try:
    from tqdm import tqdm
except ImportError:
    print("Installing tqdm for progress bars...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from extract_sections import extract_xhtml_section


def process_section(section_num, xhtml_years, base_dir, sections_dir):
    """
    Process a single section across all XHTML years.
    Returns: (section_num, {year: status, ...}, [errors])
    """
    results = {}
    errors = []

    for year, file_path in xhtml_years.items():
        xhtml_file = base_dir / file_path

        if not xhtml_file.exists():
            results[year] = 'file_not_found'
            continue

        try:
            data = extract_xhtml_section(xhtml_file, section_num, year)

            if data:
                output_file = sections_dir / section_num / f'{year}.json'
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                results[year] = 'success'
            else:
                results[year] = 'not_found'

        except Exception as e:
            results[year] = 'error'
            errors.append((year, str(e)[:60]))

    return section_num, results, errors


def main():
    base_dir = Path('data/raw/uslm')
    sections_dir = Path('data/sections')

    xhtml_years = {
        1994: '1994/1994/1994usc18.htm',
        2000: '2000/2000/2000usc18.htm',
        2006: '2006/2006/2006usc18.htm',
        2013: '2013/2013/2013usc18.htm',
        2018: '2018/2018/2018usc18.htm',
    }

    # Get all section numbers
    sections = sorted([d.name for d in sections_dir.iterdir() if d.is_dir()],
                     key=lambda x: int(x) if x.isdigit() else 0)

    # Determine number of workers
    num_workers = max(1, 4)  # Leave 1 CPU free

    print(f"\n{'=' * 70}")
    print(f"Re-extracting XHTML sections with hierarchical structure")
    print(f"{'=' * 70}")
    print(f"Total sections: {len(sections)}")
    print(f"Years: {', '.join(map(str, sorted(xhtml_years.keys())))}")
    print(f"Workers: {num_workers} parallel processes")
    print(f"{'=' * 70}\n")

    # Statistics tracking
    stats = defaultdict(lambda: {'success': 0, 'not_found': 0, 'error': 0})
    all_errors = []

    # Create worker function with fixed arguments
    worker_func = partial(
        process_section,
        xhtml_years=xhtml_years,
        base_dir=base_dir,
        sections_dir=sections_dir
    )

    # Process sections in parallel with progress bar
    with mp.Pool(processes=num_workers) as pool:
        with tqdm(total=len(sections), desc="Processing", unit="section") as pbar:
            for section_num, results, errors in pool.imap_unordered(worker_func, sections):
                # Update statistics
                for year, status in results.items():
                    stats[year][status] += 1

                # Collect errors
                for year, error_msg in errors:
                    all_errors.append(f"§{section_num} ({year}): {error_msg}")
                    # Show first few errors
                    if len(all_errors) <= 5:
                        tqdm.write(f"⚠ Error: §{section_num} ({year}): {error_msg}")

                # Update progress bar
                total_extracted = sum(s['success'] for s in stats.values())
                total_errors = sum(s['error'] for s in stats.values())
                pbar.set_postfix({
                    'extracted': total_extracted,
                    'errors': total_errors
                })
                pbar.update(1)

    # Final summary
    print(f"\n{'=' * 70}")
    print("EXTRACTION COMPLETE")
    print(f"{'=' * 70}")
    print(f"\n📊 Summary by Year:")
    print(f"{'-' * 70}")

    total_extracted = 0
    for year in sorted(xhtml_years.keys()):
        s = stats[year]
        extracted = s['success']
        total_extracted += extracted

        print(f"  {year}:")
        print(f"    ✓ Extracted:  {extracted:4d}")
        print(f"    ○ Not found:  {s['not_found']:4d}")
        if s['error'] > 0:
            print(f"    ✗ Errors:     {s['error']:4d}")
        print()

    print(f"{'-' * 70}")
    print(f"Total files extracted: {total_extracted}")

    if all_errors:
        print(f"\n⚠ Total errors: {len(all_errors)}")
        if len(all_errors) > 5:
            print(f"  (Showing first 5 of {len(all_errors)} errors)")
            for err in all_errors[:5]:
                print(f"    • {err}")
            print(f"    ... and {len(all_errors) - 5} more")
        else:
            for err in all_errors:
                print(f"    • {err}")

    print(f"\n{'=' * 70}\n")
    print("✓ Next step: Regenerate section views")
    print("  Run: python3 scripts/generate_section_views.py")
    print(f"{'=' * 70}\n")


if __name__ == '__main__':
    # Required for multiprocessing on macOS/Windows
    mp.freeze_support()
    main()
