import json
from bson import json_util

class JSONTools:
    """
    A utility class for converting BSON objects to JSON-compatible dictionaries.
    Attributes:
        bson_var (Any): The BSON object to be converted.
        clean_json (dict): The JSON-compatible dictionary representation of the BSON object.
    Methods:
        to_json():
            Converts the BSON object to a JSON-compatible dictionary using json_util.
        convert_to_json():
            Recursively converts the BSON object or its elements (if it's a list or dict) to JSON-compatible dictionaries.
    """
    def __init__(self, bson_var) -> None:
        self.bson_var = bson_var
        self.clean_json = self.to_json()

    def to_json(self):
        return json.loads(json_util.dumps(self.bson_var))
    
    def convert_to_json(self):
        if isinstance(self.bson_var, list):
            return [JSONTools(item).convert_to_json() for item in self.bson_var]
        elif isinstance(self.bson_var, dict):
            return {key: JSONTools(value).convert_to_json() for key, value in self.bson_var.items()}
        elif hasattr(self.bson_var, "__dict__"):
            return JSONTools(self.bson_var.__dict__).convert_to_json()
        else:
            return self.bson_var