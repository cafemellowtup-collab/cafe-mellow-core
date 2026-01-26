"""
Market Intelligence and Weather Integration
"""
import requests
import settings

class MarketIntelligence:
    """Get market and weather data for business insights"""
    
    def __init__(self, city="Tiruppur", state="Tamil Nadu", country="India"):
        self.city = city
        self.state = state
        self.country = country
        # You'll need to get API keys for these services
        self.weather_api_key = None  # Add your OpenWeatherMap API key
        self.weather_url = "https://api.openweathermap.org/data/2.5/weather"
    
    def get_weather(self):
        """Get current weather for Tiruppur"""
        if not self.weather_api_key:
            return {
                'status': 'unavailable',
                'message': 'Weather API key not configured. Configure in settings.'
            }
        
        try:
            params = {
                'q': f"{self.city},{self.state},{self.country}",
                'appid': self.weather_api_key,
                'units': 'metric'
            }
            response = requests.get(self.weather_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'success',
                    'temperature': data['main']['temp'],
                    'condition': data['weather'][0]['main'],
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description']
                }
            else:
                return {'status': 'error', 'message': f'API returned {response.status_code}'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_weather_insights(self):
        """Get business insights based on weather. Tiruppur context for electricity when API unavailable."""
        weather = self.get_weather()
        
        if weather['status'] != 'success':
            # Tiruppur Context (Pillar 4 fallback): enables AI to explain electricity costs
            return (
                f"{self.city}, {self.state}: In hot season (March–June) temperatures typically reach 35–40°C. "
                "High AC usage during such weeks can significantly increase electricity costs. "
                "Use this when explaining elevated electricity expenses (e.g. 'likely due to 36–40°C heat in Tiruppur requiring max AC usage')."
            )
        
        insights = []
        temp = weather.get('temperature', 0)
        condition = weather.get('condition', '').lower()
        
        # Temperature-based insights (include Tiruppur electricity angle when hot)
        if temp > 35:
            insights.append(f"🌡️ High temperature ({temp}°C). Hot beverages may sell less. Focus on cold drinks, ice cream, and AC. Electricity costs often rise in such heat in Tiruppur.")
        elif temp < 20:
            insights.append("🌡️ Cool weather. Hot beverages and warm food items will likely perform better.")
        
        # Weather condition insights
        if 'rain' in condition:
            insights.append("☔ Rainy day expected. Indoor seating will be preferred. Delivery orders may increase.")
        elif 'clear' in condition or 'sunny' in condition:
            insights.append("☀️ Clear weather. Good day for outdoor seating if available.")
        
        return "\n".join(insights) if insights else "Normal weather conditions. Standard operations expected."
    
    def get_market_context(self):
        """Get market context for Tiruppur"""
        # Placeholder for market data integration
        # This would connect to economic data APIs, local business intelligence, etc.
        return f"""
Market Context for {self.city}, {self.state}:
- Industrial textile city known for knitwear exports
- Growing food & beverage sector
- Mix of local and urban customers
- Competitive market with price sensitivity
- Seasonal variations based on local festivals and textile seasons
        """
