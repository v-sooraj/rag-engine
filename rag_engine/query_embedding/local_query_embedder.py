from sentence_transformers import SentenceTransformer

from rag_engine.query_embedding.query_embedder import QueryEmbedder


class LocalQueryEmbedder(QueryEmbedder):

    def __init__(
        self,
        model_name: str,
        model=None,
    ):
        self.model_name = model_name
        self.model = (
            model
            if model is not None
            else SentenceTransformer(model_name)
        )

    def embed(
        self,
        query: str,
    ) -> list[float]:
        self._validate(query)

        embedding = self.model.encode(query)

        return embedding.tolist()

    def _validate(
        self,
        query: str,
    ) -> None:
        if not query.strip():
            raise ValueError(
                "query must not be empty"
            )