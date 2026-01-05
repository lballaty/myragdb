# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/indexers/vector_indexer.py
# Description: Vector embedding indexing and semantic search using ChromaDB
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

import chromadb
from sentence_transformers import SentenceTransformer

from myragdb.indexers.file_scanner import ScannedFile
from myragdb.utils.id_generator import generate_document_id
from myragdb.config import settings


@dataclass
class VectorSearchResult:
    """
    Result from vector semantic search.

    Business Purpose: Represents a semantically similar document with
    similarity score and metadata.

    Example:
        result = VectorSearchResult(
            file_path="/path/to/file.py",
            repository="MyProject",
            score=0.92,
            snippet="Authentication implementation...",
            file_type=".py"
        )
    """
    file_path: str
    repository: str
    score: float
    snippet: str
    file_type: str
    relative_path: str


class VectorIndexer:
    """
    Vector embedding indexer for semantic search using ChromaDB.

    Business Purpose: Provides semantic search using vector embeddings.
    Finds conceptually similar documents even if they don't share keywords.
    Complements Meilisearch keyword search by understanding meaning, not just matching words.

    Example:
        indexer = VectorIndexer()
        indexer.index_file(scanned_file)
        results = indexer.search("user login process")
        # Finds docs about authentication even without exact keywords
    """

    def __init__(self, index_dir: Optional[str] = None, collection_name: str = "myragdb"):
        """
        Initialize vector indexer.

        Args:
            index_dir: Directory to store ChromaDB data
            collection_name: Name of ChromaDB collection
        """
        self.index_dir = index_dir or os.path.join(settings.index_dir, "vectors")
        self.collection_name = collection_name

        # Initialize ChromaDB
        self.client = self._init_chromadb()
        self.collection = self._get_or_create_collection()

        # Initialize embedding model
        self.model = self._load_embedding_model()

    def _init_chromadb(self) -> chromadb.Client:
        """
        Initialize ChromaDB client.

        Business Purpose: Sets up local ChromaDB instance for vector storage.

        Returns:
            ChromaDB client
        """
        Path(self.index_dir).mkdir(parents=True, exist_ok=True)

        return chromadb.PersistentClient(
            path=self.index_dir,
        )

    def _get_or_create_collection(self):
        """
        Get or create ChromaDB collection.

        Business Purpose: Manages collection lifecycle for storing embeddings.

        Returns:
            ChromaDB collection
        """
        try:
            return self.client.get_collection(name=self.collection_name)
        except:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "MyRAGDB document embeddings"}
            )

    def _load_embedding_model(self) -> SentenceTransformer:
        """
        Load sentence embedding model.

        Business Purpose: Initializes the model that converts text to vectors.
        Using all-MiniLM-L6-v2 for fast CPU inference with good quality.

        Returns:
            SentenceTransformer model
        """
        print(f"Loading embedding model: {settings.embedding_model}")
        model = SentenceTransformer(settings.embedding_model)
        model.to(settings.embedding_device)
        return model

    def _chunk_content(self, content: str, chunk_size: int = 1000) -> List[str]:
        """
        Split content into chunks for embedding.

        Business Purpose: Large documents need to be split into smaller pieces
        for better embedding quality and to stay within model limits.

        Args:
            content: Text content to chunk
            chunk_size: Maximum characters per chunk

        Returns:
            List of text chunks

        Example:
            chunks = self._chunk_content(long_document)
            # Each chunk is <= 1000 characters
        """
        if len(content) <= chunk_size:
            return [content]

        chunks = []
        words = content.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > chunk_size:
                if current_chunk:  # Don't add empty chunks
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length

        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def index_file(self, scanned_file: ScannedFile) -> None:
        """
        Index a single file by creating embeddings.

        Business Purpose: Converts file content to vector embeddings and
        stores in ChromaDB for semantic search. Uses Base64 hash IDs that
        match Meilisearch for perfect document parity.

        Args:
            scanned_file: File to index

        Example:
            indexer.index_file(scanned_file)
            # File is now searchable by semantic meaning
        """
        try:
            # Chunk content if needed
            chunks = self._chunk_content(scanned_file.content, settings.chunk_size)

            # Generate embeddings
            embeddings = self.model.encode(chunks, show_progress_bar=False)

            # Prepare metadata and IDs
            ids = []
            metadatas = []
            documents = []

            # Generate base document ID (same as Meilisearch for parity)
            base_doc_id = generate_document_id(scanned_file.file_path)

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{base_doc_id}::chunk_{i}"
                ids.append(chunk_id)

                metadata = {
                    "file_path": scanned_file.file_path,
                    "repository": scanned_file.repository_name,
                    "file_type": scanned_file.file_type,
                    "relative_path": scanned_file.relative_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                metadatas.append(metadata)
                documents.append(chunk)

            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                documents=documents
            )

        except Exception as e:
            print(f"Error indexing file {scanned_file.file_path}: {e}")
            raise

    def index_files(self, files: List[ScannedFile]) -> int:
        """
        Index multiple files.

        Business Purpose: Batch indexes files for better efficiency.

        Args:
            files: List of files to index

        Returns:
            Number of files successfully indexed

        Example:
            files = scan_repository(repo_config)
            count = indexer.index_files(files)
            print(f"Indexed {count} files")
        """
        indexed = 0

        for i, scanned_file in enumerate(files):
            try:
                self.index_file(scanned_file)
                indexed += 1

                if (i + 1) % 10 == 0:
                    print(f"Indexed {i + 1} files...")

            except Exception as e:
                print(f"Error indexing {scanned_file.file_path}: {e}")
                continue

        return indexed

    def search(
        self,
        query: str,
        limit: int = 10,
        repository: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """
        Semantic search using vector similarity.

        Business Purpose: Finds documents semantically similar to query,
        even if they don't share exact keywords. Understands meaning and context.

        Args:
            query: Search query (natural language)
            limit: Maximum results to return
            repository: Optional repository filter

        Returns:
            List of VectorSearchResult sorted by similarity

        Example:
            # Query doesn't mention "JWT" but finds relevant auth docs
            results = indexer.search("secure user login", limit=5)
            for result in results:
                print(f"{result.relative_path}: {result.score:.2f}")
        """
        results = []

        try:
            # Generate query embedding
            query_embedding = self.model.encode([query], show_progress_bar=False)[0]

            # Build where clause for filtering
            where_clause = None
            if repository:
                where_clause = {"repository": repository}

            # Search ChromaDB
            search_results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=limit * 3,  # Get more, then dedupe by file
                where=where_clause
            )

            # Process results and deduplicate by file
            seen_files = set()

            if search_results['ids'] and len(search_results['ids'][0]) > 0:
                for i in range(len(search_results['ids'][0])):
                    metadata = search_results['metadatas'][0][i]
                    file_path = metadata['file_path']

                    # Deduplicate (one result per file, take highest scoring chunk)
                    if file_path in seen_files:
                        continue

                    seen_files.add(file_path)

                    # Calculate similarity score (ChromaDB returns distance, convert to similarity)
                    distance = search_results['distances'][0][i]
                    similarity = 1.0 / (1.0 + distance)  # Convert distance to similarity

                    # Get snippet from document chunk
                    snippet = search_results['documents'][0][i][:200]

                    result = VectorSearchResult(
                        file_path=file_path,
                        repository=metadata['repository'],
                        score=similarity,
                        snippet=snippet,
                        file_type=metadata.get('file_type', ''),
                        relative_path=metadata['relative_path']
                    )
                    results.append(result)

                    # Stop when we have enough unique files
                    if len(results) >= limit:
                        break

        except Exception as e:
            print(f"Error during vector search: {e}")
            raise

        return results

    def get_document_count(self) -> int:
        """
        Get total number of indexed chunks.

        Business Purpose: Provides statistics about index size.

        Returns:
            Number of chunks in index
        """
        return self.collection.count()

    def clear_index(self) -> None:
        """
        Delete all documents from index.

        Business Purpose: Allows clean rebuild of index.
        """
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "MyRAGDB document embeddings"}
        )

    def delete_document(self, file_path: str) -> None:
        """
        Remove all chunks of a document from index.

        Business Purpose: Removes deleted files from index.

        Args:
            file_path: Path of file to remove
        """
        # Find all chunks for this file
        results = self.collection.get(
            where={"file_path": file_path}
        )

        if results['ids']:
            self.collection.delete(ids=results['ids'])
