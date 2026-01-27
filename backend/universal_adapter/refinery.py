"""
AI Refinery - The Intelligent Data Transformer
===============================================
Phase 3 of the Universal Adapter.

CORE PRINCIPLE: Transform ANY data into Golden Schema format using AI.

Process:
1. Fetch pending raw_logs entries
2. Check if we have a cached mapping for this source
3. If yes: Apply mapping (fast path)
4. If no: Use AI to generate mapping (slow path, but learns)
5. Validate against Golden Schema
6. Pass → Main DB | Fail → Quarantine

The AI learns from:
- Successful transformations (cached mappings)
- Human corrections (quarantine fixes)
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from .golden_schema import (
    GoldenOrder, GoldenExpense, GoldenPurchase,
    GoldenOrderItem, GoldenPayment, GoldenDiscount,
    validate_order, validate_expense, validate_purchase,
    get_schema_json, DataSource
)


class TransformResult(Enum):
    SUCCESS = "success"
    VALIDATION_FAILED = "validation_failed"
    AI_ERROR = "ai_error"
    NO_MAPPING = "no_mapping"


# =============================================================================
# BigQuery Client
# =============================================================================

def _get_bq_client():
    """Get BigQuery client with ADC fallback"""
    try:
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings
        
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        if os.path.exists(key_path):
            return bigquery.Client.from_service_account_json(key_path), cfg
        
        project_id = getattr(cfg, "PROJECT_ID", None) or os.environ.get("PROJECT_ID")
        return bigquery.Client(project=project_id) if project_id else bigquery.Client(), cfg
    except Exception as e:
        print(f"BigQuery client error: {e}")
        return None, None


# =============================================================================
# Mapping Cache
# =============================================================================

def _get_cached_mapping(client, cfg, source_identifier: str, target_schema: str) -> Optional[Dict[str, Any]]:
    """Check if we have a cached mapping for this source"""
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        table_id = f"{project_id}.{dataset_id}.schema_mappings"
        
        query = f"""
        SELECT mapping_id, field_mappings, transform_rules, confidence
        FROM `{table_id}`
        WHERE source_identifier = '{source_identifier}'
          AND target_schema = '{target_schema}'
          AND confidence >= 0.8
        ORDER BY use_count DESC, last_used_at DESC
        LIMIT 1
        """
        result = list(client.query(query).result())
        
        if result:
            row = result[0]
            # Update usage stats
            update_sql = f"""
            UPDATE `{table_id}`
            SET last_used_at = CURRENT_TIMESTAMP(), use_count = use_count + 1
            WHERE mapping_id = '{row.mapping_id}'
            """
            client.query(update_sql).result()
            
            return {
                "mapping_id": row.mapping_id,
                "field_mappings": json.loads(row.field_mappings),
                "transform_rules": json.loads(row.transform_rules) if row.transform_rules else {},
                "confidence": row.confidence
            }
        return None
    except Exception as e:
        print(f"Mapping cache lookup error: {e}")
        return None


def _save_mapping(client, cfg, source_identifier: str, target_schema: str, 
                  field_mappings: Dict[str, str], transform_rules: Dict[str, Any] = None,
                  confidence: float = 1.0, created_by: str = "ai") -> bool:
    """Save a new mapping to the cache"""
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        table_id = f"{project_id}.{dataset_id}.schema_mappings"
        
        mapping_id = f"map_{hashlib.md5(f'{source_identifier}_{target_schema}'.encode()).hexdigest()[:12]}"
        mappings_json = json.dumps(field_mappings).replace("'", "''")
        rules_json = json.dumps(transform_rules or {}).replace("'", "''")
        
        # Upsert: delete existing then insert
        delete_sql = f"""
        DELETE FROM `{table_id}`
        WHERE source_identifier = '{source_identifier}' AND target_schema = '{target_schema}'
        """
        client.query(delete_sql).result()
        
        insert_sql = f"""
        INSERT INTO `{table_id}`
        (mapping_id, source_identifier, target_schema, field_mappings, transform_rules, 
         created_at, use_count, confidence, created_by)
        VALUES (
            '{mapping_id}',
            '{source_identifier}',
            '{target_schema}',
            '{mappings_json}',
            '{rules_json}',
            CURRENT_TIMESTAMP(),
            1,
            {confidence},
            '{created_by}'
        )
        """
        client.query(insert_sql).result()
        return True
    except Exception as e:
        print(f"Mapping save error: {e}")
        return False


# =============================================================================
# AI Transformation Engine
# =============================================================================

def _get_ai_client():
    """Get Gemini AI client"""
    try:
        import google.generativeai as genai
        from pillars.config_vault import EffectiveSettings
        
        cfg = EffectiveSettings()
        api_key = getattr(cfg, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            return None
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        print(f"AI client error: {e}")
        return None


def _build_transform_prompt(raw_data: Dict[str, Any], target_schema: str) -> str:
    """Build the AI prompt for data transformation"""
    schema_json = get_schema_json(target_schema)
    
    prompt = f"""You are a data transformation expert. Your job is to map incoming data to a target schema.

