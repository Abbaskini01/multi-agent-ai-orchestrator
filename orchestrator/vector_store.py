"""
Orchestrator Vector Store Manager (Version 3)
Performs semantic AST chunking and indexes code snippets in an in-memory Qdrant Vector DB.
Uses FastEmbed for zero-config, fast local embeddings.
"""

from pathlib import Path
from typing import Dict, List, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
from orchestrator.code_graph import CodeGraphManager


class VectorStoreManager:
    def __init__(self, collection_name: str = "code_chunks"):
        self.collection_name = collection_name
        # Initialize in-memory Qdrant instance
        self.qdrant = QdrantClient(":memory:")
        # Initialize FastEmbed model (BAAI/bge-small-en-v1.5)
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.vector_size = 384  # Embedding dimension for bge-small-en-v1.5

        # Create/reset Vector Collection
        self.qdrant.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
        )

    def index_graph_chunks(self, graph_manager: CodeGraphManager) -> int:
        """
        Extracts complete AST function/class code blocks using Tree-sitter byte ranges,
        generates embeddings, and uploads them to Qdrant.
        """
        points = []
        point_id = 1

        for rel_path, file_data in graph_manager.file_map.items():
            abs_path = graph_manager.root_dir / rel_path
            if not abs_path.exists():
                continue

            code_bytes = abs_path.read_bytes()

            # Process Functions as AST Chunks
            for func in file_data.get("functions", []):
                chunk_text = code_bytes[func["start_byte"]:func["end_byte"]].decode("utf-8", errors="ignore")
                payload = {
                    "filepath": rel_path,
                    "type": "function",
                    "name": func["name"],
                    "code": chunk_text,
                }
                
                # Prepend metadata to code for embedding generation
                embed_text = f"File: {rel_path}\nFunction: {func['name']}\nCode:\n{chunk_text}"
                embeddings = list(self.embedding_model.embed([embed_text]))[0]

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embeddings.tolist(),
                        payload=payload
                    )
                )
                point_id += 1

            # Process Classes as AST Chunks
            for cls in file_data.get("classes", []):
                chunk_text = code_bytes[cls["start_byte"]:cls["end_byte"]].decode("utf-8", errors="ignore")
                payload = {
                    "filepath": rel_path,
                    "type": "class",
                    "name": cls["name"],
                    "code": chunk_text,
                }
                embed_text = f"File: {rel_path}\nClass: {cls['name']}\nCode:\n{chunk_text}"
                embeddings = list(self.embedding_model.embed([embed_text]))[0]

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embeddings.tolist(),
                        payload=payload
                    )
                )
                point_id += 1

        if points:
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )

        return len(points)

    def search_similar_code(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search against stored AST code chunks using query_points.
        """
        query_vector = list(self.embedding_model.embed([query]))[0].tolist()

        # Modern Qdrant API call
        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k
        )

        results = []
        for res in response.points:
            results.append({
                "score": round(res.score, 4),
                "filepath": res.payload.get("filepath"),
                "name": res.payload.get("name"),
                "type": res.payload.get("type"),
                "code": res.payload.get("code")
            })
        return results