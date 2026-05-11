from __future__ import annotations

import argparse
import sys
from pathlib import Path

from claude_export_viewer.html_builder import build_site
from claude_export_viewer.loader import load_export


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a Claude.ai data export ZIP into a browsable static HTML site.",
    )
    parser.add_argument("zip_file", type=Path, help="Path to the Claude export ZIP file")
    parser.add_argument("-o", "--output", type=Path, default=Path("site"), help="Output directory (default: site/)")
    args = parser.parse_args()

    if not args.zip_file.exists():
        print(f"Error: {args.zip_file} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Loading export from {args.zip_file}...")
    data = load_export(args.zip_file)
    print(f"  {len(data.conversations)} conversations, {len(data.users)} users")

    print(f"Building site in {args.output}/...")
    build_site(data, args.output)
    print(f"Done! Open {args.output}/index.html in your browser.")


if __name__ == "__main__":
    main()
