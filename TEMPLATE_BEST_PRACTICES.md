# Template Best Practices Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/TEMPLATE_BEST_PRACTICES.md
**Description:** Best practices for designing and maintaining workflow templates
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Overview

Templates are pre-built workflow definitions that encapsulate common patterns. This guide explains how to design effective templates that are easy to use and maintain.

---

## Template Structure

### Basic Template

```yaml
# File: templates/my_template.yaml
# Description: Template description
# Author: Your Name
# Created: YYYY-MM-DD

name: "template_id"
description: "One-line human-readable description"
category: "search|analysis|reporting|custom"

# Define template parameters
parameters:
  param1:
    type: "string"
    required: true
    description: "What is param1 used for?"
  param2:
    type: "integer"
    required: false
    default: 10
    description: "Optional parameter with sensible default"

# Define workflow steps
steps:
  - skill: "skill_name"
    id: "step_id"
    description: "What does this step do?"
    input:
      skill_param: "{{ param1 }}"
      another_param: "{{ step_id.field }}"
    on_error: "continue"  # or null (stop on error)
```

### Key Components

1. **Name**: Unique identifier (lowercase, underscores)
2. **Description**: Clear one-line summary
3. **Category**: Organizational category
4. **Parameters**: User-configurable inputs
5. **Steps**: Workflow definition with skills

---

## Design Principles

### 1. Single Responsibility

Each template should focus on **one primary workflow**:

**✅ GOOD:**
- `code_search` - Search for code
- `code_search_and_analyze` - Search and analyze
- `security_audit` - Find and report security issues

**❌ BAD:**
- `do_everything` - Too many different purposes
- `generic_workflow` - Not specific enough
- `utility` - Unclear what it does

### 2. Clear Parameter Design

Parameters should be self-documenting:

```yaml
# ✅ GOOD - Clear, specific parameters
parameters:
  query:
    type: "string"
    required: true
    description: "Code search query (e.g., 'authentication flow')"
  result_limit:
    type: "integer"
    required: false
    default: 10
    description: "Maximum number of results to return"

# ❌ BAD - Vague, unclear parameters
parameters:
  q:
    type: "string"
  l:
    type: "integer"
```

### 3. Meaningful Step IDs

Step IDs enable variable interpolation:

```yaml
# ✅ GOOD - Descriptive step IDs
steps:
  - skill: "search"
    id: "find_auth_code"
    input:
      query: "authentication"

  - skill: "code_analysis"
    id: "analyze_auth"
    input:
      code: "{{ find_auth_code.results[0].snippet }}"

# ❌ BAD - Cryptic step IDs
steps:
  - skill: "search"
    id: "s1"
    input:
      query: "authentication"

  - skill: "code_analysis"
    id: "a1"
    input:
      code: "{{ s1.results[0].snippet }}"
```

### 4. Progressive Complexity

Start with simple templates, add complex ones:

**Level 1 - Simple (1-2 skills):**
```yaml
name: "basic_search"
steps:
  - skill: "search"
    input: {"query": "{{ query }}"}
```

**Level 2 - Chained (3-4 skills):**
```yaml
name: "search_and_analyze"
steps:
  - skill: "search"
    id: "search"
    input: {"query": "{{ query }}"}
  - skill: "code_analysis"
    id: "analyze"
    input: {"code": "{{ search.results[0].snippet }}"}
```

**Level 3 - Complex (5+ skills, branching):**
```yaml
name: "comprehensive_audit"
steps:
  - skill: "search"
    id: "find"
    input: {"query": "{{ query }}"}
  - skill: "code_analysis"
    id: "analyze"
    input: {"code": "{{ find.results[0].snippet }}"}
  - skill: "report"
    id: "report"
    input: {"data": "{{ analyze }}"}
```

---

## Common Patterns

### Pattern 1: Search → Report

Simple pattern for displaying search results:

