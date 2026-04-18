"""Auto-completion classes for command and file input."""

# Standard library imports
import os

# Third-party imports
try:
    from prompt_toolkit.completion import Completer, Completion
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

# Local imports
from freedomcli.constants import ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE
from freedomcli.utils import format_file_size


class OrChatCompleter(Completer):
    """Optimized command completer with descriptions. (Original: OrChat by Muhamed)"""
    
    # Static command definitions for better performance
    COMMANDS = {
        'clear': 'Clear the screen and conversation history',
        'chat': 'Manage conversation history. Usage: /chat <list|save|resume> [session_id]',
        'new': 'Start a new conversation',
        'cls': 'Clear terminal screen',
        'clear-screen': 'Clear terminal screen',
        'save': 'Save conversation to file',
        'settings': 'Adjust model settings',
        'tokens': 'Show token usage statistics',
        'model': 'Change the AI model',
        'temperature': 'Adjust temperature (0.0-2.0)',
        'system': 'View or change system instructions',
        'speed': 'Show response time statistics',
        'theme': 'Change the color theme',
        'about': 'Show information about FreedomCLI',
        'update': 'Check for updates',
        'thinking': 'Show last AI thinking process',
        'thinking-mode': 'Toggle thinking mode on/off',
        'auto-summarize': 'Toggle auto-summarization of old messages',
        'web': 'Scrape and inject web content. Usage: /web <url>',
        'help': 'Show available commands'
    }
    
    def get_completions(self, document, complete_event):
        """Generate command completions efficiently."""
        text = document.text_before_cursor
        if not text.startswith('/'):
            return
            
        command_part = text[1:].lower()
        for cmd, description in self.COMMANDS.items():
            if cmd.startswith(command_part):
                yield Completion(
                    cmd,
                    start_position=-len(command_part),
                    display_meta=description
                )


class FilePickerCompleter(Completer):
    """Optimized file picker completer for @ symbol."""
    
    # File type icons (static for performance)
    FILE_ICONS = {
        '.py': '🐍', '.js': '📜', '.ts': '📜', '.java': '☕', '.cpp': '⚙️', '.c': '⚙️',
        '.cs': '💙', '.go': '🐹', '.rb': '💎', '.php': '🐘', '.swift': '🍃',
        '.txt': '📄', '.md': '📝', '.json': '📋', '.xml': '📋', '.html': '🌐',
        '.css': '🎨', '.csv': '📊', '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️',
        '.gif': '🖼️', '.webp': '🖼️', '.bmp': '🖼️'
    }
    
    def get_files_in_directory(self, directory: str = ".", filter_text: str = "") -> list:
        """Get filtered files with size checking and icons."""
        try:
            files = []
            full_path = os.path.abspath(directory)
            if not os.path.exists(full_path):
                return files
                
            for item in os.listdir(full_path):
                # Skip hidden files unless specifically requested
                if item.startswith('.') and not filter_text.startswith('.'):
                    continue
                # Apply case-insensitive filter
                if filter_text and filter_text.lower() not in item.lower():
                    continue
                
                item_path = os.path.join(full_path, item)
                
                if os.path.isfile(item_path):
                    file_ext = os.path.splitext(item)[1].lower()
                    if file_ext in ALLOWED_FILE_EXTENSIONS:
                        file_size = os.path.getsize(item_path)
                        icon = self.FILE_ICONS.get(file_ext, '📄')
                        size_str = format_file_size(file_size)
                        
                        if file_size > MAX_FILE_SIZE:
                            display = f"{icon} {item} ({size_str}) [TOO LARGE]"
                            files.append((item, display, False))
                        else:
                            display = f"{icon} {item} ({size_str})"
                            files.append((item, display, True))
                            
                    elif os.path.isdir(item_path):
                        files.append((item + "/", f"📁 {item}/", True))
                        
            # Sort: directories first, then files alphabetically
            files.sort(key=lambda x: (not x[0].endswith('/'), x[0].lower()))
            return files
            
        except (OSError, PermissionError):
            return []
    
    def get_completions(self, document, complete_event):
        """Generate file completions for @ symbol anywhere in text."""
        text = document.text
        cursor_pos = document.cursor_position
        text_before = text[:cursor_pos]
        at_index = text_before.rfind('@')
        
        if at_index == -1:
            return
            
        path_part = text_before[at_index + 1:]
        # Stop if whitespace found (separate word)
        if ' ' in path_part or '\t' in path_part:
            return
        
        # Parse directory and filter
        if '/' in path_part:
            directory = os.path.dirname(path_part)
            filter_text = os.path.basename(path_part)
        else:
            directory = "."
            filter_text = path_part
        
        # Generate completions
        for filename, display_text, selectable in self.get_files_in_directory(directory, filter_text):
            if selectable:
                completion = f"{directory}/{filename}" if directory != "." else filename
                yield Completion(
                    completion,
                    start_position=-len(path_part),
                    display=display_text
                )


class CombinedCompleter(Completer):
    """Efficient combined completer for commands and files."""
    
    def __init__(self):
        self.command_completer = OrChatCompleter()
        self.file_completer = FilePickerCompleter()
    
    def get_completions(self, document, complete_event):
        """Route to appropriate completer based on context."""
        text = document.text
        cursor_pos = document.cursor_position
        
        if text.startswith('/'):
            yield from self.command_completer.get_completions(document, complete_event)
        elif '@' in text[:cursor_pos]:
            yield from self.file_completer.get_completions(document, complete_event)


