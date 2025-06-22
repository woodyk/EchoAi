#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: scroll.py
# Author: Wadih Khairallah
# Description: Enhanced text scrolling tool for command-line use
# Created: 2025-05-29 10:53:06
# Modified: 2025-01-20

import sys
import time
import shutil
import argparse
import os
from pathlib import Path

# Platform detection
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')
IS_UNIX = not IS_WINDOWS

# Platform-specific imports and functions
if IS_WINDOWS:
    import msvcrt
    
    def wait_for_key():
        """Wait for user input on Windows"""
        print("[Press SPACE to continue, q to quit, n for next file]", end='\r')
        sys.stdout.flush()
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b' ':
                    return 'continue'
                elif key in (b'q', b'Q'):
                    return 'quit'
                elif key in (b'n', b'N'):
                    return 'next'
    
    def clear_screen():
        """Clear screen on Windows"""
        os.system('cls')
        
else:  # Unix-like systems (Linux, macOS, etc.)
    import termios
    import tty
    
    def wait_for_key():
        """Wait for user input on Unix-like systems"""
        print("[Press SPACE to continue, q to quit, n for next file]", end='\r')
        sys.stdout.flush()
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch == ' ':
                    return 'continue'
                elif ch in ('q', 'Q'):
                    return 'quit'
                elif ch in ('n', 'N'):
                    return 'next'
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def clear_screen():
        """Clear screen on Unix-like systems"""
        os.system('clear')

def clear_line():
    """Clear the current line"""
    term_width = shutil.get_terminal_size((80, 24)).columns
    print('\r' + ' ' * term_width + '\r', end='')
    sys.stdout.flush()

def is_text_file(filepath):
    """Check if a file is likely a text file"""
    text_extensions = {
        '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml',
        '.yaml', '.yml', '.ini', '.cfg', '.conf', '.log', '.sh', '.bash',
        '.c', '.cpp', '.h', '.java', '.rs', '.go', '.rb', '.php', '.pl',
        '.swift', '.kt', '.scala', '.r', '.m', '.mm', '.tex', '.rst',
        '.asciidoc', '.org', '.vim', '.env', '.gitignore', '.dockerignore'
    }
    
    # Check by extension first
    if filepath.suffix.lower() in text_extensions:
        return True
    
    # Check if no extension (often text files)
    if not filepath.suffix and filepath.name not in ('.DS_Store', 'Thumbs.db'):
        return True
    
    # Try to detect by reading first few bytes
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(512)
            if not chunk:  # Empty file
                return True
            # Check for null bytes (binary indicator)
            if b'\x00' in chunk:
                return False
            # Try to decode as UTF-8
            try:
                chunk.decode('utf-8')
                return True
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        chunk.decode(encoding)
                        return True
                    except UnicodeDecodeError:
                        continue
                return False
    except Exception:
        return False

def normalize_line_endings(text):
    """Normalize various line ending styles to Unix style"""
    # Replace Windows line endings
    text = text.replace('\r\n', '\n')
    # Replace old Mac line endings
    text = text.replace('\r', '\n')
    return text

def scroll_text(lines, delay=2, lines_per_page=None, interactive=True, show_line_endings=False):
    """Scroll through lines of text with configurable paging"""
    if lines_per_page is None:
        term_size = shutil.get_terminal_size((80, 24))
        lines_per_page = term_size.lines - 3  # Leave room for progress indicator
    
    # Ensure we have at least 1 line per page
    lines_per_page = max(1, lines_per_page)
    
    # Add line endings if requested
    if show_line_endings:
        lines = [line.rstrip('\n\r') + '$' for line in lines]
    
    total_lines = len(lines)
    if total_lines == 0:
        print("(empty file)")
        return 'complete'
    
    current_line = 0
    
    while current_line < total_lines:
        # Display current page
        page_end = min(current_line + lines_per_page, total_lines)
        page = lines[current_line:page_end]
        
        # Clear screen for better reading experience
        if interactive:
            clear_screen()
        
        # Print the page
        for line in page:
            print(line)
        
        # Show progress
        progress = f"\n[Lines {current_line + 1}-{page_end} of {total_lines}]"
        print(progress)
        
        current_line = page_end
        
        # Handle pagination
        if current_line < total_lines:
            if interactive:
                action = wait_for_key()
                clear_line()  # Clear the key prompt
                
                if action == 'quit':
                    return 'quit'
                elif action == 'next':
                    return 'next'
            else:
                time.sleep(delay)
                if current_line < total_lines:
                    print("\n" + "-" * 40 + "\n")
    
    return 'complete'

