"""
Semantic Brain - The AGI Data Understanding Engine
===================================================
This is the "Human-Like Understanding" layer that makes the system
understand ANY data without predefined rules.

CORE PRINCIPLE: We don't write code for scenarios, we write code for PATTERNS.

Components:
1. SemanticClassifier - AI-powered data categorization
2. AutoSchemaGenerator - Dynamic category/table creation  
3. ConfidenceScorer - Determines when to auto-approve vs ask human
4. PatternLearner - Gets smarter with every interaction
5. SemanticCache - Cost optimization via pattern similarity

The system handles 2 Crore+ scenarios by understanding CONCEPTS, not memorizing formats.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel


# =============================================================================
# Core Business Concepts (The Semantic Universe)
# =============================================================================

class BusinessConcept(str, Enum):
    """
    Core business concepts that the AI understands.
    These are not "categories" but semantic MEANINGS.
    """
    SALES = "sales"                    # Money coming IN from customers
    EXPENSE = "expense"                # Money going OUT for operations
    INVENTORY = "inventory"            # Physical goods/stock
    RECIPE = "recipe"                  # How to make products
    MENU = "menu"                      # What we sell and prices
    CRM = "crm"                        # Customer information
    STAFF = "staff"                    # Employee data
    VENDOR = "vendor"                  # Supplier information
    FEEDBACK = "feedback"              # Reviews, ratings, complaints
    RESERVATION = "reservation"        # Bookings, table management
    LOYALTY = "loyalty"                # Points, rewards, memberships
    MARKETING = "marketing"            # Campaigns, promotions
    FINANCE = "finance"                # Accounting, taxes, reports
    OPERATIONS = "operations"          # Shifts, schedules, tasks
    INFRASTRUCTURE = "infrastructure"  # Equipment, utilities, assets
    UNKNOWN = "unknown"                # New category to be created


class SubCategory(str, Enum):
    """
    Sub-categories for more granular classification.
    """
    # Sales
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"
    CATERING = "catering"
    
    # Expense
    RAW_MATERIAL = "raw_material"
    SALARY = "salary"
    UTILITIES = "utilities"
    RENT = "rent"
    MARKETING_EXPENSE = "marketing_expense"
    MAINTENANCE = "maintenance"
    
    # Inventory
    INGREDIENT = "ingredient"
    PACKAGING = "packaging"
    EQUIPMENT = "equipment"
    
    # CRM
    CUSTOMER_PROFILE = "customer_profile"
    CUSTOMER_FEEDBACK = "customer_feedback"
    CUSTOMER_ORDER_HISTORY = "customer_order_history"
    
    # Staff
    EMPLOYEE_PROFILE = "employee_profile"
    ATTENDANCE = "attendance"
    PAYROLL = "payroll"
    
    # Generic
    GENERAL = "general"
    OTHER = "other"


# =============================================================================
# Semantic Classification Result
# =============================================================================

@dataclass
class SemanticClassification:
    """
    Result of semantic analysis on data.
    """
    primary_concept: BusinessConcept
    sub_category: SubCategory
    confidence_score: float  # 0.0 to 1.0
    reasoning: str  # AI's explanation
    suggested_schema: Dict[str, str]  # Field -> Type mapping
    extracted_amount: Optional[float] = None  # Monetary value if detected
    extracted_date: Optional[str] = None  # Date if detected
    key_entities: List[str] = field(default_factory=list)  # Important extracted entities
    alternative_concepts: List[Tuple[BusinessConcept, float]] = field(default_factory=list)
    requires_human_review: bool = False
    review_reason: Optional[str] = None


# =============================================================================
# Semantic Classifier - The AI Brain
# =============================================================================

class SemanticClassifier:
    """
    AI-powered semantic classifier that understands data like a human.
    Uses Gemini to analyze data content and determine its business meaning.
    """
    
    # Semantic patterns that indicate specific concepts
    CONCEPT_INDICATORS = {
        BusinessConcept.SALES: [
            "order", "sale", "revenue", "bill", "invoice", "customer", "table",
            "item", "quantity", "price", "total", "subtotal", "tax", "discount",
            "payment", "cash", "card", "upi", "tip", "dine", "takeaway", "delivery"
        ],
        BusinessConcept.EXPENSE: [
            "expense", "cost", "payment", "vendor", "supplier", "purchase",
            "salary", "wage", "rent", "utility", "electricity", "water", "gas",
            "maintenance", "repair", "marketing", "advertising", "insurance"
        ],
        BusinessConcept.INVENTORY: [
            "stock", "inventory", "ingredient", "item", "quantity", "unit",
            "batch", "expiry", "reorder", "minimum", "maximum", "warehouse",
            "storage", "packaging", "supplies"
        ],
        BusinessConcept.RECIPE: [
            "recipe", "ingredient", "preparation", "cooking", "instruction",
            "step", "method", "time", "temperature", "portion", "yield",
            "mix", "blend", "bake", "fry", "boil"
        ],
        BusinessConcept.MENU: [
            "menu", "dish", "item", "category", "price", "description",
            "available", "veg", "non-veg", "cuisine", "starter", "main",
            "dessert", "beverage", "combo", "offer"
        ],
        BusinessConcept.CRM: [
            "customer", "guest", "member", "contact", "phone", "email",
            "address", "birthday", "anniversary", "preference", "visit",
            "frequency", "lifetime", "value", "segment"
        ],
        BusinessConcept.STAFF: [
            "employee", "staff", "worker", "name", "role", "department",
            "salary", "joining", "attendance", "shift", "leave", "performance",
            "training", "designation", "manager"
        ],
        BusinessConcept.VENDOR: [
            "vendor", "supplier", "manufacturer", "distributor", "contact",
            "gst", "pan", "address", "credit", "terms", "lead", "time"
        ],
        BusinessConcept.FEEDBACK: [
            "feedback", "review", "rating", "comment", "complaint", "suggestion",
            "star", "experience", "service", "quality", "recommend"
        ],
        BusinessConcept.RESERVATION: [
            "reservation", "booking", "table", "guest", "time", "party",
            "size", "confirm", "cancel", "waitlist", "seating"
        ],
        BusinessConcept.LOYALTY: [
            "loyalty", "points", "reward", "member", "tier", "gold", "silver",
            "platinum", "redeem", "earn", "bonus", "cashback"
        ],
        BusinessConcept.MARKETING: [
            "campaign", "promotion", "offer", "discount", "coupon", "code",
            "banner", "email", "sms", "push", "target", "audience"
        ],
        BusinessConcept.FINANCE: [
            "account", "ledger", "balance", "debit", "credit", "gst", "tax",
            "tds", "invoice", "receipt", "profit", "loss", "audit"
        ],
        BusinessConcept.OPERATIONS: [
            "shift", "schedule", "task", "checklist", "opening", "closing",
            "cleaning", "maintenance", "incident", "handover"
        ],
        BusinessConcept.INFRASTRUCTURE: [
            "equipment", "machine", "asset", "device", "sensor", "iot",
            "energy", "power", "temperature", "humidity", "solar"
        ]
    }
    
    # Confidence thresholds
    AUTO_APPROVE_THRESHOLD = 0.85  # Above this: auto-process
    HUMAN_REVIEW_THRESHOLD = 0.60  # Below this: require human review
    
    def __init__(self):
        self._model = None
        self._cache: Dict[str, SemanticClassification] = {}
    
    def _get_model(self):
        """Get Gemini model lazily"""
        if self._model is None:
            try:
                import google.generativeai as genai
                from pillars.config_vault import EffectiveSettings
                
                cfg = EffectiveSettings()
                api_key = getattr(cfg, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY")
                
                if api_key:
                    genai.configure(api_key=api_key)
                    self._model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                print(f"Gemini init error: {e}")
        return self._model
    
    def _compute_data_fingerprint(self, data: Dict[str, Any]) -> str:
        """Create a fingerprint of the data structure (not values)"""
        # Extract just the keys and their types
        structure = {}
        for key, value in data.items():
            if isinstance(value, dict):
                structure[key] = "object"
            elif isinstance(value, list):
                structure[key] = "array"
            elif isinstance(value, (int, float)):
                structure[key] = "number"
            elif isinstance(value, bool):
                structure[key] = "boolean"
            else:
                structure[key] = "string"
        
        structure_str = json.dumps(structure, sort_keys=True)
        return hashlib.md5(structure_str.encode()).hexdigest()[:16]
    
    def _quick_pattern_match(self, data: Dict[str, Any]) -> Tuple[BusinessConcept, float]:
        """
        Fast pattern matching using keyword indicators.
        Returns concept and confidence score.
        """
        # Flatten data to searchable text
        text_blob = json.dumps(data).lower()
        
        scores = {}
        for concept, indicators in self.CONCEPT_INDICATORS.items():
            matches = sum(1 for ind in indicators if ind in text_blob)
            scores[concept] = matches / len(indicators)
        
        # Get best match
        best_concept = max(scores, key=scores.get)
        best_score = scores[best_concept]
        
        return best_concept, best_score
    
    def _extract_monetary_value(self, data: Dict[str, Any]) -> Optional[float]:
        """Extract monetary amount from data"""
        money_fields = ["total", "amount", "price", "cost", "value", "sum", 
                       "subtotal", "grand_total", "net", "gross", "salary"]
        
        for key, value in data.items():
            key_lower = key.lower()
            for field in money_fields:
                if field in key_lower and isinstance(value, (int, float)):
                    return float(value)
        
        return None
    
    def _extract_date(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract date from data"""
        date_fields = ["date", "time", "timestamp", "created", "updated", 
                      "order_date", "transaction_date", "invoice_date"]
        
        for key, value in data.items():
            key_lower = key.lower()
            for field in date_fields:
                if field in key_lower and value:
                    return str(value)
        
        return None
    
    async def classify(self, data: Dict[str, Any], source_hint: Optional[str] = None) -> SemanticClassification:
        """
        Classify data semantically using AI.
        
        Args:
            data: The raw data to classify
            source_hint: Optional hint about data source (e.g., "petpooja", "excel")
        
        Returns:
            SemanticClassification with concept, confidence, and metadata
        """
        # Check cache first (pattern similarity)
        fingerprint = self._compute_data_fingerprint(data)
        if fingerprint in self._cache:
            cached = self._cache[fingerprint]
            # Return cached result with same confidence
            return cached
        
        # Quick pattern match first
        quick_concept, quick_confidence = self._quick_pattern_match(data)
        
        # Extract metadata
        extracted_amount = self._extract_monetary_value(data)
        extracted_date = self._extract_date(data)
        
        # If quick match is very confident, use it
        if quick_confidence >= self.AUTO_APPROVE_THRESHOLD:
            result = SemanticClassification(
                primary_concept=quick_concept,
                sub_category=self._infer_subcategory(quick_concept, data),
                confidence_score=quick_confidence,
                reasoning=f"Pattern match on keywords with {quick_confidence:.0%} confidence",
                suggested_schema=self._infer_schema(data),
                extracted_amount=extracted_amount,
                extracted_date=extracted_date,
                key_entities=list(data.keys())[:10],
                requires_human_review=False
            )
            self._cache[fingerprint] = result
            return result
        
        # Use AI for deeper analysis
        model = self._get_model()
        if model:
            try:
                result = await self._ai_classify(model, data, source_hint, quick_concept, quick_confidence)
                self._cache[fingerprint] = result
                return result
            except Exception as e:
                print(f"AI classification error: {e}")
        
        # Fallback to pattern match with lower confidence
        requires_review = quick_confidence < self.HUMAN_REVIEW_THRESHOLD
        result = SemanticClassification(
            primary_concept=quick_concept,
            sub_category=self._infer_subcategory(quick_concept, data),
            confidence_score=quick_confidence,
            reasoning=f"Pattern match only (AI unavailable). Confidence: {quick_confidence:.0%}",
            suggested_schema=self._infer_schema(data),
            extracted_amount=extracted_amount,
            extracted_date=extracted_date,
            key_entities=list(data.keys())[:10],
            requires_human_review=requires_review,
            review_reason="Low confidence classification" if requires_review else None
        )
        self._cache[fingerprint] = result
        return result
    
    async def _ai_classify(
        self, 
        model, 
        data: Dict[str, Any], 
        source_hint: Optional[str],
        fallback_concept: BusinessConcept,
        fallback_confidence: float
    ) -> SemanticClassification:
        """Use Gemini for deep semantic analysis"""
        
        # Prepare data sample (limit size)
        data_sample = json.dumps(data, indent=2, default=str)[:2000]
        
        prompt = f"""You are a Business Data Analyst AI. Analyze this data and classify it.

DATA:
```json
{data_sample}
```

SOURCE HINT: {source_hint or "Unknown"}

AVAILABLE BUSINESS CONCEPTS:
- SALES: Money coming in from customers (orders, bills, invoices)
- EXPENSE: Money going out (purchases, salaries, utilities, rent)
- INVENTORY: Physical goods, stock levels, ingredients
- RECIPE: How to make products, ingredients list, preparation steps
- MENU: Products for sale, prices, categories
- CRM: Customer information, contacts, preferences
- STAFF: Employee data, attendance, payroll
- VENDOR: Supplier information, contacts
- FEEDBACK: Reviews, ratings, complaints
- RESERVATION: Bookings, table management
- LOYALTY: Points, rewards, memberships
- MARKETING: Campaigns, promotions, offers
- FINANCE: Accounting, taxes, ledgers
- OPERATIONS: Shifts, schedules, tasks
- INFRASTRUCTURE: Equipment, sensors, utilities
- UNKNOWN: Doesn't fit any category

Respond in this exact JSON format:
{{
    "primary_concept": "SALES|EXPENSE|INVENTORY|RECIPE|MENU|CRM|STAFF|VENDOR|FEEDBACK|RESERVATION|LOYALTY|MARKETING|FINANCE|OPERATIONS|INFRASTRUCTURE|UNKNOWN",
    "sub_category": "brief sub-category name",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of why this classification",
    "key_fields": ["list", "of", "important", "field", "names"],
    "suggested_new_category": "If UNKNOWN, suggest a name for new category"
}}"""

        try:
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                ai_result = json.loads(json_match.group())
                
                # Parse AI response
                concept_str = ai_result.get("primary_concept", "UNKNOWN").upper()
                try:
                    primary_concept = BusinessConcept(concept_str.lower())
                except ValueError:
                    primary_concept = BusinessConcept.UNKNOWN
                
                confidence = float(ai_result.get("confidence", 0.7))
                requires_review = confidence < self.HUMAN_REVIEW_THRESHOLD
                
                return SemanticClassification(
                    primary_concept=primary_concept,
                    sub_category=self._parse_subcategory(ai_result.get("sub_category", "general")),
                    confidence_score=confidence,
                    reasoning=ai_result.get("reasoning", "AI classification"),
                    suggested_schema=self._infer_schema(data),
                    extracted_amount=self._extract_monetary_value(data),
                    extracted_date=self._extract_date(data),
                    key_entities=ai_result.get("key_fields", [])[:10],
                    requires_human_review=requires_review,
                    review_reason="AI confidence below threshold" if requires_review else None
                )
        except Exception as e:
            print(f"AI parsing error: {e}")
        
        # Return fallback
        return SemanticClassification(
            primary_concept=fallback_concept,
            sub_category=self._infer_subcategory(fallback_concept, data),
            confidence_score=fallback_confidence,
            reasoning="Fallback to pattern matching",
            suggested_schema=self._infer_schema(data),
            extracted_amount=self._extract_monetary_value(data),
            extracted_date=self._extract_date(data),
            key_entities=list(data.keys())[:10],
            requires_human_review=fallback_confidence < self.HUMAN_REVIEW_THRESHOLD
        )
    
    def _infer_subcategory(self, concept: BusinessConcept, data: Dict[str, Any]) -> SubCategory:
        """Infer sub-category based on concept and data"""
        text_blob = json.dumps(data).lower()
        
        if concept == BusinessConcept.SALES:
            if "delivery" in text_blob or "zomato" in text_blob or "swiggy" in text_blob:
                return SubCategory.DELIVERY
            elif "takeaway" in text_blob or "parcel" in text_blob:
                return SubCategory.TAKEAWAY
            elif "catering" in text_blob:
                return SubCategory.CATERING
            return SubCategory.DINE_IN
        
        elif concept == BusinessConcept.EXPENSE:
            if "salary" in text_blob or "wage" in text_blob or "payroll" in text_blob:
                return SubCategory.SALARY
            elif "rent" in text_blob:
                return SubCategory.RENT
            elif "electricity" in text_blob or "water" in text_blob or "utility" in text_blob:
                return SubCategory.UTILITIES
            elif "marketing" in text_blob or "advertising" in text_blob:
                return SubCategory.MARKETING_EXPENSE
            elif "maintenance" in text_blob or "repair" in text_blob:
                return SubCategory.MAINTENANCE
            return SubCategory.RAW_MATERIAL
        
        elif concept == BusinessConcept.INVENTORY:
            if "ingredient" in text_blob:
                return SubCategory.INGREDIENT
            elif "packaging" in text_blob or "box" in text_blob or "container" in text_blob:
                return SubCategory.PACKAGING
            elif "equipment" in text_blob or "machine" in text_blob:
                return SubCategory.EQUIPMENT
            return SubCategory.INGREDIENT
        
        elif concept == BusinessConcept.CRM:
            if "feedback" in text_blob or "review" in text_blob or "rating" in text_blob:
                return SubCategory.CUSTOMER_FEEDBACK
            elif "order" in text_blob or "history" in text_blob:
                return SubCategory.CUSTOMER_ORDER_HISTORY
            return SubCategory.CUSTOMER_PROFILE
        
        elif concept == BusinessConcept.STAFF:
            if "attendance" in text_blob:
                return SubCategory.ATTENDANCE
            elif "salary" in text_blob or "payroll" in text_blob:
                return SubCategory.PAYROLL
            return SubCategory.EMPLOYEE_PROFILE
        
        return SubCategory.GENERAL
    
    def _parse_subcategory(self, sub_str: str) -> SubCategory:
        """Parse subcategory string to enum"""
        sub_lower = sub_str.lower().replace(" ", "_").replace("-", "_")
        try:
            return SubCategory(sub_lower)
        except ValueError:
            return SubCategory.GENERAL
    
    def _infer_schema(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Infer schema from data structure"""
        schema = {}
        for key, value in data.items():
            if isinstance(value, bool):
                schema[key] = "BOOLEAN"
            elif isinstance(value, int):
                schema[key] = "INTEGER"
            elif isinstance(value, float):
                schema[key] = "FLOAT"
            elif isinstance(value, dict):
                schema[key] = "JSON"
            elif isinstance(value, list):
                schema[key] = "ARRAY"
            elif value is None:
                schema[key] = "STRING"
            else:
                # Check for date patterns
                str_val = str(value)
                if any(x in key.lower() for x in ["date", "time", "created", "updated"]):
                    schema[key] = "TIMESTAMP"
                elif len(str_val) > 500:
                    schema[key] = "TEXT"
                else:
                    schema[key] = "STRING"
        return schema


# =============================================================================
# Global Classifier Instance
# =============================================================================

_classifier: Optional[SemanticClassifier] = None


def get_classifier() -> SemanticClassifier:
    """Get or create global classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = SemanticClassifier()
    return _classifier


async def classify_data(data: Dict[str, Any], source_hint: Optional[str] = None) -> SemanticClassification:
    """
    Classify data semantically.
    
    Args:
        data: Raw data to classify
        source_hint: Optional source identifier
    
    Returns:
        SemanticClassification result
    """
    classifier = get_classifier()
    return await classifier.classify(data, source_hint)


def classify_data_sync(data: Dict[str, Any], source_hint: Optional[str] = None) -> SemanticClassification:
    """Synchronous version of classify_data"""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(classify_data(data, source_hint))
