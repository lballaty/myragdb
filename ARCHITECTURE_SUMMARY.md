# Complete Architecture Summary
**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/ARCHITECTURE_SUMMARY.md
**Description:** One-page executive summary of the entire agent platform architecture
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## What You're Building: The Big Picture

Transform **MyRAGDB** from a search service into an **extensible agent platform** for your workshop/book.

---

## Three Core Additions

### 1. CLOUD LLM SUPPORT ☁️
Switch between local & cloud LLMs (Gemini, ChatGPT, Claude) **without restart**

**Three Auth Methods:**
- **API Key**: Paste key → Use immediately (simplest)
- **OAuth/Subscription**: Enterprise auth with auto-refresh (production pattern)
- **CLI Device Code**: Headless/automation workflows (CI/CD friendly)

**Key Component:** `SessionManager` - tracks active LLM, enables switching

---

### 2. AGENT ORCHESTRATION 🤖
Route user queries to pre-built workflows or ask LLM to plan

**Two Execution Paths:**
1. **Template Match** (Deterministic - no LLM needed)
   - User query → Find matching template → Execute directly → Return result

2. **No Template** (Adaptive - LLM plans)
   - User query → Ask LLM "which skills do we need?" → Validate plan → Execute

**Key Components:** `AgentOrchestrator`, `WorkflowEngine`, `TemplateEngine`

---

### 3. EXTENSIBLE SKILLS FRAMEWORK 🔧
Standardized interface for capabilities - easy to add new ones

**Built-in Skills:**
- `SearchSkill`: Query codebase (supports both repos + directories)
- `SQLSkill`: Query databases (Supabase, PostgreSQL, etc)
- `ReportSkill`: Generate formatted reports
- `CodeAnalysisSkill`: Parse and analyze code
- `LLMSkill`: Call LLM for reasoning/summarization

**Add Custom Skills:** Just implement the `Skill` interface

**Key Component:** `SkillRegistry` - discovers and manages skills

---

## Example: Complete Workflow (No Code Restart Needed)

```
User Query: "Find authentication bugs and generate security report"

Step 1: Switch LLM (Web UI)
├─ Select: Claude (Cloud)
├─ Auth: Paste API key
└─ Click Switch → Session updated instantly ✓

Step 2: Execute Agent Workflow (CLI or UI)
├─ Query: "Find authentication bugs and generate security report"
├─ AgentOrchestrator: Find matching template
├─ Template: "security-audit"
└─ Execute steps:

   SearchSkill("authentication bugs")
   ↓ Returns: 20 security-related files

   CodeAnalysisSkill(files)
   ↓ Returns: 3 vulnerability findings

   ReportSkill(findings)
   ↓ Returns: Markdown report

   LLMSkill("Summarize findings") ← Uses active Claude session
   ↓ Returns: Executive summary

Step 3: Result
├─ Security audit report
├─ Executive summary
├─ Execution trace showing all steps
└─ No server restart required ✓
```

---

## Architecture Layers

```
PRESENTATION LAYER
├─ Web UI (LLM Chat Tester + Agent UI)
├─ CLI (llm commands + agent commands)
└─ Agent Library (SDK for programmatic access)

ORCHESTRATION LAYER (NEW)
├─ AgentOrchestrator (routes queries)
├─ WorkflowEngine (executes multi-step workflows)
├─ TemplateEngine (template matching + creation)
└─ SkillRegistry (skill discovery + management)

SKILLS LAYER (NEW)
├─ Skill Base Class (abstract interface)
└─ Built-in Skills: Search, SQL, Report, CodeAnalysis, LLM

LLM LAYER (ENHANCED)
├─ SessionManager (track active LLM, no restart switching)
├─ ProviderRegistry (local + cloud providers)
├─ Cloud Providers: Gemini, ChatGPT, Claude
└─ Auth Management: API key, OAuth, CLI device code

SEARCH & DATA LAYER (EXISTING - UNCHANGED)
├─ HybridSearchEngine (Meilisearch + ChromaDB)
├─ RepositoryIndexer
├─ DirectoryIndexer (from other agent)
└─ FileMetadataDB
```

---

## Workflow Templates (Deterministic Execution)

Pre-built workflows that run **without LLM overhead**

```yaml
# Example: code-security-audit.yaml
steps:
  - SearchSkill: Find security-related code
  - CodeAnalysisSkill: Analyze for vulnerabilities
  - ReportSkill: Generate findings report
  - LLMSkill: Create executive summary
```

**Users can:**
- ✅ Run pre-built templates by name
- ✅ Create custom templates (YAML)
- ✅ Modify templates for their use case

---

## Database Changes: Minimal & Non-Breaking

```
EXISTING (Unchanged):
├─ search_results
├─ file_metadata
├─ repositories
└─ observability data

NEW (Agent Platform):
├─ llm_sessions (track active LLM)
├─ workflow_templates (user-created templates)
├─ workflow_executions (execution history)
└─ agent_skills (skill registry snapshots)

Note: Directories feature adds separate tables (not agent platform)
```

---

## API Endpoints: Clean Separation

