#!/usr/bin/env python3
"""
Download historical versions of Title 18 from uscode.house.gov

Supports both:
- USLM XML (from Public Law release points, 2013+)
- XHTML (from annual archives, 1994+)

Usage:
    python download_usc_xml.py --years 2024 2022 2018 2013 2006 2000 1994
    python download_usc_xml.py --all  # Downloads all recommended versions
"""

import argparse
import sys
import time
from pathlib import Path
from urllib.request import urlretrieve, Request, urlopen
from urllib.error import URLError, HTTPError
import zipfile

# Target years for statutory history of 18 USC 922 and 933
RECOMMENDED_YEARS = {
    2024: {"format": "xml", "pl": "119-46", "description": "Current version"},
    2022: {"format": "xml", "pl": "118-158", "description": "§ 933 enacted"},
    2018: {"format": "xhtml", "description": "Recent amendments"},
    2013: {"format": "xhtml", "description": "First XML year (XHTML available)"},
    2006: {"format": "xhtml", "description": "Major amendments"},
    2000: {"format": "xhtml", "description": "Pre-9/11 version"},
    1994: {"format": "xhtml", "description": "Assault Weapons Ban"},
}


def construct_xml_url(title: int, pl_code: str) -> str:
    """Construct URL for USLM XML download (Public Law release point)."""
    congress, law = pl_code.split("-")
    return (
        f"https://uscode.house.gov/download/releasepoints/us/pl/"
        f"{congress}/{law}/xml_usc{title}@{pl_code}.zip"
    )


def construct_xhtml_url(year: int) -> str:
    """Construct URL for XHTML download (annual archive)."""
    return f"https://uscode.house.gov/download/annualhistoricalarchives/XHTML/{year}.zip"


def download_with_progress(url: str, output_path: Path, max_retries: int = 3) -> bool:
    """Download file with progress reporting and retry logic."""
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  [Attempt {attempt}/{max_retries}] {url}")

            def progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(100, downloaded * 100 / total_size)
                    print(f"\r  Progress: {percent:.1f}%", end="", flush=True)

            urlretrieve(url, output_path, reporthook=progress_hook)
            print()  # Newline after progress

            if output_path.exists() and output_path.stat().st_size > 0:
                size_mb = output_path.stat().st_size / 1024 / 1024
                print(f"  ✓ Downloaded: {output_path.name} ({size_mb:.2f} MB)")
                return True
            else:
                print(f"  ✗ Failed: File is empty")
                return False

        except HTTPError as e:
            print(f"\n  ✗ HTTP {e.code}: {e.reason}")
            if e.code == 404:
                print(f"  → File not available at this URL")
                return False
        except URLError as e:
            print(f"\n  ✗ Network error: {e.reason}")
        except Exception as e:
            print(f"\n  ✗ Error: {e}")

        if attempt < max_retries:
            wait = attempt * 2
            print(f"  → Retrying in {wait}s...")
            time.sleep(wait)

    print(f"  ✗ Failed after {max_retries} attempts")
    return False


def extract_title18(zip_path: Path, extract_dir: Path, year: int, format_type: str) -> bool:
    """Extract Title 18 files from ZIP archive."""
    try:
        print(f"  Extracting Title 18 from {zip_path.name}...")

        with zipfile.ZipFile(zip_path, 'r') as zf:
            # List all files
            all_files = zf.namelist()

            # Find Title 18 files
            if format_type == "xml":
                # USLM XML: look for usc18.xml or title18.xml
                title18_files = [f for f in all_files if 'usc18.xml' in f.lower() or 'title18.xml' in f.lower()]
            else:
                # XHTML: look for files in title18 directory
                title18_files = [f for f in all_files if '/title18/' in f.lower() or 'title18' in f.lower()]

            if not title18_files:
                print(f"  ✗ No Title 18 files found in archive")
                # Extract everything to inspect
                zf.extractall(extract_dir)
                print(f"  → Extracted all files to {extract_dir}")
                return True

            # Extract Title 18 files
            for file in title18_files:
                zf.extract(file, extract_dir)

            print(f"  ✓ Extracted {len(title18_files)} Title 18 file(s)")
            for f in title18_files[:5]:  # Show first 5
                print(f"    - {f}")
            if len(title18_files) > 5:
                print(f"    ... and {len(title18_files) - 5} more")

        return True

    except zipfile.BadZipFile:
        print(f"  ✗ Invalid ZIP file")
        return False
    except Exception as e:
        print(f"  ✗ Extraction error: {e}")
        return False


