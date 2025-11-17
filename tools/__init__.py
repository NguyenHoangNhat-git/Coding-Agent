from .fs_tools import list_files_tool, read_file_tool, write_file_tool
from .terminal_tools import run_terminal_command
from .web_tools import fetch_website_text, web_search

TOOLS = {
    "list_files_tool": list_files_tool,
    "read_file_tool": read_file_tool,
    "write_file_tool": write_file_tool,
    "run_terminal_command": run_terminal_command,
    "fetch_website_text": fetch_website_text,
    "web_search": web_search,
}
