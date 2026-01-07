# Skill Development Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/SKILL_DEVELOPMENT_GUIDE.md
**Description:** Complete guide for developing custom skills for the agent platform
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Overview

Skills are the fundamental building blocks of the agent platform. They encapsulate specific capabilities that can be composed into workflows. This guide explains how to create, test, and integrate custom skills.

---

## Skill Architecture

### Base Skill Class

All skills inherit from the `Skill` base class:

```python
from myragdb.agent.skills import Skill

class YourSkill(Skill):
    def __init__(self):
        super().__init__(
            name="your_skill",
            description="Clear description of what this skill does"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Define input parameters and their types."""
        return {
            "param1": {
                "type": "string",
                "required": True,
                "description": "What is param1 used for?"
            },
            "param2": {
                "type": "integer",
                "required": False,
                "default": 10,
                "description": "Optional parameter with default"
            }
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        """Define output structure."""
        return {
            "result": {
                "type": "string",
                "description": "The skill result"
            },
            "metadata": {
                "type": "object",
                "description": "Optional metadata about execution"
            }
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the skill with given input.

        Must validate input against input_schema and return dict matching output_schema.
        """
        # Validate required parameters
        if "param1" not in input_data:
            raise SkillExecutionError("param1 is required")

        param1 = input_data["param1"]
        param2 = input_data.get("param2", 10)

        # Perform skill logic
        result = f"Processed {param1} with param2={param2}"

        return {
            "result": result,
            "metadata": {
                "param1": param1,
                "param2": param2
            }
        }
```

### Key Requirements

1. **Name**: Must be unique, lowercase, and match the file name
2. **Description**: Clear, one-sentence description of functionality
3. **Input Schema**: JSON schema defining parameters and types
4. **Output Schema**: JSON schema defining return structure
5. **Execute Method**: Async method implementing the skill logic

---

## Step 1: Define Your Skill

### 1.1 Choose a Purpose

Skills should be focused on a single capability:

- ✅ **Good**: `TextAnalysisSkill` - Analyzes text for sentiment, entities, etc.
- ✅ **Good**: `DatabaseQuerySkill` - Executes and formats database queries
- ❌ **Bad**: `GenericUtilitySkill` - Does too many different things
- ❌ **Bad**: `DoEverythingSkill` - Not focused on a single capability

### 1.2 Design Input/Output

Think about the data contract:

```python
# Clear input schema
input_schema = {
    "text": {
        "type": "string",
        "required": True,
        "description": "Text to analyze"
    },
    "language": {
        "type": "string",
        "required": False,
        "default": "english",
        "description": "Language code (english, spanish, french)"
    }
}

# Clear output schema
output_schema = {
    "sentiment": {
        "type": "string",
        "description": "positive, negative, or neutral"
    },
    "confidence": {
        "type": "number",
        "description": "Confidence score 0.0-1.0"
    },
    "entities": {
        "type": "array",
        "description": "Extracted named entities"
    }
}
```

---

## Step 2: Implement the Skill

### 2.1 File Structure

```
src/myragdb/agent/skills/
├── __init__.py
├── base.py                    # Skill base class
├── your_custom_skill.py      # Your new skill
└── registry.py               # SkillRegistry
```

### 2.2 Implement Execute Method

```python
async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute skill with input data.

    Business Purpose: Provide specific capability to workflow.

    Args:
        input_data: Dictionary matching input_schema

    Returns:
        Dictionary matching output_schema

    Raises:
        SkillExecutionError: If execution fails
    """
    try:
        # 1. Validate input
        if "text" not in input_data:
            raise SkillExecutionError("text parameter is required")

        text = input_data["text"]
        language = input_data.get("language", "english")

        # 2. Process
        sentiment = await self._analyze_sentiment(text, language)
        confidence = await self._calculate_confidence(text, sentiment)
        entities = await self._extract_entities(text, language)

        # 3. Return structured result
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "entities": entities
        }

    except Exception as e:
        raise SkillExecutionError(f"Sentiment analysis failed: {str(e)}")
```

### 2.3 Error Handling

```python
from myragdb.agent.skills import SkillExecutionError

async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Validate required inputs
        required_fields = ["field1", "field2"]
        for field in required_fields:
            if field not in input_data:
                raise SkillExecutionError(f"Missing required field: {field}")

        # Validate field types/formats
        if not isinstance(input_data["field1"], str):
            raise SkillExecutionError("field1 must be a string")

        # Process with error handling
        try:
            result = await self._process(input_data)
        except TimeoutError:
            raise SkillExecutionError("Processing timed out after 30 seconds")
        except ConnectionError as e:
            raise SkillExecutionError(f"Connection failed: {e}")

        return result

    except SkillExecutionError:
        # Re-raise skill execution errors
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise SkillExecutionError(f"Unexpected error: {str(e)}")
```

---

## Step 3: Write Tests