def download_version(title: int, year: int, output_dir: Path) -> bool:
    """Download a specific year version of Title 18."""
    config = RECOMMENDED_YEARS.get(year)
    if not config:
        print(f"✗ Year {year} not in recommended years")
        return False

    format_type = config["format"]
    description = config.get("description", "")

    print(f"\n{'='*70}")
    print(f"Year {year} - {description}")
    print(f"Format: {format_type.upper()}")
    print(f"{'='*70}")

    # Construct URL based on format
    if format_type == "xml":
        pl_code = config.get("pl")
        if not pl_code:
            print(f"✗ No Public Law code specified for {year}")
            return False
        url = construct_xml_url(title, pl_code)
        zip_filename = f"title{title}-{year}-pl{pl_code}.zip"
    else:  # xhtml
        url = construct_xhtml_url(year)
        zip_filename = f"uscode-{year}-xhtml.zip"

    # Setup paths
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / zip_filename
    extract_dir = output_dir / str(year)

    # Check if already downloaded
    if zip_path.exists():
        print(f"  → ZIP exists: {zip_path.name}")
        if extract_dir.exists() and any(extract_dir.iterdir()):
            print(f"  → Already extracted to: {extract_dir}")
            return True

    # Download
    success = download_with_progress(url, zip_path)

    if success:
        # Extract Title 18
        extract_dir.mkdir(exist_ok=True)
        extract_title18(zip_path, extract_dir, year, format_type)

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Download historical Title 18 USC (XML and XHTML formats)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Recommended years (covers major statutory changes):
{chr(10).join(f"  {year}: {info['description']} ({info['format'].upper()})"
              for year, info in sorted(RECOMMENDED_YEARS.items(), reverse=True))}

Examples:
  # Download all recommended years
  python download_usc_xml.py --all

  # Download specific years
  python download_usc_xml.py --years 2024 2022 1994

  # Custom output directory
  python download_usc_xml.py --all --output ./downloads
"""
    )

    parser.add_argument("--years", nargs="+", type=int,
                       help="Specific years to download")
    parser.add_argument("--all", action="store_true",
                       help="Download all recommended years")
    parser.add_argument("--title", type=int, default=18,
                       help="US Code title number (default: 18)")
    parser.add_argument("--output", type=Path, default=Path("data/raw/uslm"),
                       help="Output directory (default: data/raw/uslm)")

    args = parser.parse_args()

    # Determine years to download
    if args.all:
        years = sorted(RECOMMENDED_YEARS.keys(), reverse=True)
    elif args.years:
        years = sorted(args.years, reverse=True)
    else:
        parser.print_help()
        print("\n✗ Error: Specify --all or --years")
        sys.exit(1)

    print(f"Title: {args.title}")
    print(f"Output: {args.output}")
    print(f"Years: {', '.join(map(str, years))}")

    # Download each year
    results = {}
    for year in years:
        success = download_version(args.title, year, args.output)
        results[year] = success

    # Summary
    print(f"\n{'='*70}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*70}")

    successful = [y for y, s in results.items() if s]
    failed = [y for y, s in results.items() if not s]

    print(f"✓ Successful: {len(successful)}/{len(results)}")
    for year in successful:
        fmt = RECOMMENDED_YEARS[year]["format"].upper()
        print(f"  - {year} ({fmt})")

    if failed:
        print(f"\n✗ Failed: {len(failed)}/{len(results)}")
        for year in failed:
            print(f"  - {year}")

    print()


if __name__ == "__main__":
    main()
