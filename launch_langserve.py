#!/usr/bin/env python
import os
import subprocess
import signal
import sys
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get port from environment or use default
PORT = int(os.getenv("LANGSERVE_PORT", "8000"))

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_process_using_port(port):
    """Find the process ID using the specified port."""
    try:
        # For macOS and Linux
        cmd = f"lsof -i :{port} -t"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if process.stdout:
            return process.stdout.strip()
    except:
        pass
    return None

def kill_process(pid):
    """Kill a process by its PID."""
    try:
        os.kill(int(pid), signal.SIGTERM)
        print(f"Killed process {pid} using port {PORT}")
        return True
    except:
        return False

def main():
    """Main function to launch the LangServe API server."""
    print(f"Starting LangServe API server on port {PORT}...")
    
    # Check if port is already in use
    if is_port_in_use(PORT):
        print(f"Port {PORT} is already in use.")
        pid = find_process_using_port(PORT)
        if pid:
            print(f"Process {pid} is using port {PORT}.")
            user_input = input(f"Do you want to kill the process and start LangServe? (y/n): ")
            if user_input.lower() == 'y':
                if kill_process(pid):
                    print(f"Process {pid} killed.")
                else:
                    print(f"Failed to kill process {pid}. Please close it manually.")
                    return
            else:
                print("Exiting...")
                return
        else:
            print(f"Could not find process using port {PORT}. Please close it manually.")
            return
    
    # Run LangServe API server
    try:
        subprocess.run(["python", "langserve_api.py"], check=True)
    except KeyboardInterrupt:
        print("\nLangServe API server was interrupted by user.")
    except subprocess.CalledProcessError as e:
        print(f"\nLangServe API server failed with error code {e.returncode}")

if __name__ == "__main__":
    main()
