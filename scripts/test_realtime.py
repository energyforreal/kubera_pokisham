#!/usr/bin/env python3
"""
Real-Time Communication Tester

Tests real-time communication between components including
WebSocket broadcasting, event propagation, and latency measurements.
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import websockets
import requests
import threading

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class RealTimeCommunicationTester:
    """Tests real-time communication between components."""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.received_messages = []
        self.websocket_connections = []
        
    def log_result(self, test_name: str, status: str, details: str = "", latency_ms: float = 0, metrics: Dict = None):
        """Log test result."""
        self.results[test_name] = {
            'status': status,
            'details': details,
            'latency_ms': latency_ms,
            'metrics': metrics or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status} ({latency_ms:.1f}ms)")
        if details:
            print(f"   Details: {details}")
        if metrics:
            for key, value in metrics.items():
                print(f"   {key}: {value}")
    
    async def test_trading_agent_to_backend_broadcast(self) -> bool:
        """Test trading agent → backend broadcast latency."""
        start_time = time.time()
        
        try:
            # This test simulates what the trading agent does
            # by sending a broadcast to the backend API
            broadcast_data = {
                'type': 'test_signal',
                'data': {
                    'symbol': 'BTCUSD',
                    'prediction': 'BUY',
                    'confidence': 0.75,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Send broadcast to backend
            response = requests.post(
                "http://localhost:8000/api/v1/internal/broadcast",
                json=broadcast_data,
                timeout=5
            )
            
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                clients_notified = result.get('clients_notified', 0)
                self.log_result(
                    "trading_agent_to_backend_broadcast",
                    "PASS",
                    f"Broadcast successful, {clients_notified} clients notified",
                    latency,
                    {'clients_notified': clients_notified}
                )
                return True
            else:
                self.log_result(
                    "trading_agent_to_backend_broadcast",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text}",
                    latency
                )
                return False
                
        except Exception as e:
            self.log_result(
                "trading_agent_to_backend_broadcast",
                "FAIL",
                f"Exception: {e}",
                0
            )
            return False
    
    async def test_backend_to_frontend_websocket(self) -> bool:
        """Test backend → frontend WebSocket delivery."""
        start_time = time.time()
        message_received = False
        received_message = None
        
        try:
            uri = "ws://localhost:8000/ws"
            
            async def websocket_client():
                nonlocal message_received, received_message
                try:
                    async with websockets.connect(uri, timeout=10) as websocket:
                        # Wait for any message
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        message_received = True
                        received_message = message
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    print(f"WebSocket client error: {e}")
            
            # Start WebSocket client
            client_task = asyncio.create_task(websocket_client())
            
            # Wait a bit for connection
            await asyncio.sleep(1)
            
            # Send a test broadcast
            await self.test_trading_agent_to_backend_broadcast()
            
            # Wait for message
            try:
                await asyncio.wait_for(client_task, timeout=15.0)
            except asyncio.TimeoutError:
                pass
            
            latency = (time.time() - start_time) * 1000
            
            if message_received:
                self.log_result(
                    "backend_to_frontend_websocket",
                    "PASS",
                    f"Message received: {received_message[:100]}...",
                    latency,
                    {'message_length': len(received_message) if received_message else 0}
                )
                return True
            else:
                self.log_result(
                    "backend_to_frontend_websocket",
                    "FAIL",
                    "No message received within timeout",
                    latency
                )
                return False
                
        except Exception as e:
            self.log_result(
                "backend_to_frontend_websocket",
                "FAIL",
                f"Exception: {e}",
                0
            )
            return False
    
    async def test_end_to_end_event_propagation(self) -> bool:
        """Test end-to-end event propagation timing."""
        start_time = time.time()
        events_received = []
        
        try:
            uri = "ws://localhost:8000/ws"
            
            async def websocket_client():
                try:
                    async with websockets.connect(uri, timeout=10) as websocket:
                        # Listen for multiple messages
                        for _ in range(3):  # Listen for up to 3 messages
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                events_received.append({
                                    'timestamp': time.time(),
                                    'message': message
                                })
                            except asyncio.TimeoutError:
                                break
                except Exception as e:
                    print(f"WebSocket client error: {e}")
            
            # Start WebSocket client
            client_task = asyncio.create_task(websocket_client())
            
            # Wait for connection
            await asyncio.sleep(1)
            
            # Send multiple test broadcasts
            for i in range(3):
                broadcast_data = {
                    'type': f'test_event_{i}',
                    'data': {
                        'test_id': i,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                }
                
                response = requests.post(
                    "http://localhost:8000/api/v1/internal/broadcast",
                    json=broadcast_data,
                    timeout=5
                )
                
                if response.status_code != 200:
                    print(f"Broadcast {i} failed: {response.status_code}")
                
                await asyncio.sleep(0.5)  # Small delay between broadcasts
            
            # Wait for messages
            try:
                await asyncio.wait_for(client_task, timeout=20.0)
            except asyncio.TimeoutError:
                pass
            
            latency = (time.time() - start_time) * 1000
            
            if events_received:
                # Calculate propagation times
                propagation_times = []
                for event in events_received:
                    prop_time = (event['timestamp'] - start_time) * 1000
                    propagation_times.append(prop_time)
                
                avg_propagation = sum(propagation_times) / len(propagation_times)
                max_propagation = max(propagation_times)
                
                self.log_result(
                    "end_to_end_event_propagation",
                    "PASS",
                    f"Received {len(events_received)} events",
                    latency,
                    {
                        'events_received': len(events_received),
                        'avg_propagation_ms': avg_propagation,
                        'max_propagation_ms': max_propagation
                    }
                )
                return True
            else:
                self.log_result(
                    "end_to_end_event_propagation",
                    "FAIL",
                    "No events received",
                    latency
                )
                return False
                
        except Exception as e:
            self.log_result(
                "end_to_end_event_propagation",
                "FAIL",
                f"Exception: {e}",
                0
            )
            return False
    
    async def test_websocket_reconnection_behavior(self) -> bool:
        """Test WebSocket reconnection behavior."""
        start_time = time.time()
        reconnection_attempts = 0
        successful_reconnections = 0
        
        try:
            uri = "ws://localhost:8000/ws"
            
            async def test_reconnection():
                nonlocal reconnection_attempts, successful_reconnections
                for attempt in range(3):  # Test 3 reconnection attempts
                    try:
                        reconnection_attempts += 1
                        async with websockets.connect(uri, timeout=5) as websocket:
                            # Send ping to verify connection
                            await websocket.send("ping")
                            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                            
                            if response == "pong":
                                successful_reconnections += 1
                            
                            # Close connection to simulate disconnection
                            await websocket.close()
                            
                    except Exception as e:
                        print(f"Reconnection attempt {attempt + 1} failed: {e}")
                    
                    # Wait before next attempt
                    await asyncio.sleep(1)
            
            # Test reconnection behavior
            await test_reconnection()
            
            latency = (time.time() - start_time) * 1000
            
            success_rate = (successful_reconnections / reconnection_attempts) * 100 if reconnection_attempts > 0 else 0
            
            if success_rate >= 80:  # 80% success rate
                self.log_result(
                    "websocket_reconnection_behavior",
                    "PASS",
                    f"Reconnection success rate: {success_rate:.1f}%",
                    latency,
                    {
                        'attempts': reconnection_attempts,
                        'successful': successful_reconnections,
                        'success_rate': success_rate
                    }
                )
                return True
            else:
                self.log_result(
                    "websocket_reconnection_behavior",
                    "FAIL",
                    f"Low reconnection success rate: {success_rate:.1f}%",
                    latency,
                    {
                        'attempts': reconnection_attempts,
                        'successful': successful_reconnections,
                        'success_rate': success_rate
                    }
                )
                return False
                
        except Exception as e:
            self.log_result(
                "websocket_reconnection_behavior",
                "FAIL",
                f"Exception: {e}",
                0
            )
            return False
    
    async def test_activity_stream_broadcasting(self) -> bool:
        """Test activity stream WebSocket broadcasting."""
        start_time = time.time()
        activities_received = []
        
        try:
            uri = "ws://localhost:8000/api/v1/activities/stream"
            
            async def activity_client():
                try:
                    async with websockets.connect(uri, timeout=10) as websocket:
                        # Listen for activity messages
                        for _ in range(5):  # Listen for up to 5 activities
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                                activities_received.append({
                                    'timestamp': time.time(),
                                    'message': message
                                })
                            except asyncio.TimeoutError:
                                break
                except Exception as e:
                    print(f"Activity client error: {e}")
            
            # Start activity client
            client_task = asyncio.create_task(activity_client())
            
            # Wait for connection
            await asyncio.sleep(1)
            
            # Trigger some activities by making API calls
            test_activities = [
                ("GET", "/api/v1/health"),
                ("GET", "/api/v1/portfolio/status"),
                ("GET", "/api/v1/predict?symbol=BTCUSD&timeframe=4h"),
            ]
            
            for method, endpoint in test_activities:
                try:
                    if method == "GET":
                        response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
                    # Add more methods as needed
                except Exception as e:
                    print(f"Activity trigger failed: {e}")
                
                await asyncio.sleep(0.5)  # Small delay between activities
            
            # Wait for activities
            try:
                await asyncio.wait_for(client_task, timeout=15.0)
            except asyncio.TimeoutError:
                pass
            
            latency = (time.time() - start_time) * 1000
            
            if activities_received:
                self.log_result(
                    "activity_stream_broadcasting",
                    "PASS",
                    f"Received {len(activities_received)} activity messages",
                    latency,
                    {'activities_received': len(activities_received)}
                )
                return True
            else:
                self.log_result(
                    "activity_stream_broadcasting",
                    "FAIL",
                    "No activity messages received",
                    latency
                )
                return False
                
        except Exception as e:
            self.log_result(
                "activity_stream_broadcasting",
                "FAIL",
                f"Exception: {e}",
                0
            )
            return False
    
    async def test_concurrent_websocket_clients(self) -> bool:
        """Test concurrent WebSocket client handling."""
        start_time = time.time()
        successful_connections = 0
        total_connections = 5
        
        try:
            uri = "ws://localhost:8000/ws"
            
            async def websocket_client(client_id: int):
                nonlocal successful_connections
                try:
                    async with websockets.connect(uri, timeout=10) as websocket:
                        # Send ping
                        await websocket.send("ping")
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        
                        if response == "pong":
                            successful_connections += 1
                        
                        # Keep connection alive for a bit
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    print(f"Client {client_id} error: {e}")
            
            # Start multiple concurrent clients
            client_tasks = []
            for i in range(total_connections):
                task = asyncio.create_task(websocket_client(i))
                client_tasks.append(task)
            
            # Wait for all clients to complete
            await asyncio.gather(*client_tasks, return_exceptions=True)
            
            latency = (time.time() - start_time) * 1000
            success_rate = (successful_connections / total_connections) * 100
            
            if success_rate >= 80:  # 80% success rate
                self.log_result(
                    "concurrent_websocket_clients",
                    "PASS",
                    f"Concurrent client success rate: {success_rate:.1f}%",
                    latency,
                    {
                        'total_clients': total_connections,
                        'successful': successful_connections,
                        'success_rate': success_rate
                    }
                )
                return True
            else:
                self.log_result(
                    "concurrent_websocket_clients",
                    "FAIL",
                    f"Low concurrent client success rate: {success_rate:.1f}%",
                    latency,
                    {
                        'total_clients': total_connections,
                        'successful': successful_connections,
                        'success_rate': success_rate
                    }
                )
                return False
                
        except Exception as e:
            self.log_result(
                "concurrent_websocket_clients",
                "FAIL",
                f"Exception: {e}",
                0
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all real-time communication tests."""
        print("🔍 Starting Real-Time Communication Tests...")
        print("=" * 60)
        
        tests = [
            ("Trading Agent → Backend Broadcast", self.test_trading_agent_to_backend_broadcast),
            ("Backend → Frontend WebSocket", self.test_backend_to_frontend_websocket),
            ("End-to-End Event Propagation", self.test_end_to_end_event_propagation),
            ("WebSocket Reconnection Behavior", self.test_websocket_reconnection_behavior),
            ("Activity Stream Broadcasting", self.test_activity_stream_broadcasting),
            ("Concurrent WebSocket Clients", self.test_concurrent_websocket_clients),
        ]
        
        # Run all tests
        for name, test_func in tests:
            try:
                await test_func()
            except Exception as e:
                self.log_result(name.lower().replace(" ", "_").replace("→", "to"), "ERROR", f"Exception: {e}")
        
        # Summary
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.results.values() if r['status'] == 'PASS')
        failed = sum(1 for r in self.results.values() if r['status'] == 'FAIL')
        errors = sum(1 for r in self.results.values() if r['status'] == 'ERROR')
        
        print("\n" + "=" * 60)
        print(f"📊 REAL-TIME COMMUNICATION TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"💥 Errors: {errors}")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print("=" * 60)
        
        return {
            'summary': {
                'total_tests': len(self.results),
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'total_time_seconds': total_time
            },
            'results': self.results
        }


async def main():
    """Main entry point."""
    tester = RealTimeCommunicationTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    results_file = Path("realtime_test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Exit with error code if any failures
    if results['summary']['failed'] > 0 or results['summary']['errors'] > 0:
        print("\n❌ Some real-time communication tests failed - check results above")
        sys.exit(1)
    else:
        print("\n✅ All real-time communication tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
