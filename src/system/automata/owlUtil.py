import subprocess


def execute_ltl2ldba_tool(path_to_owl, formula):
    """
    Run the ltl2ldba command with the given LTL formula.

    :param path_to_owl: path to the executable, e.g., ./owl
    :param formula: The LTL formula as a string, e.g.,
    :return: The output from the Owl command, if an error occurs, the error message is returned, which starts with 'Error: '.
    """
    command = [path_to_owl, "ltl2ldba", "-f", formula, "--state-acceptance", "--complete"]

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: Owl binary not found or not executable."
    except Exception as e:
        return f"Error: {e}"