## TARGET SCHEMA (The Law - data MUST match this structure):
```json
{schema_json}
```

## INCOMING RAW DATA:
```json
{json.dumps(raw_data, indent=2, default=str)}
```

## YOUR TASK:
1. Analyze the raw data structure
2. Map each field to the corresponding target schema field
3. Transform values if needed (e.g., date formats, number parsing)
4. Return ONLY valid JSON that matches the target schema
5. If a required field is missing, use a sensible default or null
6. Do NOT hallucinate or invent data that isn't present

## RULES:
- For dates: Convert to YYYY-MM-DD format
- For numbers: Parse strings like "₹100" or "10.00" to float
- For missing optional fields: Use null or empty string
- For order items: Each item needs item_name (required), quantity, unit_price
- Preserve the original data in raw_json field if the schema has one

## OUTPUT:
Return ONLY the transformed JSON object. No explanations, no markdown, just pure JSON.
"""
    return prompt


def _ai_transform(raw_data: Dict[str, Any], target_schema: str) -> Tuple[Optional[Dict[str, Any]], float, Optional[str]]:
    """
    Use AI to transform raw data to target schema.
    Returns: (transformed_data, confidence, error_message)
    """
    ai = _get_ai_client()
    if not ai:
        return None, 0.0, "AI client not available"
    
    try:
        prompt = _build_transform_prompt(raw_data, target_schema)
        
        response = ai.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,  # Low temperature for consistent output
                "max_output_tokens": 8192,
            }
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        transformed = json.loads(response_text)
        
        # Confidence based on how complete the response is
        confidence = 0.9  # Base confidence for successful AI transform
        
        return transformed, confidence, None
        
    except json.JSONDecodeError as e:
        return None, 0.0, f"AI returned invalid JSON: {str(e)}"
    except Exception as e:
        return None, 0.0, f"AI transform error: {str(e)}"


def _apply_mapping(raw_data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a cached mapping to transform data"""
    field_mappings = mapping.get("field_mappings", {})
    transform_rules = mapping.get("transform_rules", {})
    
    result = {}
    
    for target_field, source_field in field_mappings.items():
        if source_field in raw_data:
            value = raw_data[source_field]
            
            # Apply transform rules if any
            if target_field in transform_rules:
                rule = transform_rules[target_field]
                if rule.get("type") == "date":
                    value = _parse_date(value)
                elif rule.get("type") == "number":
                    value = _parse_number(value)
                elif rule.get("type") == "boolean":
                    value = _parse_boolean(value)
            
            result[target_field] = value
    
    return result


