"""Tool functions for the inductive coding system."""

import os
import subprocess
from pathlib import Path
from typing import Any


def read_document_from_file(file_name: str, directory: str = ".") -> str:
    """Read a document from a file in the specified directory.
    
    Args:
        file_name: The name of the file to read
        directory: The directory containing the file (default: current directory)
    
    Returns:
        The content of the file as a string
        
    Raises:
        FileNotFoundError: If the file is not found
        IOError: If there's an error reading the file
    """
    directory_path = Path(directory)
    file_path = directory_path / file_name
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with a different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()


def grep_search_directory(pattern: str, directory: str = ".", include_pattern: str = "*") -> list[str]:
    """Search for a pattern in files within a directory using grep.
    
    Args:
        pattern: The regex pattern to search for
        directory: The directory to search in (default: current directory)
        include_pattern: File glob pattern to include (default: "*" for all files)
    
    Returns:
        A list of matching lines with their file paths and line numbers
        Format: "file_path:line_number:matching_line"
        
    Raises:
        ValueError: If the directory doesn't exist or if grep fails
    """
    directory_path = Path(directory)
    
    if not directory_path.exists():
        raise ValueError(f"Directory not found: {directory_path}")
    
    if not directory_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")
    
    results = []
    
    # Use grep command (or findstr on Windows)
    try:
        if os.name == 'nt':  # Windows
            # Use findstr for Windows
            cmd = [
                'findstr',
                '/r',  # Regular expression
                '/n',  # Include line numbers
                '/s',  # Search subdirectories
                pattern,
                str(directory_path / include_pattern)
            ]
        else:  # Unix-like systems
            # Use grep for Unix-like systems
            cmd = [
                'grep',
                '-r',  # Recursive
                '-n',  # Include line numbers
                '-E',  # Extended regex
                pattern,
                str(directory_path)
            ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=directory_path
        )
        
        if result.stdout:
            results = result.stdout.strip().split('\n')
            results = [line for line in results if line.strip()]
        
        return results
    
    except Exception as e:
        raise ValueError(f"Error searching directory: {str(e)}")
