from typing import Callable, Optional, Dict, Any

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(
        self,
        store: EmbeddingStore,
        llm_fn: Callable[[str], str],
    ) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> str:
        # 1. Retrieve relevant chunks
        if metadata_filter:
            results = self.store.search_with_filter(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        else:
            results = self.store.search(
                question,
                top_k=top_k,
            )

        # 2. Không có dữ liệu → không gọi LLM
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở dữ liệu."

        # 3. Build context
        context_parts = []

        for i, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})

            source = (
                metadata.get("source")
                or metadata.get("source_url")
                or metadata.get("doc_id")
                or result.get("id", "unknown")
            )

            context_parts.append(
                f"[{i}] Source: {source}\n"
                f"{result.get('content', '')}"
            )

        context = "\n\n".join(context_parts)

        # 4. Build RAG prompt
        prompt = f"""
Bạn là trợ lý hỏi đáp dựa trên cơ sở tri thức được cung cấp.

Câu hỏi:
{question}

Ngữ cảnh:
{context}

Hãy trả lời câu hỏi CHỈ dựa trên thông tin trong ngữ cảnh.
Không được tự bịa hoặc sử dụng thông tin bên ngoài ngữ cảnh.

Nếu thông tin không đủ để trả lời, hãy nói rõ rằng
không tìm thấy thông tin phù hợp trong cơ sở dữ liệu.

Khi trả lời, hãy trích dẫn nguồn bằng số [1], [2], [3]
tương ứng với các đoạn ngữ cảnh đã cung cấp.
""".strip()

        # 5. Call LLM
        return self.llm_fn(prompt)