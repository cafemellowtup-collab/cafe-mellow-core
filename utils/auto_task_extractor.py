"""
Auto-Task Extractor: Parses AI responses for [TASK:] directives and creates operations tasks
"""
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.cloud import bigquery

def extract_tasks_from_response(ai_response: str) -> List[Dict[str, Any]]:
    """
    Extract tasks from AI response marked with [TASK:] prefix.
    
    Example input:
    "Maida wastage is up 12%. [TASK:] Retrain prep staff on dough yield by tomorrow 10 AM."
    
    Returns list of task dictionaries ready for insertion.
    """
    tasks = []
    
    # Pattern: [TASK:] followed by the task description
    pattern = r'\[TASK:\s*\](.*?)(?:\[TASK:\s*\]|$)'
    matches = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        task_text = match.strip()
        if not task_text:
            continue
        
        # Extract item if mentioned (look for ingredients/items in the task)
        item_involved = extract_item_from_task(task_text)
        
        # Determine priority based on keywords
        priority = determine_priority(task_text)
        
        # Determine department
        department = determine_department(task_text)
        
        # Extract deadline if mentioned
        deadline = extract_deadline(task_text)
        
        task = {
            "description": task_text[:500],  # Limit length
            "item_involved": item_involved,
            "priority": priority,
            "department": department,
            "deadline": deadline,
            "task_type": "AI_Generated_Action",
            "status": "Pending",
        }
        
        tasks.append(task)
    
    return tasks


def extract_item_from_task(task_text: str) -> str:
    """Extract ingredient/item name from task text"""
    # Common ingredients
    ingredients = [
        "maida", "flour", "sugar", "milk", "butter", "cheese", "chicken",
        "paneer", "vegetables", "oil", "bread", "coffee", "tea", "rice"
    ]
    
    task_lower = task_text.lower()
    for ingredient in ingredients:
        if ingredient in task_lower:
            return ingredient.title()
    
    return "General"


def determine_priority(task_text: str) -> str:
    """Determine priority based on keywords and urgency"""
    task_lower = task_text.lower()
    
    # High priority indicators
    high_keywords = ["urgent", "immediately", "critical", "now", "asap", "emergency"]
    if any(kw in task_lower for kw in high_keywords):
        return "High"
    
    # Medium priority indicators
    medium_keywords = ["today", "this morning", "this afternoon", "by end of day"]
    if any(kw in task_lower for kw in medium_keywords):
        return "Medium"
    
    # Default to Medium for AI-generated tasks (they're usually actionable)
    return "Medium"


def determine_department(task_text: str) -> str:
    """Determine which department should handle the task"""
    task_lower = task_text.lower()
    
    department_keywords = {
        "Kitchen": ["prep", "cook", "kitchen", "recipe", "ingredient", "chef", "mixing", "dough"],
        "Service": ["customer", "table", "order", "waiter", "service", "delivery"],
        "Inventory": ["stock", "purchase", "vendor", "inventory", "wastage", "storage"],
        "Management": ["staff", "schedule", "training", "policy", "manager", "retrain"],
        "Finance": ["cost", "expense", "pricing", "budget", "payment"],
    }
    
    for dept, keywords in department_keywords.items():
        if any(kw in task_lower for kw in keywords):
            return dept
    
    return "Operations"


def extract_deadline(task_text: str) -> Optional[str]:
    """Extract deadline from task text"""
    task_lower = task_text.lower()
    
    # Look for specific time mentions
    if "today" in task_lower or "this morning" in task_lower or "this afternoon" in task_lower:
        return (datetime.now().date()).isoformat()
    
    if "tomorrow" in task_lower:
        return (datetime.now().date() + timedelta(days=1)).isoformat()
    
    if "this week" in task_lower or "by friday" in task_lower:
        # End of current week
        days_until_friday = (4 - datetime.now().weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        return (datetime.now().date() + timedelta(days=days_until_friday)).isoformat()
    
    # Default: 2 days from now for actionable tasks
    return (datetime.now().date() + timedelta(days=2)).isoformat()


def insert_tasks_to_bigquery(
    client: bigquery.Client,
    settings,
    tasks: List[Dict[str, Any]],
    org_id: str = "default_org",
    location_id: str = "default_location"
) -> int:
    """
    Insert extracted tasks into operations_tasks table (or ai_task_queue).
    Returns number of tasks inserted.
    """
    if not tasks:
        return 0
    
    try:
        project_id = getattr(settings, "PROJECT_ID", "")
        dataset_id = getattr(settings, "DATASET_ID", "")
        
        # Use ai_task_queue table (existing structure)
        table_name = "ai_task_queue"
        table_id = f"{project_id}.{dataset_id}.{table_name}"
        
        # Ensure table exists
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_id}` (
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
            task_type STRING,
            item_involved STRING,
            description STRING,
            priority STRING,
            department STRING,
            status STRING DEFAULT 'Pending',
            deadline DATE,
            org_id STRING,
            location_id STRING
        )
        """
        client.query(create_table_sql).result()
        
        # Insert tasks
        inserted_count = 0
        for task in tasks:
            insert_sql = f"""
            INSERT INTO `{table_id}`
            (created_at, task_type, item_involved, description, priority, department, status, deadline, org_id, location_id)
            VALUES (
                CURRENT_TIMESTAMP(),
                '{task.get("task_type", "AI_Generated_Action").replace("'", "''")}',
                '{task.get("item_involved", "General").replace("'", "''")}',
                '''{task.get("description", "").replace("'", "''")}''',
                '{task.get("priority", "Medium")}',
                '{task.get("department", "Operations").replace("'", "''")}',
                'Pending',
                {f"DATE('{task.get('deadline')}')" if task.get('deadline') else 'NULL'},
                '{org_id}',
                '{location_id}'
            )
            """
            client.query(insert_sql).result()
            inserted_count += 1
        
        return inserted_count
        
    except Exception as e:
        print(f"Error inserting auto-tasks: {e}")
        return 0
