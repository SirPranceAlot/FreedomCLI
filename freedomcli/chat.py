"""Main chat loop with model interaction and command handling."""

# Standard library imports
import datetime
import os
import re
import shlex
import subprocess
import sys
import time

# Third-party imports
import requests
from rich.prompt import Prompt
from rich.panel import Panel

# Local imports
from freedomcli.constants import APP_NAME, APP_VERSION, console, last_thinking_content
from freedomcli.utils import clear_terminal, format_time_delta, format_file_size
from freedomcli.config import load_config, save_config, count_tokens
from freedomcli.completers import get_user_input_with_completion, HAS_PROMPT_TOOLKIT
from freedomcli.models import (
    get_available_models, get_model_info, get_model_pricing_info,
    calculate_session_cost, select_model, auto_detect_thinking_mode
)
from freedomcli.conversation import (
    save_conversation, load_conversation, generate_conversation_summary,
    save_session_metadata, get_session_summary, manage_context_window
)
from freedomcli.file_handler import handle_attachment, process_attachment_ui
from freedomcli.web_scraper import scrape_url, is_url, extract_urls, HAS_SCRAPING
from freedomcli.security import analyze_command_risk
from freedomcli.streaming import stream_response
from freedomcli.ui import (
    show_about, check_for_updates, get_help_text, get_initial_system_message,
    create_chat_ui
)

if HAS_PROMPT_TOOLKIT:
    from prompt_toolkit.history import InMemoryHistory


