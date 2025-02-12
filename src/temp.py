import subprocess
import os

# Disable ssl certificate verification
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Set the environment variable to disable SSL verification
env = os.environ.copy()
env['PYTHONHTTPSVERIFY'] = '0'

# Define the command to run (e.g., 'pysmt-install --msat')
command = ['pysmt-install', '--msat']

# Run the command using subprocess, and provide 'y' input when prompted
try:
    # Using subprocess.Popen to interact with the process (needed to send input)
    process = subprocess.Popen(command, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True)

    # Send 'y' to the process when prompted
    stdout, stderr = process.communicate(input='y\n')

    # Print the output and error (if any)
    print(stdout)
    if stderr:
        print(f"Error:\n{stderr}")
except subprocess.CalledProcessError as e:
    print(f"Command failed with error:\n{e.stderr}")