"""
Tool 4 — Safe Code Execution
Runs Python code in a restricted sandbox using RestrictedPython.
Supports: math, statistics, string ops, list comprehensions.
Blocks: file I/O, network calls, os/subprocess, imports of dangerous modules.
"""
import io
import sys
import math
import statistics
from langchain.tools import tool
from RestrictedPython import compile_restricted, safe_globals, safe_builtins
from RestrictedPython.Guards import guarded_iter_unpack_sequence


# Whitelist of safe modules the agent can use
SAFE_MODULES = {
    "math": math,
    "statistics": statistics,
}

BLOCKED_BUILTINS = {"open", "exec", "eval", "__import__", "compile", "input"}


def _build_restricted_globals() -> dict:
    globs = safe_globals.copy()
    globs["__builtins__"] = {
        k: v for k, v in safe_builtins.items()
        if k not in BLOCKED_BUILTINS
    }
    globs["_getiter_"] = iter
    globs["_getattr_"] = getattr
    globs["_inplacevar_"] = lambda op, x, y: x + y if op == "+=" else x
    globs["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence

    # Inject safe modules
    for name, mod in SAFE_MODULES.items():
        globs[name] = mod

    return globs


@tool
def execute_python(code: str) -> str:
    """
    Execute Python code safely in a sandbox.
    Use this for calculations, data processing, sorting, statistics,
    string manipulation, and algorithmic tasks.
    DO NOT use for file I/O, network requests, or system calls — those are blocked.
    Input: a string of valid Python code.
    The last expression or any print() output will be returned.
    """
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        byte_code = compile_restricted(code, filename="<agent_code>", mode="exec")
        globs = _build_restricted_globals()
        locs: dict = {}

        exec(byte_code, globs, locs)  # noqa: S102

        output = buffer.getvalue().strip()

        # If no print output, return the last assigned variable
        if not output and locs:
            last_var = list(locs.values())[-1]
            output = str(last_var)

        return output if output else "Code executed successfully (no output)."

    except SyntaxError as e:
        return f"Syntax error in code: {e}"
    except Exception as e:
        return f"Execution error: {type(e).__name__}: {e}"
    finally:
        sys.stdout = old_stdout
