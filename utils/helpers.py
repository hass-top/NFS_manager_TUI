import subprocess
import os

def run_script(script_path: str, *args: str) -> str:
    """Run a Bash script and return its output."""
    # Ensure the script is executable
    if not os.access(script_path, os.X_OK):
        os.chmod(script_path, 0o755)
    
    try:
        result = subprocess.run(
            [script_path, *args],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout   
    except subprocess.CalledProcessError as e:
        return f"Error: Script exited with status {e.returncode}. Output: {e.stderr.strip()}"
  
    except FileNotFoundError:
        return f"Error: Script {script_path} not found."
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def run_script_test(script_path: str, *args: str) -> str:
    if os.path.isfile(script_path) and not os.access(script_path, os.X_OK):
        try:
            os.chmod(script_path, 0o755)
        except Exception as e:
            return f"[-] Error: Failed to make {script_path} executable: {str(e)}"

    try:
        command = ["sudo", script_path] + list(args)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        output = (result.stdout + result.stderr).strip()
        return output if output else "No output from command."
    except subprocess.CalledProcessError as e:
        return f"[-] Error: Command exited with status {e.returncode}. Output: {e.stderr.strip() if e.stderr else 'No output.'}"
    except FileNotFoundError:
        return f"[-] Error: Command or script '{script_path}' not found. Ensure it is installed or provide the full path."
    except Exception as e:
        return f"[-] Error: Unexpected error: {str(e)}"
def run_mount_nfs() -> str:
    try:
        result = run_script_test("mount")
        if result.startswith("[-] Error"):
            return result
        if not result.strip():
            return "No output from mount command."

        # Filter lines containing 'nfs_tui'
        nfs_lines = [line for line in result.splitlines() if "nfs4" in line]

        # Remove everything after ' (' (like sed 's/ (.*//')
        clean_lines = [line.split(" (")[0] for line in nfs_lines]

        return "\n".join(clean_lines) if clean_lines else "No NFS mounts found for nfs_tui."

    except Exception as e:
        return f"[-] Error: Unexpected error in run_mount_nfs: {str(e)}"

