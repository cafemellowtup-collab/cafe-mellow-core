# settings.py
# --- THE VAULT: Store all your secrets here ---

import os

# 1. Google Cloud Keys
KEY_FILE = "service-key.json"
PROJECT_ID = "cafe-mellow-core-2026"

# THE BRAIN: Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 2. Database Config
DATASET_ID = "cafe_operations"
TABLE_EXPENSES = "expenses_master"
TABLE_CASH = "cash_flow_master"
TABLE_SALES_PARSED = "sales_items_parsed" # Ensure this is here
TABLE_BRIDGE = "titan_name_bridge"       # The Intelligence Bridge

# 3. Google Drive Folder IDs (PASTE YOUR IDS HERE)
# Folder for Expense Reports (Excel)
FOLDER_ID_EXPENSES = os.getenv("FOLDER_ID_EXPENSES", "")

# Folder for Withdrawal/Topup Reports (Excel)
# MAKE SURE you shared this folder with your Robot Email!
FOLDER_ID_CASH_OPS = os.getenv("FOLDER_ID_CASH_OPS", "")

# 4. Magic Strings (Do not touch)
# This prevents the "Markdown Corruption" error you saw earlier
SCOPE_URL = ["https://www.googleapis.com/auth/drive.readonly"]
GEMINI_URL = os.getenv(
    "GEMINI_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
)

# 5. Petpooja Inventory Config (NEW)
PP_APP_KEY = os.getenv("PP_APP_KEY", "")
PP_APP_SECRET = os.getenv("PP_APP_SECRET", "")
PP_ACCESS_TOKEN = os.getenv("PP_ACCESS_TOKEN", "")
PP_MAPPING_CODE = os.getenv("PP_MAPPING_CODE", "")

# 6. New Tables
TABLE_INGREDIENTS = "ingredients_master"

# 7. Recipe & Production Tables
TABLE_RECIPES = "recipes_sales_master"       # The "Assembly" (Sandwich -> Bread)
TABLE_PRODUCTION = "recipes_production_master" # The "Factory" (Bread -> Maida)
# ... (Keep existing code) ...

# 8. Recipe Folder Config
FOLDER_ID_RECIPES = "13gFfCEc-KEb2E8XTNZIlpQjwkjoaRmqg"
# ... (Keep existing code) ...

# 9. Purchase Config
FOLDER_ID_PURCHASES = "1a8nSjikNpE0KIl_1PfK6fgA3d-WfiXtU"
TABLE_PURCHASES = "purchases_master"
# ... (Keep existing code) ...

# 10. Wastage Config
FOLDER_ID_WASTAGE = "1P5e4QsH6l3v2nHufQP6pJhiUqb4OXSth"
TABLE_WASTAGE = "wastage_log"

# 11. Evolution & Self-Development
TABLE_DEV_EVOLUTION = "dev_evolution_log"

# 12. System Error Log (BigQuery + file)
TABLE_SYSTEM_ERROR_LOG = "system_error_log"

# 13. System Sync Log (Last Successful Sync timestamps for Drive→BQ)
TABLE_SYSTEM_SYNC_LOG = "system_sync_log"

# 14. System Cost Log (Estimated BigQuery query cost)
TABLE_SYSTEM_COST_LOG = "system_cost_log"

# 15. Budget Guardrails
BUDGET_MONTHLY_INR = float(os.getenv("BUDGET_MONTHLY_INR", "1000"))
MAX_QUERY_COST_INR = float(os.getenv("MAX_QUERY_COST_INR", "10"))
DISABLE_BUDGET_BREAKER = os.getenv("DISABLE_BUDGET_BREAKER", "").strip().lower() in ("1", "true", "yes", "y")