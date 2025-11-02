"""System Monitor - Continuous monitoring and auto-remediation for all Trading Agent components."""

import asyncio
import json
import os
import platform
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import get_component_logger, logger


class ComponentMonitor:
    """Monitors a single component."""
    
    def __init__(self, name: str, config: Dict, monitor_logger):
        self.name = name
        self.config = config
        self.logger = monitor_logger
        self.component_type = config.get('type', 'http')
        self.health_endpoint = config.get('health_endpoint')
        self.health_file = config.get('health_file')
        self.restart_command = config.get('restart_command')
        self.working_directory = config.get('working_directory', str(project_root))
        self.port = config.get('port')
        self.max_heartbeat_age = config.get('max_heartbeat_age', 120)
        self.timeout = config.get('timeout', 5000)
        
        # Status tracking
        self.process_id: Optional[int] = None
        self.is_running = False
        self.last_check: Optional[datetime] = None
        self.last_successful_check: Optional[datetime] = None
        self.health_status = 'unknown'
        self.response_time_ms: Optional[float] = None
        self.restart_attempts = 0
        self.last_restart_attempt: Optional[datetime] = None
        self.consecutive_failures = 0
        self.auto_restart_enabled = True
        
        # Health metrics
        self.recent_response_times: List[float] = []
        self.recent_errors: List[str] = []
        
    async def check_health(self) -> Dict[str, Any]:
        """Check component health."""
        self.last_check = datetime.now(timezone.utc)
        start_time = time.time()
        
        try:
            if self.component_type == 'http':
                result = await self._check_http_health()
            elif self.component_type == 'process':
                result = await self._check_process_health()
            else:
                result = {'status': 'unknown', 'message': f'Unknown component type: {self.component_type}'}
            
            self.response_time_ms = (time.time() - start_time) * 1000
            self.recent_response_times.append(self.response_time_ms)
            if len(self.recent_response_times) > 20:
                self.recent_response_times.pop(0)
            
            if result.get('status') == 'healthy':
                self.last_successful_check = self.last_check
                self.consecutive_failures = 0
                self.health_status = 'healthy'
                self.is_running = True
            else:
                self.consecutive_failures += 1
                self.health_status = result.get('status', 'unhealthy')
                self.recent_errors.append(result.get('message', 'Unknown error'))
                if len(self.recent_errors) > 10:
                    self.recent_errors.pop(0)
            
            result['response_time_ms'] = self.response_time_ms
            result['consecutive_failures'] = self.consecutive_failures
            result['last_successful_check'] = self.last_successful_check.isoformat() if self.last_successful_check else None
            
            return result
            
        except Exception as e:
            self.response_time_ms = (time.time() - start_time) * 1000
            self.consecutive_failures += 1
            error_msg = str(e)
            self.recent_errors.append(error_msg)
            if len(self.recent_errors) > 10:
                self.recent_errors.pop(0)
            
            self.logger.error("health_check_failed", f"Health check failed for {self.name}", {
                "error": error_msg,
                "component": self.name
            })
            
            return {
                'status': 'critical',
                'message': error_msg,
                'response_time_ms': self.response_time_ms,
                'consecutive_failures': self.consecutive_failures
            }
    
    async def _check_http_health(self) -> Dict[str, Any]:
        """Check HTTP component health."""
        if not self.health_endpoint:
            return {'status': 'unknown', 'message': 'No health endpoint configured'}
        
        if not HAS_AIOHTTP:
            return {'status': 'unknown', 'message': 'aiohttp not available'}
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout / 1000)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.health_endpoint) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            # Check for circuit breaker and other health indicators
                            if data.get('circuit_breaker_active'):
                                return {'status': 'warning', 'message': 'Circuit breaker active', 'data': data}
                            return {'status': 'healthy', 'data': data}
                        except:
                            return {'status': 'healthy', 'message': 'HTTP 200 response'}
                    else:
                        return {'status': 'warning', 'message': f'HTTP {response.status}'}
        except asyncio.TimeoutError:
            return {'status': 'critical', 'message': 'Health check timeout'}
        except aiohttp.ClientConnectionError:
            return {'status': 'critical', 'message': 'Connection refused'}
        except Exception as e:
            return {'status': 'critical', 'message': f'HTTP check error: {str(e)}'}
    
    async def _check_process_health(self) -> Dict[str, Any]:
        """Check process-based component health via health file."""
        if not self.health_file:
            return {'status': 'unknown', 'message': 'No health file configured'}
        
        health_file_path = Path(self.working_directory) / self.health_file
        
        try:
            if not health_file_path.exists():
                return {'status': 'critical', 'message': 'Health file not found - process may not be running'}
            
            with open(health_file_path, 'r') as f:
                data = json.load(f)
            
            # Check heartbeat age
            last_heartbeat_str = data.get('last_heartbeat')
            if not last_heartbeat_str:
                return {'status': 'critical', 'message': 'No heartbeat recorded'}
            
            last_heartbeat = datetime.fromisoformat(last_heartbeat_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            heartbeat_age = (now - last_heartbeat).total_seconds()
            
            if not data.get('is_alive', False) or heartbeat_age > self.max_heartbeat_age * 2:
                return {'status': 'critical', 'message': f'Process not alive or heartbeat too old: {heartbeat_age:.0f}s'}
            elif heartbeat_age > self.max_heartbeat_age:
                return {'status': 'warning', 'message': f'Heartbeat age high: {heartbeat_age:.0f}s'}
            
            # Check for circuit breaker
            if data.get('circuit_breaker_active'):
                return {'status': 'warning', 'message': 'Circuit breaker active', 'data': data}
            
            return {'status': 'healthy', 'data': data, 'heartbeat_age': heartbeat_age}
            
        except json.JSONDecodeError:
            return {'status': 'warning', 'message': 'Health file JSON invalid'}
        except Exception as e:
            return {'status': 'critical', 'message': f'Health check error: {str(e)}'}
    
    async def restart(self, max_attempts: int = 3, backoff_seconds: List[int] = None) -> Dict[str, Any]:
        """Restart the component."""
        if not self.auto_restart_enabled:
            return {'status': 'disabled', 'message': 'Auto-restart disabled due to repeated failures'}
        
        if self.restart_attempts >= max_attempts:
            self.auto_restart_enabled = False
            return {'status': 'failed', 'message': f'Max restart attempts ({max_attempts}) reached'}
        
        backoff = backoff_seconds or [5, 15, 30]
        delay = backoff[min(self.restart_attempts, len(backoff) - 1)]
        
        self.restart_attempts += 1
        self.last_restart_attempt = datetime.now(timezone.utc)
        
        self.logger.warning("restart_initiated", f"Restarting component {self.name} (attempt {self.restart_attempts})", {
            "component": self.name,
            "attempt": self.restart_attempts,
            "delay_seconds": delay
        })
        
        # Wait for backoff delay
        await asyncio.sleep(delay)
        
        try:
            # Kill existing process if running
            await self._kill_existing_process()
            
            # Resolve port conflicts
            if self.port:
                await self._resolve_port_conflict()
            
            # Start the component
            result = await self._start_component()
            
            if result.get('success'):
                # Reset restart attempts on success
                self.restart_attempts = 0
                self.consecutive_failures = 0
                self.auto_restart_enabled = True
                
                self.logger.info("restart_success", f"Component {self.name} restarted successfully", {
                    "component": self.name,
                    "attempt": self.restart_attempts
                })
                
                return {'status': 'success', 'message': 'Component restarted'}
            else:
                error_msg = result.get('error', 'Unknown error')
                self.logger.error("restart_failed", f"Failed to restart {self.name}", {
                    "component": self.name,
                    "error": error_msg,
                    "attempt": self.restart_attempts
                })
                
                return {'status': 'failed', 'message': error_msg}
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error("restart_exception", f"Exception during restart of {self.name}", {
                "component": self.name,
                "error": error_msg,
                "attempt": self.restart_attempts
            })
            
            return {'status': 'failed', 'message': error_msg}
    
    async def _kill_existing_process(self):
        """Kill existing process if running."""
        if not self.process_id:
            return
        
        try:
            if platform.system() == 'Windows':
                subprocess.run(['taskkill', '/F', '/PID', str(self.process_id)], 
                             capture_output=True, timeout=5)
            else:
                os.kill(self.process_id, signal.SIGTERM)
                await asyncio.sleep(2)
                # Force kill if still running
                try:
                    os.kill(self.process_id, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Already dead
        except Exception as e:
            self.logger.debug("kill_process_error", f"Error killing process {self.process_id}", {
                "process_id": self.process_id,
                "error": str(e)
            })
        
        self.process_id = None
    
    async def _resolve_port_conflict(self):
        """Resolve port conflicts by killing process using the port."""
        if not self.port:
            return
        
        try:
            if platform.system() == 'Windows':
                # Find process using port
                result = subprocess.run(
                    ['netstat', '-ano'], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if f':{self.port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                subprocess.run(['taskkill', '/F', '/PID', pid], 
                                             capture_output=True, timeout=5)
                                self.logger.info("port_conflict_resolved", f"Killed process {pid} using port {self.port}", {
                                    "port": self.port,
                                    "pid": pid
                                })
                                await asyncio.sleep(2)
                            except:
                                pass
            else:
                # Linux/Mac: use lsof
                result = subprocess.run(
                    ['lsof', '-ti', f':{self.port}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    pid = result.stdout.strip()
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        await asyncio.sleep(2)
                        os.kill(int(pid), signal.SIGKILL)
                    except:
                        pass
        except Exception as e:
            self.logger.debug("port_resolution_error", f"Error resolving port conflict", {
                "port": self.port,
                "error": str(e)
            })
    
    async def _start_component(self) -> Dict[str, Any]:
        """Start the component."""
        if not self.restart_command:
            return {'success': False, 'error': 'No restart command configured'}
        
        try:
            work_dir = Path(self.working_directory)
            work_dir.mkdir(parents=True, exist_ok=True)
            
            if platform.system() == 'Windows':
                # Windows: start in new window
                cmd_parts = self.restart_command.split()
                process = subprocess.Popen(
                    cmd_parts,
                    cwd=str(work_dir),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.executable.endswith('pythonw.exe') else 0
                )
                self.process_id = process.pid
            else:
                # Linux/Mac: start in background
                if self.restart_command.startswith('npm'):
                    # Node.js service
                    process = subprocess.Popen(
                        self.restart_command.split(),
                        cwd=str(work_dir),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                else:
                    # Python service
                    process = subprocess.Popen(
                        self.restart_command.split(),
                        cwd=str(work_dir),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                self.process_id = process.pid
            
            self.is_running = True
            
            # Wait a bit to see if process starts
            await asyncio.sleep(3)
            
            if process.poll() is None:  # Still running
                return {'success': True, 'process_id': self.process_id}
            else:
                return {'success': False, 'error': 'Process exited immediately'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}


class SystemMonitor:
    """System-wide component monitor with auto-remediation."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or (project_root / 'config' / 'monitor_config.yaml')
        self.logger = get_component_logger("system_monitor")
        
        # Load configuration
        self.config = self._load_config()
        
        # Monitoring settings
        self.check_interval = self.config.get('monitoring', {}).get('check_interval', 30)
        self.restart_enabled = self.config.get('monitoring', {}).get('restart_enabled', True)
        self.max_restart_attempts = self.config.get('monitoring', {}).get('max_restart_attempts', 3)
        self.restart_backoff = self.config.get('monitoring', {}).get('restart_backoff_seconds', [5, 15, 30])
        
        # Component monitors
        self.monitors: Dict[str, ComponentMonitor] = {}
        self._initialize_monitors()
        
        # Diagnostic service integration
        self.diagnostic_url = self.config.get('diagnostic_service', {}).get('url', 'http://localhost:8080')
        self.diagnostic_enabled = self.config.get('diagnostic_service', {}).get('enabled', True)
        self.diagnostic_session: Optional[aiohttp.ClientSession] = None
        
        # Control
        self.running = False
        self._stop_event = threading.Event()
        
        self.logger.info("initialization", "System monitor initialized", {
            "check_interval": self.check_interval,
            "restart_enabled": self.restart_enabled,
            "components": list(self.monitors.keys())
        })
    
    def _load_config(self) -> Dict:
        """Load monitor configuration."""
        if not HAS_YAML:
            self.logger.warning("yaml_missing", "PyYAML not available, using defaults")
            return self._default_config()
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.logger.info("config_loaded", f"Loaded configuration from {self.config_path}")
                    return config
            else:
                self.logger.warning("config_not_found", f"Config file not found: {self.config_path}, using defaults")
                return self._default_config()
        except Exception as e:
            self.logger.error("config_load_error", f"Failed to load config: {e}", {"error": str(e)})
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Default configuration."""
        return {
            'monitoring': {
                'check_interval': 30,
                'restart_enabled': True,
                'max_restart_attempts': 3,
                'restart_backoff_seconds': [5, 15, 30]
            },
            'components': {
                'trading_bot': {
                    'type': 'process',
                    'health_file': 'bot_health.json',
                    'restart_command': 'python src/main.py',
                    'max_heartbeat_age': 120
                },
                'backend_api': {
                    'type': 'http',
                    'health_endpoint': 'http://localhost:8000/api/v1/health',
                    'restart_command': 'python backend/api/main.py',
                    'port': 8000,
                    'timeout': 5000
                },
                'frontend': {
                    'type': 'http',
                    'health_endpoint': 'http://localhost:3000',
                    'restart_command': 'npm run dev',
                    'working_directory': 'frontend_web',
                    'port': 3000,
                    'timeout': 5000
                },
                'diagnostic_service': {
                    'type': 'http',
                    'health_endpoint': 'http://localhost:8080/api/health',
                    'restart_command': 'npm start',
                    'working_directory': 'diagnostic_service',
                    'port': 8080,
                    'timeout': 5000
                },
                'diagnostic_dashboard': {
                    'type': 'http',
                    'health_endpoint': 'http://localhost:3001',
                    'restart_command': 'npm run dev -- --port 3001',
                    'working_directory': 'diagnostic_dashboard',
                    'port': 3001,
                    'timeout': 5000
                }
            },
            'diagnostic_service': {
                'enabled': True,
                'url': 'http://localhost:8080'
            }
        }
    
    def _initialize_monitors(self):
        """Initialize component monitors."""
        components = self.config.get('components', {})
        for name, comp_config in components.items():
            self.monitors[name] = ComponentMonitor(name, comp_config, self.logger)
            self.logger.info("monitor_initialized", f"Initialized monitor for {name}", {
                "component": name,
                "type": comp_config.get('type')
            })
    
    async def start(self):
        """Start the monitor."""
        self.running = True
        self._stop_event.clear()
        
        # Initialize diagnostic session
        if self.diagnostic_enabled and HAS_AIOHTTP:
            self.diagnostic_session = aiohttp.ClientSession()
        
        self.logger.info("monitor_started", "System monitor started", {
            "components": len(self.monitors),
            "check_interval": self.check_interval
        })
        
        # Run monitoring loop
        while self.running and not self._stop_event.is_set():
            try:
                await self._monitoring_cycle()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error("monitoring_cycle_error", f"Error in monitoring cycle: {e}", {
                    "error": str(e)
                })
                await asyncio.sleep(self.check_interval)
    
    async def _monitoring_cycle(self):
        """Perform one monitoring cycle."""
        results = {}
        
        # Check all components
        for name, monitor in self.monitors.items():
            try:
                health_result = await monitor.check_health()
                results[name] = health_result
                
                # Handle failures
                if health_result.get('status') in ['critical', 'warning']:
                    await self._handle_component_failure(name, monitor, health_result)
                    
            except Exception as e:
                self.logger.error("component_check_error", f"Error checking {name}", {
                    "component": name,
                    "error": str(e)
                })
                results[name] = {'status': 'error', 'message': str(e)}
        
        # Report to diagnostic service
        await self._report_to_diagnostic(results)
    
    async def _handle_component_failure(self, name: str, monitor: ComponentMonitor, health_result: Dict):
        """Handle component failure."""
        status = health_result.get('status')
        
        # Alert
        self.logger.warning("component_failure", f"Component {name} failed health check", {
            "component": name,
            "status": status,
            "message": health_result.get('message'),
            "consecutive_failures": monitor.consecutive_failures
        })
        
        # Auto-restart for critical failures
        if status == 'critical' and self.restart_enabled and monitor.auto_restart_enabled:
            if monitor.consecutive_failures >= 2:  # Require 2 consecutive failures before restart
                restart_result = await monitor.restart(
                    max_attempts=self.max_restart_attempts,
                    backoff_seconds=self.restart_backoff
                )
                
                if restart_result.get('status') == 'success':
                    self.logger.info("restart_success", f"Component {name} restarted successfully")
                elif restart_result.get('status') == 'disabled':
                    self.logger.error("restart_disabled", f"Auto-restart disabled for {name} due to repeated failures")
                    # Send alert
                    await self._send_alert('critical', f"Auto-restart disabled for {name} after max attempts")
    
    async def _report_to_diagnostic(self, results: Dict):
        """Report status to diagnostic service."""
        if not self.diagnostic_enabled or not HAS_AIOHTTP:
            return
        
        try:
            if not self.diagnostic_session:
                self.diagnostic_session = aiohttp.ClientSession()
            
            for component, result in results.items():
                try:
                    payload = {
                        'component': component,
                        'event_type': 'health_check',
                        'data': {
                            'status': result.get('status'),
                            'message': result.get('message'),
                            'response_time_ms': result.get('response_time_ms'),
                            'consecutive_failures': result.get('consecutive_failures', 0),
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        },
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    
                    async with self.diagnostic_session.post(
                        f"{self.diagnostic_url}/api/events",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status != 200:
                            self.logger.debug("diagnostic_report_failed", f"Failed to report to diagnostic service", {
                                "component": component,
                                "status": response.status
                            })
                except Exception as e:
                    self.logger.debug("diagnostic_report_error", f"Error reporting to diagnostic service", {
                        "component": component,
                        "error": str(e)
                    })
                    
        except Exception as e:
            self.logger.debug("diagnostic_session_error", f"Diagnostic session error", {"error": str(e)})
    
    async def _send_alert(self, severity: str, message: str):
        """Send alert (console log for now)."""
        if severity == 'critical':
            self.logger.error("critical_alert", message)
        else:
            self.logger.warning("alert", message)
    
    async def stop(self):
        """Stop the monitor."""
        self.running = False
        self._stop_event.set()
        
        # Close diagnostic session
        if self.diagnostic_session:
            await self.diagnostic_session.close()
            self.diagnostic_session = None
        
        self.logger.info("monitor_stopped", "System monitor stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall monitor status."""
        component_statuses = {}
        for name, monitor in self.monitors.items():
            component_statuses[name] = {
                'status': monitor.health_status,
                'is_running': monitor.is_running,
                'consecutive_failures': monitor.consecutive_failures,
                'restart_attempts': monitor.restart_attempts,
                'auto_restart_enabled': monitor.auto_restart_enabled,
                'last_check': monitor.last_check.isoformat() if monitor.last_check else None,
                'response_time_ms': monitor.response_time_ms
            }
        
        return {
            'running': self.running,
            'check_interval': self.check_interval,
            'restart_enabled': self.restart_enabled,
            'components': component_statuses,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='System Monitor for Trading Agent')
    parser.add_argument('--config', type=str, help='Path to monitor config file')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    args = parser.parse_args()
    
    monitor = SystemMonitor(config_path=args.config)
    
    # Override check interval if provided
    if args.interval:
        monitor.check_interval = args.interval
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("Monitor interrupted by user")
    finally:
        await monitor.stop()


if __name__ == '__main__':
    asyncio.run(main())

