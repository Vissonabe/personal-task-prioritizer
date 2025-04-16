#!/usr/bin/env python3
import os
import subprocess
import socket
import time
import signal
import sys
import platform
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
STREAMLIT_PORT = 8501
LANGSERVE_PORT = int(os.getenv("LANGSERVE_PORT", "8000"))
APP_FILE = "app.py"
LANGSERVE_FILE = "langserve_api.py"
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

def check_and_clear_port(port):
    """Check if a port is in use and clear it if necessary."""
    if is_port_in_use(port):
        print(f"Port {port} is already in use.")
        pids = find_process_on_port(port)
        
        if pids:
            print(f"Found process(es) using port {port}: {pids}")
            
            if AUTO_KILL:
                print(f"Automatically terminating processes using port {port}...")
                for pid in pids:
                    kill_process(pid)
                # Wait a moment for the port to be released
                time.sleep(1)
                if is_port_in_use(port):
                    print(f"Port {port} is still in use. Please check manually.")
                    return False
                print(f"Port {port} is now available.")
                return True
            else:
                print("Exiting because port is in use and AUTO_KILL is disabled.")
                return False
        else:
            print(f"Could not identify the process using port {port}.")
            if not AUTO_KILL:
                return False
            print("Attempting to run anyway...")
            return True
    return True

def run_langserve():
    """Run the LangServe API server."""
    print(f"Starting LangServe API server on port {LANGSERVE_PORT}...")
    try:
        subprocess.run(["python", LANGSERVE_FILE], check=True)
    except KeyboardInterrupt:
        print("\nLangServe API server was interrupted by user.")
    except subprocess.CalledProcessError as e:
        print(f"\nLangServe API server failed with error code {e.returncode}")

def run_streamlit():
    """Run the Streamlit app."""
    print(f"Starting Streamlit on port {STREAMLIT_PORT}...")
    try:
        # Set environment variables
        os.environ["STREAMLIT_SERVER_PORT"] = str(STREAMLIT_PORT)
        subprocess.run(["streamlit", "run", APP_FILE], check=True)
    except KeyboardInterrupt:
        print("\nStreamlit process was interrupted by user.")
    except subprocess.CalledProcessError as e:
        print(f"\nStreamlit process failed with error code {e.returncode}")

def main():
    """Main function to launch both the LangServe API server and the Streamlit app."""
    print("Starting Personal Task Prioritizer with LangServe integration...")
    
    # Check and clear ports
    if not check_and_clear_port(LANGSERVE_PORT):
        sys.exit(1)
    if not check_and_clear_port(STREAMLIT_PORT):
        sys.exit(1)
    
    # Start LangServe API server in a separate thread
    langserve_thread = threading.Thread(target=run_langserve)
    langserve_thread.daemon = True  # This ensures the thread will exit when the main program exits
    langserve_thread.start()
    
    # Wait a moment for LangServe to start
    print("Waiting for LangServe API server to start...")
    time.sleep(2)
    
    # Start Streamlit app in the main thread
    run_streamlit()
    
    # If we get here, Streamlit has exited, so we should exit too
    print("Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    main()
