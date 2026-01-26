"""
Event Bus Implementation (Observer Pattern)
Decouples components - no more function chaining!
"""
from typing import Dict, List, Callable, Any
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class Event(BaseModel):
    """Base Event Model"""
    event_type: str
    timestamp: datetime
    org_id: str
    location_id: str
    payload: Dict[str, Any]
    
    class Config:
        arbitrary_types_allowed = True


EventHandler = Callable[[Event], None]


class EventBus:
    """
    Central Event Bus (Singleton)
    Components emit events, handlers subscribe to them
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers: Dict[str, List[EventHandler]] = {}
            cls._instance._initialized = False
        return cls._instance
    
    def subscribe(self, event_type: str, handler: EventHandler):
        """Subscribe a handler to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Subscribed handler to event: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: EventHandler):
        """Unsubscribe a handler from an event type"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
            logger.info(f"Unsubscribed handler from event: {event_type}")
    
    def emit(self, event: Event):
        """
        Emit an event to all subscribed handlers
        This replaces function chaining like sync_sales -> parse_sales -> analyze_sales
        """
        event_type = event.event_type
        logger.info(f"Emitting event: {event_type} for org={event.org_id}")
        
        if event_type not in self._handlers:
            logger.warning(f"No handlers registered for event: {event_type}")
            return
        
        for handler in self._handlers[event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {str(e)}")
    
    def clear_all(self):
        """Clear all handlers (for testing)"""
        self._handlers.clear()
