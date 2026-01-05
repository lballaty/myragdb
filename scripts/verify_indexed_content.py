#!/usr/bin/env python3
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/verify_indexed_content.py
# Description: Verify what content was actually indexed in Keyword and Vector databases
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import sys
from pathlib import Path
from collections import defaultdict, Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from myragdb.indexers.keyword_indexer import KeywordIndexer
from myragdb.indexers.vector_indexer import VectorIndexer
from myragdb.config import settings


def analyze_keyword_index():
    """Analyze Keyword index to show repositories and file types."""
    print("\n" + "="*80)
    print("KEYWORD INDEX ANALYSIS")
    print("="*80)

    indexer = KeywordIndexer(str(Path(settings.index_dir) / "meilisearch"))

    # Get all documents
    with indexer.ix.searcher() as searcher:
        # Group by repository
        repo_counts = Counter()
        file_type_counts = Counter()
        repo_file_types = defaultdict(Counter)
        repo_dirs = defaultdict(set)

        total = searcher.doc_count_all()
        print(f"\nTotal Documents: {total:,}")

        for docnum in range(total):
            doc = searcher.stored_fields(docnum)
            repo = doc.get('repository', 'unknown')
            file_type = doc.get('file_type', 'unknown')
            file_path = doc.get('file_path', '')

            repo_counts[repo] += 1
            file_type_counts[file_type] += 1
            repo_file_types[repo][file_type] += 1

            # Extract directory
            if file_path:
                dir_path = str(Path(file_path).parent)
                # Get top-level directory structure
                parts = Path(file_path).parts
                if len(parts) > 1:
                    top_dir = "/".join(parts[:3])  # Get first 3 levels
                    repo_dirs[repo].add(top_dir)

    # Print repository breakdown
    print("\n" + "-"*80)
    print("REPOSITORIES INDEXED:")
    print("-"*80)
    for repo, count in sorted(repo_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {repo:50s} {count:>8,} documents")

    # Print file type breakdown
    print("\n" + "-"*80)
    print("FILE TYPES INDEXED:")
    print("-"*80)
    for file_type, count in sorted(file_type_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {file_type:20s} {count:>8,} files")

    # Print top directories per repository
    print("\n" + "-"*80)
    print("TOP DIRECTORIES PER REPOSITORY:")
    print("-"*80)
    for repo in sorted(repo_counts.keys()):
        print(f"\n  {repo}:")
        dirs = sorted(list(repo_dirs[repo]))[:10]  # Show first 10 dirs
        for d in dirs:
            print(f"    - {d}")
        if len(repo_dirs[repo]) > 10:
            print(f"    ... and {len(repo_dirs[repo]) - 10} more directories")


def analyze_vector_index():
    """Analyze vector index to show repositories and chunks."""
    print("\n" + "="*80)
    print("VECTOR INDEX ANALYSIS")
    print("="*80)

    indexer = VectorIndexer()

    # Query metadata from ChromaDB
    collection = indexer.collection

    # Get all documents (in batches to avoid memory issues)
    print(f"\nTotal Chunks: {collection.count():,}")

    # Sample metadata to understand what's indexed
    results = collection.get(limit=10000, include=['metadatas'])

    if results and results['metadatas']:
        repo_counts = Counter()
        file_type_counts = Counter()
        repo_file_types = defaultdict(Counter)
        repo_dirs = defaultdict(set)

        for metadata in results['metadatas']:
            repo = metadata.get('repository', 'unknown')
            file_type = metadata.get('file_type', 'unknown')
            file_path = metadata.get('file_path', '')

            repo_counts[repo] += 1
            file_type_counts[file_type] += 1
            repo_file_types[repo][file_type] += 1

            # Extract directory
            if file_path:
                parts = Path(file_path).parts
                if len(parts) > 1:
                    top_dir = "/".join(parts[:3])  # Get first 3 levels
                    repo_dirs[repo].add(top_dir)

        # Print repository breakdown
        print("\n" + "-"*80)
        print("REPOSITORIES INDEXED (sampled from 10,000 chunks):")
        print("-"*80)
        for repo, count in sorted(repo_counts.items(), key=lambda x: x[1], reverse=True):
            # Extrapolate to total
            total_chunks = collection.count()
            estimated_total = int(count * total_chunks / len(results['metadatas']))
            print(f"  {repo:50s} ~{estimated_total:>8,} chunks")

        # Print file type breakdown
        print("\n" + "-"*80)
        print("FILE TYPES INDEXED (sampled):")
        print("-"*80)
        for file_type, count in sorted(file_type_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  {file_type:20s} ~{count:>8,} chunks")

        # Print top directories per repository
        print("\n" + "-"*80)
        print("TOP DIRECTORIES PER REPOSITORY (sampled):")
        print("-"*80)
        for repo in sorted(repo_counts.keys()):
            print(f"\n  {repo}:")
            dirs = sorted(list(repo_dirs[repo]))[:10]
            for d in dirs:
                print(f"    - {d}")
            if len(repo_dirs[repo]) > 10:
                print(f"    ... and {len(repo_dirs[repo]) - 10} more directories")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("MYRAGDB INDEX VERIFICATION")
    print("="*80)

    analyze_keyword_index()
    analyze_vector_index()

    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80 + "\n")