def create_command_completer():
    """Create a combined completer for FreedomCLI"""
    if not HAS_PROMPT_TOOLKIT:
        return None
    
    return CombinedCompleter()


def get_user_input_with_completion(history=None, after_execute_ref=None):
    """Get user input with command auto-completion and history support"""
    if not HAS_PROMPT_TOOLKIT:
        return input("> ")
    
    try:
        completer = create_command_completer()
        
        # Use provided history or create a new one
        if history is None:
            from prompt_toolkit.history import InMemoryHistory
            history = InMemoryHistory()
        
        from prompt_toolkit import prompt
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.filters import Condition
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.key_binding import KeyBindings
        
        # Create auto-suggest from history
        auto_suggest = AutoSuggestFromHistory()
        
        # Create key bindings for automatic completion and multiline support
        bindings = KeyBindings()
        
        # Track multiline mode
        multiline_mode = [False]  # Use list to allow modification in nested functions
        
        @bindings.add('@')
        def _(event):
            """Auto-trigger file picker completion when '@' is typed"""
            event.app.current_buffer.insert_text('@')
            # Force completion menu to show
            event.app.current_buffer.start_completion()
        
        @bindings.add('/')
        def _(event):
            """Auto-trigger completion when '/' is typed"""
            event.app.current_buffer.insert_text('/')
            # Force completion menu to show
            event.app.current_buffer.start_completion()
        
        # Add bindings for letters to keep completion active after / or #
        for char in 'abcdefghijklmnopqrstuvwxyz.-_0123456789':
            @bindings.add(char)
            def _(event, char=char):
                """Keep completion active while typing after / or @"""
                event.app.current_buffer.insert_text(char)
                # Trigger completion if we're typing after a '/' or have '@' in the text
                text = event.app.current_buffer.text
                cursor_pos = event.app.current_buffer.cursor_position
                
                # Check for command completion
                if text.startswith('/') and len(text) > 1:
                    event.app.current_buffer.start_completion()
                # Check for file picker completion (@ anywhere before cursor)
                elif '@' in text[:cursor_pos]:
                    # Find the last @ before cursor
                    text_before_cursor = text[:cursor_pos]
                    at_index = text_before_cursor.rfind('@')
                    if at_index != -1:
                        # Check if we're still in the file path (no spaces after @)
                        path_part = text_before_cursor[at_index + 1:]
                        if ' ' not in path_part and '\t' not in path_part:
                            event.app.current_buffer.start_completion()
        
        # Add binding for backspace to retrigger completion
        @bindings.add('backspace')
        def _(event):
            """Handle backspace and retrigger completion if needed"""
            if event.app.current_buffer.text:
                event.app.current_buffer.delete_before_cursor()
                # Retrigger completion if we still have / at start or @ anywhere
                text = event.app.current_buffer.text
                cursor_pos = event.app.current_buffer.cursor_position
                
                if text.startswith('/'):
                    event.app.current_buffer.start_completion()
                elif '@' in text[:cursor_pos]:
                    # Find the last @ before cursor
                    text_before_cursor = text[:cursor_pos]
                    at_index = text_before_cursor.rfind('@')
                    if at_index != -1:
                        # Check if we're still in the file path (no spaces after @)
                        path_part = text_before_cursor[at_index + 1:]
                        if ' ' not in path_part and '\t' not in path_part:
                            event.app.current_buffer.start_completion()
        
        # Add binding for Ctrl+Space to manually trigger completion
        @bindings.add('c-space')
        def _(event):
            """Manually trigger completion"""
            event.app.current_buffer.start_completion()
        
        # Add binding for Esc+Enter to toggle multiline mode
        @bindings.add('escape', 'enter')
        def _(event):
            """Toggle multiline mode with Esc+Enter"""
            multiline_mode[0] = not multiline_mode[0]
            if multiline_mode[0]:
                event.app.current_buffer.insert_text('\n')
                # Show indicator that we're in multiline mode
                event.app.invalidate()
            else:
                # Exit multiline mode and submit
                event.app.exit(result=event.app.current_buffer.text)
        
        # Custom prompt function to show multiline indicator
        def get_prompt():
            if multiline_mode[0]:
                return HTML('> <style fg="yellow">[Multi-line] </style>')
            return "> "

        if after_execute_ref is not None and after_execute_ref.get("after_execute"):
            after_execute_ref["after_execute"] = False  # Reset now - we're consuming the flag
            result = "Continue"  # Force result to "Continue" if after_execute was True
            return result

        result = prompt(
            get_prompt,
            completer=completer,
            complete_while_typing=True,
            complete_style="multi-column",
            history=history,
            auto_suggest=auto_suggest,
            enable_history_search=True,
            multiline=Condition(lambda: multiline_mode[0]),
            wrap_lines=True,
            key_bindings=bindings
        )

        return result
    except (KeyboardInterrupt, EOFError):
        raise
    except Exception as e:
        # Fallback to regular input if anything goes wrong
        print(f"[Auto-completion error: {e}]")
        return input("> ")