# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/cli/agent_commands.py
# Description: CLI commands for agent platform orchestration
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import asyncio
import json
import click
from typing import Optional
import yaml

from myragdb.agent.orchestration import AgentOrchestrator
from myragdb.agent.skills import SkillRegistry


# Global orchestrator instance (initialized on first use)
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or initialize the orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        registry = SkillRegistry()
        _orchestrator = AgentOrchestrator(skill_registry=registry)
    return _orchestrator


@click.group(name="agent")
def agent_cli():
    """Agent platform orchestration commands."""
    pass


# ==================== Execution Commands ====================

@agent_cli.command(name="execute")
@click.argument("request_type")
@click.option(
    "-p", "--param",
    multiple=True,
    help="Parameter in format KEY=VALUE (can be used multiple times)"
)
@click.option(
    "--json",
    is_flag=True,
    help="Output as JSON instead of formatted text"
)
def execute_template(request_type: str, param: tuple, json: bool):
    """
    Execute a template-based request.

    Business Purpose: Run pre-built workflows from the command line.

    Example:
        myragdb agent execute code_search --param query="authentication" --param limit=10
    """
    try:
        orchestrator = get_orchestrator()

        # Parse parameters
        parameters = {}
        for p in param:
            if "=" not in p:
                click.echo(f"Error: Parameter must be in format KEY=VALUE, got: {p}", err=True)
                raise click.Abort()
            key, value = p.split("=", 1)
            # Try to parse as JSON for proper types
            try:
                parameters[key] = json_module.loads(value)
            except:
                parameters[key] = value

        # Execute
        result = asyncio.run(
            orchestrator.execute_request(
                request_type=request_type,
                parameters=parameters
            )
        )

        # Output
        if json:
            click.echo(json_module.dumps(result, indent=2))
        else:
            click.echo(f"Status: {result['status']}")
            click.echo(f"Steps: {result['steps_completed']}/{result['total_steps']}")
            if result["status"] == "failed":
                click.echo(f"Error: {result['error']}", err=True)
            else:
                click.echo(f"Result: {json_module.dumps(result['result'], indent=2)}")

    except click.Abort:
        raise
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Exit(1)
    except Exception as e:
        click.echo(f"Error executing request: {str(e)}", err=True)
        raise click.Exit(1)


@agent_cli.command(name="workflow")
@click.argument("workflow_file", type=click.File("r"))
@click.option(
    "--json",
    is_flag=True,
    help="Output as JSON"
)
def execute_workflow(workflow_file, json: bool):
    """
    Execute a custom workflow from file.

    Business Purpose: Run custom workflows defined in YAML or JSON.

    Example:
        myragdb agent workflow my_workflow.yaml
    """
    try:
        orchestrator = get_orchestrator()

        # Load workflow
        content = workflow_file.read()
        if workflow_file.name.endswith(".json"):
            workflow = json_module.loads(content)
        else:
            workflow = yaml.safe_load(content)

        # Execute
        result = asyncio.run(
            orchestrator.execute_workflow(workflow)
        )

        # Output
        if json:
            click.echo(json_module.dumps(result, indent=2))
        else:
            click.echo(f"Workflow: {result['workflow_name']}")
            click.echo(f"Status: {result['status']}")
            click.echo(f"Steps: {result['steps_completed']}/{result['total_steps']}")
            if result["status"] == "failed":
                click.echo(f"Error: {result['error']}", err=True)
            else:
                click.echo(f"Result: {json_module.dumps(result['result'], indent=2)}")

    except Exception as e:
        click.echo(f"Error executing workflow: {str(e)}", err=True)
        raise click.Exit(1)


# ==================== Template Management Commands ====================

@agent_cli.command(name="templates")
def list_templates():
    """
    List all available workflow templates.

    Business Purpose: Show available pre-built workflows.
    """
    try:
        orchestrator = get_orchestrator()
        templates = orchestrator.list_available_templates()

        if not templates:
            click.echo("No templates available")
            return

        click.echo("Available Templates:")
        click.echo("=" * 80)
        for template in templates:
            click.echo(f"\nID: {template['id']}")
            click.echo(f"Name: {template['name']}")
            click.echo(f"Description: {template.get('description', 'N/A')}")
            click.echo(f"Steps: {template['step_count']}")
            if template.get("parameters"):
                click.echo(f"Parameters:")
                for param_name in template["parameters"]:
                    click.echo(f"  - {param_name}")

    except Exception as e:
        click.echo(f"Error listing templates: {str(e)}", err=True)
        raise click.Exit(1)


