import json 

class ToolRegistry:
    def __init__(self):
        self.__tools = {}
    def register(self, name, fn, schema):
        self.__tools[name] = (fn, schema)
    
    def get_schemas(self):
        return [schema for fn, schema in self.__tools.values()]
    
    def execute(self, name, arguments):
        if name not in self.__tools:
            return f"Error : Unknown tool '{name}'"
        try:
            args = json.loads(arguments or "{}")
            fn, schema = self.__tools[name]
            result = fn(**args)
            # print(result)
            return str(result)
        except Exception as e:
            return f"Error : {e}"
