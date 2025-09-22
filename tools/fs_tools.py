import os
from typing import List

from langchain_core.tools import tool
from pydantic import BaseModel, Field

BASE_DIR = os.path.abspath(".")


class ListFilesInput(BaseModel):
    path: str = Field(".", description="Directory path relative to project root")


@tool("list_files", args_schema=ListFilesInput, return_direct=True)
def list_files_tool(path: str = ".") -> List[str]:
    """List files and folders in a directory."""
    full_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        return [f"Path not found: {path}"]
    try:
        return os.listdir(full_path)
    except Exception as e:
        return [f"Error listing files: {str(e)}"]


class ReadFileInput(BaseModel):
    path: str = Field(..., description="File path relative to project root")


@tool("read_file", args_schema=ReadFileInput, return_direct=True)
def read_file_tool(path: str) -> str:
    """Read file content."""
    full_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        return f"File not found: {path}"
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {path}: {str(e)}"


class WriteFileInput(BaseModel):
    path: str = Field(..., description="File path relative to project root")
    content: str = Field(..., description="Content to write")


@tool("write_file", args_schema=WriteFileInput, return_direct=True)
def write_file_tool(path: str, content: str) -> str:
    """Write content to a file (overwrite)."""
    full_path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File {path} written successfully"
    except Exception as e:
        return f"Error writing file {path}: {str(e)}"
