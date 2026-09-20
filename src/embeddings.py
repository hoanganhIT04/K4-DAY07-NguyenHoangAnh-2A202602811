from __future__ import annotations

import hashlib
import math
import os


LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"


class MockEmbedder:
    def __init__(self, dim: int = 64):
        self.dim = dim
        self._backend_name = "mock"

    def __call__(self, text: str) -> list[float]:
        return _mock_embed(text, dim=self.dim)


class LocalEmbedder:
    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed"
            ) from exc

        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, text: str) -> list[float]:
        vector = self.model.encode(
            text,
            normalize_embeddings=True,
        )
        return [float(value) for value in vector]


class OpenAIEmbedder:
    def __init__(
        self,
        model_name: str = OPENAI_EMBEDDING_MODEL,
    ):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "openai is not installed"
            ) from exc

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set"
            )

        self.model_name = model_name
        self._backend_name = model_name
        self.client = OpenAI(api_key=api_key)

    def __call__(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text,
        )

        return [
            float(value)
            for value in response.data[0].embedding
        ]


class GeminiEmbedder:
    def __init__(
        self,
        model_name: str = GEMINI_EMBEDDING_MODEL,
    ):
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai is not installed"
            ) from exc

        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY or GOOGLE_API_KEY is not set"
            )

        self.model_name = model_name
        self._backend_name = model_name
        self.client = genai.Client(
            api_key=api_key
        )

    def __call__(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
        )

        return [
            float(value)
            for value in response.embeddings[0].values
        ]

    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 20,
    ) -> list[list[float]]:

        embeddings = []

        for start in range(
            0,
            len(texts),
            batch_size,
        ):
            batch = texts[
                start:start + batch_size
            ]

            response = self.client.models.embed_content(
                model=self.model_name,
                contents=batch,
            )

            batch_embeddings = [
                [
                    float(value)
                    for value in embedding.values
                ]
                for embedding in response.embeddings
            ]

            embeddings.extend(batch_embeddings)

        return embeddings


class OllamaEmbedder:
    def __init__(
        self,
        model_name: str = "qwen3-embedding:0.6b",
        base_url: str = "http://localhost:11434",
    ):
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "requests is not installed"
            ) from exc

        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self._backend_name = f"ollama:{model_name}"
        self._requests = requests

    def __call__(self, text: str) -> list[float]:
        response = self._requests.post(
            f"{self.base_url}/api/embed",
            json={
                "model": self.model_name,
                "input": text,
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        return [
            float(value)
            for value in data["embeddings"][0]
        ]


def _mock_embed(
    text: str,
    dim: int = 64,
) -> list[float]:

    digest = hashlib.md5(
        text.encode("utf-8")
    ).digest()

    values = []

    for index in range(dim):
        byte = digest[
            index % len(digest)
        ]

        value = (
            (byte / 255.0) * 2.0
        ) - 1.0

        values.append(value)

    norm = math.sqrt(
        sum(value * value for value in values)
    )

    if norm == 0:
        return [0.0] * dim

    return [
        value / norm
        for value in values
    ]