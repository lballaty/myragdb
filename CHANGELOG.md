# Changelog

**File:** `CHANGELOG.md`
**Description:** Release changelog for MyRAGDB. Entries grouped by CalVer `YYYY.MM.DD.N`.
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-07-15
**Last Updated:** 2026-07-15
**Last Updated By:** claude-opus-4-8 (versioning-rollout plan)

Versioning follows CalVer `YYYY.MM.DD.N` per the normative Versioning spec
(`~/.ai-dev-dotfiles/repo-specs/release-engineering/CLAUDE.md` §1). The `VERSION`
file is the sole source of truth; embedded literals are declared in
`.versionbump.yaml` and patched by `version-bump.py`.

---

## 2026.07.15.1

- **Standardized versioning to the 4-part house style `YYYY.MM.DD.N`.** Retired the
  previous bespoke 6-part scheme (`YYYY.MM.DD.MAJOR.MINOR.PATCH`) in
  `src/myragdb/version.py`. The repo-root `VERSION` file is now the sole source of
  truth: `version.py` reads it in source checkouts and falls back to a synced literal
  when installed. Added `.versionbump.yaml` (declares `setup.py`, `mcp_server/__init__.py`,
  and the `version.py` fallback literals) and this changelog; aligned `setup.py` and
  `mcp_server` versions (were `0.1.0`) to the `VERSION` source of truth. Part of the
  global versioning rollout (TODO #122 §1).
