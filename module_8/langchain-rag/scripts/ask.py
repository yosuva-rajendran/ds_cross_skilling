import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# windows console defaults to cp1252 and chokes on unicode chars
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.chain import ask


def main():
    question = " ".join(sys.argv[1:]).strip() or input("Question: ").strip()
    if not question:
        sys.exit("No question provided")

    result = ask(question)
    print(result["answer"])
    if result["sources"]:
        print(f"\nSources: {result['sources']}")


if __name__ == "__main__":
    main()
