"""Response streaming logic from AI models."""

# Standard library imports
import json
import re
import time

# Third-party imports
from rich.markdown import Markdown
from rich.panel import Panel

# Local imports
from freedomcli.constants import console, last_thinking_content


def stream_response(response, start_time, thinking_mode=False):
    """Stream the response from the API with proper text formatting"""
    console.print("\n[bold green]Assistant[/bold green]")

    # Full content accumulates everything
    full_content = ""
    # For thinking detection
    thinking_content = ""
    in_thinking = False
    # For capturing usage information
    usage_info = None

    # Create a temporary file to collect all content
    # This avoids terminal display issues
    collected_content = []

    # For debugging purposes
    global last_thinking_content

    try:
        for chunk in response.iter_lines():
            if not chunk:
                continue

            chunk_text = chunk.decode('utf-8', errors='replace')

            if "OPENROUTER PROCESSING" in chunk_text:
                continue

            if chunk_text.startswith('data:'):
                chunk_text = chunk_text[5:].strip()

            if chunk_text == "[DONE]":
                continue

            try:
                chunk_data = json.loads(chunk_text)
                
                # Capture usage information if present
                if 'usage' in chunk_data:
                    usage_info = chunk_data['usage']
                
                if 'choices' in chunk_data and chunk_data['choices']:
                    delta = chunk_data['choices'][0].get('delta', {})
                    content = delta.get('content', delta.get('text', ''))

                    if content:
                        # Add to full content
                        full_content += content

                        # Only process thinking tags if thinking mode is enabled
                        if thinking_mode:
                            # Check for thinking tags
                            if "<thinking>" in content:
                                in_thinking = True
                                # Extract content after the tag
                                thinking_part = content.split("<thinking>", 1)[1]
                                thinking_content += thinking_part
                                # Skip this chunk - don't display the <thinking> tag
                                continue

                            if "</thinking>" in content:
                                in_thinking = False
                                # Extract content before the tag
                                thinking_part = content.split("</thinking>", 1)[0]
                                thinking_content += thinking_part
                                # Skip this chunk - don't display the </thinking> tag
                                continue

                            if in_thinking:
                                thinking_content += content
                                continue

                        # Not in thinking mode or model doesn't support thinking, collect for display
                        collected_content.append(content)
            except json.JSONDecodeError:
                # For non-JSON chunks, quietly ignore
                pass
    except Exception as e:
        console.print(f"\n[red]Error during streaming: {str(e)}[/red]")

    # More robust thinking extraction - uses regex pattern to look for any thinking tags in the full content
    thinking_section = ""
    thinking_pattern = re.compile(r'<thinking>(.*?)</thinking>', re.DOTALL)
    thinking_matches = thinking_pattern.findall(full_content)

    if thinking_mode and thinking_matches:
        thinking_section = "\n".join(thinking_matches)
        # Update the global thinking content variable
        last_thinking_content = thinking_section

        # Display thinking content immediately if found
        console.print(Panel.fit(
            Markdown(last_thinking_content),
            title="🧠 AI Thinking Process",
            border_style="yellow"
        ))
    else:
        # Also check if thinking_content has any content from our incremental collection
        if thinking_content.strip():
            last_thinking_content = thinking_content

            # Display thinking content immediately if found
            console.print(Panel.fit(
                Markdown(last_thinking_content),
                title="🧠 AI Thinking Process",
                border_style="yellow"
            ))

    # Clean the full content - only if model supports thinking
    cleaned_content = full_content
    if thinking_mode and "<thinking>" in full_content:
        # Remove the thinking sections with a more robust pattern
        try:
            # Use a non-greedy match to handle multiple thinking sections
            cleaned_content = re.sub(r'<thinking>.*?</thinking>', '', full_content, flags=re.DOTALL)
            cleaned_content = cleaned_content.strip()
        except:
            # Fallback to simpler method
            parts = full_content.split("</thinking>")
            if len(parts) > 1:
                cleaned_content = parts[-1].strip()

    # If after cleaning we have nothing, use a default response
    if not cleaned_content.strip():
        cleaned_content = "Hello! I'm here to help you."

    if cleaned_content:
        console.print(Markdown(cleaned_content))
    else:
        console.print("Hello! I'm here to help you.")

    response_time = time.time() - start_time
    return cleaned_content, response_time, usage_info