"""Constants and global state for FreedomCLI."""

# Standard library imports
from collections import Counter

# Third-party imports
from rich.console import Console

# ============================================================================
# APPLICATION CONSTANTS
# ============================================================================

# App metadata
APP_NAME = "FreedomCLI"
APP_VERSION = "1.0.0"
REPO_URL = "https://github.com/SirPranceAlot/FreedomCLI"
API_URL = "https://github.com/SirPranceAlot/FreedomCLI/releases/latest"

# Security & file constraints
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
ALLOWED_FILE_EXTENSIONS = {
    # Text files
    '.txt', '.md', '.json', '.xml', '.csv',
    # Code files  
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rb', '.php', '.swift',
    # Web files
    '.html', '.css',
    # Image files
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'
}

# Commands that are blocked for security reasons
# These commands can modify system state, escalate privileges, or download malicious content
DANGEROUS_COMMANDS = {
    # File deletion/destruction
    'rm', 'del', 'erase', 'format', 'rmdir', 'rd',
    # Disk/filesystem modification
    'mkfs', 'dd', 'fdisk', 'parted', 'diskpart',
    # Permission/ownership changes
    'chmod', 'chown', 'chgrp', 'icacls', 'attrib',
    # Privilege escalation
    'sudo', 'su', 'doas', 'runas',
    # System control
    'shutdown', 'reboot', 'halt', 'poweroff', 'init', 'systemctl',
    # Kernel/module loading
    'insmod', 'rmmod', 'modprobe', 'kextload',
    # Network configuration
    'iptables', 'netsh', 'route', 'ifconfig', 'ipconfig',
    # Process termination
    'kill', 'killall', 'pkill', 'taskkill',
    # Network downloads (could download malware)
    'wget', 'certutil',
    # Script interpreters (bypasses shell=False protection)
    'python', 'python3', 'python2', 'node', 'ruby', 'perl', 'php',
    'sh', 'bash', 'zsh', 'fish', 'dash',
    'powershell', 'pwsh', 'cmd',
    # Package managers (could install malicious packages)
    'pip', 'pip3', 'npm', 'yarn', 'gem', 'cargo', 'apt', 'apt-get',
    'yum', 'dnf', 'pacman', 'brew', 'choco', 'winget',
}

# Global state
console = Console()
last_thinking_content = ""
command_history = []