#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: run_python_code.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-04-04 22:51:54
# Modified: 2025-05-09 19:48:02

import io
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any

from rich.console import Console
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.panel import Panel
from rich.rule import Rule

# Persistent namespace
persistent_python_env = {}
console = Console()
print = console.print
log = console.log

def python(code: str) -> Dict[str, Any]:
    """Execute Python code with support for GUI subprocess routing and final expression evaluation."""
    import tempfile, subprocess, os, ast

    def _is_gui_code(_code: str) -> bool:
        gui_indicators = [
            "plt.show", "tkinter", "Tk()", "QApplication", "cv2.imshow",
            "Image.show", "NSWindow", "pyplot.show"
        ]
        return any(marker in _code for marker in gui_indicators)

    def _run_gui_code_in_subprocess(_code: str) -> Dict[str, Any]:
        import tempfile, subprocess, os
        with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
            f.write(_code)
            path = f.name
        try:
            subprocess.Popen(['python3', path], start_new_session=True)
            return {
                "status": "success",
                "output": f"Launched GUI subprocess: {path}",
                "error": None,
                "namespace": {}
            }
        except Exception as e:
            return {
                "status": "error",
                "output": None,
                "error": str(e),
                "namespace": {}
            }


    def _extract_last_expression(_code: str) -> str:
        try:
            parsed = ast.parse(_code)
            if parsed.body and isinstance(parsed.body[-1], ast.Expr):
                return compile(ast.Expression(parsed.body[-1].value), "<ast>", "eval")
        except Exception:
            return None

    print(Syntax(f"\n{code.strip()}\n", "python", theme="monokai"))
    answer = Confirm.ask("Execute? [y/n]:", default=False)
    if not answer:
        print("[red]Execution cancelled[/red]")
        return {"status": "cancelled", "message": "Execution aborted by user."}

    if _is_gui_code(code):
        #print("[yellow]GUI code detected. Running in subprocess to support window creation.[/yellow]")
        return _run_gui_code_in_subprocess(code)

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    print(Rule())

    try:
        final_expr = _extract_last_expression(code)
        exec_code = code if final_expr is None else '\n'.join(code.strip().splitlines()[:-1])

        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            if exec_code.strip():
                exec(exec_code, persistent_python_env)
            if final_expr is not None:
                result = eval(final_expr, persistent_python_env)
                persistent_python_env['_'] = result

        stdout_output = stdout_capture.getvalue().strip()
        stderr_output = stderr_capture.getvalue().strip()

        if stdout_output:
            print(stdout_output)
        if stderr_output:
            print(f"[red]Error output:[/red] {stderr_output}")

        print(Rule())

        return {
            "status": "success",
            "output": stdout_output,
            "error": stderr_output if stderr_output else None,
            "namespace": {k: str(v) for k, v in persistent_python_env.items() if not k.startswith('__')}
        }

    except Exception as e:
        stderr_output = stderr_capture.getvalue().strip() or str(e)
        print(f"[red]Execution failed:[/red] {stderr_output}")
        print(Rule())
        return {
            "status": "error",
            "error": stderr_output,
            "output": stdout_capture.getvalue().strip(),
            "namespace": {k: str(v) for k, v in persistent_python_env.items() if not k.startswith('__')}
        }


# Optional interactive use
if __name__ == "__main__":
    user_code = input("Enter Python code to execute: ")
    result = run_python_code(user_code)
    print(result)
