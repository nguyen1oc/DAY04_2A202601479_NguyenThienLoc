from __future__ import annotations

import re
from typing import Any

def calculate(expression: str) -> dict[str, Any]:
    expr_clean = expression.strip()
    # Validate that the expression only contains digits, whitespace, and basic math operators
    if not re.match(r"^[\d\s+\-*/().]+$", expr_clean):
        return {
            "tool": "calculator",
            "expression": expression,
            "error": "unsafe_expression",
            "message": "Only basic arithmetic operators (+, -, *, /, parentheses) and numbers are allowed."
        }
    try:
        # Evaluate safely with disabled builtins
        result = eval(expr_clean, {"__builtins__": None}, {})
        # Convert float to integer if it represents a whole number
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return {
            "tool": "calculator",
            "expression": expression,
            "result": result
        }
    except Exception as exc:
        return {
            "tool": "calculator",
            "expression": expression,
            "error": type(exc).__name__,
            "message": str(exc)
        }
