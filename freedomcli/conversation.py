"""Conversation management: save, load, summarize, and context window management."""

# Standard library imports
import datetime
import json
import os
import re
import time

# Third-party imports
import requests

# Local imports
from freedomcli.constants import console
from freedomcli.config import count_tokens


def save_conversation(conversation_history, filename, fmt="markdown"):
    """Save conversation to file in various formats"""
    if fmt == "markdown":
        with open(filename, 'w', encoding="utf-8") as f:
            f.write("# FreedomCLI Conversation\n\n")
            f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for msg in conversation_history:
                if msg['role'] == 'system':
                    f.write(f"## System Instructions\n\n{msg['content']}\n\n")
                else:
                    f.write(f"## {msg['role'].capitalize()}\n\n{msg['content']}\n\n")
    elif fmt == "json":
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(conversation_history, f, indent=2)
    elif fmt == "html":
        with open(filename, 'w', encoding="utf-8") as f:
            f.write("<!DOCTYPE html>\n<html>\n<head>\n")
            f.write("<title>FreedomCLI Conversation</title>\n")
            f.write("<style>\n")
            f.write("body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }\n")
            f.write(".system { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }\n")
            f.write(".user { background-color: #e1f5fe; padding: 10px; border-radius: 5px; margin: 10px 0; }\n")
            f.write(".assistant { background-color: #f1f8e9; padding: 10px; border-radius: 5px; margin: 10px 0; }\n")
            f.write("</style>\n</head>\n<body>\n")
            f.write("<h1>FreedomCLI Conversation</h1>\n")
            f.write(f"<p>Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>\n")

            for msg in conversation_history:
                f.write(f"<div class='{msg['role']}'>\n")
                f.write(f"<h2>{msg['role'].capitalize()}</h2>\n")
                content_html = msg['content'].replace('\n', '<br>')
                f.write(f"<p>{content_html}</p>\n")
                f.write("</div>\n")

            f.write("</body>\n</html>")

    return filename


def load_conversation(session_id):
    """Load conversation from a session directory"""
    sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")
    session_path = os.path.join(sessions_dir, session_id)
    
    if not os.path.exists(session_path):
        return None, "Session not found"
    
    # Look for JSON file first (preferred for resume)
    json_files = [f for f in os.listdir(session_path) if f.endswith('.json')]
    if json_files:
        json_file = os.path.join(session_path, json_files[0])
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                conversation_history = json.load(f)
            return conversation_history, None
        except Exception as e:
            return None, f"Error loading JSON file: {str(e)}"
    
    # Fallback to parsing markdown file
    md_files = [f for f in os.listdir(session_path) if f.endswith('.md')]
    if md_files:
        md_file = os.path.join(session_path, md_files[0])
        try:
            conversation_history = []
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple markdown parser for conversation format
            sections = content.split('## ')
            for section in sections[1:]:  # Skip header
                lines = section.strip().split('\n', 1)
                if len(lines) >= 2:
                    role = lines[0].lower()
                    if role == 'system instructions':
                        role = 'system'
                    content_text = lines[1].strip()
                    conversation_history.append({"role": role, "content": content_text})
            
            return conversation_history, None
        except Exception as e:
            return None, f"Error parsing markdown file: {str(e)}"
    
    return None, "No conversation files found in session"