def process_file(filepath, args):
    """Process a single file"""
    try:
        # Read file in binary mode first to handle various encodings
        with open(filepath, 'rb') as f:
            raw_content = f.read()
        
        # Try to decode with specified encoding
        try:
            content = raw_content.decode(args.encoding)
        except UnicodeDecodeError:
            # Fall back to other encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    content = raw_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # If all fail, use replace errors
                content = raw_content.decode(args.encoding, errors='replace')
        
        # Normalize line endings
        content = normalize_line_endings(content)
        
        # Split into lines
        lines = content.splitlines()
        
        # Show file header if processing multiple files
        if args.show_headers:
            header = f"\n{'='*60}\nFile: {filepath}\n{'='*60}\n"
            print(header)
            if not args.interactive:
                time.sleep(1)
        
        # Scroll through the file
        result = scroll_text(
            lines,
            delay=args.delay,
            lines_per_page=args.lines,
            interactive=args.interactive,
            show_line_endings=args.show_endings
        )
        
        return result
        
    except PermissionError:
        print(f"Error: Permission denied for file {filepath}", file=sys.stderr)
        return 'error'
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        return 'error'
    except Exception as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        return 'error'

def process_directory(dirpath, args):
    """Process all text files in a directory"""
    path = Path(dirpath)
    
    if not path.exists():
        print(f"Error: Directory does not exist: {dirpath}", file=sys.stderr)
        return
    
    if not path.is_dir():
        print(f"Error: Not a directory: {dirpath}", file=sys.stderr)
        return
    
    text_files = []
    
    # Collect text files
    pattern = '**/*' if args.recursive else '*'
    try:
        for filepath in path.glob(pattern):
            if filepath.is_file() and is_text_file(filepath):
                text_files.append(filepath)
    except PermissionError:
        print(f"Warning: Permission denied for some files in {dirpath}", file=sys.stderr)
    
    # Sort files for consistent ordering
    text_files.sort()
    
    if not text_files:
        print(f"No text files found in {dirpath}", file=sys.stderr)
        return
    
    print(f"Found {len(text_files)} text files to process\n")
    
    # Process each file
    for i, filepath in enumerate(text_files):
        print(f"\nProcessing file {i+1}/{len(text_files)}: {filepath}")
        
        result = process_file(filepath, args)
        
        if result == 'quit':
            break
        elif result == 'complete' and i < len(text_files) - 1:
            if args.interactive:
                print("\n[Press SPACE for next file, q to quit]", end='')
                sys.stdout.flush()
                action = wait_for_key()
                clear_line()
                if action == 'quit':
                    break

def main():
    parser = argparse.ArgumentParser(
        description='Scroll through text content from files, directories, or stdin',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scroll through a single file
  %(prog)s file.txt
  
  # Process stdin
  cat file.txt | %(prog)s
  
  # Process all text files in a directory
  %(prog)s -d /path/to/directory
  
  # Recursively process all text files
  %(prog)s -d /path/to/directory -r
  
  # Non-interactive mode with custom delay
  %(prog)s -n -t 3 file.txt
  
  # Show line endings like 'cat -e'
  %(prog)s -e file.txt
  
  # Process with specific encoding
  %(prog)s --encoding latin-1 old_file.txt
"""
    )
    
    parser.add_argument('input', nargs='?', help='Input file path (omit to read from stdin)')
    parser.add_argument('-d', '--directory', help='Process all text files in directory')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='Recursively process subdirectories')
    parser.add_argument('-t', '--delay', type=float, default=2.0,
                       help='Delay between pages in non-interactive mode (default: 2.0 seconds)')
    parser.add_argument('-l', '--lines', type=int,
                       help='Lines per page (default: terminal height - 3)')
    parser.add_argument('-n', '--non-interactive', dest='interactive',
                       action='store_false', default=True,
                       help='Non-interactive mode (auto-scroll with delay)')
    parser.add_argument('-e', '--show-endings', action='store_true',
                       help='Show line endings with $ (like cat -e)')
    parser.add_argument('--encoding', default='utf-8',
                       help='File encoding (default: utf-8)')
    parser.add_argument('--no-headers', dest='show_headers', action='store_false',
                       default=True, help="Don't show file headers when processing multiple files")
    
    args = parser.parse_args()
    
    try:
        # Determine input source
        if args.directory:
            # Process directory
            process_directory(args.directory, args)
        elif args.input:
            # Check if input is a file or directory
            path = Path(args.input)
            if path.is_dir():
                process_directory(path, args)
            elif path.is_file():
                process_file(path, args)
            else:
                print(f"Error: '{args.input}' is not a valid file or directory", file=sys.stderr)
                sys.exit(1)
        else:
            # Read from stdin
            if sys.stdin.isatty():
                print("Error: No input provided. Use -h for help.", file=sys.stderr)
                sys.exit(1)
            
            # Read all stdin content
            content = sys.stdin.read()
            
            # Normalize line endings
            content = normalize_line_endings(content)
            
            # Split into lines
            lines = content.splitlines()
            
            scroll_text(
                lines,
                delay=args.delay,
                lines_per_page=args.lines,
                interactive=args.interactive,
                show_line_endings=args.show_endings
            )
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except BrokenPipeError:
        # Handle broken pipe gracefully (e.g., when piping to head)
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
