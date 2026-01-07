# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/cli/auth_commands.py
# Description: CLI commands for authentication management
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import click
import json
import webbrowser
from typing import Optional
from rich import print as rprint
from rich.table import Table
from rich.panel import Panel

from myragdb.auth import AuthenticationManager


# Global auth manager instance
_auth_manager: Optional[AuthenticationManager] = None


def get_auth_manager() -> AuthenticationManager:
    """Get or initialize the auth manager."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthenticationManager()
    return _auth_manager


@click.group(name="auth")
def auth_cli():
    """Authentication and credential management commands."""
    pass


# ==================== API Key Commands ====================

@auth_cli.group(name="api-key")
def api_key_cli():
    """Manage API key credentials."""
    pass


@api_key_cli.command(name="add")
@click.option(
    "-p", "--provider",
    required=True,
    type=click.Choice(["claude", "gpt", "gemini"], case_sensitive=False),
    help="LLM provider"
)
@click.option(
    "-k", "--key",
    prompt=True,
    hide_input=True,
    help="API key (will be hidden on input)"
)
@click.option(
    "-d", "--description",
    default="",
    help="Optional description for this key"
)
@click.option(
    "--default",
    is_flag=True,
    default=True,
    help="Set as default for provider [default: True]"
)
def add_api_key(provider: str, key: str, description: str, default: bool):
    """
    Add a new API key credential.

    Business Purpose: Store API key for direct authentication with LLM providers.
    Keys are stored securely in ~/.myragdb/keys/

    Example:
        myragdb auth api-key add --provider claude --description "Production key"
        Enter API key: (hidden input)
    """
    auth_manager = get_auth_manager()
    provider = provider.lower()

    rprint("[yellow]Adding API key credential...[/yellow]")

    credential = auth_manager.authenticate_with_api_key(
        provider=provider,
        api_key=key,
        description=description,
        set_as_default=default,
    )

    if credential:
        rprint("[green]✓ API key credential added successfully[/green]")
        rprint(f"[cyan]ID:[/cyan] {credential.credential_id}")
        rprint(f"[cyan]Provider:[/cyan] {credential.provider}")
        rprint(f"[cyan]Default:[/cyan] {'Yes' if credential.is_default else 'No'}")
    else:
        rprint("[red]✗ Failed to add API key credential[/red]")
        raise click.Abort()


@api_key_cli.command(name="list")
@click.option(
    "-p", "--provider",
    type=click.Choice(["claude", "gpt", "gemini"], case_sensitive=False),
    help="Filter by provider"
)
@click.option(
    "--json",
    is_flag=True,
    help="Output as JSON"
)
def list_api_keys(provider: Optional[str], json_output: bool):
    """
    List all stored API key credentials.

    Example:
        myragdb auth api-key list
        myragdb auth api-key list --provider claude
    """
    auth_manager = get_auth_manager()
    provider = provider.lower() if provider else None

    credentials = auth_manager.list_api_key_credentials(provider)

    if json_output:
        data = [
            {
                "id": c.credential_id,
                "provider": c.provider,
                "default": c.is_default,
            }
            for c in credentials
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        if not credentials:
            rprint("[yellow]No API key credentials found[/yellow]")
            return

        table = Table(title="API Key Credentials")
        table.add_column("ID", style="cyan")
        table.add_column("Provider", style="magenta")
        table.add_column("Default", style="green")

        for cred in credentials:
            table.add_row(
                cred.credential_id,
                cred.provider,
                "✓" if cred.is_default else ""
            )

        rprint(table)
        rprint(f"\n[cyan]Total:[/cyan] {len(credentials)} credentials")


@api_key_cli.command(name="remove")
@click.argument("credential_id")
@click.confirmation_option(prompt="Are you sure you want to delete this credential?")
def remove_api_key(credential_id: str):
    """
    Delete an API key credential.

    Example:
        myragdb auth api-key remove claude-abc12345
    """
    auth_manager = get_auth_manager()

    if auth_manager.delete_credential(credential_id):
        rprint("[green]✓ API key credential deleted[/green]")
    else:
        rprint(f"[red]✗ Credential not found: {credential_id}[/red]")
        raise click.Abort()


# ==================== OAuth Commands ====================

@auth_cli.group(name="oauth")
def oauth_cli():
    """Manage OAuth credentials."""
    pass


@oauth_cli.command(name="login")
@click.option(
    "-p", "--provider",
    required=True,
    type=click.Choice(["claude", "gpt", "gemini"], case_sensitive=False),
    help="LLM provider"
)
@click.option(
    "--no-browser",
    is_flag=True,
    help="Don't automatically open browser"
)
def oauth_login(provider: str, no_browser: bool):
    """
    Login via OAuth with a provider.

    Business Purpose: Authenticate using web-based OAuth flow.
    Provides secure authentication without exposing API keys.

    Example:
        myragdb auth oauth login --provider claude
    """
    auth_manager = get_auth_manager()
    provider = provider.lower()

    rprint(f"[yellow]Initiating OAuth flow for {provider}...[/yellow]")

    auth_url = auth_manager.initiate_oauth(provider)

    if not auth_url:
        rprint(f"[red]✗ Failed to initiate OAuth[/red]")
        raise click.Abort()

    rprint(f"[green]✓ Authorization URL generated[/green]")
    rprint(f"\n[cyan]Authorization URL:[/cyan]")
    rprint(f"[blue]{auth_url}[/blue]")

    if not no_browser:
        try:
            webbrowser.open(auth_url)
            rprint("\n[yellow]Browser should open automatically...[/yellow]")
        except Exception as e:
            rprint(f"[yellow]Could not open browser: {e}[/yellow]")

    rprint("\n[cyan]After authorizing, you will receive an authorization code.[/cyan]")
    auth_code = click.prompt("Enter authorization code")

    rprint("[yellow]Completing OAuth flow...[/yellow]")

    credential = auth_manager.complete_oauth(
        provider=provider,
        auth_code=auth_code,
    )

    if credential:
        rprint("[green]✓ OAuth login successful[/green]")
        rprint(f"[cyan]ID:[/cyan] {credential.credential_id}")
        rprint(f"[cyan]Provider:[/cyan] {credential.provider}")
    else:
        rprint("[red]✗ OAuth login failed[/red]")
        raise click.Abort()


@oauth_cli.command(name="list")
@click.option(
    "-p", "--provider",
    type=click.Choice(["claude", "gpt", "gemini"], case_sensitive=False),
    help="Filter by provider"
)
@click.option(
    "--json",
    is_flag=True,
    help="Output as JSON"
)
def list_oauth_credentials(provider: Optional[str], json_output: bool):
    """
    List all OAuth credentials.

    Example:
        myragdb auth oauth list
        myragdb auth oauth list --provider claude
    """
    auth_manager = get_auth_manager()
    provider = provider.lower() if provider else None

    credentials = auth_manager.list_oauth_credentials(provider)

    if json_output:
        data = [
            {
                "id": c.credential_id,
                "provider": c.provider,
                "identifier": c.identifier,
                "default": c.is_default,
            }
            for c in credentials
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        if not credentials:
            rprint("[yellow]No OAuth credentials found[/yellow]")
            return

        table = Table(title="OAuth Credentials")
        table.add_column("ID", style="cyan")
        table.add_column("Provider", style="magenta")
        table.add_column("User", style="green")
        table.add_column("Default", style="yellow")

        for cred in credentials:
            table.add_row(
                cred.credential_id,
                cred.provider,
                cred.identifier[:20] + "..." if len(cred.identifier) > 20 else cred.identifier,
                "✓" if cred.is_default else ""
            )

        rprint(table)
        rprint(f"\n[cyan]Total:[/cyan] {len(credentials)} credentials")


# ==================== Device Code Commands ====================

@auth_cli.group(name="device")
def device_cli():
    """Manage device code credentials."""
    pass


@device_cli.command(name="login")
@click.option(
    "-p", "--provider",
    required=True,
    type=click.Choice(["claude", "gpt", "gemini"], case_sensitive=False),
    help="LLM provider"
)
def device_login(provider: str):
    """
    Login via device code flow (CLI-friendly).

    Business Purpose: Authenticate from CLI without exposing keys in terminal.
    Perfect for CI/CD, automation, and air-gapped systems.

    Example:
        myragdb auth device login --provider claude
    """
    auth_manager = get_auth_manager()
    provider = provider.lower()

    rprint("[yellow]Initiating device code flow...[/yellow]")

    device_code = auth_manager.initiate_device_code(provider)

    if not device_code:
        rprint("[red]✗ Failed to initiate device code[/red]")
        raise click.Abort()

    # Display instructions
    panel = Panel(
        f"[cyan]Visit:[/cyan] [blue]{device_code.verification_url}[/blue]\n"
        f"[cyan]Enter code:[/cyan] [yellow]{device_code.user_code}[/yellow]\n\n"
        f"[cyan]Expires in:[/cyan] {device_code.expires_in}s",
        title="Device Code Authentication",
        expand=False
    )
    rprint(panel)

    rprint(f"\n[yellow]Polling for approval (will wait up to {device_code.expires_in}s)...[/yellow]")

    credential = auth_manager.complete_device_code(device_code.device_code)

    if credential:
        rprint("[green]✓ Device code login successful[/green]")
        rprint(f"[cyan]ID:[/cyan] {credential.credential_id}")
        rprint(f"[cyan]Provider:[/cyan] {credential.provider}")
    else:
        rprint("[red]✗ Device code not approved or expired[/red]")
        raise click.Abort()


@device_cli.command(name="list")
@click.option(
    "-p", "--provider",
    type=click.Choice(["claude", "gpt", "gemini"], case_sensitive=False),
    help="Filter by provider"
)
@click.option(
    "--json",
    is_flag=True,
    help="Output as JSON"
)
def list_device_credentials(provider: Optional[str], json_output: bool):
    """
    List all device code credentials.

    Example:
        myragdb auth device list
        myragdb auth device list --provider claude
    """
    auth_manager = get_auth_manager()
    provider = provider.lower() if provider else None

    credentials = auth_manager.list_device_code_credentials(provider)

    if json_output:
        data = [
            {
                "id": c.credential_id,
                "provider": c.provider,
                "user_code": c.identifier,
                "default": c.is_default,
            }
            for c in credentials
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        if not credentials:
            rprint("[yellow]No device code credentials found[/yellow]")
            return

        table = Table(title="Device Code Credentials")
        table.add_column("ID", style="cyan")
        table.add_column("Provider", style="magenta")
        table.add_column("User Code", style="yellow")
        table.add_column("Default", style="green")

        for cred in credentials:
            table.add_row(
                cred.credential_id[:20] + "..." if len(cred.credential_id) > 20 else cred.credential_id,
                cred.provider,
                cred.identifier,
                "✓" if cred.is_default else ""
            )

        rprint(table)
        rprint(f"\n[cyan]Total:[/cyan] {len(credentials)} credentials")


# ==================== General Credential Commands ====================

@auth_cli.command(name="list")
@click.option(
    "-p", "--provider",
    type=click.Choice(["claude", "gpt", "gemini"], case_sensitive=False),
    help="Filter by provider"
)
@click.option(
    "--json",
    is_flag=True,
    help="Output as JSON"
)
def list_all_credentials(provider: Optional[str], json_output: bool):
    """
    List all credentials across all authentication methods.

    Example:
        myragdb auth list
        myragdb auth list --provider claude
    """
    auth_manager = get_auth_manager()
    provider = provider.lower() if provider else None

    credentials = auth_manager.list_credentials(provider)

    if json_output:
        data = [
            {
                "id": c.credential_id,
                "provider": c.provider,
                "auth_method": c.auth_method.value,
                "default": c.is_default,
            }
            for c in credentials
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        if not credentials:
            rprint("[yellow]No credentials found[/yellow]")
            return

        table = Table(title="All Credentials")
        table.add_column("ID", style="cyan")
        table.add_column("Provider", style="magenta")
        table.add_column("Method", style="blue")
        table.add_column("Default", style="green")

        for cred in credentials:
            table.add_row(
                cred.credential_id[:15] + "..." if len(cred.credential_id) > 15 else cred.credential_id,
                cred.provider,
                cred.auth_method.value,
                "✓" if cred.is_default else ""
            )

        rprint(table)
        rprint(f"\n[cyan]Total:[/cyan] {len(credentials)} credentials")


@auth_cli.command(name="remove")
@click.argument("credential_id")
@click.confirmation_option(prompt="Are you sure you want to delete this credential?")
def remove_credential(credential_id: str):
    """
    Delete a credential.

    Example:
        myragdb auth remove claude-abc12345
    """
    auth_manager = get_auth_manager()

    if auth_manager.delete_credential(credential_id):
        rprint("[green]✓ Credential deleted[/green]")
    else:
        rprint(f"[red]✗ Credential not found: {credential_id}[/red]")
        raise click.Abort()


@auth_cli.command(name="default")
@click.argument("credential_id")
def set_default_credential(credential_id: str):
    """
    Set a credential as default for its provider.

    Example:
        myragdb auth default claude-abc12345
    """
    auth_manager = get_auth_manager()

    if auth_manager.set_default_credential(credential_id):
        rprint("[green]✓ Credential set as default[/green]")
    else:
        rprint(f"[red]✗ Credential not found: {credential_id}[/red]")
        raise click.Abort()
