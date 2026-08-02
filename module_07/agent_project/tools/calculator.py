import ast
import math
import operator

SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": (
            "Evaluate a mathematical expression. Supports +, -, *, /, ** "
            "(power), parentheses, and the functions sqrt, sin, cos, log. "
            "Use this for any arithmetic instead of computing it yourself."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression, e.g. '(3.5 * 12) / sqrt(4)'",
                }
            },
            "required": ["expression"],
        },
    },
}

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_FUNCS = {name: getattr(math, name) for name in ("sqrt", "sin", "cos", "log")}


def _eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed")
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
        return _FUNCS[node.func.id](*[_eval(a) for a in node.args])
    raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def execute(expression: str):
    """Raises ValueError on invalid/unsafe input."""
    tree = ast.parse(expression, mode="eval")
    return {"expression": expression, "result": _eval(tree.body)}
