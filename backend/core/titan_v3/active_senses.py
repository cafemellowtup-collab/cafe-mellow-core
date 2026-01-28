"""
TITAN v3 Active Senses
======================
Real-time external data integration - TITAN's "Windows to the World"

Senses:
1. Climate Module - Weather data for demand prediction
2. Market Crawler - Commodity pricing for cost optimization
3. Event Detector - Local events affecting foot traffic
4. Trend Scanner - Social/market trends

TITAN stops living in a box and perceives the outside world.
"""

import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

from google.cloud import bigquery


class SenseType(str, Enum):
    WEATHER = "weather"
    MARKET = "market"
    EVENTS = "events"
    TRENDS = "trends"
    NEWS = "news"


@dataclass
class SenseReading:
    """A reading from an external sense"""
    sense_type: SenseType
    timestamp: datetime
    location: str
    data: Dict[str, Any]
    confidence: float
    ttl_minutes: int = 60  # How long this reading is valid
    
    @property
    def is_valid(self) -> bool:
        age = datetime.now() - self.timestamp
        return age.total_seconds() < (self.ttl_minutes * 60)


@dataclass
class WeatherContext:
    """Weather-specific context"""
    condition: str  # sunny, rainy, cloudy, etc.
    temperature_c: float
    humidity: float
    precipitation_chance: float
    wind_speed_kmh: float
    forecast_24h: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def business_impact(self) -> str:
        """Generate business impact assessment"""
        impacts = []
        
        if self.precipitation_chance > 70:
            impacts.append("High rain probability - expect reduced walk-ins, boost delivery promotions")
        elif self.condition == "sunny" and self.temperature_c > 25:
            impacts.append("Hot sunny day - promote cold beverages and AC seating")
        elif self.temperature_c < 15:
            impacts.append("Cold weather - promote hot beverages and comfort food")
        
        if self.wind_speed_kmh > 30:
            impacts.append("High winds - outdoor seating may be affected")
        
        return "; ".join(impacts) if impacts else "Normal weather conditions"


@dataclass
class MarketContext:
    """Market/commodity pricing context"""
    commodities: Dict[str, float]  # name -> price
    price_changes: Dict[str, float]  # name -> % change
    alerts: List[str] = field(default_factory=list)
    
    @property
    def cost_opportunities(self) -> List[str]:
        """Identify cost-saving opportunities"""
        opportunities = []
        
        for item, change in self.price_changes.items():
            if change < -10:
                opportunities.append(f"{item} price dropped {abs(change):.1f}% - consider bulk purchase")
            elif change > 15:
                opportunities.append(f"{item} price spiked {change:.1f}% - review alternatives")
        
        return opportunities


