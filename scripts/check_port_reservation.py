# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/check_port_reservation.py
# Description: Check if PORT-RESERVATIONS.md is in the index
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

from pathlib import Path
from myragdb.indexers.keyword_indexer import KeywordIndexer
from myragdb.indexers.vector_indexer import VectorIndexer
from myragdb.config import settings

def check_keyword_index():
    """Check if PORT-RESERVATIONS.md is in Keyword index."""
    print("=" * 80)
    print("CHECKING KEYWORD INDEX FOR PORT-RESERVATIONS.md")
    print("=" * 80)

    indexer = KeywordIndexer(str(Path(settings.index_dir) / "meilisearch"))

    found = False
    with indexer.ix.searcher() as searcher:
        for docnum in range(searcher.doc_count_all()):
            doc = searcher.stored_fields(docnum)
            file_path = doc.get('file_path', '')

            if 'PORT-RESERVATIONS' in file_path.upper():
                print(f"\n✓ FOUND in Keyword index:")
                print(f"  File Path: {file_path}")
                print(f"  Repository: {doc.get('repository', 'unknown')}")
                print(f"  Relative Path: {doc.get('relative_path', 'unknown')}")
                found = True

    if not found:
        print("\n✗ NOT FOUND in Keyword index")

    return found

def check_vector_index():
    """Check if PORT-RESERVATIONS.md is in vector index."""
    print("\n" + "=" * 80)
    print("CHECKING VECTOR INDEX FOR PORT-RESERVATIONS.md")
    print("=" * 80)

    indexer = VectorIndexer(str(Path(settings.index_dir) / "chroma"))
    collection = indexer.collection

    # Get all documents (this might be slow for large collections)
    results = collection.get(limit=100000)

    found = False
    for i, metadata in enumerate(results['metadatas']):
        file_path = metadata.get('file_path', '')

        if 'PORT-RESERVATIONS' in file_path.upper():
            if not found:
                print(f"\n✓ FOUND in Vector index:")
            print(f"  Chunk {i}: {file_path}")
            print(f"  Repository: {metadata.get('repository', 'unknown')}")
            print(f"  Relative Path: {metadata.get('relative_path', 'unknown')}")
            found = True

    if not found:
        print("\n✗ NOT FOUND in vector index")

    return found

def test_search():
    """Test searching for 'port reservation'."""
    print("\n" + "=" * 80)
    print("TESTING SEARCH FOR 'port reservation'")
    print("=" * 80)

    from myragdb.search.hybrid_search import HybridSearchEngine

    keyword_indexer = KeywordIndexer(str(Path(settings.index_dir) / "meilisearch"))
    vector_indexer = VectorIndexer(str(Path(settings.index_dir) / "chroma"))
    engine = HybridSearchEngine(keyword_indexer, vector_indexer)

    results = engine.search("port reservation", limit=10)

    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.relative_path}")
        print(f"   Score: {result.combined_score:.4f} (Keyword: {result.keyword_score:.4f}, Vector: {result.vector_score:.4f})")
        print(f"   Snippet: {result.snippet[:100]}...")

if __name__ == "__main__":
    keyword_found = check_keyword_index()
    vector_found = check_vector_index()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Keyword Index: {'✓ Found' if keyword_found else '✗ NOT Found'}")
    print(f"Vector Index:  {'✓ Found' if vector_found else '✗ NOT Found'}")

    test_search()
