# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/utils/id_generator.py
# Description: Deterministic Base64 ID generator for document parity across Meilisearch and ChromaDB
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import base64
import hashlib
from pathlib import Path


def generate_document_id(file_path: str) -> str:
    """
    Generate a deterministic Base64-encoded document ID from absolute file path.

    Business Purpose: Ensures the same file has the same ID in both Meilisearch
    and ChromaDB, enabling perfect document parity and lookup across both systems.

    Args:
        file_path: Absolute path to the file

    Returns:
        Base64-encoded SHA256 hash of the file path (URL-safe)

    Example:
        doc_id = generate_document_id("/path/to/file.py")
        # Returns: "xK7JmH9vQpL2..."

        # Same path always returns same ID
        assert generate_document_id("/path/to/file.py") == generate_document_id("/path/to/file.py")
    """
    # Normalize path to absolute path
    abs_path = str(Path(file_path).resolve())

    # SHA256 hash for collision resistance
    hash_obj = hashlib.sha256(abs_path.encode('utf-8'))
    hash_bytes = hash_obj.digest()

    # Base64 encode (URL-safe variant, no padding)
    doc_id = base64.urlsafe_b64encode(hash_bytes).decode('utf-8').rstrip('=')

    return doc_id


def verify_document_id(file_path: str, doc_id: str) -> bool:
    """
    Verify that a document ID matches a file path.

    Business Purpose: Allows validation that a document ID corresponds to
    the expected file path, useful for debugging and integrity checks.

    Args:
        file_path: Absolute path to the file
        doc_id: Document ID to verify

    Returns:
        True if the doc_id matches the file_path, False otherwise

    Example:
        doc_id = generate_document_id("/path/to/file.py")
        assert verify_document_id("/path/to/file.py", doc_id) == True
        assert verify_document_id("/different/path.py", doc_id) == False
    """
    expected_id = generate_document_id(file_path)
    return expected_id == doc_id
