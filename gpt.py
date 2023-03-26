import requests
import os


# Print the response


def ask_gpt(prompt):
    """
    Ask GPT-4 a question and return the response
    """

    prompt_prefix = "Here is a part of a zoo app that I am working on. Please make suggestions for refactoring it. CODE:"
    # Set the API endpoint URL
    url = "https://api.openai.com/v1/engines/davinci-codex/completions"

    # Set the API key
    api_key = os.environ.get("api_key")

    # Set the prompt for the AI to complete
    prompt = prompt_prefix + prompt

    # Set the parameters for the API request
    data = {
        "prompt": prompt,  # The prompt for the AI to complete
        "max_tokens": 50,  # The maximum number of tokens to generate a token is a word or a punctuation mark
        "temperature": 0.5,  # The temperature for the AI to generate the response which controls the randomness of the response
        "n": 1,  # The number of responses to generate for the prompt
        "stop": "\n",  # The character to stop the response generation
    }

    # Set the request headers with the API key
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    # Make the API request
    response = requests.post(url, json=data, headers=headers)
    import pdb

    pdb.set_trace()
    print(response.json())


# create a script that iterates through each python file except for this one in this project
# and by class and by method makes a request to chat gpt for each class and method asking for refactors
# and then prints the response

import inspect
import os
import sys
import ast


def get_methods_in_module(module):
    return inspect.getmembers(module, inspect.isfunction)


def scan_directory_for_modules(path, modules=[]):
    ignored_directories = [
        "__pycache__",
        ".git",
        "venv",
        "node_modules",
        ".idea",
        ".pytest_cache",
        "htmlcov",
    ]
    # import pdb

    # pdb.set_trace()
    # Get all modules in the specified directory
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            print(f"dir: {dir}")
            if len(dir) == 2:
                return modules
            if dir not in ignored_directories:
                print(f"dir: {dir} not in ignored directories")
                modules += scan_directory_for_modules(dir)
        for file in files:
            print(f"file: {file}")
            if file.endswith(".py") and file != os.path.basename(__file__):
                print(f"file: {file} ends with .py")
                module_name = os.path.splitext(file)[0]
                try:
                    # add the contents of the module file to the modules list without using the import keyword
                    # which would cause the module to be executed
                    module = ast.parse(open(file).read())
                    module.__name__ = module_name
                    modules.append(module)
                    print(f"module: {module} appended to modules list")

                except FileNotFoundError:
                    print(f"file not found: {file}")
                    pass
    return modules


if __name__ == "__main__":
    # Get the path argument from the command line
    path = "./"

    # Scan the directory for modules
    modules = scan_directory_for_modules(path)
    print(len(modules))
    # Print the method names in each module
    for module in modules:
        # ast_methods is a list of ast nodes
        # each node has a name and a body
        # the name is the name of the method
        # the body is the body of the method
        for obj in module.body:
            if isinstance(obj, ast.FunctionDef):
                print(obj.name)
                print(obj.body)
                print("")
            if isinstance(obj, ast.ClassDef):
                print(obj.name)
                print(obj.body)
                print("")
            if isinstance(obj, ast.Assign):
                print(obj.targets)
                print(obj.value)
                print("")
            if isinstance(obj, ast.Expr):
                print(obj.value)
                print("")
            if isinstance(obj, ast.Import):
                print(obj.names)
                print("")
            if isinstance(obj, ast.ImportFrom):
                print(obj.names)
                print("")
            if isinstance(obj, ast.AnnAssign):
                print(obj.target)
                print(obj.value)
                print("")
            if isinstance(obj, ast.AugAssign):
                print(obj.target)
                print(obj.value)
                print("")
            if isinstance(obj, ast.Await):
                print(obj.value)
                print("")
            if isinstance(obj, ast.AsyncFor):
                print(obj.target)
                print(obj.iter)
                print(obj.body)
                print("")
            if isinstance(obj, ast.AsyncFunctionDef):
                print(obj.name)
                print(obj.body)
                print("")
            if isinstance(obj, ast.AsyncWith):
                print(obj.items)
                print(obj.body)
                print("")
            if isinstance(obj, ast.Assert):
                print(obj.test)
                print(obj.msg)
                print("")
            if isinstance(obj, ast.Assign):
                print(obj.targets)
                print(obj.value)
                print("")
            if isinstance(obj, ast.AugAssign):
                print(obj.target)
                print(obj.value)
                print("")
            if isinstance(obj, ast.Await):
                print(obj.value)
                print("")
            if isinstance(obj, ast.BinOp):
                print(obj.left)
                print(obj.op)
                print(obj.right)
                print("")