@agent_cli.command(name="template-info")
@click.argument("template_id")
def template_info(template_id: str):
    """
    Show detailed information about a template.

    Business Purpose: Display template schema and requirements.

    Example:
        myragdb agent template-info code_search
    """
    try:
        orchestrator = get_orchestrator()
        info = orchestrator.template_engine.get_template_info(template_id)

        click.echo(f"Template: {info['name']}")
        click.echo(f"Description: {info['description']}")
        click.echo(f"Category: {info.get('category', 'N/A')}")
        click.echo(f"\nSteps: {info['step_count']}")

        if info.get("parameters"):
            click.echo("\nParameters:")
            for param_name, param_spec in info["parameters"].items():
                click.echo(f"  {param_name}:")
                click.echo(f"    Type: {param_spec.get('type', 'unknown')}")
                click.echo(f"    Required: {param_spec.get('required', False)}")
                if "default" in param_spec:
                    click.echo(f"    Default: {param_spec['default']}")
                if "description" in param_spec:
                    click.echo(f"    Description: {param_spec['description']}")

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Exit(1)
    except Exception as e:
        click.echo(f"Error getting template info: {str(e)}", err=True)
        raise click.Exit(1)


@agent_cli.command(name="template-register")
@click.argument("template_file", type=click.File("r"))
@click.option(
    "-i", "--id",
    required=True,
    help="Template ID (used to reference template)"
)
def register_template(template_file, id: str):
    """
    Register a custom workflow template.

    Business Purpose: Add new reusable workflows.

    Example:
        myragdb agent template-register my_workflow.yaml --id my_workflow
    """
    try:
        orchestrator = get_orchestrator()

        # Load template
        content = template_file.read()
        if template_file.name.endswith(".json"):
            template = json_module.loads(content)
        else:
            template = yaml.safe_load(content)

        # Register
        orchestrator.template_engine.register_template(id, template)
        click.echo(f"✓ Template '{id}' registered successfully")

    except Exception as e:
        click.echo(f"Error registering template: {str(e)}", err=True)
        raise click.Exit(1)


# ==================== Skill Management Commands ====================

@agent_cli.command(name="skills")
def list_skills():
    """
    List all available skills.

    Business Purpose: Show available skill capabilities.
    """
    try:
        orchestrator = get_orchestrator()
        skills = orchestrator.list_available_skills()

        if not skills:
            click.echo("No skills available")
            return

        click.echo("Available Skills:")
        click.echo("=" * 80)
        for skill in skills:
            click.echo(f"\nName: {skill['name']}")
            click.echo(f"Description: {skill['description']}")

    except Exception as e:
        click.echo(f"Error listing skills: {str(e)}", err=True)
        raise click.Exit(1)


@agent_cli.command(name="skill-info")
@click.argument("skill_name")
def skill_info(skill_name: str):
    """
    Show detailed information about a skill.

    Business Purpose: Display skill schema and capabilities.

    Example:
        myragdb agent skill-info search
    """
    try:
        orchestrator = get_orchestrator()
        skill = orchestrator.skill_registry.get(skill_name)

        if not skill:
            click.echo(f"Error: Skill '{skill_name}' not found", err=True)
            raise click.Exit(1)

        info = skill.get_info()

        click.echo(f"Skill: {info.name}")
        click.echo(f"Description: {info.description}")

        click.echo("\nInput Schema:")
        click.echo(json_module.dumps(info.input_schema, indent=2))

        click.echo("\nOutput Schema:")
        click.echo(json_module.dumps(info.output_schema, indent=2))

    except click.Exit:
        raise
    except Exception as e:
        click.echo(f"Error getting skill info: {str(e)}", err=True)
        raise click.Exit(1)


# ==================== Orchestrator Info Commands ====================

@agent_cli.command(name="info")
def orchestrator_info():
    """
    Show orchestrator information and capabilities.

    Business Purpose: Display available platform resources.
    """
    try:
        orchestrator = get_orchestrator()
        info = orchestrator.get_orchestrator_info()

        click.echo("Agent Platform Information:")
        click.echo("=" * 80)
        click.echo(f"Total Skills: {info['total_skills']}")
        click.echo(f"Total Templates: {info['total_templates']}")
        click.echo(f"Session Manager: {'✓' if info['has_session_manager'] else '✗'}")
        click.echo(f"Search Engine: {'✓' if info['has_search_engine'] else '✗'}")

        if info['available_skills']:
            click.echo(f"\nAvailable Skills ({len(info['available_skills'])}):")
            for skill_name in info['available_skills']:
                click.echo(f"  - {skill_name}")

        if info['available_templates']:
            click.echo(f"\nAvailable Templates ({len(info['available_templates'])}):")
            for template_id in info['available_templates']:
                click.echo(f"  - {template_id}")

    except Exception as e:
        click.echo(f"Error getting orchestrator info: {str(e)}", err=True)
        raise click.Exit(1)


# Import json module at module level to avoid name conflict with parameter
import json as json_module