```yaml
name: "search_and_report"
description: "Search and format results as report"
category: "reporting"

parameters:
  query:
    type: "string"
    required: true
    description: "Search query"
  limit:
    type: "integer"
    required: false
    default: 5

steps:
  - skill: "search"
    id: "search_results"
    input:
      query: "{{ query }}"
      limit: "{{ limit }}"

  - skill: "report"
    id: "format_results"
    input:
      title: "Search Results: {{ query }}"
      format: "markdown"
      content:
        - section: "Files Found"
          data:
            results: "{{ search_results.results }}"
```

### Pattern 2: Search → Analyze → Report

Multi-step analysis workflow:

```yaml
name: "search_analyze_report"
description: "Search, analyze, and report on findings"
category: "analysis"

parameters:
  query:
    type: "string"
    required: true
  language:
    type: "string"
    required: false
    default: "python"

steps:
  - skill: "search"
    id: "find_code"
    input:
      query: "{{ query }}"
      limit: 1

  - skill: "code_analysis"
    id: "analyze_code"
    input:
      code: "{{ find_code.results[0].snippet }}"
      language: "{{ language }}"
    on_error: "continue"

  - skill: "report"
    id: "report"
    input:
      title: "Analysis: {{ query }}"
      content:
        - section: "Found Code"
          data:
            results: "{{ find_code.results }}"
        - section: "Structure Analysis"
          data:
            structures: "{{ analyze_code.structures }}"
```

### Pattern 3: Multiple Searches

Searching multiple repositories or with different queries:

```yaml
name: "multi_search"
description: "Search with multiple queries or repositories"
category: "search"

parameters:
  primary_query:
    type: "string"
    required: true
  secondary_query:
    type: "string"
    required: true
  limit:
    type: "integer"
    required: false
    default: 5

steps:
  - skill: "search"
    id: "primary"
    input:
      query: "{{ primary_query }}"
      limit: "{{ limit }}"

  - skill: "search"
    id: "secondary"
    input:
      query: "{{ secondary_query }}"
      limit: "{{ limit }}"

  - skill: "report"
    id: "comparison"
    input:
      title: "Search Comparison"
      content:
        - section: "Results for {{ primary_query }}"
          data:
            results: "{{ primary.results }}"
        - section: "Results for {{ secondary_query }}"
          data:
            results: "{{ secondary.results }}"
```

### Pattern 4: Conditional with Error Handling

Handle failures gracefully:

```yaml
name: "robust_workflow"
description: "Workflow with error handling"
category: "analysis"

parameters:
  query:
    type: "string"
    required: true

steps:
  - skill: "search"
    id: "search"
    input:
      query: "{{ query }}"

  # This step fails gracefully if search finds nothing
  - skill: "code_analysis"
    id: "analyze"
    input:
      code: "{{ search.results[0].snippet }}"
    on_error: "continue"

  # Report always completes, even if analysis failed
  - skill: "report"
    id: "report"
    input:
      title: "Results"
      content:
        - section: "Search"
          data:
            results: "{{ search.results }}"
        - section: "Analysis (if available)"
          data:
            structures: "{{ analyze.structures }}"
```

---

## Design Checklist

### Clarity
- ✅ Template name is descriptive and unique
- ✅ Description clearly explains what template does
- ✅ Category accurately reflects template purpose
- ✅ Parameter descriptions are clear
- ✅ Step descriptions explain what each step does
- ✅ Step IDs are meaningful (not s1, s2, etc)

### Usability
- ✅ Required parameters are truly required
- ✅ Optional parameters have sensible defaults
- ✅ Parameter count is reasonable (3-5 ideal)
- ✅ Variables are interpolated clearly
- ✅ Error handling is appropriate
- ✅ Output format is useful

### Maintainability
- ✅ Template follows consistent formatting
- ✅ Comments explain complex logic
- ✅ No unused parameters or steps
- ✅ Skills used are documented elsewhere
- ✅ Dependencies are clear (e.g., search skill required)
- ✅ Template version is current

