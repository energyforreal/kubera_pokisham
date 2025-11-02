"""
Activity Manager for Trading Bot

Handles real-time activity logging with 24-hour TTL and WebSocket broadcasting.
Memory-only storage for clean, fast operations.
"""

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Activity:
    """Activity data structure"""
    id: str
    timestamp: datetime
    type: str  # 'prediction', 'trade', 'position_change', 'error'
    message: str
    data: Dict[str, Any]
    level: str  # 'info', 'success', 'warning', 'error'

class ActivityManager:
    """
    Thread-safe activity manager with 24-hour TTL and WebSocket broadcasting.
    """
    
    def __init__(self, max_age_hours: int = 24):
        self.max_age_hours = max_age_hours
        self.activities: List[Activity] = []
        self._lock = threading.Lock()
        self._websocket_connections: List[Any] = []  # Will store WebSocket connections
        self._cleanup_interval = 3600  # Cleanup every hour
        self._last_cleanup = time.time()
        self._connection_cleanup_interval = 300  # 5 minutes
        self._last_connection_cleanup = time.time()
        
        logger.info(f"ActivityManager initialized with {max_age_hours}h TTL")
    
    def log_activity(self, 
                    activity_type: str, 
                    message: str, 
                    data: Optional[Dict[str, Any]] = None,
                    level: str = 'info') -> str:
        """
        Log a new activity with UTC timestamp.
        
        Args:
            activity_type: Type of activity ('prediction', 'trade', 'position_change', 'error')
            message: Human-readable message
            data: Additional data payload
            level: Log level ('info', 'success', 'warning', 'error')
            
        Returns:
            Activity ID
        """
        with self._lock:
            # Generate unique ID
            activity_id = f"{activity_type}_{len(self.activities) + 1}_{int(time.time())}"
            
            # Create activity with UTC timestamp
            activity = Activity(
                id=activity_id,
                timestamp=datetime.now(timezone.utc),
                type=activity_type,
                message=message,
                data=data or {},
                level=level
            )
            
            # Add to activities list
            self.activities.append(activity)
            
            # Cleanup old activities periodically
            self._cleanup_if_needed()
            
            logger.debug(f"Logged activity: {message}")
            
            # Broadcast to WebSocket connections
            self._broadcast_activity(activity)
            
            return activity_id
    
    def get_recent_activities(self, 
                             limit: int = 50, 
                             since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get recent activities, optionally filtered by timestamp.
        
        Args:
            limit: Maximum number of activities to return
            since: Only return activities after this timestamp
            
        Returns:
            List of activity dictionaries
        """
        with self._lock:
            # Cleanup old activities first
            self._cleanup_if_needed()
            
            # Filter activities
            filtered_activities = self.activities
            
            if since:
                filtered_activities = [
                    a for a in filtered_activities 
                    if a.timestamp >= since
                ]
            
            # Sort by timestamp (newest first)
            sorted_activities = sorted(
                filtered_activities, 
                key=lambda x: x.timestamp, 
                reverse=True
            )
            
            # Limit results
            limited_activities = sorted_activities[:limit]
            
            # Convert to dictionaries
            return [
                {
                    'id': a.id,
                    'timestamp': a.timestamp.isoformat(),
                    'type': a.type,
                    'message': a.message,
                    'data': a.data,
                    'level': a.level
                }
                for a in limited_activities
            ]
    
    def cleanup_old_activities(self) -> int:
        """
        Remove activities older than max_age_hours.
        
        Returns:
            Number of activities removed
        """
        with self._lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.max_age_hours)
            
            # Count activities to be removed
            old_count = len([a for a in self.activities if a.timestamp < cutoff_time])
            
            # Remove old activities
            self.activities = [
                a for a in self.activities 
                if a.timestamp >= cutoff_time
            ]
            
            if old_count > 0:
                logger.info(f"Cleaned up {old_count} old activities (older than {self.max_age_hours}h)")
            
            return old_count
    
    def _cleanup_if_needed(self):
        """Clean up old activities and dead connections if cleanup interval has passed."""
        current_time = time.time()
        
        # Clean up old activities
        if current_time - self._last_cleanup > self._cleanup_interval:
            self.cleanup_old_activities()
            self._last_cleanup = current_time
        
        # Clean up dead connections
        if current_time - self._last_connection_cleanup > self._connection_cleanup_interval:
            self._cleanup_dead_connections()
            self._last_connection_cleanup = current_time
    
    def _cleanup_dead_connections(self):
        """Remove dead WebSocket connections."""
        with self._lock:
            dead_connections = []
            for connection in self._websocket_connections:
                try:
                    # Test if connection is still alive
                    if hasattr(connection, 'closed') and connection.closed:
                        dead_connections.append(connection)
                except Exception:
                    dead_connections.append(connection)
            
            for connection in dead_connections:
                self._websocket_connections.remove(connection)
            
            if dead_connections:
                logger.info(f"Cleaned up {len(dead_connections)} dead WebSocket connections")
    
    def _broadcast_activity(self, activity: Activity):
        """Broadcast activity to all WebSocket connections."""
        if not self._websocket_connections:
            return
        
        # Convert activity to dict for JSON serialization
        activity_dict = {
            'id': activity.id,
            'timestamp': activity.timestamp.isoformat(),
            'type': activity.type,
            'message': activity.message,
            'data': activity.data,
            'level': activity.level
        }
        
        # Broadcast to all connections
        for connection in self._websocket_connections[:]:  # Copy list to avoid modification during iteration
            try:
                connection.send_json(activity_dict)
            except Exception as e:
                logger.warning(f"Failed to broadcast to WebSocket connection: {e}")
                # Remove dead connection
                self._websocket_connections.remove(connection)
    
    def add_websocket_connection(self, websocket):
        """Add a WebSocket connection for real-time broadcasting."""
        with self._lock:
            self._websocket_connections.append(websocket)
            logger.info(f"Added WebSocket connection. Total connections: {len(self._websocket_connections)}")
    
    def remove_websocket_connection(self, websocket):
        """Remove a WebSocket connection."""
        with self._lock:
            if websocket in self._websocket_connections:
                self._websocket_connections.remove(websocket)
                logger.info(f"Removed WebSocket connection. Total connections: {len(self._websocket_connections)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get activity statistics."""
        with self._lock:
            total_activities = len(self.activities)
            
            # Count by type
            type_counts = {}
            for activity in self.activities:
                type_counts[activity.type] = type_counts.get(activity.type, 0) + 1
            
            # Get oldest and newest timestamps
            if self.activities:
                oldest = min(a.timestamp for a in self.activities)
                newest = max(a.timestamp for a in self.activities)
            else:
                oldest = newest = None
            
            return {
                'total_activities': total_activities,
                'type_counts': type_counts,
                'oldest_activity': oldest.isoformat() if oldest else None,
                'newest_activity': newest.isoformat() if newest else None,
                'websocket_connections': len(self._websocket_connections),
                'max_age_hours': self.max_age_hours
            }

# Global instance
activity_manager = ActivityManager()
