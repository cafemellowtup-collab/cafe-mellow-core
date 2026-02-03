"""
TITAN v3 Personality Engine
============================
Dual-Heart System: PREDATOR mode (Strategic) and PARTNER mode (Supportive)

The AI dynamically switches personality based on:
1. User sentiment (anxiety, frustration, confidence)
2. Query type (data query vs emotional support)
3. Business context (crisis vs normal operations)
"""

import re
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime


class PersonalityMode(str, Enum):
    PREDATOR = "predator"  # Cold, strategic, chart-heavy, action-focused
    PARTNER = "partner"    # Warm, supportive, text-focused, empathetic
    HYBRID = "hybrid"      # Balanced approach for neutral queries


class SentimentLevel(str, Enum):
    ANXIOUS = "anxious"
    FRUSTRATED = "frustrated"
    NEUTRAL = "neutral"
    CONFIDENT = "confident"
    EXCITED = "excited"


class QueryType(str, Enum):
    DATA_REQUEST = "data_request"      # "Show me revenue"
    ANALYSIS = "analysis"               # "Why is profit down?"
    EMOTIONAL = "emotional"             # "I'm worried about..."
    STRATEGIC = "strategic"             # "Should I expand?"
    CRISIS = "crisis"                   # "Sales crashed!"
    CASUAL = "casual"                   # "How's business?"


@dataclass
class PersonalityContext:
    """Context for personality selection"""
    mode: PersonalityMode
    sentiment: SentimentLevel
    query_type: QueryType
    confidence: float
    triggers: List[str]
    tone_instructions: str
    response_style: Dict[str, Any]


# Sentiment detection patterns
ANXIETY_PATTERNS = [
    r'\b(worried|anxious|scared|nervous|concerned|afraid|stressed|panic)\b',
    r'\b(not sure|uncertain|confused|lost|struggling)\b',
    r'\b(help me|what should i|what do i do|any advice)\b',
    r'\?\?+',  # Multiple question marks indicate uncertainty
]

FRUSTRATION_PATTERNS = [
    r'\b(frustrated|angry|annoyed|upset|furious|mad)\b',
    r'\b(why (is|are|does|do|isn\'t|won\'t)|what the|how come)\b',
    r'\b(stupid|useless|broken|failing|crashed|disaster)\b',
    r'!{2,}',  # Multiple exclamation marks
]

CONFIDENCE_PATTERNS = [
    r'\b(show me|tell me|give me|i want|i need|get me)\b',
    r'\b(analyze|compare|calculate|optimize|maximize)\b',
    r'\b(strategy|plan|decision|expand|invest|grow)\b',
]

CRISIS_PATTERNS = [
    r'\b(crash|crashed|plummet|disaster|emergency|urgent|asap)\b',
    r'\b(lost|losing|down \d+%|dropped|collapsed|failed)\b',
    r'\b(zero|nothing|no sales|empty|bankrupt)\b',
]

DATA_PATTERNS = [
    r'\b(revenue|sales|profit|expense|cost|margin|orders)\b',
    r'\b(how much|what is|show|display|chart|graph|table)\b',
    r'\b(today|yesterday|this week|last month|ytd|q[1-4])\b',
]


