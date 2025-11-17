import subprocess
from langchain.tools import tool


@tool("run_terminal_command", return_direct=False)
def run_terminal_command(command: str) -> str:
    """
    Execute a Linux terminal command and return its output.

    Args:
        command (str): The command to run in the shell.

    Returns:
        str: The standard output or error message from the command.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,  # Prevents hanging processes
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[Error] Command failed:\n{result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "[Error] Command timed out after 10 seconds."
    except Exception as e:
        return f"[Exception] {e}"
