from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app import config
from app.vectorstore import get_vectorstore


def load_documents(data_dir: Path) -> list[Document]:
    docs = []
    for path in sorted(data_dir.iterdir()):
        if path.suffix.lower() not in {".txt", ".md", ".markdown"}:
            continue
        text = path.read_text(encoding="utf-8").strip()
        if text:
            docs.append(Document(page_content=text, metadata={"source": path.name}))
    return docs


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)


def ingest(data_dir=None, reset=False):
    vs = get_vectorstore()

    if reset:
        try:
            vs.delete_collection()
            get_vectorstore.cache_clear()
            vs = get_vectorstore()
            print("Cleared existing collection")
        except Exception as exc:
            print(f"Could not reset collection: {exc}")

    documents = load_documents(data_dir or config.DATA_DIR)
    if not documents:
        raise SystemExit("No documents found to ingest")

    chunks = split_documents(documents)

    ids = [f"{c.metadata['source']}#{i}" for i, c in enumerate(chunks)]

    vs.add_documents(chunks, ids=ids)
    print(f"Indexed {len(chunks)} chunks from {len(documents)} document(s)")
    for src in sorted({c.metadata["source"] for c in chunks}):
        print(f"  {src}: {sum(1 for c in chunks if c.metadata['source'] == src)} chunk(s)")
