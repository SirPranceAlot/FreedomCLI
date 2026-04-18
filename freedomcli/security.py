"""Command security analysis and risk assessment."""

# Local imports
from freedomcli.constants import DANGEROUS_COMMANDS


def analyze_command_risk(command: str) -> tuple:
    """
    Analyze the risk level of a shell command.
    Returns: (color, icon, warning_message, is_blocked)
    """
    cmd = command.lower().strip()
    
    # Block obviously dangerous command patterns
    dangerous_patterns = [
        'rm -rf', 'rm -r /', 'del /f', 'format ',
        '> /dev/sda', '> /dev/hda',
        ':(){:|:&};:',  # fork bomb
    ]
    
    for pattern in dangerous_patterns:
        if pattern in cmd:
            return "red", "⛔", f"[red]⛔ Command blocked: contains dangerous pattern '{pattern}'[/red]", True
    
    # Extract base command (first word before any pipe or semicolon)
    base_cmd = command.split('|')[0].split(';')[0].split()[0].lower() if command.split('|')[0].split(';')[0].split() else ''
    
    # Check against DANGEROUS_COMMANDS set
    if base_cmd in DANGEROUS_COMMANDS:
        return "red", "⛔", f"[red]⛔ Command '{base_cmd}' is blocked for security reasons[/red]", True
    
    # High risk keywords (file deletion, system modification, network downloads, execution)
    high_risk = [
        'rm ', 'del ', 'erase', 'format ', 'mv ', 'move ', 'python', 'node', 'sh ', 'bash ', 'powershell',
        'pip install', 'npm install', 'git clean', 'dd ', 'wget ', 'chmod ', 'chown ', 'sudo ',
        'reg ', 'attrib'
    ]
    
    # Check for keywords
    for risk in high_risk:
        if risk in cmd or cmd.startswith(risk.strip()):
            return "red", "⛔", "[red]CRITICAL: Command may modify files or system settings[/red]", False
            
    # Medium risk (potential writes, file creation)
    medium_risk = ['mkdir', 'touch', 'echo', '>>', '>', 'copy', 'cp ', 'rename', 'ren ', 'git']
    for risk in medium_risk:
        if risk in cmd:
            return "orange1", "⚠️", "[orange1]WARNING: Command may write to files[/orange1]", False
            
    # Low risk (likely read-only)
    return "green", "🛡️", "[dim green]Safe: Command appears to be read-only[/dim green]", False