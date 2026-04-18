"""UI components: panels, about, help, welcome screen, and system messages."""

# Standard library imports
import datetime
import json
import os
import platform
import sys
import time
import urllib.request
import webbrowser

# Third-party imports
from rich.prompt import Prompt
from rich.panel import Panel

# Local imports
from freedomcli.constants import APP_NAME, APP_VERSION, REPO_URL, API_URL, console
from freedomcli.config import load_config, save_config
from freedomcli.models import get_model_pricing_info


def show_about():
    """Display information about FreedomCLI"""
    console.print(Panel.fit(
        f"[bold blue]Freedom[/bold blue][bold green]CLI[/bold green] [dim]v{APP_VERSION}[/dim]\n\n"
        "A powerful CLI for chatting with AI models through OpenRouter.\n\n"
        f"[link={REPO_URL}]{REPO_URL}[/link]\n\n"
        "Fork of OrChat by Muhamed (MIT License)\n"
        "Licensed under MIT License",
        title="ℹ️ About FreedomCLI",
        border_style="blue"
    ))


def check_for_updates(silent=False):
    """Check GitHub for newer versions of FreedomCLI"""
    if not silent:
        console.print("[bold cyan]Checking for updates...[/bold cyan]")
    try:
        with urllib.request.urlopen(API_URL) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data.get('tag_name', 'v0.0.0').lstrip('v')

                from packaging import version
                if version.parse(latest_version) > version.parse(APP_VERSION):
                    console.print(Panel.fit(
                        f"[yellow]A new version of FreedomCLI is available![/yellow]\n"
                        f"Current version: [cyan]{APP_VERSION}[/cyan]\n"
                        f"Latest version: [green]{latest_version}[/green]\n\n"
                        f"Update at: {REPO_URL}/releases",
                        title="📢 Update Available",
                        border_style="yellow"
                    ))

                    if silent:
                        update_choice = Prompt.ask("Would you like to update now?", choices=["y", "n"], default="n")
                        if update_choice.lower() == "y":
                            try:
                                console.print("[cyan]Attempting to update via pip...[/cyan]")
                                result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "freedomcli"],
                                                      capture_output=True, text=True)
                                if result.returncode == 0:
                                    console.print("[green]Update successful! Please restart FreedomCLI.[/green]")
                                    sys.exit(0)
                                else:
                                    console.print(f"[yellow]Update failed: {result.stderr}[/yellow]")
                                    open_browser = Prompt.ask("Open release page for manual update?", choices=["y", "n"], default="y")
                                    if open_browser.lower() == "y":
                                        webbrowser.open(f"{REPO_URL}/releases")
                            except Exception as e:
                                console.print(f"[yellow]Auto-update failed: {str(e)}[/yellow]")
                                open_browser = Prompt.ask("Open release page for manual update?", choices=["y", "n"], default="y")
                                if open_browser.lower() == "y":
                                    webbrowser.open(f"{REPO_URL}/releases")
                    else:
                        open_browser = Prompt.ask("Open release page in browser?", choices=["y", "n"], default="n")
                        if open_browser.lower() == "y":
                            webbrowser.open(f"{REPO_URL}/releases")
                    return True  # Update available
                else:
                    if not silent:
                        console.print("[green]You are using the latest version of FreedomCLI![/green]")
                    return False  # No update available
            else:
                if not silent:
                    console.print("[yellow]Could not check for updates. Server returned status "
                                f"code {response.getcode()}[/yellow]")
                return False
    except Exception as e:
        if not silent:
            console.print(f"[yellow]Could not check for updates: {str(e)}[/yellow]")
        return False


