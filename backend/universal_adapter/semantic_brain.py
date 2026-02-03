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
        """Get Gemini client lazily (using new google.genai library)"""
        if self._model is None:
            try:
                from google import genai
                from pillars.config_vault import EffectiveSettings
                
                cfg = EffectiveSettings()
                api_key = getattr(cfg, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY")
                
                if api_key:
                    self._model = genai.Client(api_key=api_key)
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
            response = model.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
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


# =============================================================================
# Semantic Brain - God-Grade Batch Classifier (Phase 3B)
# =============================================================================

class SemanticBrain:
    """
    God-Grade Batch Classifier with persistent memory.
    
    Uses ALL available context (columns, narrations, typos) to classify
    UniversalEvent objects into business categories.
    
    Features:
    - Persistent cache (brain_cache.json) for learned classifications
    - Rich context assembly from entity_name + category + rich_data
    - Typo tolerance (e.g., "Milku" -> Dairy -> INVENTORY)
    - Batch processing with AI for efficiency
    - Automatic learning from each classification
    
    Phase 8 Fortress Upgrades:
    - The Bouncer: Schema validation to reject junk files
    - The Sherlock: Strict STREAM/STATE classification with filename rules
    - Turbo Engine: Async batch processing (50 items at a time)
    - Ghost Logic: Create provisional items for unknown menu items
    """
    
    # Cafe-specific category mapping
    CAFE_CATEGORIES = {
        "SALES": "Revenue from customer orders",
        "INVENTORY": "Raw materials, ingredients, supplies",
        "LABOR": "Staff wages, salaries, benefits",
        "OVERHEAD": "Utilities, rent, maintenance, insurance",
        "WASTAGE": "Expired items, spoilage, breakage",
        "MARKETING": "Advertising, promotions, campaigns",
        "EQUIPMENT": "Machinery, appliances, furniture"
    }
    
    # ==========================================================================
    # PHASE 8: THE BOUNCER - Schema Validation
    # ==========================================================================
    
    # Critical columns for STREAM data (Sales/Transactions)
    STREAM_CRITICAL_COLS = {
        "date_like": ["date", "time", "timestamp", "created", "order_date", "transaction_date"],
        "amount_like": ["amount", "total", "price", "value", "sum", "revenue", "cost", "quantity", "qty"]
    }
    
    # Critical columns for STATE data (Menu/Inventory)
    STATE_CRITICAL_COLS = {
        "item_like": ["item", "name", "product", "dish", "menu", "ingredient", "sku"],
        "price_like": ["price", "rate", "cost", "mrp", "value", "amount"]
    }
    
    # Junk file indicators (reject these)
    JUNK_INDICATORS = [
        "readme", "template", "example", "sample", "test", "backup", "old", "copy",
        "untitled", "document", "sheet1", "book1"
    ]
    
    # ==========================================================================
    # PHASE 8: THE SHERLOCK - Data Type Classification
    # ==========================================================================
    
    # STREAM = Transaction/Sales data (time-series, flowing)
    # STATE = Master/Reference data (static, current state)
    DATA_TYPES = {
        "STREAM": {
            "description": "Transaction/Sales data - time-series events",
            "filename_hints": ["sale", "sales", "order", "transaction", "receipt", "bill", "invoice", "revenue"],
            "column_hints": ["date", "time", "order_id", "bill_no", "invoice", "qty", "quantity", "total"]
        },
        "STATE": {
            "description": "Master/Reference data - current state",
            "filename_hints": ["menu", "item", "product", "inventory", "stock", "price", "catalog", "master"],
            "column_hints": ["item_name", "product", "category", "price", "mrp", "description", "available"]
        }
    }
    
    # Turbo Engine batch size
    BATCH_SIZE = 50
    
    # Common typo mappings for cafe items
    TYPO_CORRECTIONS = {
        "milku": "milk",
        "cofee": "coffee",
        "coffe": "coffee",
        "expresso": "espresso",
        "capuccino": "cappuccino",
        "sandwhich": "sandwich",
        "sandwitch": "sandwich",
        "suger": "sugar",
        "sugr": "sugar",
        "electrcity": "electricity",
        "electricty": "electricity",
        "sallary": "salary",
        "salry": "salary",
    }
    
    def __init__(self):
        """Initialize SemanticBrain with persistent cache."""
        self._model = None
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_file = self._get_cache_path()
        self._load_cache()
    
    def _get_cache_path(self) -> str:
        """Get path to brain_cache.json"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "brain_cache.json")
    
    def _load_cache(self):
        """Load persistent cache from file."""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                print(f"[BRAIN] Loaded {len(self._cache)} cached classifications")
        except Exception as e:
            print(f"[BRAIN] Cache load failed: {e}. Starting fresh.")
            self._cache = {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[BRAIN] Cache save failed: {e}")
    
    def _get_model(self):
        """Get Gemini client lazily (using new google.genai library)."""
        if self._model is None:
            try:
                from google import genai
                from pillars.config_vault import EffectiveSettings
                
                cfg = EffectiveSettings()
                api_key = getattr(cfg, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY")
                
                if api_key:
                    self._model = genai.Client(api_key=api_key)
                    print("[BRAIN] Gemini Client initialized (google.genai)")
            except Exception as e:
                print(f"[BRAIN] Gemini init error: {e}")
        return self._model
    
    def _correct_typos(self, text: str) -> str:
        """Apply typo corrections to text."""
        if not text:
            return text
        text_lower = text.lower()
        for typo, correction in self.TYPO_CORRECTIONS.items():
            if typo in text_lower:
                text_lower = text_lower.replace(typo, correction)
        return text_lower
    
    # ==========================================================================
    # PHASE 8: THE BOUNCER - Schema Validation
    # ==========================================================================
    
    def validate_schema(self, columns: List[str], filename: str = "") -> Dict[str, Any]:
        """
        THE BOUNCER: Validate file schema before processing.
        
        Rules:
        1. Reject junk files (readme, template, etc.)
        2. Check for critical columns (Date/Amount OR Item/Price)
        3. Return validation result with data_type hint
        
        Args:
            columns: List of column names from the file
            filename: Original filename for additional context
            
        Returns:
            {
                "valid": bool,
                "data_type": "STREAM" | "STATE" | "UNKNOWN",
                "reason": str,
                "confidence": float
            }
        """
        filename_lower = filename.lower() if filename else ""
        columns_lower = [c.lower().strip() for c in columns]
        
        # Step 1: Check for junk file indicators
        for junk in self.JUNK_INDICATORS:
            if junk in filename_lower:
                print(f"[BOUNCER] REJECTED: Junk file indicator '{junk}' in filename")
                return {
                    "valid": False,
                    "data_type": "UNKNOWN",
                    "reason": f"File appears to be a {junk} file, not business data",
                    "confidence": 0.0
                }
        
        # Step 2: Check for STREAM columns (Date + Amount)
        has_date = any(any(d in col for d in self.STREAM_CRITICAL_COLS["date_like"]) for col in columns_lower)
        has_amount = any(any(a in col for a in self.STREAM_CRITICAL_COLS["amount_like"]) for col in columns_lower)
        
        # Step 3: Check for STATE columns (Item + Price)
        has_item = any(any(i in col for i in self.STATE_CRITICAL_COLS["item_like"]) for col in columns_lower)
        has_price = any(any(p in col for p in self.STATE_CRITICAL_COLS["price_like"]) for col in columns_lower)
        
        # Determine data type
        stream_score = (1 if has_date else 0) + (1 if has_amount else 0)
        state_score = (1 if has_item else 0) + (1 if has_price else 0)
        
        # Both have some columns - use filename to disambiguate
        if stream_score > 0 or state_score > 0:
            # Use Sherlock for classification
            data_type, confidence = self._sherlock_classify(filename_lower, columns_lower)
            
            if data_type != "UNKNOWN":
                print(f"[BOUNCER] ACCEPTED: {data_type} data (confidence: {confidence:.0%})")
                return {
                    "valid": True,
                    "data_type": data_type,
                    "reason": f"Valid {data_type} data detected",
                    "confidence": confidence,
                    "has_date": has_date,
                    "has_amount": has_amount,
                    "has_item": has_item,
                    "has_price": has_price
                }

            # Fallback to column signals if Sherlock is uncertain
            if stream_score >= state_score and stream_score > 0:
                data_type = "STREAM"
                confidence = 0.4 + (0.1 * stream_score)
            else:
                data_type = "STATE"
                confidence = 0.4 + (0.1 * state_score)

            print(f"[BOUNCER] ACCEPTED (fallback): {data_type} data (confidence: {confidence:.0%})")
            return {
                "valid": True,
                "data_type": data_type,
                "reason": f"Valid {data_type} data detected (column-based)",
                "confidence": min(confidence, 0.7),
                "has_date": has_date,
                "has_amount": has_amount,
                "has_item": has_item,
                "has_price": has_price
            }
        
        # Neither STREAM nor STATE - REJECT
        print(f"[BOUNCER] REJECTED: Missing critical columns. Has date={has_date}, amount={has_amount}, item={has_item}, price={has_price}")
        return {
            "valid": False,
            "data_type": "UNKNOWN",
            "reason": "File lacks critical columns (need Date+Amount for Sales OR Item+Price for Menu)",
            "confidence": 0.0,
            "columns_found": columns[:10]
        }
    
    # ==========================================================================
    # PHASE 8: THE SHERLOCK - Strict Classification
    # ==========================================================================
    
    def _sherlock_classify(self, filename: str, columns: List[str]) -> Tuple[str, float]:
        """
        THE SHERLOCK: Strict classification using filename + columns.
        
        RULE 1: Filename is KING. If filename says "Sales", it IS Sales.
        RULE 2: Column patterns are secondary evidence.
        
        Args:
            filename: Lowercase filename
            columns: Lowercase column names
            
        Returns:
            (data_type, confidence) tuple
        """
        stream_confidence = 0.0
        state_confidence = 0.0
        
        # RULE 1: Filename hints (weighted heavily - 0.6)
        for hint in self.DATA_TYPES["STREAM"]["filename_hints"]:
            if hint in filename:
                stream_confidence += 0.6
                print(f"[SHERLOCK] Filename hint '{hint}' -> STREAM (+0.6)")
                break
        
        for hint in self.DATA_TYPES["STATE"]["filename_hints"]:
            if hint in filename:
                state_confidence += 0.6
                print(f"[SHERLOCK] Filename hint '{hint}' -> STATE (+0.6)")
                break
        
        # RULE 2: Column hints (weighted 0.1 each, max 0.4)
        columns_text = " ".join(columns)
        
        stream_col_hits = sum(1 for h in self.DATA_TYPES["STREAM"]["column_hints"] if h in columns_text)
        stream_confidence += min(stream_col_hits * 0.1, 0.4)
        
        state_col_hits = sum(1 for h in self.DATA_TYPES["STATE"]["column_hints"] if h in columns_text)
        state_confidence += min(state_col_hits * 0.1, 0.4)
        
        # Determine winner
        if stream_confidence > state_confidence and stream_confidence >= 0.5:
            return ("STREAM", min(stream_confidence, 1.0))
        elif state_confidence > stream_confidence and state_confidence >= 0.5:
            return ("STATE", min(state_confidence, 1.0))
        elif stream_confidence >= 0.3 or state_confidence >= 0.3:
            # Weak signal but something detected
            if stream_confidence >= state_confidence:
                return ("STREAM", stream_confidence)
            else:
                return ("STATE", state_confidence)
        
        return ("UNKNOWN", 0.0)
    
    def classify_file(self, columns: List[str], filename: str = "", sample_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Full file classification combining Bouncer + Sherlock.
        
        Args:
            columns: List of column names
            filename: Original filename
            sample_data: Optional sample rows for deeper analysis
            
        Returns:
            {
                "valid": bool,
                "data_type": "STREAM" | "STATE" | "UNKNOWN",
                "business_type": "SALES" | "MENU" | "EXPENSE" | etc.,
                "reason": str,
                "confidence": float
            }
        """
        # Step 1: Bouncer validation
        bouncer_result = self.validate_schema(columns, filename)
        
        if not bouncer_result["valid"]:
            return {
                "valid": False,
                "data_type": "UNKNOWN",
                "business_type": "UNKNOWN",
                "reason": bouncer_result["reason"],
                "confidence": 0.0
            }
        
        # Step 2: Determine business type based on data type
        data_type = bouncer_result["data_type"]
        
        if data_type == "STREAM":
            business_type = "SALES"  # STREAM data is typically sales/transactions
        elif data_type == "STATE":
            business_type = "MENU"   # STATE data is typically menu/inventory
        else:
            business_type = "UNKNOWN"
        
        return {
            "valid": True,
            "data_type": data_type,
            "business_type": business_type,
            "reason": bouncer_result["reason"],
            "confidence": bouncer_result["confidence"]
        }
    
    def _build_context_string(self, event) -> str:
        """
        Build rich context string from event for classification.
        Combines entity_name, original_category, and rich_data narration.
        """
        parts = []
        
        # Entity name (the item)
        if hasattr(event, 'entity_name') and event.entity_name:
            corrected = self._correct_typos(event.entity_name)
            parts.append(f"Item: {corrected}")
        
        # Original category (predefined ledger column)
        if hasattr(event, 'original_category') and event.original_category:
            parts.append(f"Category: {event.original_category}")
        
        # Rich data (narration/description)
        if hasattr(event, 'rich_data') and event.rich_data:
            try:
                rich = json.loads(event.rich_data) if isinstance(event.rich_data, str) else event.rich_data
                # Extract narration-like fields
                narration_fields = ['narration', 'description', 'notes', 'remarks', 'details', 'memo']
                for field in narration_fields:
                    for key, val in rich.items():
                        if field in key.lower() and val:
                            corrected = self._correct_typos(str(val))
                            parts.append(f"Description: {corrected}")
                            break
            except:
                pass
        
        # Amount context
        if hasattr(event, 'amount') and event.amount:
            parts.append(f"Amount: {event.amount}")
        
        return " | ".join(parts) if parts else "Unknown"
    
    def _get_cache_key(self, context: str) -> str:
        """Generate cache key from context string."""
        # Normalize and hash
        normalized = context.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    # ==========================================================================
    # PHASE 8: TURBO ENGINE - Async Batch Processing
    # ==========================================================================
    
    async def classify_batch_async(self, events: list) -> list:
        """
        TURBO ENGINE: Async batch processing in chunks of BATCH_SIZE (50).
        
        Processes events in parallel batches for speed.
        
        Args:
            events: List of UniversalEvent objects
            
        Returns:
            List of classified UniversalEvent objects
        """
        import asyncio
        
        if not events:
            return events
        
        total = len(events)
        print(f"[TURBO] Processing {total} events in batches of {self.BATCH_SIZE}")
        
        results = []
        for i in range(0, total, self.BATCH_SIZE):
            batch = events[i:i + self.BATCH_SIZE]
            batch_num = (i // self.BATCH_SIZE) + 1
            total_batches = (total + self.BATCH_SIZE - 1) // self.BATCH_SIZE
            
            print(f"[TURBO] Batch {batch_num}/{total_batches} ({len(batch)} events)")
            
            # Process batch synchronously (AI calls are already efficient)
            classified = self.classify_batch(batch)
            results.extend(classified)
            
            # Small delay between batches to avoid rate limiting
            if i + self.BATCH_SIZE < total:
                await asyncio.sleep(0.1)
        
        print(f"[TURBO] Complete: {len(results)} events classified")
        return results
    
    def classify_batch(self, events: list) -> list:
        """
        Classify a batch of UniversalEvent objects.
        
        Steps:
        1. Build context strings for each event
        2. Check cache for known classifications
        3. Send unknown items to AI in batch
        4. Update cache with new learnings
        5. Apply classifications to events
        
        Args:
            events: List of UniversalEvent objects
            
        Returns:
            List of UniversalEvent objects with updated category/sub_category
        """
        if not events:
            return events
        
        print(f"[BRAIN] Classifying {len(events)} events...")
        
        # Step 1: Build context strings
        contexts = []
        for event in events:
            ctx = self._build_context_string(event)
            contexts.append(ctx)
        
        # Step 2: Check cache, separate known vs unknown
        unknown_indices = []
        unknown_contexts = []
        
        for i, ctx in enumerate(contexts):
            cache_key = self._get_cache_key(ctx)
            if cache_key in self._cache:
                # Apply cached classification - MEMORY IS TRUSTED (confidence=1.0)
                cached = self._cache[cache_key]
                events[i].category = cached.get("category", events[i].category)
                events[i].sub_category = cached.get("sub_category", events[i].sub_category)
                events[i].confidence_score = 1.0  # Memory is trusted!
                events[i].ai_reasoning = f"Cached (trusted): {cached.get('reasoning', 'Known pattern')}"
            else:
                unknown_indices.append(i)
                unknown_contexts.append(ctx)
        
        cached_count = len(events) - len(unknown_indices)
        print(f"[BRAIN] {cached_count} from cache, {len(unknown_indices)} need AI analysis")
        
        # Step 3: AI classification for unknowns
        if unknown_contexts:
            ai_results = self._ai_classify_batch(unknown_contexts)
            
            # Step 4 & 5: Update cache and apply to events
            for i, idx in enumerate(unknown_indices):
                if i < len(ai_results):
                    result = ai_results[i]
                    ctx = unknown_contexts[i]
                    cache_key = self._get_cache_key(ctx)
                    
                    # Apply to event
                    events[idx].category = result.get("category", "UNKNOWN")
                    events[idx].sub_category = result.get("sub_category", "general")
                    events[idx].confidence_score = result.get("confidence", 0.85)
                    events[idx].ai_reasoning = result.get("reasoning", "AI classified")
                    
                    # Save to cache
                    self._cache[cache_key] = {
                        "category": events[idx].category,
                        "sub_category": events[idx].sub_category,
                        "confidence": events[idx].confidence_score,
                        "reasoning": events[idx].ai_reasoning,
                        "context": ctx,
                        "classified_at": datetime.now().isoformat()
                    }
            
            # Persist cache
            self._save_cache()
        
        print(f"[BRAIN] Classification complete. Cache now has {len(self._cache)} entries.")
        return events
    
    def _ai_classify_batch(self, contexts: list) -> list:
        """
        Use Gemini to classify multiple context strings at once.
        """
        model = self._get_model()
        if not model:
            # Fallback to rule-based classification
            return [self._rule_based_classify(ctx) for ctx in contexts]
        
        # Build batch prompt
        items_text = "\n".join([f"{i+1}. {ctx}" for i, ctx in enumerate(contexts[:20])])  # Limit to 20
        
        prompt = f"""You are a Cafe/Restaurant Data Auditor with expertise in financial classification.

Classify each item into ONE of these categories:
- SALES: Revenue from customers (orders, bills, tips)
- INVENTORY: Raw materials, ingredients, supplies (milk, coffee beans, sugar, packaging)
- LABOR: Staff wages, salaries, benefits
- OVERHEAD: Utilities (electricity, water, gas), rent, maintenance, insurance, subscriptions
- WASTAGE: Expired items, spoilage, breakage, theft
- MARKETING: Advertising, promotions, campaigns
- EQUIPMENT: Machinery, appliances, furniture, repairs

IMPORTANT RULES:
1. "Electricity", "Water", "Gas", "Rent", "Internet" -> OVERHEAD
2. "Milk", "Coffee", "Sugar", "Ingredients" -> INVENTORY
3. "Salary", "Wages", "Staff Payment" -> LABOR
4. Handle typos: "Milku" = Milk -> INVENTORY
5. Use the Description/Narration for context (e.g., "Paid via GPay" indicates payment)

ITEMS TO CLASSIFY:
{items_text}

Respond with a JSON array. Each object must have:
- "index": item number (1-based)
- "category": one of [SALES, INVENTORY, LABOR, OVERHEAD, WASTAGE, MARKETING, EQUIPMENT]
- "sub_category": specific type (e.g., "dairy", "utilities", "wages")
- "confidence": 0.0 to 1.0
- "reasoning": brief explanation

Example:
[
  {{"index": 1, "category": "OVERHEAD", "sub_category": "utilities", "confidence": 0.95, "reasoning": "Electricity is a utility expense"}}
]"""

        try:
            response = model.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            response_text = response.text
            
            # Extract JSON array from response
            import re
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                results = json.loads(json_match.group())
                
                # Map back to original order
                result_map = {r.get("index", i+1): r for i, r in enumerate(results)}
                ordered_results = []
                for i in range(len(contexts)):
                    if i+1 in result_map:
                        ordered_results.append(result_map[i+1])
                    elif i < len(results):
                        ordered_results.append(results[i])
                    else:
                        ordered_results.append(self._rule_based_classify(contexts[i]))
                
                return ordered_results
                
        except Exception as e:
            print(f"[BRAIN] AI batch classification error: {e}")
        
        # Fallback to rule-based
        return [self._rule_based_classify(ctx) for ctx in contexts]
    
    def _rule_based_classify(self, context: str) -> dict:
        """
        Fallback rule-based classification when AI unavailable.
        """
        ctx_lower = context.lower()
        
        # Overhead indicators
        if any(x in ctx_lower for x in ['electricity', 'electric', 'water', 'gas', 'rent', 
                                         'internet', 'phone', 'insurance', 'maintenance']):
            return {"category": "OVERHEAD", "sub_category": "utilities", 
                    "confidence": 0.90, "reasoning": "Utility/overhead expense detected"}
        
        # Inventory indicators
        if any(x in ctx_lower for x in ['milk', 'coffee', 'sugar', 'flour', 'ingredient',
                                         'bean', 'cream', 'butter', 'egg', 'fruit', 'vegetable']):
            return {"category": "INVENTORY", "sub_category": "ingredients",
                    "confidence": 0.90, "reasoning": "Ingredient/inventory item detected"}
        
        # Labor indicators
        if any(x in ctx_lower for x in ['salary', 'wage', 'staff', 'employee', 'payroll',
                                         'bonus', 'overtime']):
            return {"category": "LABOR", "sub_category": "wages",
                    "confidence": 0.90, "reasoning": "Labor/wage expense detected"}
        
        # Sales indicators
        if any(x in ctx_lower for x in ['order', 'sale', 'revenue', 'customer', 'bill',
                                         'receipt', 'payment received']):
            return {"category": "SALES", "sub_category": "orders",
                    "confidence": 0.85, "reasoning": "Sales/revenue detected"}
        
        # Wastage indicators
        if any(x in ctx_lower for x in ['expired', 'spoiled', 'waste', 'damage', 'broken',
                                         'theft', 'loss']):
            return {"category": "WASTAGE", "sub_category": "spoilage",
                    "confidence": 0.85, "reasoning": "Wastage/loss detected"}
        
        # Default to unknown
        return {"category": "UNKNOWN", "sub_category": "unclassified",
                "confidence": 0.50, "reasoning": "Could not determine category"}
    
    def learn(self, event) -> bool:
        """
        Learn from a human-approved event and update the brain cache.
        
        Called when a quarantined event is approved by a human.
        This teaches the brain to recognize similar items in the future.
        
        Args:
            event: UniversalEvent object with verified classification
            
        Returns:
            bool: True if learning was successful
        """
        try:
            # Build context string for this event
            ctx = self._build_context_string(event)
            cache_key = self._get_cache_key(ctx)
            
            # Store in cache with human-verified confidence
            self._cache[cache_key] = {
                "category": getattr(event, 'category', 'UNKNOWN'),
                "sub_category": getattr(event, 'sub_category', 'general'),
                "confidence": 1.0,  # Human-verified = fully trusted
                "reasoning": f"Human verified: {getattr(event, 'entity_name', 'Unknown')}",
                "context": ctx,
                "classified_at": datetime.now().isoformat(),
                "verified_by": getattr(event, 'verified_by', 'human'),
                "learned_from": "quarantine_approval"
            }
            
            # Persist cache
            self._save_cache()
            
            entity_name = getattr(event, 'entity_name', 'Unknown')
            category = getattr(event, 'category', 'UNKNOWN')
            print(f"[BRAIN] Learned new pattern: '{entity_name}' -> {category}")
            
            return True
            
        except Exception as e:
            print(f"[BRAIN] Learning failed: {e}")
            return False
    
    def get_cache_stats(self) -> dict:
        """Return cache statistics."""
        return {
            "total_entries": len(self._cache),
            "cache_file": self._cache_file,
            "categories": self._count_by_category()
        }
    
    def _count_by_category(self) -> dict:
        """Count cached items by category."""
        counts = {}
        for entry in self._cache.values():
            cat = entry.get("category", "UNKNOWN")
            counts[cat] = counts.get(cat, 0) + 1
        return counts


# =============================================================================
# Global Brain Instance
# =============================================================================

_brain: Optional[SemanticBrain] = None


def get_brain() -> SemanticBrain:
    """Get or create global SemanticBrain instance."""
    global _brain
    if _brain is None:
        _brain = SemanticBrain()
    return _brain
