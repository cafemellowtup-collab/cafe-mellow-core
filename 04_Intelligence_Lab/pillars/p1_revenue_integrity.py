from datetime import datetime
import json

def run_audit(client, settings):
    """Audit revenue integrity - detects cancellations and discounts"""
    findings = []
    
    try:
        q = f"""
            SELECT order_id, bill_date, full_json 
            FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_raw_layer`
            WHERE bill_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        """
        raw_df = client.query(q).to_dataframe()
        
        if raw_df.empty:
            return findings
        
    except Exception as e:
        print(f"P1 ERROR: Could not query sales_raw_layer: {e}")
        return findings
    
    for _, row in raw_df.iterrows():
        # Check if full_json is actually there
        raw_json_str = row.get('full_json')
        if raw_json_str is None or raw_json_str == "":
            continue
        
        try:
            data = json.loads(raw_json_str)
            order_meta = data.get('Order', {})
            discounts = data.get('Discount', [])
            
            # CANCELLATION AUDIT
            status = order_meta.get('status', 'Unknown')
            if isinstance(status, str) and status.lower() in ['cancelled', 'void', 'deleted']:
                reason = order_meta.get('cancel_reason', 'No reason provided')
                findings.append({
                    'created_at': datetime.now(),
                    'target_date': row['bill_date'].strftime('%Y-%m-%d') if hasattr(row['bill_date'], 'strftime') else str(row['bill_date']),
                    'department': 'Finance',
                    'task_type': 'Order Cancellation',
                    'item_involved': f"Order {row['order_id']}",
                    'description': f"Order CANCELLED. Reason: {reason}.",
                    'status': 'Pending',
                    'priority': 'High'
                })
            
            # DISCOUNT AUDIT
            if isinstance(discounts, list):
                for disc in discounts:
                    if isinstance(disc, dict):
                        disc_name = disc.get('discount_name', 'Manual Discount')
                        findings.append({
                            'created_at': datetime.now(),
                            'target_date': row['bill_date'].strftime('%Y-%m-%d') if hasattr(row['bill_date'], 'strftime') else str(row['bill_date']),
                            'department': 'Finance',
                            'task_type': 'Discount Audit',
                            'item_involved': f"Order {row['order_id']}",
                            'description': f"Discount Applied: '{disc_name}'.",
                            'status': 'Pending',
                            'priority': 'Medium'
                        })
        except json.JSONDecodeError:
            continue
        except Exception as e:
            continue
    
    return findings