### 3.1 Test Structure

```python
import pytest
from myragdb.agent.skills import YourSkill, SkillExecutionError

class TestYourSkill:
    """Test YourSkill functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.skill = YourSkill()

    @pytest.mark.asyncio
    async def test_basic_execution(self):
        """Test basic skill execution."""
        result = await self.skill.execute({
            "param1": "test",
            "param2": 5
        })

        assert "result" in result
        assert result["param2"] == 5

    @pytest.mark.asyncio
    async def test_missing_required_parameter(self):
        """Test that missing required parameter raises error."""
        with pytest.raises(SkillExecutionError):
            await self.skill.execute({"param2": 5})

    @pytest.mark.asyncio
    async def test_optional_parameter_default(self):
        """Test that optional parameters use defaults."""
        result = await self.skill.execute({"param1": "test"})
        # param2 should default to 10
        assert result.get("param2") == 10
```

### 3.2 Run Tests

```bash
# Activate venv
source venv/bin/activate

# Run specific test file
pytest tests/test_your_skill.py -v

# Run specific test
pytest tests/test_your_skill.py::TestYourSkill::test_basic_execution -v

# Run with coverage
pytest tests/test_your_skill.py --cov=src/myragdb/agent/skills
```

---

## Step 4: Register and Use

### 4.1 Register with SkillRegistry

```python
from myragdb.agent.skills import SkillRegistry
from myragdb.agent.skills.your_custom_skill import YourSkill

# Create registry
registry = SkillRegistry()

# Register skill
skill = YourSkill()
registry.register_skill(skill)

# Verify registration
assert registry.has_skill("your_skill")
```

### 4.2 Use in Workflows

```python
workflow = {
    "name": "my_workflow",
    "steps": [
        {
            "skill": "your_skill",
            "id": "step1",
            "input": {
                "param1": "hello",
                "param2": 5
            }
        }
    ]
}

result = await orchestrator.execute_workflow(workflow)
```

---

## Best Practices

### 1. Schema Design

**DO:**
- ✅ Use clear, descriptive parameter names
- ✅ Document each parameter with description
- ✅ Specify types accurately (string, integer, array, object)
- ✅ Mark required vs optional clearly
- ✅ Provide sensible defaults for optional parameters

**DON'T:**
- ❌ Use ambiguous names (data, result, value)
- ❌ Mix multiple types in one parameter
- ❌ Require too many parameters (aim for 3-5)
- ❌ Return inconsistent output structure

### 2. Error Handling

**DO:**
- ✅ Validate all inputs before processing
- ✅ Provide clear error messages
- ✅ Catch specific exceptions, not generic Exception
- ✅ Clean up resources (files, connections) even on error
- ✅ Use SkillExecutionError for workflow integration

**DON'T:**
- ❌ Silently ignore errors
- ❌ Return error in result (use exceptions)
- ❌ Leave resources open after error
- ❌ Wrap errors without context

### 3. Performance

**DO:**
- ✅ Make execute() async if I/O involved
- ✅ Add timeouts for external calls
- ✅ Cache expensive computations if appropriate
- ✅ Profile and optimize hot paths
- ✅ Document performance characteristics

**DON'T:**
- ❌ Perform blocking operations in async code
- ❌ Load large files entirely into memory
- ❌ Make unbounded network requests
- ❌ Recalculate same result repeatedly

### 4. Documentation

**DO:**
- ✅ Include file header with purpose
- ✅ Document execute() method with business purpose
- ✅ Add examples in docstrings
- ✅ Document edge cases and limitations
- ✅ Include sample input/output

**DON'T:**
- ❌ Assume readers know what skill does
- ❌ Omit examples
- ❌ Leave edge cases undocumented
- ❌ Use cryptic variable names

### 5. Composition

**DO:**
- ✅ Design skills to be independently useful
- ✅ Support parameter substitution in workflows
- ✅ Return data that other skills can use
- ✅ Handle partial input gracefully

**DON'T:**
- ❌ Create skills that only work in specific workflows
- ❌ Assume skills execute in specific order
- ❌ Make skills too generic (jack of all trades)
- ❌ Create circular dependencies

---

## Example: Text Analysis Skill

Complete example of a well-designed skill:

