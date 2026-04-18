"""File validation, attachment processing, and content extraction."""

# Standard library imports
import base64
import os
import re

# Local imports
from freedomcli.constants import ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE, console
from freedomcli.utils import format_file_size


def validate_file_security(file_path):
    """Validate file for security concerns before processing"""
    try:
        # Check if file exists and is readable
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        if not os.path.isfile(file_path):
            return False, "Path is not a file"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large ({format_file_size(file_size)}). Maximum allowed: {format_file_size(MAX_FILE_SIZE)}"
        
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in ALLOWED_FILE_EXTENSIONS:
            return False, f"File type '{file_ext}' not allowed. Allowed types: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}"
        
        # Basic path traversal prevention
        normalized_path = os.path.normpath(file_path)
        if '..' in normalized_path:
            return False, "Invalid file path detected"
        
        # Check for executable files (additional security)
        dangerous_extensions = {'.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.jar', '.sh'}
        if file_ext in dangerous_extensions:
            return False, f"Executable file type '{file_ext}' not allowed for security reasons"
        
        return True, "File validation passed"
    
    except Exception as e:
        return False, f"File validation error: {str(e)}"


def extract_file_content(file_path, file_ext):
    """Extract and format content from different file types"""
    # Determine file type based on extension
    if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
        return "image", ""

    elif file_ext in ['.pdf']:
        # Basic PDF handling - just mention it's a PDF
        return "PDF document", "[PDF content not displayed in chat, but AI can analyze the document]"

    elif file_ext in ['.py', '.js', '.java', '.cpp', '.c', '.cs', '.go', '.rb', '.php', '.ts', '.swift']:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return "code", f"```{file_ext[1:]}\n{content}\n```"

    elif file_ext in ['.txt', '.md', '.csv']:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return "text", content

    elif file_ext in ['.json', '.xml']:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return "data", f"```{file_ext[1:]}\n{content}\n```"

    elif file_ext in ['.html', '.css']:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return "web", f"```{file_ext[1:]}\n{content}\n```"
    
    # Default: try to read as text
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return "text", content
    except Exception:
        return "unknown", "[File content could not be read]"


def process_file_upload(file_path, conversation_history):
    """Process a file upload and add its contents to the conversation"""
    try:
        # Validate file security first
        is_valid, validation_message = validate_file_security(file_path)
        if not is_valid:
            return False, f"Security validation failed: {validation_message}"

        # Read file with proper encoding handling
        try:
            with open(file_path, 'r', encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding for non-UTF8 files
            with open(file_path, 'r', encoding="latin-1") as f:
                content = f.read()
        
        # Limit content size for processing
        max_content_length = 50000  # 50KB of text content
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[Content truncated due to size limit]"

        file_ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)

        # Sanitize file name to prevent issues
        safe_file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)

        # Determine file type and create appropriate message
        if file_ext in ['.py', '.js', '.java', '.cpp', '.c', '.cs', '.go', '.rb', '.php', '.ts', '.swift']:
            file_type = "code"
            message = f"I'm uploading a code file named '{safe_file_name}'. Please analyze it:\n\n```{file_ext[1:]}\n{content}\n```"
        elif file_ext in ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.css']:
            file_type = "text"
            message = f"I'm uploading a text file named '{safe_file_name}'. Here are its contents:\n\n{content}"
        else:
            file_type = "unknown"
            message = f"I'm uploading a file named '{safe_file_name}'. Here are its contents:\n\n{content}"

        # Add to conversation history
        conversation_history.append({"role": "user", "content": message})
        return True, f"File '{safe_file_name}' uploaded successfully as {file_type}."
    except Exception as e:
        console.print(f"[red]File processing error: {str(e)}[/red]")
        return False, f"Error processing file: {str(e)}"


def handle_attachment(file_path, conversation_history):
    """Enhanced file attachment handling with preview and metadata"""
    try:
        # Validate file security first
        is_valid, validation_message = validate_file_security(file_path)
        if not is_valid:
            return False, f"Security validation failed: {validation_message}"

        # Get file information
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        file_size = os.path.getsize(file_path)
        file_size_formatted = format_file_size(file_size)

        # Sanitize file name
        safe_file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)

        # Determine file type and create appropriate message
        file_type, content = extract_file_content(file_path, file_ext)

        # Create a message that includes metadata about the attachment
        message = f"I'm sharing a file: **{safe_file_name}** ({file_type}, {file_size_formatted})\n\n"

        if file_type == "image":
            # For images, validate and process safely
            if file_size > 5 * 1024 * 1024:  # 5MB limit for images
                return False, "Image file too large (max 5MB)"
            
            try:
                with open(file_path, 'rb') as img_file:
                    image_data = img_file.read()
                    # Basic image validation (check for image headers)
                    if not (image_data.startswith(b'\xff\xd8') or  # JPEG
                           image_data.startswith(b'\x89PNG') or  # PNG
                           image_data.startswith(b'GIF8') or     # GIF
                           image_data.startswith(b'RIFF')):     # WebP
                        return False, "Invalid or corrupted image file"
                    
                    base64_image = base64.b64encode(image_data).decode('utf-8')

                # Add to messages with proper format for multimodal models
                conversation_history.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": message},
                        {"type": "image_url", "image_url": {"url": f"data:image/{file_ext[1:]};base64,{base64_image}"}}
                    ]
                })
                return True, f"Image '{safe_file_name}' attached successfully."
            except Exception as e:
                return False, f"Error processing image: {str(e)}"
        else:
            # For other file types, add content to the message
            message += content
            conversation_history.append({"role": "user", "content": message})
            return True, f"File '{safe_file_name}' attached successfully as {file_type}."

    except Exception as e:
        console.print(f"[red]Attachment processing error: {str(e)}[/red]")
        return False, f"Error processing attachment: {str(e)}"


def process_attachment_ui(file_path, conversation_history):
    """Handles the UI and logic for attaching a file."""
    # Handle relative paths - make them absolute
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        console.print(f"[red]File not found: {file_path}[/red]")
        console.print("[dim]Make sure the file path is correct and the file exists.[/dim]")
        return False

    # Show attachment preview
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_path)[1].lower()
    try:
        file_size = os.path.getsize(file_path)
        file_size_formatted = format_file_size(file_size)
    except OSError:
        file_size_formatted = "Unknown"

    from rich.panel import Panel
    console.print(Panel.fit(
        f"File: [bold]{file_name}[/bold]\n"
        f"Type: {file_ext[1:].upper() if file_ext else 'Unknown'}\n"
        f"Size: {file_size_formatted}",
        title="📎 Attachment Preview",
        border_style="cyan"
    ))

    # Process the file attachment
    success, message = handle_attachment(file_path, conversation_history)
    if success:
        console.print(f"[green]{message}[/green]")
        return True
    else:
        console.print(f"[red]{message}[/red]")
        return False