class ActiveSenses:
    """
    TITAN's External Perception System
    
    Integrates real-time external data to enhance AI decisions.
    """
    
    PROJECT_ID = "cafe-mellow-core-2026"
    DATASET_ID = "cafe_operations"
    
    # Cache for readings
    _cache: Dict[str, SenseReading] = {}
    
    def __init__(self, location: str = "Bangalore, India"):
        self.location = location
        self.bq_client = bigquery.Client(project=self.PROJECT_ID)
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create sense readings table"""
        schema = [
            bigquery.SchemaField("reading_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("sense_type", "STRING"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("location", "STRING"),
            bigquery.SchemaField("data", "JSON"),
            bigquery.SchemaField("confidence", "FLOAT64"),
        ]
        
        table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.titan_sense_readings"
        try:
            self.bq_client.get_table(table_ref)
        except Exception:
            table = bigquery.Table(table_ref, schema=schema)
            self.bq_client.create_table(table)
    
    async def get_weather(self, location: Optional[str] = None) -> WeatherContext:
        """Get current weather and forecast"""
        loc = location or self.location
        cache_key = f"weather:{loc}"
        
        # Check cache
        if cache_key in self._cache and self._cache[cache_key].is_valid:
            return self._parse_weather(self._cache[cache_key].data)
        
        # Fetch from API (using Open-Meteo - free, no API key)
        try:
            weather_data = await self._fetch_weather(loc)
            
            reading = SenseReading(
                sense_type=SenseType.WEATHER,
                timestamp=datetime.now(),
                location=loc,
                data=weather_data,
                confidence=0.9,
                ttl_minutes=30,
            )
            
            self._cache[cache_key] = reading
            self._log_reading(reading)
            
            return self._parse_weather(weather_data)
            
        except Exception as e:
            # Return default context on failure
            return WeatherContext(
                condition="unknown",
                temperature_c=25.0,
                humidity=60.0,
                precipitation_chance=20.0,
                wind_speed_kmh=10.0,
            )
    
    async def _fetch_weather(self, location: str) -> Dict[str, Any]:
        """Fetch weather from Open-Meteo API"""
        # Geocode location first (simplified - using hardcoded for Bangalore)
        lat, lon = self._geocode(location)
        
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&"
            f"hourly=temperature_2m,precipitation_probability&"
            f"timezone=auto&forecast_days=1"
        )
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return {}
    
    def _geocode(self, location: str) -> tuple:
        """Simple geocoding (extendable)"""
        # Common Indian cities
        locations = {
            "bangalore": (12.9716, 77.5946),
            "mumbai": (19.0760, 72.8777),
            "delhi": (28.6139, 77.2090),
            "chennai": (13.0827, 80.2707),
            "hyderabad": (17.3850, 78.4867),
            "pune": (18.5204, 73.8567),
            "kolkata": (22.5726, 88.3639),
        }
        
        loc_lower = location.lower()
        for city, coords in locations.items():
            if city in loc_lower:
                return coords
        
        return (12.9716, 77.5946)  # Default to Bangalore
    
    def _parse_weather(self, data: Dict) -> WeatherContext:
        """Parse weather API response"""
        current = data.get("current", {})
        hourly = data.get("hourly", {})
        
        # Weather code to condition mapping
        weather_codes = {
            0: "sunny", 1: "mostly_sunny", 2: "partly_cloudy", 3: "cloudy",
            45: "foggy", 48: "foggy", 51: "drizzle", 53: "drizzle", 55: "drizzle",
            61: "rainy", 63: "rainy", 65: "heavy_rain", 80: "showers", 81: "showers",
            95: "thunderstorm", 96: "thunderstorm", 99: "thunderstorm",
        }
        
        weather_code = current.get("weather_code", 0)
        condition = weather_codes.get(weather_code, "unknown")
        
        # Build 24h forecast
        forecast = []
        temps = hourly.get("temperature_2m", [])
        precip_probs = hourly.get("precipitation_probability", [])
        
        for i in range(min(24, len(temps))):
            forecast.append({
                "hour": i,
                "temperature_c": temps[i] if i < len(temps) else 25,
                "precipitation_chance": precip_probs[i] if i < len(precip_probs) else 20,
            })
        
        return WeatherContext(
            condition=condition,
            temperature_c=current.get("temperature_2m", 25),
            humidity=current.get("relative_humidity_2m", 60),
            precipitation_chance=precip_probs[0] if precip_probs else 20,
            wind_speed_kmh=current.get("wind_speed_10m", 10),
            forecast_24h=forecast,
        )
    
    async def get_market_prices(self, commodities: List[str] = None) -> MarketContext:
        """Get commodity prices (simulated - can connect to real APIs)"""
        default_commodities = [
            "milk", "coffee_beans", "sugar", "wheat_flour", 
            "vegetable_oil", "eggs", "tomatoes", "onions"
        ]
        
        items = commodities or default_commodities
        cache_key = f"market:{','.join(sorted(items))}"
        
        if cache_key in self._cache and self._cache[cache_key].is_valid:
            return self._parse_market(self._cache[cache_key].data)
        
        # Simulated market data (in production, connect to commodity APIs)
        market_data = self._simulate_market_data(items)
        
        reading = SenseReading(
            sense_type=SenseType.MARKET,
            timestamp=datetime.now(),
            location=self.location,
            data=market_data,
            confidence=0.7,
            ttl_minutes=240,  # 4 hour cache
        )
        
        self._cache[cache_key] = reading
        self._log_reading(reading)
        
        return self._parse_market(market_data)
    
    def _simulate_market_data(self, items: List[str]) -> Dict:
        """Simulate market data (replace with real API in production)"""
        import random
        
        base_prices = {
            "milk": 60, "coffee_beans": 800, "sugar": 45, "wheat_flour": 35,
            "vegetable_oil": 150, "eggs": 7, "tomatoes": 40, "onions": 35,
            "chicken": 220, "paneer": 380, "butter": 500, "cheese": 450,
        }
        
        prices = {}
        changes = {}
        
        for item in items:
            base = base_prices.get(item, 100)
            # Random fluctuation ±15%
            variance = random.uniform(-0.15, 0.15)
            prices[item] = round(base * (1 + variance), 2)
            changes[item] = round(variance * 100, 1)
        
        return {"prices": prices, "changes": changes}
    
    def _parse_market(self, data: Dict) -> MarketContext:
        """Parse market data"""
        prices = data.get("prices", {})
        changes = data.get("changes", {})
        
        context = MarketContext(
            commodities=prices,
            price_changes=changes,
        )
        
        context.alerts = context.cost_opportunities
        return context
    
    async def get_local_events(self) -> List[Dict[str, Any]]:
        """Get local events that might affect business"""
        cache_key = f"events:{self.location}"
        
        if cache_key in self._cache and self._cache[cache_key].is_valid:
            return self._cache[cache_key].data.get("events", [])
        
        # Simulated events (can connect to event APIs)
        events = self._simulate_local_events()
        
        reading = SenseReading(
            sense_type=SenseType.EVENTS,
            timestamp=datetime.now(),
            location=self.location,
            data={"events": events},
            confidence=0.6,
            ttl_minutes=120,
        )
        
        self._cache[cache_key] = reading
        self._log_reading(reading)
        
        return events
    
    def _simulate_local_events(self) -> List[Dict]:
        """Simulate local events (replace with real API)"""
        # This would connect to event APIs, social media, etc.
        return [
            {
                "name": "Tech Conference",
                "type": "business",
                "distance_km": 2.5,
                "expected_footfall": "high",
                "start_time": "09:00",
                "end_time": "18:00",
                "impact": "Expect 30% higher lunch traffic",
            }
        ]
    
    def _log_reading(self, reading: SenseReading):
        """Log sense reading to BigQuery"""
        reading_id = hashlib.md5(
            f"{reading.sense_type.value}:{reading.timestamp.isoformat()}".encode()
        ).hexdigest()[:16]
        
        row = {
            "reading_id": reading_id,
            "sense_type": reading.sense_type.value,
            "timestamp": reading.timestamp.isoformat(),
            "location": reading.location,
            "data": reading.data,
            "confidence": reading.confidence,
        }
        
        table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.titan_sense_readings"
        try:
            self.bq_client.insert_rows_json(table_ref, [row])
        except Exception:
            pass
    
    async def build_external_context(self) -> str:
        """Build complete external context for AI injection"""
        weather = await self.get_weather()
        market = await self.get_market_prices()
        events = await self.get_local_events()
        
        context_parts = [
            "## EXTERNAL CONTEXT (Real-Time Senses)",
            "",
            "### Weather",
            f"- Condition: {weather.condition}",
            f"- Temperature: {weather.temperature_c}°C",
            f"- Rain chance: {weather.precipitation_chance}%",
            f"- Impact: {weather.business_impact}",
            "",
            "### Market Prices",
        ]
        
        for item, price in list(weather.humidity and market.commodities.items())[:5]:
            change = market.price_changes.get(item, 0)
            arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
            context_parts.append(f"- {item.title()}: ₹{price} ({arrow}{abs(change):.1f}%)")
        
        if market.alerts:
            context_parts.append("")
            context_parts.append("### Cost Alerts")
            for alert in market.alerts[:3]:
                context_parts.append(f"- {alert}")
        
        if events:
            context_parts.append("")
            context_parts.append("### Local Events")
            for event in events[:2]:
                context_parts.append(f"- {event['name']}: {event.get('impact', 'Unknown impact')}")
        
        return "\n".join(context_parts)
    
    def get_recommendation(self, context_type: str = "all") -> List[str]:
        """Get AI-ready recommendations based on external senses"""
        recommendations = []
        
        # Weather-based
        weather_cache = self._cache.get(f"weather:{self.location}")
        if weather_cache and weather_cache.is_valid:
            weather = self._parse_weather(weather_cache.data)
            if weather.precipitation_chance > 60:
                recommendations.append(
                    "WEATHER ALERT: Rain expected. Suggest: Push delivery promotions, "
                    "reduce outdoor prep, stock umbrellas for customers."
                )
            if weather.temperature_c > 32:
                recommendations.append(
                    "HEAT ALERT: High temperature. Suggest: Feature cold beverages, "
                    "ensure AC maintenance, offer water bottles."
                )
        
        # Market-based
        market_cache = self._cache.get(f"market:{self.location}")
        if market_cache and market_cache.is_valid:
            market = self._parse_market(market_cache.data)
            for opp in market.cost_opportunities[:2]:
                recommendations.append(f"COST OPPORTUNITY: {opp}")
        
        return recommendations
