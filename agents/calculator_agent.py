"""The calculator specialist.

The evaluator is the one from tool_calling/1-calculator.py. It lives here
too because that filename ("1-calculator.py") is not importable as a module, and
only the checker is allowed to reach into the task folders.
"""
import ast

TOOL_SCHEMA = {
    "type" : "function",
    "function":{
        "name": "calculator",
        "description": ("evaluate an arithmitic expression string and return the numeric "
                        "result. Use this for EVERY calculation, even an easy one - "
                        "supports + - * / ** % and parentheses, e.g. '(17*3 + 4) / 2'"),
        "parameters":{
            "type": "object",
            "properties":{
                "expression": {"type": "string",
                               "description": "the arithmetic expression to evaluate, "
                                              "digits and operators only - no names, no units"}
            },
            "required": ["expression"]
        }
    }
}

def calculator(expression):
    """ evaluates an arithmetic expression string"""
    # ast.parse + a whitelist walk, never eval(): the expression comes from the
    # model, and eval() would happily run __import__('os').system(...).
    tree = ast.parse(expression, mode="eval")
    def evaluate(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants are allowed")

        elif isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / right
            elif isinstance(node.op, ast.Pow):
                return left ** right
            elif isinstance(node.op, ast.Mod):
                return left % right

            raise ValueError("unsupported operator.")

        elif isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)

            if isinstance(node.op, ast.USub):
                return -value
            elif isinstance(node.op, ast.UAdd):
                return value

            raise ValueError("Unsupported unary operator.")

        raise ValueError(f"Unsupported expression: {type(node).__name__}")
    return evaluate(tree.body)


def build_calculator_registry():
    """No service to pass in - this one needs nothing but Python."""
    from core.tools import ToolRegistry
    registry = ToolRegistry()
    registry.register(name="calculator", fn=calculator, schema=TOOL_SCHEMA)
    return registry