def generate_conversation_summary(conversation_history):
    """Generate a short summary of the conversation using a lightweight model"""
    try:
        # Extract meaningful content (skip system messages)
        user_messages = [msg['content'] for msg in conversation_history if msg['role'] == 'user']
        assistant_messages = [msg['content'] for msg in conversation_history if msg['role'] == 'assistant']
        
        if not user_messages:
            return "empty_conversation"
        
        # Create a condensed version for summarization
        conversation_text = ""
        for i, (user_msg, assistant_msg) in enumerate(zip(user_messages[:3], assistant_messages[:3])):
            conversation_text += f"User: {user_msg[:100]}...\n"
            if assistant_msg:
                conversation_text += f"Assistant: {assistant_msg[:100]}...\n"
        
        # Use a lightweight free model for summarization
        summary_prompt = f"""Create a very short (2-4 words) topic summary for this conversation. Use lowercase with underscores, no spaces. Examples: "python_coding", "travel_advice", "cooking_tips", "math_help", "job_interview".

Conversation:
{conversation_text}

Summary:"""

        # Make API call with lightweight model
        data = {
            "model": "meta-llama/llama-3.3-8b-instruct:free",
            "messages": [{"role": "user", "content": summary_prompt}],
            "temperature": 0.3,
            "max_tokens": 20
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                summary = result['choices'][0]['message']['content'].strip()
                # Clean up the summary
                summary = summary.replace('"', '').replace("'", "").replace(' ', '_').lower()
                summary = re.sub(r'[^a-z0-9_]', '', summary)[:20]
                return summary if summary else "conversation"
        
        # Fallback to simple topic detection
        combined_text = " ".join(user_messages[:2]).lower()
        if any(word in combined_text for word in ['code', 'program', 'python', 'javascript', 'html']):
            return "coding_help"
        elif any(word in combined_text for word in ['travel', 'trip', 'vacation', 'visit']):
            return "travel_advice"
        elif any(word in combined_text for word in ['cook', 'recipe', 'food', 'eat']):
            return "cooking_tips"
        elif any(word in combined_text for word in ['work', 'job', 'career', 'interview']):
            return "career_advice"
        else:
            return "general_chat"
            
    except Exception as e:
        return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def save_session_metadata(session_dir, summary):
    """Save session metadata including the human-readable summary"""
    metadata = {
        "summary": summary,
        "created": datetime.datetime.now().isoformat(),
        "session_id": os.path.basename(session_dir)
    }
    metadata_file = os.path.join(session_dir, "metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)


def get_session_summary(session_dir):
    """Get the human-readable summary for a session"""
    metadata_file = os.path.join(session_dir, "metadata.json")
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return metadata.get('summary', os.path.basename(session_dir))
        except:
            pass
    return os.path.basename(session_dir)


def summarize_messages(messages, api_key, model=None):
    """
    Summarize a list of messages using AI to preserve context while reducing tokens.
    
    Args:
        messages: List of message dictionaries to summarize
        api_key: OpenRouter API key
        model: Model to use for summarization (uses user's current model)
        
    Returns:
        str: Concise summary of the messages
    """
    try:
        # Format messages for summarization
        conversation_text = ""
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            # Handle multimodal content
            if isinstance(content, list):
                text_parts = [item.get('text', '') for item in content if isinstance(item, dict) and item.get('type') == 'text']
                content = ' '.join(text_parts)
            conversation_text += f"{role.upper()}: {content}\n\n"
        
        # Create summarization prompt
        summary_request = [
            {
                "role": "system",
                "content": "You are a helpful assistant that creates concise summaries of conversations. Preserve key information, decisions, code snippets, and important context. Be brief but comprehensive."
            },
            {
                "role": "user",
                "content": f"Please provide a concise summary of the following conversation, preserving important details, decisions, and context:\n\n{conversation_text}\n\nSummary:"
            }
        ]
        
        # Make API request for summary
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": model,
            "messages": summary_request,
            "temperature": 0.3,
            "max_tokens": 500,
            "stream": False
        }
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result['choices'][0]['message']['content'].strip()
            return summary
        else:
            return f"[Previous conversation with {len(messages)} messages]"
            
    except Exception as e:
        console.print(f"[yellow]Warning: Could not generate summary: {str(e)}[/yellow]")
        return f"[Previous conversation with {len(messages)} messages]"


def manage_context_window(conversation_history, max_tokens=8000, model_name="cl100k_base", config=None):
    """Manage the context window to prevent exceeding token limits with optional summarization"""
    # Always keep the system message
    system_message = conversation_history[0] if conversation_history else None
    if not system_message:
        return conversation_history, 0

    # Count total tokens in the conversation
    total_tokens = 0
    for msg in conversation_history:
        content = msg.get("content", "")
        # Handle multimodal content
        if isinstance(content, list):
            text_parts = [item.get('text', '') for item in content if isinstance(item, dict) and item.get('type') == 'text']
            content = ' '.join(text_parts)
        total_tokens += count_tokens(str(content), model_name)

    # If we're under the limit, no need to trim
    if total_tokens <= max_tokens:
        return conversation_history, 0

    # Check if auto-summarization is enabled
    auto_summarize = config.get('auto_summarize', True) if config else True
    summarize_threshold = config.get('summarize_threshold', 0.7) if config else 0.7
    
    # Calculate how many tokens we need to free up
    tokens_to_free = total_tokens - int(max_tokens * summarize_threshold)
    
    if auto_summarize and len(conversation_history) > 3:
        # Collect old messages to summarize
        messages_to_summarize = []
        current_token_count = 0
        
        # Start from index 1 (after system message) and collect messages until we have enough tokens
        for i in range(1, len(conversation_history)):
            msg = conversation_history[i]
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = [item.get('text', '') for item in content if isinstance(item, dict) and item.get('type') == 'text']
                content = ' '.join(text_parts)
            msg_tokens = count_tokens(str(content), model_name)
            
            messages_to_summarize.append(msg)
            current_token_count += msg_tokens
            
            # Stop when we've collected enough messages to summarize
            if current_token_count >= tokens_to_free and len(messages_to_summarize) >= 2:
                break
        
        # Only summarize if we have at least 2 messages and we're not summarizing the most recent exchange
        if len(messages_to_summarize) >= 2 and len(messages_to_summarize) < len(conversation_history) - 2:
            api_key = config.get('api_key') if config else None
            user_model = config.get('model') if config else 'openai/gpt-4o'
            if api_key:
                summary = summarize_messages(messages_to_summarize, api_key, user_model)
                
                # Create new history with summary
                new_history = [system_message]
                summary_msg = {
                    "role": "system",
                    "content": f"[Summary of previous conversation]\n{summary}"
                }
                new_history.append(summary_msg)
                
                # Add remaining messages after the summarized ones
                new_history.extend(conversation_history[1 + len(messages_to_summarize):])
                
                console.print(f"[cyan]ℹ️  Summarized {len(messages_to_summarize)} older messages to maintain context within token limits[/cyan]")
                return new_history, len(messages_to_summarize)
    
    # Fallback to trimming if summarization is disabled or failed
    trimmed_history = [system_message]
    current_tokens = count_tokens(str(system_message["content"]), model_name)

    # Add messages from the end (most recent) until we approach the limit
    messages_to_consider = conversation_history[1:]
    trimmed_count = 0

    for msg in reversed(messages_to_consider):
        content = msg.get("content", "")
        if isinstance(content, list):
            text_parts = [item.get('text', '') for item in content if isinstance(item, dict) and item.get('type') == 'text']
            content = ' '.join(text_parts)
        msg_tokens = count_tokens(str(content), model_name)
        
        if current_tokens + msg_tokens < max_tokens - 1000:  # Leave 1000 tokens buffer
            trimmed_history.insert(1, msg)
            current_tokens += msg_tokens
        else:
            trimmed_count += 1

    # Add a note about trimmed messages if any were removed
    if trimmed_count > 0:
        note = {"role": "system", "content": f"Note: {trimmed_count} earlier messages have been removed to stay within the context window."}
        trimmed_history.insert(1, note)

    return trimmed_history, trimmed_count