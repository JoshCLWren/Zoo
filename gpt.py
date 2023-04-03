import ast
import inspect
import os
import time

import openai
import requests

# Print the response


def ask_gpt(prompt):
    """
    Ask GPT-4 a question and return the response
    """

    prompt_prefix = "Are there any bugs in this code? :\n\n"
    # Set the API endpoint URL

    # Set the prompt for the AI to complete
    prompt = prompt_prefix + prompt

    # Set the parameters for the API request
    print("Asking GPT for a refactor...")
    start_time = time.time()
    session = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    print("GPT took", time.time() - start_time, "seconds to respond")

    session = session["choices"][0]["text"]

    print(session)
    return session


# create a script that iterates through each python file except for this one in this project
# and by class and by method makes a request to chat gpt for each class and method asking for refactors
# and then prints the response

import os


def get_python_files(directory):
    """
    Returns a list of all Python files in the specified directory.
    """
    python_files = []
    for file in os.listdir(directory):
        if file.endswith(".py"):
            python_files.append(file)
    return python_files


def get_code_blocks(file):
    """
    Returns a list of all code blocks in the specified file.
    """
    with open(file, "r") as f:
        lines = f.readlines()
    code_blocks = []
    block = ""
    in_block = False
    for line in lines:
        if line.strip().startswith("def ") or line.strip().startswith("class "):
            if in_block:
                code_blocks.append(block)
                block = ""
                in_block = False
            block += line
            in_block = True
        elif line.strip().startswith("#"):
            block += line
        else:
            if in_block:
                code_blocks.append(block)
                block = ""
                in_block = False
            block += line
    if block:
        code_blocks.append(block)
    return code_blocks


def get_directories(directory):
    """
    Returns a list of all directories in the specified directory.
    """
    directories = []
    for file in os.listdir(directory):
        if os.path.isdir(file):
            directories.append(file)
    return directories


def scan_code(directory):
    directories = get_directories(directory)
    python_files = get_python_files(directory)
    print(
        f"Directory: {directory} contains {len(directories)} directories and {len(python_files)} Python files."
    )
    i = 0
    for i, file in enumerate(python_files):
        print(f"{i+1}. {file}")
    directory_change = i + 2
    print(f"{directory_change}. Change Directory")

    selection = input("Enter the number of a Python file to display its code blocks: ")
    if selection == str(directory_change):
        # print the directories
        for i, directory in enumerate(directories):
            print(f"{i+1}. {directory}")
        go_back = i + 2
        print(f"{go_back}. Go Back")
        selection = input("Enter the number of a directory to scan: ")
        if selection == str(go_back):
            return scan_code(directory=directory)
        try:
            if int(selection) > len(directories):
                print("Invalid selection.")
                exit()
            directory = directories[int(selection) - 1]
            return scan_code(directory=directory)
        except:
            print("Invalid selection.")
            exit()
    selected_file = ""
    try:
        file_index = int(selection) - 1
        selected_file = python_files[file_index]
    except:
        print("Invalid selection.")
        exit()

    code_blocks = get_code_blocks(selected_file)

    print("Code blocks in file:")
    for i, block in enumerate(code_blocks):
        if len(block.strip()) == 0:
            continue
        print(f"{i+1}. {block.strip()[:50]}...")  # print only first 50 chars of block

    print(
        f"{i+2}. Whole File"
    )  # add the option to select the whole file as a code block

    selection = input("Enter the number of a code block to display its contents: ")

    try:
        block_index = int(selection) - 1
        if block_index == i + 1:  # if the user selected the whole file
            selected_block = "".join(code_blocks)  # concatenate all code blocks
        else:
            selected_block = code_blocks[block_index]
    except:
        print("Invalid selection.")
        exit()

    return selected_block


def main():
    while True:
        local = input("Scan local code? (y/n): ")
        if local == "y":
            directory = "."  # scan the current directory
        elif local == "n":
            directory = input("Enter the directory to scan: ")
        else:
            print("Invalid selection.")
            continue
        code_block = scan_code(directory=directory)
        print(code_block)
        ask_gpt(code_block)
        continue_prompt = input("Continue? (y/n): ")
        if continue_prompt == "n":
            break


if __name__ == "__main__":
    main()
