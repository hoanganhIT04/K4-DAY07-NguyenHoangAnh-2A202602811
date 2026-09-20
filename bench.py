from pathlib import Path
import re

from src.embeddings import GeminiEmbedder

from src.models import Document
from src.store import EmbeddingStore
from src.chunking import RecursiveChunker


# ============================================================
# CONFIG
# ============================================================

DATA_DIR = Path("data/ecommerce")

# Strategy cá nhân của Nguyễn Hoàng Anh
CHUNKER = RecursiveChunker(chunk_size=500)


QUERIES = [
    {
        "id": 1,
        "question": "Tiền hoàn qua Ví ShopeePay sẽ nhận được trong bao lâu?",
        "metadata_filter": None,
    },
    {
        "id": 2,
        "question": (
            "Trong bao nhiêu ngày kể từ khi giao hàng thành công, "
            "người mua vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền?"
        ),
        "metadata_filter": None,
    },
    {
        "id": 3,
        "question": (
            "Video mở kiện hàng cần đảm bảo những yêu cầu gì "
            "để được chấp nhận làm bằng chứng?"
        ),
        "metadata_filter": None,
    },
    {
        "id": 4,
        "question": (
            "Sau khi nhận hàng hoàn trả, cần khiếu nại trong bao lâu "
            "và cần bằng chứng gì?"
        ),
        "metadata_filter": {"audience": "seller"},
    },
    {
        "id": 5,
        "question": (
            "Nếu chọn hình thức Tự sắp xếp để gửi hàng hoàn trả, "
            "phí trả hàng có được hoàn lại không?"
        ),
        "metadata_filter": None,
    },
]


# ============================================================
# FRONTMATTER PARSER
# ============================================================

def parse_frontmatter(text):
    """
    Parse YAML frontmatter đơn giản.

    Expected format:

    ---
    doc_id: "..."
    title: "..."
    source_url: "..."
    retrieved_at: "..."
    document_version: "..."
    audience: "..."
    ---
    body...
    """

    text = text.lstrip()

    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)

    if len(parts) < 3:
        return {}, text

    raw_frontmatter = parts[1]
    body = parts[2].strip()

    metadata = {}

    for line in raw_frontmatter.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)

        if not match:
            continue

        key = match.group(1)
        value = match.group(2).strip()

        # Remove quote
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ('"', "'")
        ):
            value = value[1:-1]

        metadata[key] = value

    return metadata, body


# ============================================================
# LOAD DOCUMENTS + CHUNKING
# ============================================================

def load_documents():
    documents = []
    total_chunks = 0

    files = sorted(DATA_DIR.glob("*.md"))

    print("=" * 70)
    print("LOADING CORPUS")
    print("=" * 70)
    print(f"Data directory : {DATA_DIR}")
    print(f"Documents      : {len(files)}")
    print("Strategy       : RecursiveChunker")
    print()

    for path in files:
        text = path.read_text(encoding="utf-8")

        frontmatter, body = parse_frontmatter(text)

        if not body.strip():
            print(f"[SKIP] {path.name}: empty body")
            continue

        chunks = CHUNKER.chunk(body)

        doc_id = frontmatter.get("doc_id", path.stem)

        print(f"{path.name}")
        print(f"  doc_id : {doc_id}")
        print(f"  audience : {frontmatter.get('audience', 'unknown')}")
        print(f"  chunks : {len(chunks)}")

        for index, chunk in enumerate(chunks):
            metadata = dict(frontmatter)

            # Original document ID
            metadata["doc_id"] = doc_id

            # Path để truy vết file
            metadata["file_path"] = str(path).replace("\\", "/")

            document = Document(
                id=f"{path.stem}#{index}",
                content=chunk,
                metadata=metadata,
            )

            documents.append(document)

        total_chunks += len(chunks)

    print()
    print(f"Total chunks: {total_chunks}")
    print("=" * 70)
    print()

    return documents


# ============================================================
# BENCHMARK
# ============================================================

def run_benchmark(store):
    print("=" * 70)
    print("BENCHMARK — 5 GROUP QUERIES")
    print("=" * 70)

    for item in QUERIES:
        query_id = item["id"]
        question = item["question"]
        metadata_filter = item["metadata_filter"]

        print()
        print("-" * 70)
        print(f"QUERY {query_id}")
        print(f"Question: {question}")

        if metadata_filter:
            print(f"Filter: {metadata_filter}")
        else:
            print("Filter: None")

        print("-" * 70)

        results = store.search_with_filter(
            question,
            top_k=3,
            metadata_filter=metadata_filter,
        )

        if not results:
            print("No results.")
            continue

        for rank, result in enumerate(results, start=1):
            print()
            print(f"TOP {rank}")
            print(f"Score   : {result['score']:.4f}")
            print(f"Chunk ID: {result['id']}")
            print(f"Doc ID  : {result['metadata'].get('doc_id')}")
            print(f"Audience: {result['metadata'].get('audience')}")

            content = result["content"].replace("\n", " ").strip()

            # Chỉ in preview để terminal không quá dài
            if len(content) > 300:
                content = content[:300] + "..."

            print(f"Content : {content}")


# ============================================================
# MAIN
# ============================================================

def main():
    documents = load_documents()

    if not documents:
        print("No documents found.")
        return

    store = EmbeddingStore()

    print("Adding documents to EmbeddingStore...")
    store.add_documents(documents)

    print(f"Stored chunks: {store.get_collection_size()}")
    print()

    run_benchmark(store)


if __name__ == "__main__":
    main()