```
EXISTING (Unchanged):
POST /search/hybrid
POST /search/keyword
GET  /repositories
POST /index
[all existing search endpoints work as-is]

NEW - LLM Control:
GET  /llm/session                    → Current active LLM
POST /llm/switch                     → Change LLM (no restart)
POST /llm/validate-credentials
POST /llm/logout

NEW - Agent Orchestration:
POST /agent/execute                  → Run query (template or LLM-planned)
GET  /agent/templates                → List templates
POST /agent/templates                → Create custom template

NEW - Skills Discovery:
GET  /skills                         → List all available skills
GET  /skills/{name}                  → Get skill details/schema
```

---

## CLI Commands: New + Enhanced

```
EXISTING (Work as-is):
python -m myragdb.cli search "query"
python -m myragdb.cli index

NEW - LLM Session:
python -m myragdb.cli llm login gemini --method api_key
python -m myragdb.cli llm switch claude --model claude-3-opus
python -m myragdb.cli llm status

NEW - Agent Execution:
python -m myragdb.cli agent execute "Find security bugs"
python -m myragdb.cli agent run-template security-audit
python -m myragdb.cli agent templates list
```

---

## Integration with Directories Feature ✅

**Status:** ZERO CONFLICTS - Works perfectly together

**Directory Feature** (Other agent):
- Index arbitrary directories (not just git repos)
- New search filtering for directories

**Agent Platform:**
- SearchSkill already supports directories (just add optional parameter)
- Templates can specify which directories to search

**Result:** Agents can analyze custom directories automatically

**Integration Effort:** ~2 hours (just add directories parameter to SearchSkill)

---

## Why Perfect for Your Workshop/Book

### 1. **Three Auth Method Examples**
- Shows API key usage (simplest)
- Shows OAuth flow (enterprise pattern)
- Shows CLI device code (automation pattern)

### 2. **Agent Architecture from First Principles**
- Deterministic + adaptive routing
- Skill abstraction layer
- Template composition
- Multi-step workflows

### 3. **Real-World Patterns**
- Session management (state in cloud apps)
- Provider abstraction (multi-vendor strategies)
- Extensible frameworks (building platforms)
- Modular architecture (no tight coupling)

### 4. **Complete Stack**
- LLM integration (bottom layer)
- Agent orchestration (middle layer)
- Workflow automation (top layer)
- Students learn FULL architecture

### 5. **Hands-On Learning**
- Switch LLM → See immediate effect
- Create skill → Add to registry
- Build template → Run workflow
- All changes visible, testable

---

## Implementation Timeline

### Week 1-2: LLM Layer
- SessionManager (track active LLM)
- ProviderRegistry (abstract local + cloud)
- Three auth methods (API key, OAuth, CLI)
- **Deliverable:** Switch between cloud LLMs without restart

### Week 2-3: Skills Framework
- Skill base class
- 5 built-in skills (Search, SQL, Report, CodeAnalysis, LLM)
- SkillRegistry
- **Deliverable:** Basic skills working independently

### Week 3-4: Orchestration
- WorkflowEngine (multi-step execution)
- TemplateEngine (template matching)
- AgentOrchestrator (main router)
- **Deliverable:** Execute template-based workflows

### Week 4-5: Templates & UI
- 10+ example templates (YAML)
- Agent execution UI
- Template builder
- **Deliverable:** Users can run/create workflows

### Week 5-6: Workshop Content
- Tutorials & documentation
- Example notebooks
- Book chapters
- **Deliverable:** Workshop-ready materials

---

## Breaking Changes: NONE ✅

All existing MyRAGDB functionality works **exactly as before**:
- ✅ Search API unchanged
- ✅ Local LLM management unchanged
- ✅ Indexing unchanged
- ✅ Repository management unchanged
- ✅ CLI commands work as-is

**New features are purely additive** - no modifications to existing code paths.

---

## Key Design Principles

1. **Deterministic-First:** Templates run without LLM when possible
2. **LLM as Orchestrator:** Use LLM only for planning/reasoning
3. **Extensible Skills:** Easy to add new capabilities
4. **Zero Restarts:** Session-based switching, not process-based
5. **Minimal Changes:** Don't break existing system
6. **Workshop-Ready:** Complete, teachable, understandable

---

## Success Criteria

✅ Cloud LLMs (Gemini, ChatGPT, Claude) integrated with 3 auth methods
✅ Switch between LLMs without restart
✅ Agent orchestration working (templates + LLM planning)
✅ 5+ built-in skills available
✅ Users can create custom skills
✅ Users can create custom templates
✅ Complete workshop/book materials
✅ Integration with directories feature seamless
✅ All existing MyRAGDB functionality preserved
✅ Zero breaking changes

---

## Recommended Next Steps

1. **Approve this architecture**
2. **Start implementation Week 1:** LLM layer
3. **Week 2-3:** Skills framework in parallel with directories team
4. **Week 4-5:** Integrate features + build UI
5. **Week 5-6:** Workshop content + finalization

---

**Ready to proceed with implementation?**

Questions: libor@arionetworks.com
