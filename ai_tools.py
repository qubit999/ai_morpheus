import os
import inspect
import json
from typing import Annotated, get_type_hints

class AITools():
    """
    AITools class provides various utility methods.
    Methods
    -------
    __init__():
        Initializes the AITools class instance.
    greet_user(user: Annotated[str, "This is the name of the user"]) -> str:
        Greets the user with a personalized message.
        Parameters:
        user (str): This is the name of the user.
        Returns:
        str: Greeting message.
    is_even(number: Annotated[int, "This is the number to check if it is even or not"]) -> bool:
        Checks if a number is even.
        Parameters:
        number (int): Number to check if it is even or not.
        Returns:
        bool: True if number is even, False otherwise.
    return_tools(methods: Annotated[list, "Dictionary containing all tools available in the ToolsAI class"]) -> list:
        Returns all tools available in the ToolsAI class.
        Parameters:
        methods (list): Dictionary containing all tools available in the ToolsAI class.
        Returns:
        list: List of dictionaries containing method details.
    """
    def __init__(self):
        self.toolsai = self

    def greet_user(self, user: Annotated[str, "This is the name of the user"]):
        return f"Hello {user}! How can I help you today? My name is John."
    
    def is_even(self, number: Annotated[int, "This is the number to check if it is even or not"]):
        return number % 2 == 0
        
    def return_tools(self, methods: Annotated[list, "Dictionary containing all tools available in the ToolsAI class"]):
        class_instance = self.toolsai

        tools = []
        for name, method in inspect.getmembers(class_instance, predicate=inspect.ismethod):
            signature = inspect.signature(method)
            if name not in methods:
                continue
            if name == '__init__' or name == 'return_tools':
                continue
            method_details = {
                'type': 'function',
                'function': {
                    'name': name,
                    'description': method.__doc__.strip(),  # Strip whitespace
                    'parameters': {
                        'type': 'object',
                        'properties': {},
                        'required': [],
                        'additionalProperties': False
                    }
                }
            }
            
            for param in signature.parameters.values():
                annotation = param.annotation
                if hasattr(annotation, '__metadata__'):
                    param_type = str(annotation.__origin__.__name__)
                    
                    param_description = annotation.__metadata__[0]
                else:
                    param_type = 'string'
                    param_description = f'Description for {param.name}'
                
                param_details = {
                    'type': param_type,
                    'description': param_description
                }
                
                method_details['function']['parameters']['properties'][param.name] = param_details
                if param.default == param.empty:
                    method_details['function']['parameters']['required'].append(param.name)
            
            tools.append(method_details)
        return tools
