# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/version.py
# Description: CalVer version information for MyRAGDB. Standardized 2026-07-15 to the
#              cross-repo house style YYYY.MM.DD.N (4-part), per the normative Versioning
#              spec (~/.ai-dev-dotfiles/repo-specs/release-engineering/CLAUDE.md §1).
#              The repo-root VERSION file is the sole source of truth; this module reads it
#              in dev/source checkouts and falls back to _FALLBACK_VERSION when installed.
#              version-bump.py keeps _FALLBACK_VERSION, setup.py, and mcp_server in sync.
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04
# Last Updated: 2026-07-15
# Last Updated By: claude-opus-4-8 (versioning-rollout — TODO #122 §1)
#
# NOTE: the previous 6-part scheme (YYYY.MM.DD.MAJOR.MINOR.PATCH) was retired in favor of
# the 4-part standard. Same-day releases increment the final N; a new day resets N to 1.

from pathlib import Path

# Synced fallback (patched by version-bump.py via .versionbump.yaml) used when no repo-root
# VERSION file is reachable — e.g. when MyRAGDB is installed into site-packages.
_FALLBACK_VERSION = "2026.07.15.1"


def _read_version() -> str:
    """Return the CalVer version from the repo-root VERSION file when running from a
    source checkout, else the synced fallback. Only a VERSION file sitting next to a
    repo-root marker (setup.py / .git) is trusted, to avoid picking up a stray file."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        version_file = parent / "VERSION"
        if version_file.is_file() and (
            (parent / "setup.py").exists() or (parent / ".git").exists()
        ):
            text = version_file.read_text().strip()
            if text:
                return text
    return _FALLBACK_VERSION


# CalVer: YYYY.MM.DD.N  (year . month . day . same-day sequence)
__version__ = _read_version()
__version_info__ = tuple(int(p) for p in __version__.split(".") if p.isdigit())
# Build date is the YYYY-MM-DD prefix of the CalVer version.
_parts = __version__.split(".")
__build_date__ = "-".join(_parts[:3]) if len(_parts) >= 3 else __version__

# Release notes for the current version.
RELEASE_NOTES = f"""
MyRAGDB v{__version__} ({__build_date__})

Changes in v{__version__}:
- Standardized versioning to the cross-repo house style CalVer YYYY.MM.DD.N (4-part),
  retiring the prior YYYY.MM.DD.MAJOR.MINOR.PATCH scheme. The repo-root VERSION file is
  now the sole source of truth (read by this module); version-bump.py keeps setup.py and
  mcp_server in sync via .versionbump.yaml. See TODO #122 §1.

Historical notes (pre-standardization, 6-part scheme):
- v2026.01.06.2.28.0 — Aligned MCP middleware to official port 8093 (per port-registry.json).
- v2026.01.06.2.24.0 — Integrated MCP HTTP middleware into start.sh (automatic startup).
- v2026.01.06.2.22.0 — Integrated Meilisearch startup into start.sh (single-command startup).
- v2026.01.05.2.13.2 — Fixed lock/unlock button; implemented remove-repository endpoint.
- v2026.01.05.2.13.1 — Fixed keyword search 404; added asset cache busting.
- v2026.01.05.1.0.2 — Replaced Whoosh with Meilisearch 1.31.0; M4 Max indexing optimizations.

Features:
- Hybrid search combining Meilisearch keyword search and semantic vector search
- Independent parallel indexing for keyword and vector indexes
- Real-time indexing progress tracking with web UI
- Incremental and full rebuild indexing modes
- Repository-based file scanning and indexing; FastAPI backend with CORS

Technology Stack:
- Keyword: Meilisearch 1.31.0 (Rust-based, memory-mapped indexes)
- Vector: Sentence Transformers (all-MiniLM-L6-v2) + ChromaDB
- FastAPI REST API; vanilla JavaScript frontend

Version Format: CalVer YYYY.MM.DD.N
- YYYY.MM.DD: release date (zero-padded month/day)
- N: same-day release sequence (resets to 1 each new day)
"""
