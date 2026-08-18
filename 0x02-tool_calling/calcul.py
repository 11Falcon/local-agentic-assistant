import ast
TOOL_SCHEMA = {
    "type" : "function",
    "function":{
        "name" : "calculator",
        "description" : "evaluate an arithmitic string expression and return the numeric result.",
        "parameters":{
            "type": "object",
            "properties":{
                "expression":{"type": "string"},
            },
            "required": ["expresssion"],
        }
    }
}

def calculator(expression):
    "evaluate an arithmitic expression string and returns the numeric result"
    root = ast.parse(expression, mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("only numeric constant are allowed")
        
        elif isinstance(node, ast.BinOp):
            left = node.left
            right = node.right
            
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Mod):
                return left % right
            if isinstance(node.op, ast.Pow):
                return left ** right
            raise ValueError("not supported Operator")
        
        elif isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)
            
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return value
            raise ValueError("Unsuported Unary operator.")
        raise ValueError()

























def calculator(expression):
    root = ast.parse(expression, mode='eval')

    def evaluate(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constant are allowed")
        elif isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Div):
                return left / right
            elif isinstance(node.op, ast.Mod):
                return left % right
            elif isinstance(node.op, ast.Pow):
                return left ** right
            raise ValueError("Unsupported operator")
        
        elif isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)
            if isinstance(node.op, ast.USub):
                return - value
            elif isinstance(node.op, ast.UAdd):
                return value
            raise ValueError("Unsupported unary operator")