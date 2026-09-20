from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import GeminiEmbedder
from src.models import Document
from src.store import EmbeddingStore


load_dotenv()

DATA_DIR = Path("data/ecommerce")
RESULT_FILE = Path("ket_qua_benchmark.txt")


def read_markdown(path):
    text = path.read_text(encoding="utf-8")

    if text.startswith("---"):
        parts = text.split("---", 2)
        frontmatter = parts[1]
        body = parts[2].strip()
    else:
        frontmatter = ""
        body = text

    metadata = {}

    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"')

    return metadata, body


def demo_llm(prompt):
    preview = prompt.replace("\n", " ")

    return (
        "[DEMO LLM] Generated answer from prompt preview: "
        f"{preview[:500]}..."
    )


def print_results(results):
    for rank, result in enumerate(results, start=1):

        print(f"\nTOP {rank}")

        print(
            f"Score   : "
            f"{result['score']:.4f}"
        )

        print(
            f"Chunk ID : "
            f"{result['id']}"
        )

        print(
            f"Doc ID  : "
            f"{result['metadata'].get('doc_id')}"
        )

        print(
            f"Audience: "
            f"{result['metadata'].get('audience')}"
        )

        print(
            f"Content : "
            f"{result['content'][:500]}"
        )


def run_benchmark():

    print("=" * 70)
    print("EMBEDDING CONFIGURATION")
    print("=" * 70)

    print("Embedding provider: Gemini")
    print("Embedding model: gemini-embedding-001")
    print("Embedding mode: batched")

    print("\n" + "=" * 70)
    print("LOADING CORPUS")
    print("=" * 70)

    embedding_model = GeminiEmbedder(
        model_name="gemini-embedding-001"
    )

    store = EmbeddingStore(
        embedding_fn=embedding_model
    )

    chunker = RecursiveChunker(
        chunk_size=500
    )

    all_documents = []

    for path in sorted(DATA_DIR.glob("*.md")):

        metadata, body = read_markdown(path)

        chunks = chunker.chunk(body)

        for i, chunk in enumerate(chunks):

            document = Document(
                id=f"{path.stem}#{i}",
                content=chunk,
                metadata={
                    **metadata,
                    "doc_id": path.stem,
                    "file_path": str(path),
                },
            )

            all_documents.append(document)

        print(
            f"{path.name}: "
            f"{len(chunks)} chunks"
        )

    print(
        f"\nTotal chunks: "
        f"{len(all_documents)}"
    )

    print("\n" + "=" * 70)
    print("GENERATING GEMINI EMBEDDINGS")
    print("=" * 70)

    texts = [
        document.content
        for document in all_documents
    ]

    embeddings = embedding_model.embed_batch(
        texts,
        batch_size=20,
    )

    print(
        f"Generated embeddings: "
        f"{len(embeddings)}"
    )

    if len(embeddings) != len(all_documents):
        raise RuntimeError(
            "Number of embeddings does not match "
            "number of documents"
        )

    store.add_documents_with_embeddings(
        all_documents,
        embeddings,
    )

    print(
        f"Stored chunks: "
        f"{store.get_collection_size()}"
    )

    agent = KnowledgeBaseAgent(
        store=store,
        llm_fn=demo_llm,
    )

    queries = [
        "Tiền hoàn qua Ví ShopeePay sẽ nhận được trong bao lâu?",

        "Trong bao nhiêu ngày kể từ khi giao hàng thành công, "
        "người mua vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền?",

        "Video mở kiện hàng cần đảm bảo những yêu cầu gì "
        "để được chấp nhận làm bằng chứng?",

        "Sau khi nhận hàng hoàn trả, cần khiếu nại trong bao lâu "
        "và cần bằng chứng gì?",

        "Nếu chọn hình thức Tự sắp xếp để gửi hàng hoàn trả, "
        "phí trả hàng có được hoàn lại không?",
    ]

    for index, query in enumerate(
        queries,
        start=1,
    ):

        print("\n" + "=" * 70)
        print(f"QUERY {index}")
        print("=" * 70)

        print(
            f"Question: {query}"
        )

        if index == 4:

            print("\n" + "-" * 70)
            print("A — WITHOUT METADATA FILTER")
            print("-" * 70)

            results_without_filter = store.search(
                query,
                top_k=3,
            )

            print_results(
                results_without_filter
            )

            print(
                "\nAGENT ANSWER — WITHOUT FILTER"
            )

            print(
                agent.answer(
                    query,
                    top_k=3,
                )
            )

            print("\n" + "-" * 70)
            print(
                "B — WITH METADATA FILTER: "
                "audience=seller"
            )
            print("-" * 70)

            results_with_filter = (
                store.search_with_filter(
                    query,
                    top_k=3,
                    metadata_filter={
                        "audience": "seller"
                    },
                )
            )

            print_results(
                results_with_filter
            )

            print(
                "\nAGENT ANSWER — WITH FILTER"
            )

            print(
                agent.answer(
                    query,
                    top_k=3,
                    metadata_filter={
                        "audience": "seller"
                    },
                )
            )

        else:

            results = store.search(
                query,
                top_k=3,
            )

            print(
                "\nTOP-3 RETRIEVAL"
            )

            print_results(
                results
            )

            print(
                "\nAGENT ANSWER"
            )

            print(
                agent.answer(
                    query,
                    top_k=3,
                )
            )

    print("\n" + "=" * 70)
    print("BENCHMARK FINISHED")
    print("=" * 70)


if __name__ == "__main__":

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        with redirect_stdout(f):
            run_benchmark()

    print(
        "Benchmark finished."
    )

    print(
        f"Result saved to: "
        f"{RESULT_FILE}"
    )