### Robustness
- ✅ Missing search results handled (on_error)
- ✅ Output format validates correctly
- ✅ Skill parameters match schemas
- ✅ Variable references are correct
- ✅ No infinite loops or circular dependencies
- ✅ Performance is acceptable

---

## Parameter Guidelines

### Required vs Optional

```yaml
# Use required when:
# - User must provide input for template to work
# - No reasonable default exists
parameters:
  query:
    type: "string"
    required: true
    description: "Code search query"

# Use optional when:
# - Sensible default exists
# - Most users can use default
# - Parameter refines behavior
parameters:
  limit:
    type: "integer"
    required: false
    default: 10
    description: "Maximum results (1-100)"
```

### Type Specification

```yaml
# String parameters
name:
  type: "string"
  description: "Free-form text"

# Integer parameters
limit:
  type: "integer"
  description: "Whole number"
  default: 10

# Boolean parameters
include_analysis:
  type: "boolean"
  description: "Whether to analyze results"
  default: false

# Array parameters
repositories:
  type: "array"
  description: "List of repository names"
  default: []

# Object parameters
filters:
  type: "object"
  description: "Complex filter specification"
  default: {}
```

---

## Variable Interpolation

### Basic Syntax

```yaml
# String interpolation
input:
  query: "{{ query }}"  # From parameter

# Step result access
input:
  code: "{{ search.results[0].snippet }}"  # From previous step

# Nested field access
input:
  data: "{{ step_id.field.nested }}"

# Array access
input:
  first: "{{ results[0] }}"
  last: "{{ results[-1] }}"
```

### Common Patterns

```yaml
# Use first search result for analysis
- skill: "code_analysis"
  input:
    code: "{{ search.results[0].snippet }}"

# Pass entire step result
- skill: "report"
  input:
    data: "{{ search }}"

# Aggregate multiple results
- skill: "report"
  input:
    content:
      - section: "Search 1"
        data:
          results: "{{ search1.results }}"
      - section: "Search 2"
        data:
          results: "{{ search2.results }}"
```

---

## Documentation Requirements

Each template should have:

1. **YAML Comment Header** (in template file):
   ```yaml
   # File: templates/my_template.yaml
   # Description: What the template does
   # Author: Your Name
   # Created: YYYY-MM-DD
   ```

2. **Template Metadata** (in YAML):
   ```yaml
   name: "my_template"
   description: "One-line human-readable description"
   category: "category"
   ```

3. **Parameter Documentation** (in YAML):
   ```yaml
   parameters:
     query:
       type: "string"
       required: true
       description: "Clear description of what query is used for"
   ```

4. **Usage Example** (in comments or separate doc):
   ```
   Usage:
   myragdb agent execute my_template --param query="authentication" --param limit=5
   ```

---

## Testing Templates

### Manual Testing

```bash
# Test template execution
myragdb agent execute template_id --param param1="value1"

# Test with JSON output
myragdb agent execute template_id --param param1="value1" --json

# Test from Python
result = await orchestrator.execute_request(
    "template_id",
    parameters={"param1": "value1"}
)
```

### Validation Checklist

- ✅ Template is valid YAML syntax
- ✅ All referenced skills exist
- ✅ All parameter references are correct
- ✅ Variable interpolation is correct
- ✅ Output format is valid
- ✅ Execution completes without errors
- ✅ Results are meaningful

---

## Performance Guidelines

### Efficient Templates

- Use 3-5 steps (not 10+)
- Limit search results (use sensible limit)
- Process only necessary results (take [0] not all)
- Avoid redundant searches (combine queries if possible)
- Use error handling to avoid bottlenecks

### Example - Efficient

