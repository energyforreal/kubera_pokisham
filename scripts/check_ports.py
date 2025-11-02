#!/usr/bin/env python3
"""
Port Availability Checker

Checks if required ports are available before starting services.
Prevents silent failures due to port conflicts.
"""

import socket
import sys
from typing import Dict, List, Tuple


def check_port_available(port: int, host: str = "127.0.0.1") -> Tuple[bool, str]:
    """
    Check if a port is available for binding.
    
    Args:
        port: Port number to check
        host: Host address to check (default: 127.0.0.1)
    
    Returns:
        Tuple of (is_available, message)
    """
    try:
        # Try to create a socket and bind to the port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            # Port is in use
            return False, f"Port {port} is already in use"
        else:
            # Port is available
            return True, f"Port {port} is available"
    except socket.error as e:
        return False, f"Error checking port {port}: {e}"


def get_process_using_port(port: int) -> str:
    """
    Try to identify which process is using a port (Windows).
    
    Args:
        port: Port number to check
    
    Returns:
        Process information or empty string
    """
    try:
        import subprocess
        # Use netstat to find process using the port
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return f"Unable to check process (netstat failed)"
        
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                # Extract PID (last column)
                parts = line.split()
                if parts:
                    pid = parts[-1]
                    # Try to get process name
                    try:
                        tasklist_result = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if tasklist_result.returncode == 0 and tasklist_result.stdout:
                            process_name = tasklist_result.stdout.split(',')[0].strip('"')
                            return f"PID {pid} ({process_name})"
                    except:
                        return f"PID {pid}"
        return ""
    except subprocess.TimeoutExpired:
        return "Process check timed out"
    except FileNotFoundError:
        return "netstat/tasklist not available"
    except Exception:
        return "Unable to identify process"


def check_all_ports(ports: Dict[int, str]) -> Tuple[bool, List[str]]:
    """
    Check availability of all required ports.
    
    Args:
        ports: Dictionary mapping port numbers to service names
    
    Returns:
        Tuple of (all_available, list_of_issues)
    """
    issues = []
    all_available = True
    
    for port, service_name in ports.items():
        available, message = check_port_available(port)
        
        if not available:
            all_available = False
            process_info = get_process_using_port(port)
            if process_info:
                issues.append(f"❌ {service_name} (port {port}): In use by {process_info}")
            else:
                issues.append(f"❌ {service_name} (port {port}): In use by unknown process")
        else:
            issues.append(f"✅ {service_name} (port {port}): Available")
    
    return all_available, issues


def main():
    """Main entry point."""
    print("🔍 Checking port availability...")
    print("=" * 60)
    
    # Define required ports for all services
    required_ports = {
        8000: "Backend API (FastAPI)",
        8080: "Diagnostic Service (Node.js)",
        3000: "Frontend Dashboard (Next.js)",
        3001: "Diagnostic Dashboard (Next.js)"
    }
    
    all_available, issues = check_all_ports(required_ports)
    
    # Print results
    for issue in issues:
        print(issue)
    
    print("=" * 60)
    
    if all_available:
        print("✅ All ports are available!")
        print("\nYou can proceed with starting the services.")
        sys.exit(0)
    else:
        print("⚠️  Some ports are already in use!")
        print("\n💡 SOLUTIONS:")
        print("1. Stop the processes using these ports")
        print("2. Use Task Manager to end the processes")
        print("3. Restart your computer to free up all ports")
        print("4. Change port numbers in the configuration")
        print("\n💡 To stop KUBERA services:")
        print("   Run: taskkill /F /FI \"WINDOWTITLE eq KUBERA*\"")
        print("\n⚠️  Continuing with startup - services may fail if ports are busy")
        print("   Check the service windows for error messages")
        sys.exit(0)  # Don't fail - let services handle port conflicts


if __name__ == "__main__":
    main()