```python
# File: src/myragdb/agent/skills/text_analysis_skill.py
# Description: Analyze text for sentiment, entities, and key phrases
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from myragdb.agent.skills import Skill, SkillExecutionError
from typing import Dict, Any, List
import asyncio


class TextAnalysisSkill(Skill):
    """
    Analyze text for sentiment, entities, and key phrases.

    Business Purpose: Provide automated text analysis capabilities for
    understanding document content, extracting insights, and categorizing text.
    """

    def __init__(self):
        super().__init__(
            name="text_analysis",
            description="Analyze text for sentiment, entities, and key phrases"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "text": {
                "type": "string",
                "required": True,
                "description": "Text to analyze"
            },
            "language": {
                "type": "string",
                "required": False,
                "default": "english",
                "description": "Language code (english, spanish, french)"
            },
            "analysis_type": {
                "type": "string",
                "required": False,
                "default": "all",
                "description": "Type of analysis: sentiment, entities, keywords, all"
            }
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "sentiment": {
                "type": "string",
                "description": "positive, negative, or neutral"
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score 0.0-1.0"
            },
            "entities": {
                "type": "array",
                "description": "Extracted named entities with types"
            },
            "keywords": {
                "type": "array",
                "description": "Key phrases extracted from text"
            }
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze text content.

        Business Purpose: Extract insights from text for understanding
        document meaning and content classification.

        Args:
            input_data: Dictionary with text and analysis options

        Returns:
            Analysis results with sentiment, entities, keywords

        Example:
            result = await skill.execute({
                "text": "The product is amazing!",
                "analysis_type": "sentiment"
            })
            # Returns: {"sentiment": "positive", "confidence": 0.95, ...}
        """
        try:
            # Validate input
            if "text" not in input_data:
                raise SkillExecutionError("text parameter is required")

            text = input_data["text"]
            if not text.strip():
                raise SkillExecutionError("text cannot be empty")

            language = input_data.get("language", "english")
            analysis_type = input_data.get("analysis_type", "all")

            # Perform analysis
            result = {
                "sentiment": None,
                "confidence": 0.0,
                "entities": [],
                "keywords": []
            }

            if analysis_type in ["sentiment", "all"]:
                sentiment, confidence = await self._analyze_sentiment(text, language)
                result["sentiment"] = sentiment
                result["confidence"] = confidence

            if analysis_type in ["entities", "all"]:
                result["entities"] = await self._extract_entities(text, language)

            if analysis_type in ["keywords", "all"]:
                result["keywords"] = await self._extract_keywords(text)

            return result

        except SkillExecutionError:
            raise
        except Exception as e:
            raise SkillExecutionError(f"Text analysis failed: {str(e)}")

    async def _analyze_sentiment(self, text: str, language: str) -> tuple:
        """Analyze text sentiment."""
        # Simplified implementation for example
        positive_words = ["good", "great", "amazing", "excellent", "love"]
        negative_words = ["bad", "terrible", "awful", "hate", "poor"]

        text_lower = text.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)

        if pos_count > neg_count:
            return "positive", min(0.95, 0.5 + (pos_count * 0.1))
        elif neg_count > pos_count:
            return "negative", min(0.95, 0.5 + (neg_count * 0.1))
        else:
            return "neutral", 0.5

    async def _extract_entities(self, text: str, language: str) -> List[Dict]:
        """Extract named entities."""
        # Simplified implementation for example
        return [
            {"text": "example entity", "type": "organization"}
        ]

    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract key phrases."""
        # Simplified implementation for example
        words = text.split()
        return [w for w in words if len(w) > 5]
```

---

## Common Patterns

### Pattern 1: Input Validation

```python
async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    # Check required fields
    required = ["field1", "field2"]
    for field in required:
        if field not in input_data:
            raise SkillExecutionError(f"Missing required field: {field}")

    # Validate types
    if not isinstance(input_data["field1"], str):
        raise SkillExecutionError("field1 must be a string")

    # Validate ranges
    limit = input_data.get("limit", 10)
    if limit < 1 or limit > 1000:
        raise SkillExecutionError("limit must be between 1 and 1000")
```

### Pattern 2: Async Resource Management

```python
async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    connection = None
    try:
        # Open resource
        connection = await self._create_connection()

        # Use resource
        result = await connection.query(input_data["sql"])

        return {"results": result}

    finally:
        # Always clean up
        if connection:
            await connection.close()
```

### Pattern 3: Fallback Behavior

```python
async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    # Try preferred method
    try:
        result = await self._method_a(input_data)
    except Exception as e:
        # Fall back to alternative
        try:
            result = await self._method_b(input_data)
        except Exception as e:
            raise SkillExecutionError(f"All methods failed: {str(e)}")

    return result
```

---

## Testing Checklist

- ✅ All required parameters are validated
- ✅ Optional parameters use correct defaults
- ✅ Error cases raise SkillExecutionError
- ✅ Output matches output_schema
- ✅ Async operations work correctly
- ✅ Resource cleanup happens on error
- ✅ Performance is acceptable
- ✅ Edge cases are handled

---

## Next Steps

1. Create your skill file following the template
2. Write unit tests
3. Register with SkillRegistry
4. Create workflow templates using your skill
5. Test in actual workflow execution
6. Document with examples

For more information:
- See `src/myragdb/agent/skills/` for built-in skill examples
- Check `AGENT_PLATFORM_QUICKSTART.md` for usage examples
- Review `tests/test_agent_platform.py` for test patterns

Questions: libor@arionetworks.com