def get_help_text():
    """Returns the help text for the /help command"""
    help_text = "/new - Start a new conversation\n" \
               "/clear - Clear conversation history\n" \
               "/cls or /clear-screen - Clear terminal screen\n" \
               "/save - Save conversation to file\n" \
               "/chat <list|save|resume> [session_id] - Manage conversation history\n" \
               "/settings - Adjust model settings\n" \
               "/tokens - Show token usage statistics\n" \
               "/model - Change the AI model\n" \
               "/temperature <0.0-2.0> - Adjust temperature\n" \
               "/system - View or change system instructions\n" \
               "/speed - Show response time statistics\n" \
               "/theme <theme> - Change the color theme\n" \
               "/about - Show information about FreedomCLI\n" \
               "/update - Check for updates\n" \
               "/thinking - Show last AI thinking process\n" \
               "/thinking-mode - Toggle thinking mode on/off\n" \
               "/auto-summarize - Toggle auto-summarization of old messages\n" \
               "/web <url> - Scrape and inject web content into context\n" \
               "@ - Browse and attach files (can be used anywhere in your message)\n" \
               "[yellow]Press Ctrl+C twice to exit[/yellow]"
    
    try:
        from prompt_toolkit.completion import Completer
        has_prompt_toolkit = True
    except ImportError:
        has_prompt_toolkit = False
    
    if has_prompt_toolkit:
        help_text += "\n\n[dim]💡 Interactive Features:[/dim]\n"
        help_text += "[dim]• Command auto-completion: Type '/' and all commands appear instantly[/dim]\n"
        help_text += "[dim]• File picker: Type '#' anywhere to browse and select files[/dim]\n"
        help_text += "[dim]• Continue typing to filter commands/files (e.g., '/c' or '#main'[/dim]\n"
        help_text += "[dim]• Press ↑/↓ arrow keys to navigate through previous prompts[/dim]\n"
        help_text += "[dim]• Press Ctrl+R to search through prompt history[/dim]\n"
        help_text += "[dim]• Press Esc+Enter to toggle multi-line input mode[/dim]\n"
        help_text += "[dim]• Auto-suggestions: Previous prompts appear as grey text while typing[/dim]"
    
    return help_text


def get_initial_system_message(config):
    """Generates the initial system message with OS info and instructions"""
    current_os = platform.system()
    os_info = f"Operating System: {current_os} {platform.release()}"
    
    # Use user's thinking mode preference
    if config['thinking_mode']:
        thinking_instruction = (
            f"{config['system_instructions']}\n\n"
            f"You are running on {os_info}.\n"
            "You have access to the local system terminal.\n"
            "To execute a command, output it inside a boolean block like this:\n"
            "[EXECUTE: command]\n"
            "Example: [EXECUTE: ls -la]\n"
            "The user will be asked for confirmation. If confirmed, the output will be returned to you.\n"
            "CRITICAL INSTRUCTION: For EVERY response without exception, you MUST first explain your "
            "thinking process between <thinking> and </thinking> tags, even for simple greetings or short "
            "responses. This thinking section should explain your reasoning and approach. "
            "After the thinking section, provide your final response."
        )
    else:
        thinking_instruction = (
            f"{config['system_instructions']}\n\n"
            f"You are running on {os_info}.\n"
            "You have access to the local system terminal.\n"
            "To execute a command, output it inside a boolean block like this:\n"
            "[EXECUTE: command]\n"
            "Example: [EXECUTE: ls -la] or [EXECUTE: dir]\n"
            "The user will be asked for confirmation. If confirmed, the output will be returned to you."
        )

    return {"role": "system", "content": thinking_instruction}


def create_chat_ui():
    """Creates a modern, attractive CLI interface using rich components"""
    console.print(Panel.fit(
        f"[bold blue]Freedom[/bold blue][bold green]CLI[/bold green] [dim]v{APP_VERSION}[/dim]\n"
        "[dim]A powerful CLI for AI models via OpenRouter (fork of OrChat)[/dim]",
        title="🚀 Welcome",
        border_style="green",
        padding=(1, 2)
    ))

    # Display a starting tip
    console.print(Panel(
        "Type [bold green]/help[/bold green] for commands\n"
        "[bold cyan]/model[/bold cyan] to change AI models\n"
        "[bold yellow]/theme[/bold yellow] to customize appearance",
        title="Quick Tips",
        border_style="blue",
        width=40
    ))