def chat_with_model(config, conversation_history=None, after_execute_ref=None):
    """Main chat loop with model interaction"""
    if conversation_history is None:
        conversation_history = [get_initial_system_message(config)]
    
    # Initialize command history for session
    if HAS_PROMPT_TOOLKIT:
        session_history = InMemoryHistory()
    else:
        session_history = None
    
    # Initialize double CTRL+C exit tracking
    ctrl_c_count = 0
    last_ctrl_c_time = 0

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    # Check if temperature is too high and warn the user
    if config['temperature'] > 1.0:
        console.print(Panel.fit(
            f"[yellow]Warning: High temperature setting ({config['temperature']}) may cause erratic responses.[/yellow]\n"
            f"Consider using a value between 0.0 and 1.0 for more coherent outputs.",
            title="⚠️ High Temperature Warning",
            border_style="yellow"
        ))

    # Get pricing information for the model
    pricing_info = get_model_pricing_info(config['model'])
    pricing_display = f"[cyan]Pricing:[/cyan] {pricing_info['display']}"
    if pricing_info['is_free']:
        pricing_display += f" [green]({pricing_info['provider']})[/green]"
    else:
        pricing_display += f" [dim]({pricing_info['provider']})[/dim]"

    console.print(Panel.fit(
        f"[bold blue]Freedom[/bold blue][bold green]CLI[/bold green] [dim]v{APP_VERSION}[/dim]\n"
        f"[cyan]Model:[/cyan] {config['model']}\n"
        f"[cyan]Temperature:[/cyan] {config['temperature']}\n"
        f"[cyan]Thinking mode:[/cyan] {'[green]✓ Enabled[/green]' if config['thinking_mode'] else '[yellow]✗ Disabled[/yellow]'}\n"
        f"{pricing_display}\n"
        f"[cyan]Session started:[/cyan] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Type your message or use commands: /help for available commands\n"
        f"[dim]Press Ctrl+C again to exit[/dim]",
        title="🤖 Chat Session Active",
        border_style="green"
    ))

    # Add session tracking
    session_start_time = time.time()
    total_tokens_used = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    response_times = []
    message_count = 0
    max_tokens = config.get('max_tokens')
    
    if not max_tokens or max_tokens == 0:
        model_info = get_model_info(config['model'])
        if model_info and 'context_length' in model_info and model_info['context_length']:
            max_tokens = model_info['context_length']
            console.print(f"[dim]Using model's context length: {max_tokens:,} tokens[/dim]")
        else:
            max_tokens = 8192
            console.print(f"[yellow]Could not determine model's context length. Using default: {max_tokens:,} tokens[/yellow]")
    else:
        console.print(f"[dim]Using user-defined max tokens: {max_tokens:,}[/dim]")

    # Create a session directory for saving files
    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions", session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Auto-save conversation periodically
    last_autosave = time.time()
    autosave_interval = config['autosave_interval']

    # Check if we need to trim the conversation history
    conversation_history, trimmed_count = manage_context_window(conversation_history, max_tokens=max_tokens, model_name=config['model'], config=config)
    if trimmed_count > 0:
        console.print(f"[yellow]Note: Removed {trimmed_count} earlier messages to stay within the context window.[/yellow]")

    while True:
        try:
            # Display user input panel similar to assistant style
            console.print("\n")
            console.print(Panel.fit(
                "Enter your message",
                title="👤 You",
                border_style="blue"
            ))

            # Use auto-completion if available, otherwise fallback to regular input
            if HAS_PROMPT_TOOLKIT:
                user_input = get_user_input_with_completion(session_history, after_execute_ref=after_execute_ref)
            else:
                print("> ", end="")
                user_input = input()

            # Ignore empty or whitespace-only input
            if not user_input.strip():
                continue

            # Reset CTRL+C counter when user provides valid input
            ctrl_c_count = 0

            # Handle special commands and file picker
            if user_input.startswith('/'):
                # Handle regular commands starting with /
                command = user_input.lower()
            elif user_input.startswith('@'):
                # Handle file picker with @
                file_path = user_input[1:].strip()
                
                if not file_path:
                    console.print("[yellow]Please select a file using the file picker.[/yellow]")
                    console.print("[dim]Type @ to browse files in the current directory[/dim]")
                    continue
                
                # Check for existence and attach using helper
                if process_attachment_ui(file_path, conversation_history):
                    # Continue to get user's actual message about the file
                    console.print("\n[dim]The file has been attached. Now enter your message about this file:[/dim]")
                    
                    # Get user input for the message about the file
                    if HAS_PROMPT_TOOLKIT:
                        user_message = get_user_input_with_completion(session_history)
                    else:
                        print("> ", end="")
                        user_message = input()
                    
                    if user_message.strip():
                        user_input = user_message  # Use the message as the actual input
                    else:
                        continue  # Skip if no message provided
                else:
                    continue
            
            elif '@' in user_input:
                # Handle file picker anywhere in the message
                parts = user_input.split('@', 1)
                if len(parts) == 2:
                    message_part = parts[0].strip()
                    file_and_rest = parts[1].strip()
                    
                    if file_and_rest:
                        # Parse filename and any additional text after it
                        file_tokens = file_and_rest.split()
                        file_part = file_tokens[0] if file_tokens else ""
                        additional_text = " ".join(file_tokens[1:]) if len(file_tokens) > 1 else ""
                        
                        if file_part:
                            if process_attachment_ui(file_part, conversation_history):
                                # Combine message part with any additional text after filename
                                combined_message = ""
                                if message_part:
                                    combined_message = message_part
                                if additional_text:
                                    if combined_message:
                                        combined_message += " " + additional_text
                                    else:
                                        combined_message = additional_text
                                
                                if combined_message:
                                    user_input = combined_message
                                else:
                                    console.print("\n[dim]File attached. Enter your message about this file:[/dim]")
                                    if HAS_PROMPT_TOOLKIT:
                                        user_input = get_user_input_with_completion(session_history)
                                    else:
                                        print("> ", end="")
                                        user_input = input()
                            else:
                                continue
            
            # Process commands if we have one
            if user_input.startswith('/'):
                command = user_input.lower()

                if command == '/help':
                    console.print(Panel.fit(
                        get_help_text(),
                        title="Available Commands"
                    ))
                    continue

                elif command == '/clear':
                    conversation_history = [get_initial_system_message(config)]
                    console.print("[green]Conversation history cleared![/green]")
                    continue

                elif command == '/new':
                    # Check if there's any actual conversation to save
                    if len(conversation_history) > 1:
                        save_prompt = Prompt.ask(
                            "Would you like to save the current conversation before starting a new one?",
                            choices=["y", "n"],
                            default="n"
                        )

                        if save_prompt.lower() == "y":
                            # Auto-generate a filename with timestamp
                            filename = f"conversation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                            filepath = os.path.join(session_dir, filename)
                            save_conversation(conversation_history, filepath, "markdown")
                            console.print(f"[green]Conversation saved to {filepath}[/green]")

                    # Reset conversation
                    conversation_history = [get_initial_system_message(config)]

                    # Reset session tracking variables
                    total_tokens_used = 0
                    response_times = []
                    message_count = 0
                    last_autosave = time.time()

                    # Create a new session directory
                    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions", session_id)
                    os.makedirs(session_dir, exist_ok=True)

                    console.print(Panel.fit(
                        "[green]New conversation started![/green]\n"
                        "Previous conversation history has been cleared.",
                        title="🔄 New Conversation",
                        border_style="green"
                    ))
                    continue

                elif command == '/save':
                    parts = user_input.split(' ', 1)
                    if len(parts) > 1:
                        filename = parts[1]
                    else:
                        filename = Prompt.ask("Enter filename to save conversation",
                                            default=f"conversation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md")

                    format_options = ["markdown", "json", "html"]
                    format_choice = Prompt.ask("Choose format", choices=format_options, default="markdown")

                    if not filename.endswith(f".{format_choice.split('.')[-1]}"):
                        if format_choice == "markdown":
                            filename += ".md"
                        elif format_choice == "json":
                            filename += ".json"
                        elif format_choice == "html":
                            filename += ".html"

                    filepath = os.path.join(session_dir, filename)
                    save_conversation(conversation_history, filepath, format_choice)
                    console.print(f"[green]Conversation saved to {filepath}[/green]")
                    continue

                elif command == '/settings':
                    auto_sum_status = '✓ Enabled' if config.get('auto_summarize', True) else '✗ Disabled'
                    console.print(Panel.fit(
                        f"Current Settings:\n"
                        f"Model: {config['model']}\n"
                        f"Temperature: {config['temperature']}\n"
                        f"Thinking Mode: {'✓ Enabled' if config.get('thinking_mode', False) else '✗ Disabled'}\n"
                        f"Auto-Summarize: {auto_sum_status} (threshold: {config.get('summarize_threshold', 0.7):.0%})\n"
                        f"System Instructions: {config['system_instructions'][:50]}...",
                        title="Settings"
                    ))
                    continue

                elif command == '/tokens':
                    # Calculate session statistics
                    session_duration = time.time() - session_start_time
                    session_cost = calculate_session_cost(total_prompt_tokens, total_completion_tokens, pricing_info)
                    
                    # Create detailed token statistics
                    stats_text = f"[bold cyan]📊 Session Statistics[/bold cyan]\n\n"
                    stats_text += f"[cyan]Model:[/cyan] {config['model']}\n"
                    stats_text += f"[cyan]Session duration:[/cyan] {format_time_delta(session_duration)}\n"
                    stats_text += f"[cyan]Messages exchanged:[/cyan] {message_count}\n\n"
                    
                    stats_text += f"[bold]Token Usage:[/bold]\n"
                    stats_text += f"[cyan]Prompt tokens:[/cyan] {total_prompt_tokens:,}\n"
                    stats_text += f"[cyan]Completion tokens:[/cyan] {total_completion_tokens:,}\n"
                    stats_text += f"[cyan]Total tokens:[/cyan] {total_tokens_used:,}\n"
                    stats_text += f"[dim]Token counts from OpenRouter API (accurate)[/dim]\n\n"
                    
                    if pricing_info['is_free']:
                        stats_text += f"[green]💰 Cost: FREE[/green]\n"
                    else:
                        if session_cost < 0.01:
                            cost_display = f"${session_cost:.6f}"
                        else:
                            cost_display = f"${session_cost:.4f}"
                        stats_text += f"[cyan]💰 Session cost:[/cyan] {cost_display}\n"
                        stats_text += f"[dim]{pricing_info['display']}[/dim]\n"
                    
                    if response_times:
                        avg_time = sum(response_times) / len(response_times)
                        stats_text += f"\n[cyan]⏱️ Avg response time:[/cyan] {format_time_delta(avg_time)}"
                        
                        if total_completion_tokens > 0 and avg_time > 0:
                            tokens_per_second = total_completion_tokens / sum(response_times)
                            stats_text += f"\n[cyan]⚡ Speed:[/cyan] {tokens_per_second:.1f} tokens/second"
                    
                    console.print(Panel.fit(
                        stats_text,
                        title="📈 Token Statistics",
                        border_style="cyan"
                    ))
                    continue

                elif command == '/speed':
                    if not response_times:
                        console.print("[yellow]No response time data available yet.[/yellow]")
                    else:
                        avg_time = sum(response_times) / len(response_times)
                        min_time = min(response_times)
                        max_time = max(response_times)
                        console.print(Panel.fit(
                            f"Response Time Statistics:\n"
                            f"Average: {format_time_delta(avg_time)}\n"
                            f"Fastest: {format_time_delta(min_time)}\n"
                            f"Slowest: {format_time_delta(max_time)}\n"
                            f"Total responses: {len(response_times)}",
                            title="Speed Statistics"
                        ))
                    continue

                elif command.startswith('/model'):
                    selected_model = select_model(config)
                    if selected_model:
                        config['model'] = selected_model
                        save_config(config)
                        console.print(f"[green]Model changed to {config['model']}[/green]")
                    else:
                        console.print("[yellow]Model selection cancelled[/yellow]")
                    continue

                elif command.startswith('/temperature'):
                    parts = command.split()
                    if len(parts) > 1:
                        try:
                            temp = float(parts[1])
                            if 0 <= temp <= 2:
                                if temp > 1.0:
                                    console.print("[yellow]Warning: High temperature values (>1.0) may cause erratic or nonsensical responses.[/yellow]")
                                    confirm = Prompt.ask("Are you sure you want to use this high temperature? (y/n)", default="n")
                                    if confirm.lower() != 'y':
                                        continue

                                config['temperature'] = temp
                                save_config(config)
                                console.print(f"[green]Temperature set to {temp}[/green]")
                            else:
                                console.print("[red]Temperature must be between 0 and 2[/red]")
                        except ValueError:
                            console.print("[red]Invalid temperature value[/red]")
                    else:
                        new_temp = Prompt.ask("Enter new temperature (0.0-2.0)", default=str(config['temperature']))
                        try:
                            temp = float(new_temp)
                            if 0 <= temp <= 2:
                                if temp > 1.0:
                                    console.print("[yellow]Warning: High temperature values (>1.0) may cause erratic or nonsensical responses.[/yellow]")
                                    confirm = Prompt.ask("Are you sure you want to use this high temperature? (y/n)", default="n")
                                    if confirm.lower() != 'y':
                                        continue

                                config['temperature'] = temp
                                save_config(config)
                                console.print(f"[green]Temperature set to {temp}[/green]")
                            else:
                                console.print("[red]Temperature must be between 0 and 2[/red]")
                        except ValueError:
                            console.print("[red]Invalid temperature value[/red]")
                    continue

                elif command.startswith('/system'):
                    parts = user_input.split(' ', 1)
                    if len(parts) > 1:
                        config['system_instructions'] = parts[1]
                        conversation_history[0] = get_initial_system_message(config)
                        save_config(config)
                        console.print("[green]System instructions updated![/green]")
                    else:
                        console.print(Panel(config['system_instructions'], title="Current System Instructions"))
                        change = Prompt.ask("Update system instructions? (y/n)", default="n")
                        if change.lower() == 'y':
                            console.print("[bold]Enter new system instructions (guide the AI's behavior)[/bold]")
                            console.print("[dim]Press Enter twice to finish[/dim]")
                            lines = []
                            empty_line_count = 0
                            while True:
                                line = input()
                                if not line:
                                    empty_line_count += 1
                                    if empty_line_count >= 2:
                                        break
                                else:
                                    empty_line_count = 0
                                    lines.append(line)
                            system_instructions = "\n".join(lines)
                            config['system_instructions'] = system_instructions
                            conversation_history[0] = get_initial_system_message(config)
                            save_config(config)
                            console.print("[green]System instructions updated![/green]")
                    continue

                elif command.startswith('/theme'):
                    parts = command.split()
                    available_themes = ['default', 'dark', 'light', 'hacker']
                    
                    if len(parts) > 1:
                        theme = parts[1].lower()
                        if theme in available_themes:
                            config['theme'] = theme
                            save_config(config)
                            console.print(f"[green]Theme changed to {theme}[/green]")
                        else:
                            console.print(f"[red]Invalid theme. Available themes: {', '.join(available_themes)}[/red]")
                    else:
                        console.print(f"[cyan]Current theme:[/cyan] {config['theme']}")
                        console.print(f"[cyan]Available themes:[/cyan] {', '.join(available_themes)}")
                        new_theme = Prompt.ask("Select theme", choices=available_themes, default=config['theme'])
                        config['theme'] = new_theme
                        save_config(config)
                        console.print(f"[green]Theme changed to {new_theme}[/green]")
                    continue

                elif command == '/about':
                    show_about()
                    continue

                elif command == '/update':
                    check_for_updates(silent=False)
                    continue

                elif command == '/thinking':
                    from freedomcli.constants import last_thinking_content as thinking_content
                    if thinking_content:
                        console.print(Panel.fit(
                            thinking_content,
                            title="🧠 Last Thinking Process",
                            border_style="yellow"
                        ))
                    else:
                        console.print("[yellow]No thinking content available from the last response.[/yellow]")
                    continue

                elif command == '/thinking-mode':
                    # Toggle thinking mode
                    config['thinking_mode'] = not config['thinking_mode']
                    save_config(config)

                    # Update the system prompt for future messages
                    if len(conversation_history) > 0 and conversation_history[0]['role'] == 'system':
                        original_instructions = config['system_instructions']
                        if config['thinking_mode']:
                            thinking_instruction = (
                                f"{original_instructions}\n\n"
                                "CRITICAL INSTRUCTION: For EVERY response without exception, you MUST first explain your "
                                "thinking process between <thinking> and </thinking> tags, even for simple greetings or short "
                                "responses. This thinking section should explain your reasoning and approach. "
                                "After the thinking section, provide your final response. Example format:\n"
                                "<thinking>Here I analyze what to say, considering context and appropriate responses...</thinking>\n"
                                "This is my actual response to the user."
                            )
                            conversation_history[0]['content'] = thinking_instruction
                        else:
                            # Revert to original instructions without thinking tags
                            conversation_history[0]['content'] = original_instructions

                    console.print(f"[green]Thinking mode is now {'enabled' if config['thinking_mode'] else 'disabled'}[/green]")
                    continue

                elif command == '/auto-summarize':
                    # Toggle auto-summarization mode
                    config['auto_summarize'] = not config.get('auto_summarize', True)
                    save_config(config)
                    console.print(f"[green]Auto-summarization is now {'enabled' if config['auto_summarize'] else 'disabled'}[/green]")
                    if config['auto_summarize']:
                        console.print(f"[dim]Older messages will be summarized when reaching {config.get('summarize_threshold', 0.7):.0%} of token limit[/dim]")
                    else:
                        console.print(f"[dim]Older messages will be trimmed instead of summarized[/dim]")
                    continue

                elif command.startswith('/web'):
                    # Extract URL from command
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        console.print("[yellow]Usage: /web <url>[/yellow]")
                        console.print("[dim]Example: /web https://example.com[/dim]")
                        continue
                    
                    url = parts[1].strip()
                    
                    # Scrape the URL
                    success, content = scrape_url(url)
                    
                    if success:
                        # Add scraped content to conversation history
                        conversation_history.append({
                            "role": "user",
                            "content": f"Here is web content I'd like you to analyze:\n\n{content}"
                        })
                        
                        # Show preview of scraped content
                        preview_lines = content.split('\n')[:10]
                        preview = '\n'.join(preview_lines)
                        if len(content.split('\n')) > 10:
                            preview += f"\n\n[dim]... ({len(content.split(chr(10))) - 10} more lines)[/dim]"
                        
                        console.print(Panel.fit(
                            f"[green]✓ Successfully scraped content from URL[/green]\n\n"
                            f"[dim]Preview:[/dim]\n{preview[:500]}{'...' if len(preview) > 500 else ''}",
                            title="🌐 Web Content Injected",
                            border_style="green"
                        ))
                        
                        console.print("\n[dim]The web content has been added to context. What would you like to know about it?[/dim]")
                        
                        # Get user's question about the content
                        if HAS_PROMPT_TOOLKIT:
                            user_input = get_user_input_with_completion(session_history)
                        else:
                            print("> ", end="")
                            user_input = input()
                        
                        if not user_input.strip():
                            continue
                    else:
                        console.print(f"[red]Failed to scrape URL: {content}[/red]")
                        continue

                elif command in ('/cls', '/clear-screen'):
                    # Clear the terminal
                    clear_terminal()

                    # After clearing, redisplay the session header for context
                    current_pricing_info = get_model_pricing_info(config['model'])
                    pricing_display = f"[cyan]Pricing:[/cyan] {current_pricing_info['display']}"
                    if not current_pricing_info['is_free']:
                        pricing_display += f" [dim]({current_pricing_info['provider']})[/dim]"
                    else:
                        pricing_display += f" [green]({current_pricing_info['provider']})[/green]"
                        
                    console.print(Panel.fit(
                        f"[bold blue]Freedom[/bold blue][bold green]CLI[/bold green] [dim]v{APP_VERSION}[/dim]\n"
                        f"[cyan]Model:[/cyan] {config['model']}\n"
                        f"[cyan]Temperature:[/cyan] {config['temperature']}\n"
                        f"[cyan]Thinking mode:[/cyan] {'[green]✓ Enabled[/green]' if config['thinking_mode'] else '[yellow]✗ Disabled[/yellow]'}\n"
                        f"{pricing_display}\n"
                        f"[cyan]Session started:[/cyan] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Type your message or use commands: /help for available commands",
                        title="🤖 Chat Session Active",
                        border_style="green"
                    ))
                    console.print("[green]Terminal screen cleared. Chat session continues.[/green]")
                    continue

                elif command.startswith('/chat'):
                    parts = user_input.split()
                    if len(parts) < 2:
                        console.print("[yellow]Usage: /chat <list|save|resume> [session_id][/yellow]")
                        continue
                    
                    action = parts[1].lower()
                    session_id_param = parts[2] if len(parts) > 2 else None
                    
                    if action == 'list':
                        # List saved conversations with human-readable summaries
                        sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")
                        if os.path.exists(sessions_dir):
                            sessions = [d for d in os.listdir(sessions_dir) if os.path.isdir(os.path.join(sessions_dir, d))]
                            if sessions:
                                session_list = []
                                for session in sorted(sessions, reverse=True):  # Most recent first
                                    session_path = os.path.join(sessions_dir, session)
                                    summary = get_session_summary(session_path)
                                    session_list.append(f"{summary} ({session})")
                                
                                console.print(Panel.fit(f"Saved sessions:\n" + "\n".join(session_list), title="Chat History"))
                            else:
                                console.print("[yellow]No saved conversations found.[/yellow]")
                        else:
                            console.print("[yellow]No sessions directory found.[/yellow]")
                    elif action == 'save':
                        # Generate a meaningful summary for this conversation
                        console.print("[cyan]Generating conversation summary...[/cyan]")
                        summary = generate_conversation_summary(conversation_history)
                        
                        # Save both markdown and JSON for resume capability
                        md_filepath = os.path.join(session_dir, f"{summary}.md")
                        json_filepath = os.path.join(session_dir, f"{summary}.json")
                        save_conversation(conversation_history, md_filepath, "markdown")
                        save_conversation(conversation_history, json_filepath, "json")
                        
                        # Save metadata with summary
                        save_session_metadata(session_dir, summary)
                        
                        console.print(f"[green]Conversation saved as '{summary}'[/green]")
                    elif action == 'resume':
                        if not session_id_param:
                            console.print("[yellow]Please specify a session ID to resume. Use '/chat list' to see available sessions.[/yellow]")
                        else:
                            # If user provides a summary name, find the corresponding session
                            sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")
                            target_session = session_id_param
                            
                            # Check if it's a summary name by looking through all sessions
                            if os.path.exists(sessions_dir):
                                for session in os.listdir(sessions_dir):
                                    session_path = os.path.join(sessions_dir, session)
                                    if os.path.isdir(session_path):
                                        summary = get_session_summary(session_path)
                                        if summary == session_id_param:
                                            target_session = session
                                            break
                            
                            loaded_history, error = load_conversation(target_session)
                            if error:
                                console.print(f"[red]Error loading conversation: {error}[/red]")
                            else:
                                conversation_history.clear()
                                conversation_history.extend(loaded_history)
                                console.print(f"[green]Conversation resumed from session {target_session}![/green]")
                                # Show a brief summary
                                msg_count = len([msg for msg in conversation_history if msg['role'] in ['user', 'assistant']])
                                console.print(f"[cyan]Loaded {msg_count} messages from previous conversation.[/cyan]")
                    else:
                        console.print("[yellow]Unknown chat action. Use: list, save, or resume[/yellow]")
                    continue

                else:
                    console.print("[yellow]Unknown command. Type /help for available commands.[/yellow]")
                    continue

            # Check for URLs in user input and offer to scrape them
            if is_url(user_input) and not user_input.startswith('/'):
                urls = extract_urls(user_input)
                if urls:
                    console.print(f"\n[cyan]🔗 Detected {len(urls)} URL(s) in your message:[/cyan]")
                    for idx, url in enumerate(urls, 1):
                        console.print(f"  {idx}. {url}")
                    
                    scrape_choice = Prompt.ask(
                        "\nWould you like to scrape and inject the web content into context?",
                        choices=["y", "n", "a"],
                        default="y"
                    )
                    
                    if scrape_choice.lower() == 'y':
                        # Ask which URL to scrape if multiple
                        if len(urls) > 1:
                            url_choice = Prompt.ask(
                                "Which URL would you like to scrape?",
                                choices=[str(i) for i in range(1, len(urls) + 1)] + ["all"],
                                default="1"
                            )
                            
                            if url_choice.lower() == "all":
                                urls_to_scrape = urls
                            else:
                                urls_to_scrape = [urls[int(url_choice) - 1]]
                        else:
                            urls_to_scrape = urls
                        
                        # Scrape selected URLs
                        for url in urls_to_scrape:
                            success, content = scrape_url(url)
                            
                            if success:
                                # Add scraped content before the user's message
                                conversation_history.append({
                                    "role": "user",
                                    "content": f"[Web content from {url}]\n\n{content}"
                                })
                                console.print(f"[green]✓ Successfully scraped: {url}[/green]")
                            else:
                                console.print(f"[red]✗ Failed to scrape {url}: {content}[/red]")
                    elif scrape_choice.lower() == 'a':
                        # Scrape all URLs automatically
                        for url in urls:
                            success, content = scrape_url(url)
                            if success:
                                conversation_history.append({
                                    "role": "user",
                                    "content": f"[Web content from {url}]\n\n{content}"
                                })
                                console.print(f"[green]✓ Scraped: {url}[/green]")

            # Count tokens in user input
            estimated_input_tokens = count_tokens(user_input)
            input_tokens = estimated_input_tokens
            total_prompt_tokens += input_tokens

            # Add user message to conversation history
            conversation_history.append({"role": "user", "content": user_input})

            # Get model max tokens
            model_info = get_model_info(config['model'])
            if model_info and 'context_length' in model_info:
                display_max_tokens = model_info['context_length']
            else:
                display_max_tokens = max_tokens

            # Check if we need to trim the conversation history
            conversation_history, trimmed_count = manage_context_window(conversation_history, max_tokens=max_tokens, model_name=config['model'], config=config)
            if trimmed_count > 0:
                console.print(f"[yellow]Note: Removed {trimmed_count} earlier messages to stay within the context window.[/yellow]")

            # Clean conversation history for API - remove any messages with invalid fields
            clean_conversation = []
            for msg in conversation_history:
                clean_msg = {
                    "role": msg["role"],
                    "content": msg["content"]
                }
                # Handle models that don't support system messages (like Gemma)
                if clean_msg["role"] == "system":
                    if "gemma" in config['model'].lower():
                        if clean_msg["content"] and clean_msg["content"].strip():
                            clean_msg["role"] = "user"
                            clean_msg["content"] = f"Please follow these instructions: {clean_msg['content']}"
                        else:
                            continue
                
                # Only include valid roles for OpenRouter API
                if clean_msg["role"] in ["system", "user", "assistant"]:
                    clean_conversation.append(clean_msg)

            # Update the API call to use streaming
            data = {
                "model": config['model'],
                "messages": clean_conversation,
                "temperature": config['temperature'],
                "stream": True,
            }

            # Start timing the response
            start_time = time.time()
            timer_display = console.status("[bold cyan]⏱️ Waiting for response...[/bold cyan]")
            timer_display.start()

            try:
                # Make streaming request
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    stream=True,
                    timeout=60
                )

                if response.status_code == 200:
                    timer_display.stop()
                    # Pass config['thinking_mode'] to stream_response
                    message_content, response_time, usage_info = stream_response(response, start_time, config['thinking_mode'])

                    # Only add to history if we got actual content
                    if message_content:
                        response_times.append(response_time)

                        # Add assistant response to conversation history
                        conversation_history.append({"role": "assistant", "content": message_content})

                        # --- AGENTIC TOOL EXECUTION ---
                        # Look for all [EXECUTE: ...] patterns
                        exec_matches = re.finditer(r'\[EXECUTE: (.*?)\]', message_content, re.DOTALL)
                        commands_found = False
                        for exec_match in exec_matches:
                            commands_found = True
                            command_to_run = exec_match.group(1).strip()
                            
                            # Analyze security risk
                            risk_color, risk_icon, risk_msg, is_blocked = analyze_command_risk(command_to_run)
                            
                            console.print(Panel.fit(
                                f"[bold {risk_color}]{risk_icon} The AI wants to execute this command:[/bold {risk_color}]\n\n"
                                f"[bold white]{command_to_run}[/bold white]\n\n"
                                f"{risk_msg}\n"
                                f"[dim]OS: {platform.system()}[/dim]",
                                title="🛡️ Security Check",
                                border_style=risk_color
                            ))
                            
                            confirm = Prompt.ask(
                                "Allow execution?", 
                                choices=["y", "n"], 
                                default="n"
                            )
                            
                            if confirm.lower() == 'y':
                                _, _, block_msg, is_blocked = analyze_command_risk(command_to_run)
                                
                                if is_blocked:
                                    console.print(block_msg)
                                    conversation_history.append({
                                        "role": "system", 
                                        "content": f"Command was blocked for security reasons."
                                    })
                                    continue
                                
                                console.print(f"[cyan]Running: {command_to_run}...[/cyan]")
                                try:
                                    # Try safe parsing first, fall back to shell for complex commands
                                    use_shell = False
                                    command_list = None
                                    
                                    try:
                                        command_list = shlex.split(command_to_run)
                                    except ValueError:
                                        use_shell = True
                                    
                                    # Execute the command
                                    if use_shell:
                                        console.print("[dim]Using shell mode for complex command[/dim]")
                                        result = subprocess.run(
                                            command_to_run,
                                            shell=True,
                                            capture_output=True, 
                                            text=True,
                                            timeout=30
                                        )
                                    else:
                                        result = subprocess.run(
                                            command_list,
                                            shell=False,
                                            capture_output=True, 
                                            text=True,
                                            timeout=30
                                        )
                                    
                                    stdout = result.stdout.strip()
                                    stderr = result.stderr.strip()
                                    
                                    output = ""
                                    if stdout:
                                        output += f"STDOUT:\n{stdout}\n"
                                    if stderr:
                                        output += f"STDERR:\n{stderr}\n"
                                    if not output:
                                        output = "(Command executed with no output)"
                                    
                                    # Truncate if too long
                                    if len(output) > 5000:
                                        output = output[:5000] + "\n...[truncated output]"
                                        
                                    console.print(Panel.fit(
                                        output[:500] + ("..." if len(output) > 500 else ""), 
                                        title="Output", 
                                        border_style="green"
                                    ))
                                    
                                    # Feed back to LLM
                                    conversation_history.append({
                                        "role": "system", 
                                        "content": f"Command '{command_to_run}' executed.\nExit Code: {result.returncode}\nOutput:\n{output}"
                                    })
                                    console.print("[dim]Output added to context. You can press Enter to let it continue or type a message.[/dim]")

                                except Exception as e:
                                    error_msg = f"Execution failed: {str(e)}"
                                    console.print(f"[red]{error_msg}[/red]")
                                    conversation_history.append({
                                        "role": "system", 
                                        "content": error_msg
                                    })
                            else:
                                console.print("[red]Execution denied.[/red]")
                                conversation_history.append({
                                    "role": "system", 
                                    "content": "User denied permission to execute the command."
                                })

                        # Use API-provided token counts if available, otherwise fallback to tiktoken
                        if usage_info:
                            actual_prompt_tokens = usage_info.get('prompt_tokens', 0)
                            actual_completion_tokens = usage_info.get('completion_tokens', 0)
                            actual_total_tokens = usage_info.get('total_tokens', actual_prompt_tokens + actual_completion_tokens)
                            
                            total_prompt_tokens += actual_prompt_tokens
                            total_completion_tokens += actual_completion_tokens
                            total_tokens_used += actual_total_tokens
                            
                            input_tokens = actual_prompt_tokens
                            response_tokens = actual_completion_tokens
                        else:
                            # Fallback to tiktoken estimation
                            response_tokens = count_tokens(message_content)
                            total_tokens_used += input_tokens + response_tokens
                            total_completion_tokens += response_tokens

                        # Calculate cost for this exchange
                        exchange_cost = calculate_session_cost(input_tokens, response_tokens, pricing_info)

                        # Display speed and token information
                        formatted_time = format_time_delta(response_time)
                        console.print(f"[dim]⏱️ Response time: {formatted_time}[/dim]")
                        
                        # Enhanced token display with cost and accuracy indicator
                        token_source = "API" if usage_info else "estimated"
                        token_display = f"[dim]Tokens: {input_tokens} (input) + {response_tokens} (response) = {input_tokens + response_tokens} (total) [{token_source}]"
                        if exchange_cost > 0:
                            if exchange_cost < 0.01:
                                token_display += f" | Cost: ${exchange_cost:.6f}"
                            else:
                                token_display += f" | Cost: ${exchange_cost:.4f}"
                        token_display += "[/dim]"
                        console.print(token_display)
                        
                        if max_tokens:
                            console.print(f"[dim]Total Tokens: {total_tokens_used:,} / {display_max_tokens:,}[/dim]")
                        
                        # Increment message count for successful exchanges
                        message_count += 1

                        # Only set after_execute if commands were actually found and executed
                        if commands_found:
                            after_execute_ref["after_execute"] = True
                            console.print(f"after execute set: {after_execute_ref['after_execute']}")
                    else:
                        console.print("[red]Error: Received empty response from API[/red]")
                        if conversation_history and conversation_history[-1]["role"] == "user":
                            conversation_history.pop()
                else:
                    # Try to get error details from response
                    try:
                        error_data = response.json()
                        error_message = error_data.get('error', {}).get('message', str(response.text))
                        
                        # Special handling for insufficient credits errors (402)
                        if response.status_code == 402:
                            suggestions_text = (
                                f"[yellow]Solutions:[/yellow]\n"
                                f"• Add credits at: [link=https://openrouter.ai/settings/credits]https://openrouter.ai/settings/credits[/link]\n"
                                f"• Browse free models: [cyan]/model[/cyan] → [cyan]2[/cyan] (Show free models only)\n"
                                f"• Try the free version if available: [cyan]{config['model']}:free[/cyan]\n"
                                f"\n[dim]Original error: {error_message}[/dim]"
                            )
                            
                            console.print(Panel.fit(
                                f"[red]💳 Insufficient Credits[/red]\n\n"
                                f"The model '[cyan]{config['model']}[/cyan]' requires credits to use.\n\n"
                                f"{suggestions_text}",
                                title="⚠️ Payment Required",
                                border_style="red"
                            ))
                        # Special handling for rate limits (429)
                        elif response.status_code == 429:
                            console.print(Panel.fit(
                                f"[yellow]⏳ Rate Limit Exceeded[/yellow]\n\n"
                                f"You are sending requests too quickly for the current model.\n\n"
                                f"[bold]Recommendations:[/bold]\n"
                                f"• Wait a few moments before trying again\n"
                                f"• Switch to a different free model ([cyan]/model[/cyan])\n"
                                f"• Upgrade to a paid model for higher limits\n\n"
                                f"[dim]Original error: {error_message}[/dim]",
                                title="⚠️ Rate Limit",
                                border_style="yellow"
                            ))
                        else:
                            console.print(f"[red]API Error ({response.status_code}): {error_message}[/red]")
                    except Exception:
                        console.print(f"[red]API Error: Status code {response.status_code}[/red]")
                        console.print(f"[red]{response.text}[/red]")

                    if conversation_history and conversation_history[-1]["role"] == "user":
                        conversation_history.pop()
            except requests.exceptions.RequestException as e:
                console.print(f"[red]Network error: {str(e)}[/red]")
                if conversation_history and conversation_history[-1]["role"] == "user":
                    conversation_history.pop()
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                if conversation_history and conversation_history[-1]["role"] == "user":
                    conversation_history.pop()
            finally:
                timer_display.stop()

        except KeyboardInterrupt:
            current_time = time.time()
            # Check if this is a double CTRL+C (within 2 seconds)
            if ctrl_c_count > 0 and (current_time - last_ctrl_c_time) <= 2.0:
                console.print("\n[yellow]Exiting chat...[/yellow]")
                break
            else:
                ctrl_c_count = 1
                last_ctrl_c_time = current_time
                console.print("\n[yellow]Press Ctrl+C again to exit.[/yellow]")
                continue
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")