class PersonalityEngine:
    """
    The Dual-Heart Personality System
    
    Dynamically switches between PREDATOR (strategic) and PARTNER (supportive)
    modes based on user sentiment and context.
    """
    
    def __init__(self):
        self.sentiment_history: List[SentimentLevel] = []
        self.mode_history: List[PersonalityMode] = []
        self.user_preferences: Dict[str, Any] = {}

    def detect_sentiment(self, message: str) -> SentimentLevel:
        sentiment, _ = self._detect_sentiment(message)
        return sentiment

    def classify_query_type(self, message: str) -> QueryType:
        return self._detect_query_type(message)

    def select_mode(
        self,
        sentiment: SentimentLevel,
        query_type: QueryType,
        business_context: Optional[Dict] = None,
    ) -> PersonalityMode:
        is_crisis = self._check_crisis_context(business_context)
        mode, _ = self._select_mode(sentiment, query_type, is_crisis)
        return mode

    def get_tone_instructions(
        self,
        mode: PersonalityMode,
        sentiment: Optional[SentimentLevel] = None,
    ) -> str:
        return self._generate_tone_instructions(mode, sentiment or SentimentLevel.NEUTRAL)
        
    def analyze_message(self, message: str, business_context: Optional[Dict] = None) -> PersonalityContext:
        """
        Analyze user message and determine optimal personality mode
        """
        message_lower = message.lower()
        
        # Detect sentiment
        sentiment, sentiment_confidence = self._detect_sentiment(message_lower)
        
        # Detect query type
        query_type = self._detect_query_type(message_lower)
        
        # Check business context for crisis indicators
        is_crisis = self._check_crisis_context(business_context)
        
        # Determine personality mode
        mode, triggers = self._select_mode(sentiment, query_type, is_crisis)
        
        # Generate tone instructions
        tone_instructions = self._generate_tone_instructions(mode, sentiment)
        
        # Build response style guidelines
        response_style = self._build_response_style(mode, query_type)
        
        # Track history for learning
        self.sentiment_history.append(sentiment)
        self.mode_history.append(mode)
        
        return PersonalityContext(
            mode=mode,
            sentiment=sentiment,
            query_type=query_type,
            confidence=sentiment_confidence,
            triggers=triggers,
            tone_instructions=tone_instructions,
            response_style=response_style
        )
    
    def _detect_sentiment(self, message: str) -> Tuple[SentimentLevel, float]:
        """Detect user sentiment from message patterns"""
        scores = {
            SentimentLevel.ANXIOUS: 0,
            SentimentLevel.FRUSTRATED: 0,
            SentimentLevel.CONFIDENT: 0,
            SentimentLevel.NEUTRAL: 0.3,  # Base score
        }
        
        # Check anxiety patterns
        for pattern in ANXIETY_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                scores[SentimentLevel.ANXIOUS] += 0.3
                
        # Check frustration patterns
        for pattern in FRUSTRATION_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                scores[SentimentLevel.FRUSTRATED] += 0.3
                
        # Check confidence patterns
        for pattern in CONFIDENCE_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                scores[SentimentLevel.CONFIDENT] += 0.25
        
        # Find highest scoring sentiment
        max_sentiment = max(scores, key=scores.get)
        confidence = min(scores[max_sentiment], 1.0)
        
        return max_sentiment, confidence
    
    def _detect_query_type(self, message: str) -> QueryType:
        """Classify the type of query"""
        # Check for crisis first (highest priority)
        for pattern in CRISIS_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return QueryType.CRISIS
        
        # Check for data requests
        data_score = 0
        for pattern in DATA_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                data_score += 1
        
        if data_score >= 2:
            return QueryType.DATA_REQUEST
        
        # Check for emotional queries
        for pattern in ANXIETY_PATTERNS + FRUSTRATION_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return QueryType.EMOTIONAL
        
        # Check for strategic queries
        if re.search(r'\b(should i|would it|is it worth|strategy|plan|expand|invest)\b', message):
            return QueryType.STRATEGIC
        
        # Check for analysis queries
        if re.search(r'\b(why|how come|analyze|explain|reason|cause)\b', message):
            return QueryType.ANALYSIS
        
        return QueryType.CASUAL
    
    def _check_crisis_context(self, context: Optional[Dict]) -> bool:
        """Check if business metrics indicate a crisis"""
        if not context:
            return False
            
        # Crisis indicators
        revenue_change = context.get("revenue_change_7d", 0)
        profit_margin = context.get("profit_margin_7d", 100)
        low_stock = context.get("low_stock_items", 0)
        active_alerts = context.get("active_alerts", 0)
        
        crisis_score = 0
        if revenue_change < -30:
            crisis_score += 2
        elif revenue_change < -15:
            crisis_score += 1
            
        if profit_margin < 5:
            crisis_score += 2
        elif profit_margin < 15:
            crisis_score += 1
            
        if low_stock > 10:
            crisis_score += 1
            
        if active_alerts > 3:
            crisis_score += 1
            
        return crisis_score >= 3
    
    def _select_mode(
        self, 
        sentiment: SentimentLevel, 
        query_type: QueryType,
        is_crisis: bool
    ) -> Tuple[PersonalityMode, List[str]]:
        """Select personality mode based on analysis"""
        triggers = []
        
        # Partner mode triggers (emotional support needed)
        if sentiment in [SentimentLevel.ANXIOUS, SentimentLevel.FRUSTRATED]:
            triggers.append(f"User sentiment: {sentiment.value}")
            return PersonalityMode.PARTNER, triggers
            
        if query_type == QueryType.EMOTIONAL:
            triggers.append("Emotional query detected")
            return PersonalityMode.PARTNER, triggers
        
        # Predator mode triggers (strategic/data focus)
        if query_type in [QueryType.DATA_REQUEST, QueryType.STRATEGIC]:
            triggers.append(f"Query type: {query_type.value}")
            return PersonalityMode.PREDATOR, triggers
            
        if sentiment == SentimentLevel.CONFIDENT:
            triggers.append("User shows confidence")
            return PersonalityMode.PREDATOR, triggers
            
        if is_crisis:
            triggers.append("Crisis context detected")
            return PersonalityMode.PREDATOR, triggers
        
        # Hybrid for analysis and casual
        if query_type in [QueryType.ANALYSIS, QueryType.CASUAL]:
            triggers.append(f"Balanced query: {query_type.value}")
            return PersonalityMode.HYBRID, triggers
        
        return PersonalityMode.HYBRID, ["Default mode"]
    
    def _generate_tone_instructions(self, mode: PersonalityMode, sentiment: SentimentLevel) -> str:
        """Generate specific tone instructions for the AI"""
        
        if mode == PersonalityMode.PREDATOR:
            return """PREDATOR MODE ACTIVE:
- Be direct, concise, and action-oriented
- Lead with numbers and data visualizations
- Use imperative language: "Cut X", "Increase Y", "Stop Z"
- No pleasantries or emotional cushioning
- Structure: METRIC → INSIGHT → ACTION → EXPECTED RESULT
- Use tables and charts liberally
- Speak like a ruthless CFO advisor"""
        
        elif mode == PersonalityMode.PARTNER:
            instructions = """PARTNER MODE ACTIVE:
- Be warm, supportive, and reassuring
- Acknowledge emotions before presenting data
- Use collaborative language: "Let's look at...", "Together we can..."
- Provide context and explanations
- Structure: ACKNOWLEDGMENT → CONTEXT → DATA → ENCOURAGEMENT → SMALL WIN
- Minimize charts; focus on narrative
- Speak like a trusted business mentor"""
            
            if sentiment == SentimentLevel.ANXIOUS:
                instructions += "\n- Extra reassurance needed - emphasize stability and controllables"
            elif sentiment == SentimentLevel.FRUSTRATED:
                instructions += "\n- Validate frustration first - then pivot to solutions"
                
            return instructions
        
        else:  # HYBRID
            return """HYBRID MODE ACTIVE:
- Balance data with explanation
- Professional but approachable tone
- Use "Here's what the data shows..." style
- Include both charts and narrative
- Structure: SUMMARY → DATA → ANALYSIS → RECOMMENDATION
- Speak like a knowledgeable business partner"""
    
    def _build_response_style(self, mode: PersonalityMode, query_type: QueryType) -> Dict[str, Any]:
        """Build response style guidelines"""
        
        base_style = {
            "include_charts": True,
            "include_tables": True,
            "include_tasks": True,
            "max_narrative_length": "medium",
            "emoji_level": "minimal",
            "data_density": "high",
        }
        
        if mode == PersonalityMode.PREDATOR:
            return {
                **base_style,
                "include_charts": True,
                "include_tables": True,
                "include_tasks": True,
                "max_narrative_length": "short",
                "emoji_level": "none",
                "data_density": "very_high",
                "opening_style": "direct_metric",
                "closing_style": "action_command",
            }
        
        elif mode == PersonalityMode.PARTNER:
            return {
                **base_style,
                "include_charts": False,
                "include_tables": False,
                "include_tasks": True,
                "max_narrative_length": "long",
                "emoji_level": "moderate",
                "data_density": "low",
                "opening_style": "empathetic_acknowledgment",
                "closing_style": "encouragement",
            }
        
        else:  # HYBRID
            return {
                **base_style,
                "include_charts": True,
                "include_tables": True,
                "include_tasks": True,
                "max_narrative_length": "medium",
                "emoji_level": "minimal",
                "data_density": "medium",
                "opening_style": "summary",
                "closing_style": "recommendation",
            }
    
    def get_system_prompt_modifier(self, context: PersonalityContext) -> str:
        """Get the personality-specific system prompt modifier"""
        return f"""
{context.tone_instructions}

TRIGGERS FOR THIS MODE: {', '.join(context.triggers)}
USER SENTIMENT: {context.sentiment.value} (confidence: {context.confidence:.0%})
QUERY TYPE: {context.query_type.value}

RESPONSE STYLE GUIDELINES:
- Charts/Graphs: {"Yes" if context.response_style.get("include_charts") else "No"}
- Tables: {"Yes" if context.response_style.get("include_tables") else "No"}
- Data Density: {context.response_style.get("data_density", "medium")}
- Narrative Length: {context.response_style.get("max_narrative_length", "medium")}
- Opening: {context.response_style.get("opening_style", "summary")}
- Closing: {context.response_style.get("closing_style", "recommendation")}
"""

    def learn_from_feedback(self, message: str, response_rating: int, mode_used: PersonalityMode):
        """Learn from user feedback to improve mode selection"""
        # Store feedback for future learning
        # This would connect to the evolution core for pattern learning
        pass
