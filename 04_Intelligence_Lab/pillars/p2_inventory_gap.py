from datetime import datetime

def run_audit(client, settings):
    """Audit inventory gaps - finds unlinked sales items"""
    findings = []
    
    try:
        # Logic to find unlinked items
        q = f"""
            SELECT DISTINCT item_name FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed`
            WHERE item_name NOT IN (SELECT sales_name FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.titan_name_bridge`)
            AND item_name NOT IN (SELECT parent_item FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.recipes_sales_master`)
            LIMIT 5
        """
        df = client.query(q).to_dataframe()
        
        if df.empty:
            return findings
        
        for _, row in df.iterrows():
            item_name = row.get('item_name')
            if item_name:
                findings.append({
                    'created_at': datetime.now(),
                    'target_date': datetime.now().strftime('%Y-%m-%d'),
                    'department': 'Operations',
                    'task_type': 'Recipe Gap',
                    'item_involved': str(item_name),
                    'description': f"'{item_name}' has no linked recipe. Petpooja cleanup required.",
                    'status': 'Pending',
                    'priority': 'High'
                })
    except Exception as e:
        print(f"P2 ERROR: Could not query for inventory gaps: {e}")
        return findings
    
    return findings
