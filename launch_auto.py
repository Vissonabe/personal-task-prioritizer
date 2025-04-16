#!/usr/bin/env python3
import os
import subprocess
import socket
import time
import signal
import sys
import platform

# Configuration
PORT = 8501
APP_FILE = "app.py"
AUTO_KILL = True  # Automatically kill processes without asking

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_process_on_port(port):
    """Find the process ID using the specified port."""
    system = platform.system()
    
    try:
        if system == "Darwin" or system == "Linux":  # macOS or Linux
            cmd = f"lsof -i :{port} -t"
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            if output:
                return [int(pid) for pid in output.split('\n')]
        elif system == "Windows":
            cmd = f"netstat -ano | findstr :{port}"
            output = subprocess.check_output(cmd, shell=True).decode()
            if output:
                lines = output.strip().split('\n')
                pids = set()
                for line in lines:
                    if f":{port}" in line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pids.add(int(parts[-1]))
                return list(pids)
    except subprocess.CalledProcessError:
        pass
    
    return []

def kill_process(pid):
    """Kill a process by its PID."""
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
        else:  # macOS or Linux
            os.kill(pid, signal.SIGTERM)
            # Give it a moment to terminate gracefully
            time.sleep(0.5)
            # If still running, force kill
            if is_process_running(pid):
                os.kill(pid, signal.SIGKILL)
        print(f"Process with PID {pid} has been terminated.")
        return True
    except (subprocess.CalledProcessError, OSError, ProcessLookupError) as e:
        print(f"Failed to kill process {pid}: {e}")
        return False

def is_process_running(pid):
    """Check if a process is still running."""
    try:
        if platform.system() == "Windows":
            subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}"])
            return True
        else:  # macOS or Linux
            os.kill(pid, 0)  # Signal 0 doesn't kill the process but checks if it exists
            return True
    except (subprocess.CalledProcessError, OSError, ProcessLookupError):
        return False

def main():
    print(f"Checking if port {PORT} is available...")
    
    # Check if port is in use
    if is_port_in_use(PORT):
        print(f"Port {PORT} is already in use.")
        pids = find_process_on_port(PORT)
        
        if pids:
            print(f"Found process(es) using port {PORT}: {pids}")
            
            if AUTO_KILL:
                print(f"Automatically terminating processes using port {PORT}...")
                for pid in pids:
                    kill_process(pid)
                # Wait a moment for the port to be released
                time.sleep(1)
                if is_port_in_use(PORT):
                    print(f"Port {PORT} is still in use. Please check manually.")
                    sys.exit(1)
                print(f"Port {PORT} is now available.")
            else:
                print("Exiting because port is in use and AUTO_KILL is disabled.")
                sys.exit(1)
        else:
            print(f"Could not identify the process using port {PORT}.")
            if not AUTO_KILL:
                sys.exit(1)
            print("Attempting to run Streamlit anyway...")
    
    # Set environment variables
    os.environ["STREAMLIT_SERVER_PORT"] = str(PORT)
    
    print(f"Starting Streamlit on port {PORT}...")
    # Run Streamlit
    try:
        subprocess.run(["streamlit", "run", APP_FILE], check=True)
    except KeyboardInterrupt:
        print("\nStreamlit process was interrupted by user.")
    except subprocess.CalledProcessError as e:
        print(f"\nStreamlit process failed with error code {e.returncode}")

if __name__ == "__main__":
    main()
