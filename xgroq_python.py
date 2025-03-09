import groq
import subprocess
import re
import shutil
import time
from datetime import datetime
import os
import platform

"""
This script uses the Groq API to generate a Python program based on a prompt, iteratively
refines it until it runs successfully without errors, and optionally prints the output.
Configuration parameters are read from 'config.txt', including the model, max attempts,
max time for code generation, prompt file, source file, whether to print the output,
whether to print the final code, whether to print runtime error messages, and the Python
interpreter. The Groq API key is read from 'groq_key.txt'. Generated code includes comments
with the prompt file name, model, generation time, and timestamp. Previous attempts are
archived with numbered suffixes (e.g., foo1.py, foo2.py). Lines starting with a backtick (`)
are commented out as they are invalid in Python.

Config file format (config.txt):
    model: <model_name> (e.g., llama-3.3-70b-versatile)
    max_attempts: <integer> (e.g., 5)
    max_time: <seconds> (e.g., 10)
    prompt_file: <filename> (e.g., prompt.txt)
    source_file: <filename> (e.g., foo.py)
    print_output: <yes/no> (e.g., yes)
    print_code: <yes/no> (e.g., yes)
    print_runtime_error_messages: <yes/no> (e.g., yes)
    interpreter: <interpreter_name> (e.g., python3)

Dependencies: groq, subprocess, re, shutil, time, datetime, os, platform
Requires: Specified Python interpreter installed (e.g., python3)
"""

# Read Groq API key from file
with open("groq_key.txt", "r") as key_file:
    api_key = key_file.read().strip()

# Read configuration parameters from file
config_file = "config.txt"
config = {}
with open(config_file, "r") as f:
    for line in f:
        if not line.strip():
            continue  # skip blank lines
        key, value = line.strip().split(": ", 1)  # Split on first ": " only
        config[key] = value

# Extract parameters
model = config["model"]
max_attempts = int(config["max_attempts"])
max_time = float(config["max_time"])  # Maximum cumulative generation time in seconds
prompt_file = config["prompt_file"]
source_file = config["source_file"]
base_name = os.path.splitext(source_file)[0]  # Extract base name (e.g., "foo" from "foo.py")
print_output = config["print_output"].lower() == "yes"
print_code = config["print_code"].lower() == "yes"
print_runtime_error_messages = config["print_runtime_error_messages"].lower() == "yes"
interpreter = config["interpreter"]

# Initialize Groq client
client = groq.Groq(api_key=api_key)

def generate_code(prompt):
    # Measure time taken to generate code
    start_time = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096
    )
    end_time = time.time()
    generation_time = end_time - start_time

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Extract raw content
    content = response.choices[0].message.content

    # Split content into lines
    lines = content.splitlines()

    # Find the index of the first ```python line
    code_start_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == "```python":
            code_start_idx = i
            break

    # Comment out everything up to and including ```python
    if code_start_idx != -1:
        for i in range(code_start_idx + 1):
            if not lines[i].startswith("#"):
                lines[i] = "#" + lines[i]
        # Extract code after ```python until ``` (if present)
        code_lines = []
        for line in lines[code_start_idx + 1:]:
            if line.strip() == "```":
                break
            code_lines.append(line)
        code = "\n".join(code_lines)
    else:
        # If no ```python found, comment everything and use it as-is
        code = "\n".join("#" + line if not line.startswith("#") else line for line in lines)

    # Comment out lines starting with a backtick within the code
    code_lines = code.splitlines()
    for i in range(len(code_lines)):
        if code_lines[i].strip().startswith("`"):
            code_lines[i] = "#" + code_lines[i]
    code = "\n".join(code_lines)

    # Calculate lines of code (excluding header)
    loc = len([line for line in code.splitlines() if line.strip()])

    # Add comment lines to the top of the code
    header = (
        f"# Generated from prompt file: {prompt_file}\n"
        f"# Model used: {model}\n"
        f"# Time generated: {timestamp}\n"
        f"# Generation time: {generation_time:.3f} seconds\n"
    )
    return header + code, generation_time, loc

def test_code(code, filename=source_file, attempt=1):
    # If not the first attempt, save a copy with suffix (e.g., foo1.py, foo2.py)
    if attempt > 1:
        archive_filename = f"{base_name}{attempt-1}.py"
        shutil.copyfile(filename, archive_filename)
    
    # Write the new code to the source file
    with open(filename, "w") as f:
        f.write(code)
    
    # Run the Python script with the specified interpreter
    run_command = [interpreter, filename]
    if print_runtime_error_messages:
        result = subprocess.run(
            run_command,
            capture_output=True,
            text=True,
            input="5\n"  # Provide input if the script expects it; adjust as needed
        )
        output = result.stdout
        error = result.stderr
    else:
        with open("temp_runtime_error.txt", "w") as error_file:
            result = subprocess.run(
                run_command,
                stdout=subprocess.PIPE,
                stderr=error_file,
                text=True,
                input="5\n"
            )
        output = result.stdout
        with open("temp_runtime_error.txt", "r") as error_file:
            error = error_file.read()
        os.remove("temp_runtime_error.txt")
    
    return result.returncode == 0, output, error

# Read initial prompt from file specified in config
with open(prompt_file, "r") as f:
    prompt = f.read() + "Only output Python code. Do not give commentary.\n"
    print("prompt:\n" + prompt)
print("model: " + model + "\n")
code, initial_gen_time, initial_loc = generate_code(prompt)
total_gen_time = initial_gen_time
attempts = 1

# Iterate until the code runs successfully or limits are exceeded
while True:
    success, output, error = test_code(code, attempt=attempts)
    if success:
        print(f"Code ran successfully after {attempts} {'attempt' if attempts == 1 else 'attempts'} (generation time: {initial_gen_time if attempts == 1 else gen_time:.3f} seconds, LOC={initial_loc if attempts == 1 else loc})!")
        if print_code:
            print("Final version:\n\n", code)
        if print_output:
            print("\nOutput:\n", output)
        else:
            print("\nSkipping output as per config (print_output: no)")
        print(f"\nTotal generation time: {total_gen_time:.3f} seconds across {attempts} {'attempt' if attempts == 1 else 'attempts'}")
        break
    else:
        if print_runtime_error_messages:
            print(f"Attempt {attempts} failed with error (generation time: {initial_gen_time if attempts == 1 else gen_time:.3f} seconds, LOC={initial_loc if attempts == 1 else loc}): {error}")
        else:
            print(f"Attempt {attempts} failed (error details suppressed, generation time: {initial_gen_time if attempts == 1 else gen_time:.3f} seconds, LOC={initial_loc if attempts == 1 else loc})")
        
        # Check if we've exceeded max_time before generating more code
        if total_gen_time >= max_time:
            print(f"Max generation time ({max_time} seconds) exceeded after {attempts} attempts.")
            if print_code:
                print("Last code:\n", code)
            print(f"\nTotal generation time: {total_gen_time:.3f} seconds")
            break
        
        prompt = (
            f"The following Python code failed to run: \n```python\n{code}\n```\n"
            f"Error: {error}\nPlease fix the code and return it in a ```python``` block."
        )
        code, gen_time, loc = generate_code(prompt)
        total_gen_time += gen_time
        attempts += 1
        
        if attempts > max_attempts:
            print(f"Max attempts ({max_attempts}) reached.")
            if print_code:
                print("Last code:\n", code)
            print(f"Total generation time: {total_gen_time:.3f} seconds")
            break

# Print the run command
run_command = [interpreter, source_file]
print(f"\nRun command: {' '.join(run_command)}")
