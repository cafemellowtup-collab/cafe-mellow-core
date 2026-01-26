from datetime import datetime

def run_audit(client, settings):
    """Audit expense purity - tags personal/loan expenses"""
    findings = []
    
    try:
        # We scan recent expenses to see if they follow your naming rules
        q = f"""
            SELECT item_name, amount, expense_date, paid_from, employee_name
            FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.expenses_master`
            WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        """
        
        df = client.query(q).to_dataframe()
        
        if df.empty:
            return findings
        
        for _, row in df.iterrows():
            try:
                item_name = str(row.get('item_name', ''))
                
                # LOGIC: Check for your '-' delimiter
                if " - " in item_name:
                    parts = item_name.split(" - ")
                    if len(parts) >= 2:
                        category = parts[1].strip().lower()
                        
                        # Flag if it's a 'Personal' or 'Loan' type
                        if any(x in category for x in ["personal", "interests", "loan"]):
                            expense_date = row.get('expense_date')
                            date_str = expense_date.strftime('%Y-%m-%d') if hasattr(expense_date, 'strftime') else str(expense_date)
                            
                            findings.append({
                                'created_at': datetime.now(),
                                'target_date': date_str,
                                'department': 'Finance',
                                'task_type': 'P&L Purity',
                                'item_involved': parts[0].strip(),
                                'description': f"Tag Detected: '{category}'. AI will offer to ignore this in Business Profit prompts.",
                                'status': 'Logged',
                                'priority': 'Low'
                            })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"P3 ERROR: Could not query expenses_master: {e}")
        return findings
        
    return findings
