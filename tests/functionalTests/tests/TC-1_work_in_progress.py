import subprocess

def TC_1_work_in_progress():
    # Simple command without capturing output
    subprocess.run(['ls', '-l'])

    # Command with output capture
    result = subprocess.run(['ls', '-l'], capture_output=True, text=True)
    print(result.stdout)  # Prints the command output