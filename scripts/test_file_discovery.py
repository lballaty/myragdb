# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/test_file_discovery.py
# Description: Test if PORT-RESERVATIONS.md is being discovered by file scanner
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

from myragdb.config import load_repositories_config
from myragdb.indexers.file_scanner import FileScanner

def test_file_discovery():
    """Test if PORT-RESERVATIONS.md is discovered during file scanning."""
    print("=" * 80)
    print("TESTING FILE DISCOVERY FOR PORT-RESERVATIONS.md")
    print("=" * 80)

    # Load repository configuration
    repo_config = load_repositories_config()
    xllm_repo = None

    for repo in repo_config.repositories:
        if repo.name == "xLLMArionComply":
            xllm_repo = repo
            break

    if not xllm_repo:
        print("✗ xLLMArionComply repository not found in config")
        return

    print(f"\nRepository: {xllm_repo.name}")
    print(f"Path: {xllm_repo.path}")
    print(f"\nInclude patterns:")
    for pattern in xllm_repo.file_patterns.include:
        print(f"  - {pattern}")
    print(f"\nExclude patterns:")
    for pattern in xllm_repo.file_patterns.exclude:
        print(f"  - {pattern}")

    # Create scanner and test
    scanner = FileScanner(xllm_repo)

    print("\n" + "=" * 80)
    print("SCANNING FOR FILES...")
    print("=" * 80)

    found_port_reservations = False
    total_files = 0
    root_md_files = []

    for scanned_file in scanner.scan():
        total_files += 1

        # Check if this is a root-level .md file
        if scanned_file.relative_path.count('/') == 0 and scanned_file.file_type == '.md':
            root_md_files.append(scanned_file.relative_path)

        # Check for PORT-RESERVATIONS.md
        if 'PORT-RESERVATIONS' in scanned_file.file_path.upper():
            found_port_reservations = True
            print(f"\n✓ FOUND PORT-RESERVATIONS.md:")
            print(f"  File Path: {scanned_file.file_path}")
            print(f"  Relative Path: {scanned_file.relative_path}")
            print(f"  File Type: {scanned_file.file_type}")
            print(f"  Size: {scanned_file.size_bytes} bytes")
            print(f"  Content Preview: {scanned_file.content[:200]}...")

    print(f"\n" + "=" * 80)
    print(f"SCAN COMPLETE: {total_files} files discovered")
    print("=" * 80)

    if not found_port_reservations:
        print("\n✗ PORT-RESERVATIONS.md was NOT discovered during scan")

        print(f"\nFound {len(root_md_files)} .md files in repository root:")
        for md_file in sorted(root_md_files)[:20]:  # Show first 20
            print(f"  - {md_file}")
        if len(root_md_files) > 20:
            print(f"  ... and {len(root_md_files) - 20} more")

if __name__ == "__main__":
    test_file_discovery()
