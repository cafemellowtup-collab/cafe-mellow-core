"""
Learned Strategies Engine
AI learns user-specific business rules without code changes
Example: "Overtime = 1.5x base rate after 8 hours"
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class StrategyType(str, Enum):
    """Strategy Types"""
    OVERTIME_RULE = "overtime_rule"
    DISCOUNT_POLICY = "discount_policy"
    PRICING_RULE = "pricing_rule"
    INVENTORY_THRESHOLD = "inventory_threshold"
    EXPENSE_APPROVAL = "expense_approval"
    CUSTOM = "custom"


class Strategy(BaseModel):
    """Learned Strategy Model"""
    id: str
    org_id: str
    location_id: Optional[str] = None
    
    type: StrategyType
    name: str
    description: str
    
    rule_json: Dict[str, Any] = Field(description="JSON representation of the rule")
    
    confidence_score: float = Field(ge=0, le=1, description="AI confidence in this rule")
    
    learned_from: str = Field(description="Source: 'user_input', 'pattern_detection', etc.")
    
    is_active: bool = True
    requires_approval: bool = True
    approved_by: Optional[str] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LearnedStrategiesEngine:
    """
    Learned Strategies Engine
    Allows AI to learn business rules from user interactions
    """
    
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
        self.table_name = "learned_strategies"
    
    def add_strategy(self, strategy: Strategy) -> bool:
        """Add a new learned strategy"""
        try:
            table_id = f"{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.{self.table_name}"
            rows = [strategy.dict()]
            errors = self.client.insert_rows_json(table_id, rows)
            return not errors
        except Exception:
            return False
    
    def get_strategies(
        self, 
        org_id: str, 
        location_id: Optional[str] = None, 
        type: Optional[StrategyType] = None,
        is_active: bool = True
    ) -> List[Strategy]:
        """Get strategies for a tenant"""
        try:
            where_conditions = [f"org_id = '{org_id}'", f"is_active = {is_active}"]
            
            if location_id:
                where_conditions.append(f"location_id = '{location_id}'")
            
            if type:
                where_conditions.append(f"type = '{type.value}'")
            
            where_clause = " AND ".join(where_conditions)
            
            sql = f"""
            SELECT *
            FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.{self.table_name}`
            WHERE {where_clause}
            ORDER BY created_at DESC
            """
            
            result = self.client.query(sql).result()
            
            strategies = []
            for row in result:
                strategies.append(Strategy(**dict(row)))
            
            return strategies
        except Exception:
            return []
    
    def apply_overtime_rule(self, hours_worked: float, base_rate: float, org_id: str, location_id: str) -> float:
        """
        Apply learned overtime rule
        If no learned rule exists, use default (1.5x after 8 hours)
        """
        strategies = self.get_strategies(org_id, location_id, StrategyType.OVERTIME_RULE)
        
        if strategies and strategies[0].is_active:
            rule = strategies[0].rule_json
            threshold = rule.get("threshold_hours", 8)
            multiplier = rule.get("overtime_multiplier", 1.5)
        else:
            threshold = 8
            multiplier = 1.5
        
        if hours_worked <= threshold:
            return hours_worked * base_rate
        else:
            regular_pay = threshold * base_rate
            overtime_hours = hours_worked - threshold
            overtime_pay = overtime_hours * base_rate * multiplier
            return regular_pay + overtime_pay
    
    def learn_from_user_input(self, user_message: str, org_id: str, location_id: str) -> Optional[Strategy]:
        """
        Extract strategy from user input using AI
        Example: "We pay 2x for overtime after 9 hours"
        """
        import uuid
        import re
        
        overtime_pattern = r"(?:overtime|ot)\s+(?:is\s+)?(\d+(?:\.\d+)?)[x×]\s+(?:after|beyond)\s+(\d+)\s+hours"
        match = re.search(overtime_pattern, user_message.lower())
        
        if match:
            multiplier = float(match.group(1))
            threshold = int(match.group(2))
            
            strategy = Strategy(
                id=str(uuid.uuid4()),
                org_id=org_id,
                location_id=location_id,
                type=StrategyType.OVERTIME_RULE,
                name=f"Overtime Rule: {multiplier}x after {threshold}h",
                description=f"Learned from user: {user_message}",
                rule_json={
                    "threshold_hours": threshold,
                    "overtime_multiplier": multiplier
                },
                confidence_score=0.85,
                learned_from="user_input",
                requires_approval=True
            )
            
            return strategy
        
        return None