```yaml
name: "efficient"
steps:
  # Only search for what we need
  - skill: "search"
    input:
      query: "{{ query }}"
      limit: 3  # Not 100

  # Only analyze first result
  - skill: "code_analysis"
    input:
      code: "{{ search.results[0].snippet }}"

  # Generate report from results
  - skill: "report"
    input:
      content: "{{ search.results }}"
```

### Example - Inefficient

```yaml
name: "inefficient"
steps:
  # Search for everything
  - skill: "search"
    input:
      query: "{{ query }}"
      limit: 100  # Too many

  # Analyze ALL results
  - skill: "code_analysis"
    input:
      code: "{{ search.results }}"  # Wrong - can't analyze array

  # Report on everything
  - skill: "report"
    input:
      content: "{{ search.results }}"  # Process all 100
```

---

## Organization

### Directory Structure

```
templates/
├── basic_code_search.yaml         # Simple search
├── search_and_analyze.yaml        # Search + analyze
├── search_analyze_report.yaml     # Search + analyze + report
├── multi_repo_search.yaml         # Multiple repositories
├── search_with_filters.yaml       # Advanced search options
├── pattern_detection.yaml         # Code pattern detection
├── security_audit.yaml            # Security analysis
└── README.md                      # Templates documentation
```

### Naming Convention

- Use `snake_case` for file and template names
- Start with action verb: `search_`, `analyze_`, `audit_`
- Include main subject: `_code`, `_security`, `_performance`
- Examples:
  - `search_code.yaml`
  - `analyze_patterns.yaml`
  - `audit_security.yaml`

---

## Versioning

Track template evolution:

```yaml
# Version 1.0 - Initial release
name: "my_template"
version: "1.0"
description: "Initial implementation"

# Later: Version 1.1 - Added optional parameter
# Update description and version
version: "1.1"
description: "Added support for custom languages"
```

---

## Template Examples

See `templates/` directory for complete examples:

1. **basic_code_search.yaml** - Simple search
2. **search_and_analyze.yaml** - Search + analysis
3. **search_analyze_report.yaml** - Full workflow
4. **multi_repo_search.yaml** - Multiple repositories
5. **search_with_filters.yaml** - Advanced filtering
6. **pattern_detection.yaml** - Pattern analysis
7. **security_audit.yaml** - Security auditing

---

## Migration Guide

When creating new templates:

1. Start with existing template that's closest
2. Modify parameters for your use case
3. Add/remove steps as needed
4. Test manually first
5. Document well
6. Create example workflows
7. Update this guide if introducing new pattern

---

## Troubleshooting

### Variable Not Interpolating

```yaml
# ❌ WRONG - Missing curly braces
input:
  code: search.results[0].snippet

# ✅ CORRECT - Proper syntax
input:
  code: "{{ search.results[0].snippet }}"
```

### Step Not Found

```yaml
# ❌ WRONG - Step ID typo
input:
  code: "{{ serch.results[0].snippet }}"  # typo: "serch"

# ✅ CORRECT - Exact step ID
input:
  code: "{{ search.results[0].snippet }}"
```

### Parameter Not Substituted

```yaml
# ❌ WRONG - Missing parameter reference
input:
  query: "hardcoded_value"

# ✅ CORRECT - Parameter reference
input:
  query: "{{ query }}"
```

---

## Best Practices Summary

1. **Focus**: One primary workflow per template
2. **Clarity**: Descriptive names, clear parameters
3. **Simplicity**: 3-5 steps, linear flow
4. **Documentation**: Comments, descriptions, examples
5. **Error Handling**: Graceful failure with on_error
6. **Performance**: Reasonable limits, efficient processing
7. **Testing**: Manual testing before deployment
8. **Maintainability**: Consistent formatting, versioning

---

For more information:
- See `AGENT_PLATFORM_QUICKSTART.md` for usage examples
- See `SKILL_DEVELOPMENT_GUIDE.md` for skill development
- Review `templates/` directory for template examples

Questions: libor@arionetworks.com
