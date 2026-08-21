import ast

TOOL_SCHEMA = {
    "type" : "function",
    "function":{
        "name": "calculator",
        "description": "evaluate an arithmitic expression string and return the numeric result",
        "parameters":{
            "type": "object",
            "properties":{
                "expression": {"type": "string"}
            },
            "required": ["expression"]
        }
    }
}
def calculator(expression):
    """ evaluates an arithmetic expression string"""
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