def _parse_date(value) -> Optional[str]:
    """Parse various date formats to YYYY-MM-DD"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    
    str_val = str(value).strip()
    formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d.%m.%Y']
    
    for fmt in formats:
        try:
            return datetime.strptime(str_val, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return str_val  # Return as-is if parsing fails


def _parse_number(value) -> float:
    """Parse various number formats to float"""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    
    str_val = str(value).strip()
    # Remove currency symbols and commas
    str_val = str_val.replace('₹', '').replace('$', '').replace(',', '').strip()
    
    try:
        return float(str_val)
    except ValueError:
        return 0.0


def _parse_boolean(value) -> bool:
    """Parse various boolean representations"""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    
    str_val = str(value).lower().strip()
    return str_val in ('true', 'yes', '1', 'y', 'on')


# =============================================================================
# Main Transform Functions
# =============================================================================

def transform_to_order(raw_data: Dict[str, Any], source_identifier: str = "unknown") -> Tuple[TransformResult, Optional[GoldenOrder], List[str]]:
    """
    Transform raw data to GoldenOrder schema.
    
    Returns: (result_status, validated_order_or_none, list_of_errors)
    """
    client, cfg = _get_bq_client()
    errors = []
    
    # Step 1: Check for cached mapping
    cached_mapping = None
    if client and cfg:
        cached_mapping = _get_cached_mapping(client, cfg, source_identifier, "order")
    
    transformed_data = None
    confidence = 0.0
    
    if cached_mapping:
        # Fast path: Use cached mapping
        transformed_data = _apply_mapping(raw_data, cached_mapping)
        confidence = cached_mapping.get("confidence", 0.9)
    else:
        # Slow path: Use AI
        transformed_data, confidence, ai_error = _ai_transform(raw_data, "order")
        
        if ai_error:
            errors.append(ai_error)
            return TransformResult.AI_ERROR, None, errors
        
        # Save the mapping for future use (if it validates)
        # We'll save after validation
    
    if not transformed_data:
        errors.append("No transformation result")
        return TransformResult.NO_MAPPING, None, errors
    
    # Add source metadata
    transformed_data["source"] = DataSource.UNKNOWN.value
    transformed_data["raw_json"] = json.dumps(raw_data, default=str)
    
    # Step 2: Validate against Golden Schema
    is_valid, validated_order, validation_errors = validate_order(transformed_data)
    
    if not is_valid:
        errors.extend(validation_errors)
        return TransformResult.VALIDATION_FAILED, None, errors
    
    # Save mapping if it was AI-generated and validated
    if not cached_mapping and client and cfg:
        # Extract field mapping from the transformation
        field_mappings = {}
        for target_key in transformed_data.keys():
            for source_key in raw_data.keys():
                if source_key.lower().replace("_", "") == target_key.lower().replace("_", ""):
                    field_mappings[target_key] = source_key
                    break
        
        if field_mappings:
            _save_mapping(client, cfg, source_identifier, "order", field_mappings, confidence=confidence)
    
    return TransformResult.SUCCESS, validated_order, []


def transform_to_expense(raw_data: Dict[str, Any], source_identifier: str = "unknown") -> Tuple[TransformResult, Optional[GoldenExpense], List[str]]:
    """Transform raw data to GoldenExpense schema."""
    client, cfg = _get_bq_client()
    errors = []
    
    cached_mapping = None
    if client and cfg:
        cached_mapping = _get_cached_mapping(client, cfg, source_identifier, "expense")
    
    transformed_data = None
    confidence = 0.0
    
    if cached_mapping:
        transformed_data = _apply_mapping(raw_data, cached_mapping)
        confidence = cached_mapping.get("confidence", 0.9)
    else:
        transformed_data, confidence, ai_error = _ai_transform(raw_data, "expense")
        
        if ai_error:
            errors.append(ai_error)
            return TransformResult.AI_ERROR, None, errors
    
    if not transformed_data:
        return TransformResult.NO_MAPPING, None, ["No transformation result"]
    
    transformed_data["source"] = DataSource.UNKNOWN.value
    
    is_valid, validated_expense, validation_errors = validate_expense(transformed_data)
    
    if not is_valid:
        errors.extend(validation_errors)
        return TransformResult.VALIDATION_FAILED, None, errors
    
    if not cached_mapping and client and cfg:
        field_mappings = {}
        for target_key in transformed_data.keys():
            for source_key in raw_data.keys():
                if source_key.lower().replace("_", "") == target_key.lower().replace("_", ""):
                    field_mappings[target_key] = source_key
                    break
        if field_mappings:
            _save_mapping(client, cfg, source_identifier, "expense", field_mappings, confidence=confidence)
    
    return TransformResult.SUCCESS, validated_expense, []


def transform_to_purchase(raw_data: Dict[str, Any], source_identifier: str = "unknown") -> Tuple[TransformResult, Optional[GoldenPurchase], List[str]]:
    """Transform raw data to GoldenPurchase schema."""
    client, cfg = _get_bq_client()
    errors = []
    
    cached_mapping = None
    if client and cfg:
        cached_mapping = _get_cached_mapping(client, cfg, source_identifier, "purchase")
    
    transformed_data = None
    confidence = 0.0
    
    if cached_mapping:
        transformed_data = _apply_mapping(raw_data, cached_mapping)
        confidence = cached_mapping.get("confidence", 0.9)
    else:
        transformed_data, confidence, ai_error = _ai_transform(raw_data, "purchase")
        
        if ai_error:
            errors.append(ai_error)
            return TransformResult.AI_ERROR, None, errors
    
    if not transformed_data:
        return TransformResult.NO_MAPPING, None, ["No transformation result"]
    
    transformed_data["source"] = DataSource.UNKNOWN.value
    
    is_valid, validated_purchase, validation_errors = validate_purchase(transformed_data)
    
    if not is_valid:
        errors.extend(validation_errors)
        return TransformResult.VALIDATION_FAILED, None, errors
    
    if not cached_mapping and client and cfg:
        field_mappings = {}
        for target_key in transformed_data.keys():
            for source_key in raw_data.keys():
                if source_key.lower().replace("_", "") == target_key.lower().replace("_", ""):
                    field_mappings[target_key] = source_key
                    break
        if field_mappings:
            _save_mapping(client, cfg, source_identifier, "purchase", field_mappings, confidence=confidence)
    
    return TransformResult.SUCCESS, validated_purchase, []


# =============================================================================
# Dispatch Function
# =============================================================================

def transform_data(raw_data: Dict[str, Any], target_schema: str, source_identifier: str = "unknown"):
    """
    Main dispatch function - transforms data to the specified schema.
    
    Args:
        raw_data: The raw incoming data
        target_schema: "order", "expense", or "purchase"
        source_identifier: Identifier for caching mappings
    
    Returns:
        Tuple of (TransformResult, validated_object_or_none, list_of_errors)
    """
    if target_schema == "order":
        return transform_to_order(raw_data, source_identifier)
    elif target_schema == "expense":
        return transform_to_expense(raw_data, source_identifier)
    elif target_schema == "purchase":
        return transform_to_purchase(raw_data, source_identifier)
    else:
        return TransformResult.NO_MAPPING, None, [f"Unknown target schema: {target_schema}"]


# =============================================================================
# Petpooja-Specific Transformer (Optimized)
# =============================================================================

def transform_petpooja_order(raw_data: Dict[str, Any]) -> Tuple[TransformResult, Optional[GoldenOrder], List[str]]:
    """
    Optimized transformer for Petpooja API data.
    Uses known field mappings - no AI needed.
    """
    try:
        order_obj = raw_data.get("Order", raw_data)
        
        # Extract items
        items = []
        order_items = raw_data.get("OrderItem", []) or raw_data.get("items", []) or []
        for item in order_items:
            if not isinstance(item, dict):
                continue
            items.append(GoldenOrderItem(
                item_name=str(item.get("name") or item.get("item_name") or "Unknown"),
                item_id=str(item.get("item_id") or item.get("itemId") or ""),
                category=item.get("category") or item.get("category_name"),
                quantity=float(item.get("quantity", 1) or 1),
                unit_price=float(item.get("price", 0) or 0) / max(float(item.get("quantity", 1) or 1), 1),
                line_total=float(item.get("price", 0) or 0),
                item_discount=float(item.get("discount", 0) or 0),
                tax_rate=float(item.get("tax_rate", 0) or 0),
                variant=item.get("variant") or item.get("item_variant"),
                addons=json.dumps(item.get("addons", [])) if item.get("addons") else None,
                special_instructions=item.get("special_instructions") or item.get("instructions"),
                is_cancelled=bool(item.get("is_cancelled") or item.get("isCancelled")),
                cancelled_reason=item.get("cancelled_reason") or item.get("cancelledReason")
            ))
        
        # Extract payments
        payments = []
        payment_list = raw_data.get("Payment", []) or raw_data.get("payments", []) or []
        for p in payment_list:
            if isinstance(p, dict):
                payments.append(GoldenPayment(
                    payment_method=p.get("payment_method") or p.get("method") or "unknown",
                    amount=float(p.get("amount", 0) or 0),
                    status=p.get("status") or "completed"
                ))
        
        # Extract discounts
        discounts = []
        discount_list = raw_data.get("Discount", []) or raw_data.get("discounts", []) or []
        for d in discount_list:
            if isinstance(d, dict):
                discounts.append(GoldenDiscount(
                    discount_name=d.get("discount_name") or d.get("name"),
                    discount_type=d.get("discount_type") or d.get("type"),
                    amount=float(d.get("discount_amount") or d.get("amount") or 0),
                    reason=d.get("reason"),
                    coupon_code=d.get("coupon_code") or d.get("couponCode") or d.get("code")
                ))
        
        # Build order
        order = GoldenOrder(
            order_id=str(order_obj.get("orderID") or order_obj.get("order_id") or f"ord_{datetime.now().timestamp()}"),
            bill_date=order_obj.get("order_date") or datetime.now().date(),
            order_total=float(order_obj.get("order_total") or order_obj.get("total") or 0),
            subtotal=float(order_obj.get("subtotal") or order_obj.get("sub_total") or 0),
            tax_amount=float(order_obj.get("tax") or order_obj.get("tax_amount") or 0),
            service_charge=float(order_obj.get("service_charge") or order_obj.get("serviceCharge") or 0),
            delivery_charge=float(order_obj.get("delivery_charge") or order_obj.get("deliveryCharge") or 0),
            packing_charge=float(order_obj.get("packing_charge") or order_obj.get("packingCharge") or 0),
            total_discount=sum(d.amount for d in discounts),
            order_status=order_obj.get("status") or "completed",
            order_type=order_obj.get("order_type") or order_obj.get("orderType") or order_obj.get("delivery_type"),
            order_time=order_obj.get("order_time"),
            payment_mode=order_obj.get("payment_mode") or order_obj.get("paymentMode") or order_obj.get("payment_type"),
            payment_status=order_obj.get("payment_status") or order_obj.get("paymentStatus"),
            customer_name=order_obj.get("customer_name") or order_obj.get("cust_name"),
            customer_phone=order_obj.get("customer_phone") or order_obj.get("cust_phone") or order_obj.get("phone"),
            customer_email=order_obj.get("customer_email") or order_obj.get("cust_email") or order_obj.get("email"),
            delivery_partner=order_obj.get("delivery_partner") or order_obj.get("deliveryPartner") or order_obj.get("partner"),
            outlet_id=order_obj.get("outlet_id") or order_obj.get("outletId"),
            waiter_name=order_obj.get("waiter_name") or order_obj.get("waiterName"),
            table_number=order_obj.get("table_number") or order_obj.get("table_no") or order_obj.get("table"),
            coupon_codes=", ".join(d.coupon_code for d in discounts if d.coupon_code),
            items=items,
            payments=payments,
            discounts=discounts,
            source=DataSource.PETPOOJA,
            raw_json=json.dumps(raw_data, default=str)
        )
        
        return TransformResult.SUCCESS, order, []
        
    except Exception as e:
        return TransformResult.VALIDATION_FAILED, None, [str(e)]
