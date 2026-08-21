def make_tool_schema(name, description, parameters):
    return{'type': "function",
           'function': {
               "name": name,
               "description": description,
               "parameters" : parameters
           }
           }