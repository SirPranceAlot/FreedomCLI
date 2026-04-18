<div align="center">

# 🤖 FreedomCLI

[![PyPI version](https://img.shields.io/pypi/v/freedomcli?color=86efac&style=for-the-badge&logo=pypi&logoColor=black)](https://badge.fury.io/py/freedomcli)
[![License: MIT](https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge&logo=opensource&logoColor=white)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-10b981?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Downloads](https://img.shields.io/pepy/dt/freedomcli?color=1f2937&style=for-the-badge&logo=download&logoColor=white)](https://pepy.tech/project/freedomcli)
[![GitHub Stars](https://img.shields.io/github/stars/oop7/OrChat?color=86efac&style=for-the-badge&logo=github&logoColor=black)](https://github.com/oop7/OrChat/stargazers)

[🚀 Installation](#installation) • [✨ Features](#features) • [💬 Chat Commands](#chat-commands) • [🗂️ Conversation Management](#conversation-management) • [📁 File Attachment](#file-attachment) • [🧠 Thinking Mode](#thinking-mode) • [⚙️ Configuration](#configuration) • [🔍 Troubleshooting](#troubleshooting) • [🤝 Contributing](#contributing)

A powerful CLI for chatting with AI models through OpenRouter with streaming responses, token tracking, auto-update checking, multi-line input, conversation management with AI-generated summaries, and extensive customization options.

*FreedomCLI is a fork of [OrChat](https://github.com/oop7/OrChat) by Muhamed, used under the MIT License.*

</div>


<a id="features"></a>
## ✨ Features

<details>
<summary><strong>🔗 Core Features</strong></summary>

- **Universal Model Access**: Connect to any AI model available on OpenRouter with dynamic model retrieval
- **Interactive Chat**: Enjoy a smooth conversation experience with real-time streaming responses
- **Rich Markdown Rendering**: View formatted text, code blocks, tables and more directly in your terminal
- **Agentic Shell Access**: The assistant can request commands via `[EXECUTE: ...]`, with human approval and contextual output injection
- **Security Gating**: Every command request shows a color-coded risk panel (safe/warning/critical) before you choose to run it
- **Performance Analytics**: Track token usage, response times, and total cost with accurate API-reported counts
- **Command Auto-completion**: Intelligent command suggestions, prompt history navigation, and inline auto-suggest while typing
- **Pricing Display**: Real-time pricing information displayed during active chat sessions
- **Auto-Update System**: Automatic update checking at startup with pip integration
- **Multi-line Input Support**: Compose multi-paragraph messages with `Esc+Enter` and visual feedback
- **Conversation Management**: Save, list, and resume conversations with AI-generated topic summaries
- **Auto-Summarization**: Intelligently summarizes old messages instead of trimming them to preserve context within token limits
- **Session Persistence**: Resume conversations exactly where you left off with full context
- **Web Scraping**: Fetch and analyze web content directly in your conversations with automatic URL detection

</details>

<details>
<summary><strong>📎 File & Media Support</strong></summary>

- **Smart File Picker**: Attach files anywhere in your message using `@` (e.g., `analyze @myfile.py`)
- **Attachment Preview**: See filename, type, and size before injecting content into the conversation
- **Multimodal Support**: Share images and various file types with compatible AI models
- **Enhanced File Processing**: Better error handling, security validation (10 MB limit), and path sanitation
- **Web Content Scraping**: Fetch and inject web content from URLs with automatic detection and clean markdown conversion

</details>

<details>
<summary><strong>🧠 Advanced Features</strong></summary>

- **Smart Thinking Mode**: See the AI's reasoning process with compatible models
- **Conversation Export**: Save conversations as Markdown, HTML, or JSON (the supported formats in-app)
- **Smart Context Management**: Automatically summarizes or trims history to stay within token limits
- **AI Session Summaries**: Generates short, meaningful names for saved sessions
- **Customizable Themes**: Choose from different visual themes for your terminal

</details>

<details>
<summary><strong>⌨️ Interactive Input Features</strong></summary>

- **Multi-line Input**: Use `Esc+Enter` to toggle multi-line mode, with status indicator and seamless toggling
- **Command History Navigation**: Press ↑/↓ arrow keys to cycle through previous prompts and commands
- **History Search**: Use Ctrl+R to search through your prompt history with keywords
- **Automatic Command Completion**: Start typing "/" and command suggestions appear instantly - no Tab key needed!
- **Auto-Suggest from History**: Previous commands and prompts appear as grey suggestions as you type
- **Smart File Picker**: Use `@` anywhere in your message for inline file selection with auto-completion and previews
- **Double Ctrl+C Exit**: Press Ctrl+C twice within 2 seconds to gracefully exit the chat session

**💡 How Auto-Completion Works:**
- Type `/` → All available commands appear automatically
- Type `/c` → Filters to commands starting with 'c' (clear, cls, clear-screen, etc.)
- Type `/temp` → Shows `/temperature` command
- Type `/think` → Shows `/thinking` and `/thinking-mode` commands
- No Tab key required - completions appear as you type!

**💡 How File Picker Works:**
- Type `@` anywhere in your message to open the file picker
- Choose files interactively with inline metadata previews
- Insert filenames naturally into your prompt, e.g., `examine @test.py and check for errors`
- File picker works anywhere in your message, not just at the beginning

**💡 How to Exit:**
- Press **Ctrl+C** once → Shows "Press Ctrl+C again to exit" message
- Press **Ctrl+C** again within 2 seconds → Gracefully exits the chat
- This prevents accidental exits while allowing quick termination when needed

</details>
<details>
<summary><strong>🛡️ Command Execution Workflow </strong></summary>

FreedomCLI supports secure, agentic shell access so the AI can help you explore your project without ever leaving the terminal.

1. **Structured Requests**: The assistant emits `[EXECUTE: your_command]` inside its response when it needs shell access.
2. **Risk Panel**: FreedomCLI classifies the command (Safe 🟢, Warning 🟠, Critical 🔴) based on keywords such as `rm`, `pip install`, etc., and shows the OS context plus the exact command.
3. **Explicit Approval**: You must confirm with `y/n`. Declining keeps the conversation going; the AI is notified that access was denied.
4. **Sandboxed Execution**: Approved commands run through your native shell with a 30-second timeout, capturing both stdout and stderr (truncated after 5 000 chars to protect context length).
5. **Automatic Feedback**: Results are added back to the conversation so the AI can reason over the output immediately.

This flow keeps you in control while still giving the model the ability to `dir`, `find`, `grep`, or run tests when you approve it.
</details>

<a id="installation"></a>
## 🚀 Installation

<details>
<summary><strong>📦 Installation Methods</strong></summary>

### From PyPI (Recommended)

```bash
pip install freedomcli
```
```bash
# Run the application
freedomcli
```

### From Source

```bash
git clone https://github.com/oop7/OrChat.git
cd OrChat
pip install -e .

# Run directly (development)
python -m orchat.main
```

</details>

<details>
<summary><strong>📋 Prerequisites</strong></summary>

- Python 3.9 or higher
- An OpenRouter API key (get one at [OpenRouter.ai](https://openrouter.ai))
- Optional: [fzf](https://github.com/junegunn/fzf) + `pyfzf` for fuzzy model selection

</details>

<details>
<summary><strong>🏁 Getting Started</strong></summary>

1. Install FreedomCLI using one of the methods above
2. Run the setup wizard
   - After a PyPI install:
     ```bash
     freedomcli --setup
     ```
   - From a cloned repository:
     ```bash
     python -m orchat.main --setup
     ```
3. Enter your OpenRouter API key when prompted
4. Select your preferred AI model and configure settings
5. Start chatting!

</details>

<details>
<summary><strong>🪛 Add-Ons</strong></summary>

### FZF fuzzy search (Enhanced Model Selection)

1. Install fzf and pyfzf

   - Install pyfzf
     ```bash
     pip install pyfzf
     ```
   - Fzf can be downloaded from https://github.com/junegunn/fzf?tab=readme-ov-file#installation

2. Ensure fzf is in your path
3. From now on, the model selection will use fzf for powerful fuzzy search and filtering capabilities!

**Note**: If fzf is not installed, FreedomCLI will automatically fall back to standard model selection.

</details>

<a id="configuration"></a>
## ⚙️ Configuration

<details>
<summary><strong>🔧 Configuration Methods</strong></summary>

FreedomCLI can be configured in multiple ways:

1. **Setup Wizard**: Run `freedomcli --setup` (or `python -m orchat.main --setup` inside the repo) for interactive configuration
2. **Config File**: Edit the `config.ini` file in the application directory
3. **Environment Variables**: Create a `.env` file with your configuration
4. **System Environment Variables**: Set environment variables directly in your system (recommended for security)

**Enhanced Environment Support**: FreedomCLI now supports system/user environment variables, removing the strict requirement for `.env` files.

</details>

<details>
<summary><strong>📄 Configuration Examples</strong></summary>

Example `.env` file:

```
OPENROUTER_API_KEY=your_api_key_here
```

Example `config.ini` structure:

```ini
[API]
OPENROUTER_API_KEY = your_api_key_here

[SETTINGS]
MODEL = anthropic/claude-3-opus
TEMPERATURE = 0.7
SYSTEM_INSTRUCTIONS = You are a helpful AI assistant.
THEME = default
MAX_TOKENS = 8000
AUTOSAVE_INTERVAL = 300
STREAMING = True
THINKING_MODE = False
```

</details>

<details>
<summary><strong>🖥️ Command-Line Options</strong></summary>

- `--setup`: Run the setup wizard
- `--model MODEL`: Specify the model to use (e.g., `--model "anthropic/claude-3-opus"`)
- `--task {creative,coding,analysis,chat}`: Optimize for a specific task type
- `--image PATH`: Analyze an image file

</details>

<a id="chat-commands"></a>
## 💬 Chat Commands

| Command                   | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| `/help`                   | Show available commands                               |
| `/new`                    | Start a new conversation                              |
| `/clear`                  | Clear conversation history                            |
| `/cls` or `/clear-screen` | Clear the terminal screen                             |
| `/save [format]`          | Save conversation (formats: md, html, json)            |
| `/chat list`              | List saved conversations with human-readable summaries |
| `/chat save`              | Save current conversation with auto-generated summary  |
| `/chat resume <session>`  | Resume a saved conversation by name or ID              |
| `/model`                  | Change the AI model                                   |
| `/temperature <0.0-2.0>`  | Adjust temperature setting                            |
| `/system`                 | View or change system instructions                    |
| `/tokens`                 | Show token usage statistics (now API-accurate)        |
| `/speed`                  | Show response time statistics                         |
| `/theme <theme>`          | Change the color theme (default, dark, light, hacker) |
| `/thinking`               | Show last AI thinking process                         |
| `/thinking-mode`          | Toggle thinking mode on/off                           |
| `/auto-summarize`         | Toggle auto-summarization of old messages             |
| `/web <url>`              | Scrape and inject web content into context            |
| `/about`                  | Show information about FreedomCLI                     |
| `/update`                 | Check for updates                                     |
| `/settings`               | View current settings                                 |
| **Ctrl+C** (twice)        | **Exit the chat (press twice within 2 seconds)**     |

<a id="conversation-management"></a>
## 💾 Conversation Management

<details>
<summary><strong>📋 Session Management</strong></summary>

FreedomCLI provides powerful conversation management with human-readable session summaries:

**Commands:**
- `/chat list` - View all saved conversations with meaningful names
- `/chat save` - Save current conversation with auto-generated topic summary
- `/chat resume <session>` - Resume any saved conversation by name or ID

**Features:**
- **Smart Summarization**: Uses AI to generate 2-4 word topic summaries (e.g., "python_coding", "travel_advice", "cooking_tips")
- **Fallback Detection**: Automatically detects topics like coding, travel, cooking, career advice
- **Dual Storage**: Saves both human-readable summaries and original timestamp IDs
- **Easy Resume**: Resume conversations using either the summary name or original ID

**Example Session List:**
```
Saved sessions:
general_chat (20250906_141133)
python_coding (20250906_140945)
travel_advice (20250906_140812)
cooking_tips (20250906_140734)
```

</details>

<a id="file-attachment"></a>
## 📁 File Attachment

<details>
<summary><strong>📎 Basic Usage</strong></summary>

Attach files naturally in your messages using the smart file picker:

```
analyze @path/to/your/file.ext for issues
examine @script.py and explain its logic
```
- Use `@` anywhere in your message to attach a file with preview and validation

</details>

<details>
<summary><strong>✨ Enhanced Features</strong></summary>

- **Inline Auto-Completion**: Type `@` and continue typing to filter files; relative paths expand automatically
- **Metadata Preview**: Panel shows filename, extension, and size before injection
- **Improved Error Handling**: Clear messages for missing files, oversized attachments, or unsupported types
- **Security Validation**: Built-in file size (10 MB) and type checks with sanitized filenames
- **Web Content Bridge**: URLs inside your message can be scraped and attached alongside local files

</details>

<details>
<summary><strong>📋 Supported File Types</strong></summary>

- **Images**: JPG, PNG, GIF, WEBP, BMP (rendered with multimodal-friendly data URLs)
- **Code Files**: Python, JavaScript, Java, C++, TypeScript, Swift, etc. (wrapped in fenced code blocks)
- **Text Documents**: TXT, MD, CSV (raw text included)
- **Data Files**: JSON, XML (fenced blocks for readability)
- **Web Files**: HTML, CSS (inlined for context)
- **PDFs**: Metadata only (the assistant is told a PDF was provided)

</details>

## 🌐 Web Scraping

<details>
<summary><strong>🔗 Basic Usage</strong></summary>

Fetch and analyze web content directly in your conversations:

```
/web https://example.com
```

Or simply paste a URL in your message and FreedomCLI will automatically detect it and offer to scrape the content:

```
check out this article: https://example.com/article
```

</details>

<details>
<summary><strong>✨ Features</strong></summary>

- **Automatic URL Detection**: Paste URLs anywhere in your messages and get prompted to scrape them
- **Clean Markdown Conversion**: Web content is converted to readable markdown format
- **Smart Content Extraction**: Removes scripts, styles, navigation, and other non-essential elements
- **Multiple URL Support**: Handle multiple URLs in a single message
- **Content Preview**: See a preview of scraped content before it's injected into context
- **Flexible Options**: Choose to scrape selected URLs or all detected URLs at once

</details>

<details>
<summary><strong>📋 Supported Content Types</strong></summary>

- **HTML Pages**: Automatically converted to clean, readable markdown
- **JSON Data**: Displayed with proper formatting
- **Plain Text**: Rendered as-is for easy reading
- **Articles & Documentation**: Main content extracted automatically

</details>

<a id="thinking-mode"></a>
## 🧠 Thinking Mode

<details>
<summary><strong>🎯 Basic Usage</strong></summary>

FreedomCLI can display the AI's reasoning process with enhanced thinking mode:

```
/thinking-mode       # Toggle thinking mode on/off
/thinking            # Show the most recent thinking process
```

This feature allows you to see how the AI approached your question before giving its final answer. **Auto Thinking Mode** automatically enables this feature when you select models with reasoning support.

</details>

<details>
<summary><strong>✨ Enhanced Features</strong></summary>

- **Improved Detection**: Better extraction of thinking content from model responses
- **Model Compatibility**: Automatic handling of models that don't support thinking mode
- **Visual Indicators**: Clear status indicators showing if thinking mode is enabled
- **Flexible Setup**: Option to enable/disable during model selection

</details>

## 🎨 Themes

<details>
<summary><strong>🎨 Available Themes</strong></summary>

Change the visual appearance with the `/theme` command:

- **default**: Blue user, green assistant
- **dark**: Cyan user, magenta assistant
- **light**: Blue user, green assistant with lighter colors
- **hacker**: Matrix-inspired green text on black

</details>

## 📊 Token Management

<details>
<summary><strong>📊 Smart Context Management</strong></summary>

FreedomCLI intelligently manages conversation context to keep within token limits:

- **Auto-Summarization** (NEW): Instead of simply trimming old messages, FreedomCLI uses AI to create concise summaries of earlier conversation parts, preserving important context while freeing up tokens
- **Configurable Threshold**: Set when summarization kicks in (default: 70% of token limit)
- **Fallback Trimming**: If summarization is disabled or fails, automatically trims old messages
- **Visual Feedback**: Clear notifications when messages are summarized or trimmed
- Displays comprehensive token usage statistics including total tokens and cost tracking
- Shows real-time pricing information during active sessions
- Displays total cost tracking across conversations
- Allows manual clearing of context with `/clear`
- Toggle auto-summarization with `/auto-summarize` command

**How it works:**
- When your conversation approaches the token limit (default: 70%), FreedomCLI automatically summarizes the oldest messages
- The summary preserves key information, decisions, and context in a condensed form
- Recent messages are kept in full to maintain conversation flow
- You can disable this feature and revert to simple trimming with `/auto-summarize`

</details>

## 🔄 Updates

<details>
<summary><strong>🔄 Version Management</strong></summary>

Check for updates with the `/update` command to see if a newer version is available.

</details>



<a id="troubleshooting"></a>
## 🔍 Troubleshooting

<details>
<summary><strong>🔍 Common Issues & Solutions</strong></summary>

- **API Key Issues**: Ensure your OpenRouter API key is correctly set in config.ini, .env file, or system environment variables. FreedomCLI will prompt for re-entry if an incorrect key is detected
- **Insufficient Account Credit**: If you receive a 402 error, check your OpenRouter account balance and add funds as needed
- **Rate Limits (429)**: Too many rapid requests will trigger a yellow "Rate Limit" panel—wait a few seconds or switch to another model with `/model`
- **File Path Problems**: When attaching files via `@`, use quotes for paths with spaces and ensure the path is valid for your OS
- **Model Compatibility**: Some features like thinking mode only work with specific models
- **Conversation Management**: Use `/chat list` to see saved conversations, `/chat save` to save current session, and `/chat resume <name>` to continue previous conversations
- **Command Usage**: Remember that `@` attachments and `/web` scraping prompts can appear anywhere inside your message for flexibility

</details>

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Original project: [OrChat](https://github.com/oop7/OrChat) by Muhamed

<a id="contributing"></a>
## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 🙏 Acknowledgments

<details>
<summary><strong>🙏 Special Thanks</strong></summary>

- [OpenRouter](https://openrouter.ai/) for providing unified API access to AI models
- [Rich](https://github.com/Textualize/rich) for the beautiful terminal interface
- [Muhamed](https://github.com/oop7) - Original author of OrChat, the foundation of FreedomCLI
- All contributors and users who provide feedback and help improve FreedomCLI

</details>