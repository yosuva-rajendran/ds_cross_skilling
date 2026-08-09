import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingest import ingest


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into the Chroma store")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory containing .txt/.md files (default: ./data)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing collection before re-indexing",
    )
    args = parser.parse_args()
    ingest(data_dir=args.data_dir, reset=args.reset)


if __name__ == "__main__":
    main()
