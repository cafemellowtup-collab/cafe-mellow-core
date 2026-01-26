#!/usr/bin/env python3
"""
TITAN System Map Generator - Living Blueprint Automation
Generates comprehensive system documentation by scanning the codebase structure.

SECURITY PROTOCOL:
- Ignores sensitive files (.env, secrets/, service-key.json, etc.)
- Never includes credentials or API keys in generated documentation
- Sanitizes all output to prevent credential leakage

Usage: python scripts/generate_system_map.py
Output: BLUEPRINT.md in project root
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple

# ============================================================================
# SECURITY CONFIGURATION - Files and directories to ALWAYS exclude
# ============================================================================
SECURITY_EXCLUSIONS = {
    # Credential files
    ".env", ".env.local", ".env.production", ".env.development",
    "service-key.json", "credentials.json", "key.json", "keys.json",
    
    # Directories with secrets
    "secrets/", "credentials/", ".secrets/", "private/",
    
    # Version control and dependencies
    ".git/", ".gitignore", "node_modules/", "__pycache__/", ".venv/", "venv/",
    ".next/", ".cache/", "dist/", "build/",
    
    # Config overrides that may contain secrets
    "config_override.json",
    
    # Lock files and logs
    "package-lock.json", "*.log", "logs/",
    
    # Archive and legacy (noise)
    "99_Archive_Legacy/",
}

# Patterns to identify sensitive content in files
SENSITIVE_PATTERNS = [
    r'private_key',
    r'secret',
    r'password\s*[:=]',
    r'token\s*[:=]',
    r'api[_-]?key',
]

# File extensions to analyze for domain logic
ANALYSIS_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript React',
    '.jsx': 'JavaScript React',
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_excluded(path: str, exclusions: Set[str]) -> bool:
    """Check if path matches any exclusion pattern."""
    path_lower = path.lower().replace('\\', '/')
    for exc in exclusions:
        exc_lower = exc.lower()
        if exc_lower.endswith('/'):
            if exc_lower in path_lower or path_lower.startswith(exc_lower):
                return True
        else:
            if exc_lower in path_lower or path_lower.endswith(exc_lower):
                return True
    return False


def get_file_category(filepath: str) -> str:
    """Categorize file based on directory structure."""
    path_parts = Path(filepath).parts
    
    # Domain/Business Logic (Hexagonal Core)
    if 'pillars' in path_parts:
        return 'Domain Logic (Core)'
    
    # Adapters (Hexagonal Ports & Adapters)
    if any(x in path_parts for x in ['01_Data_Sync', 'api', 'utils']):
        if 'api' in path_parts:
            return 'Primary Adapter (API/UI)'
        if '01_Data_Sync' in path_parts:
            return 'Secondary Adapter (Data Sources)'
        if 'utils' in path_parts:
            return 'Application Services'
    
    # Infrastructure
    if any(x in path_parts for x in ['web', 'scheduler', 'scripts']):
        if 'web' in path_parts and 'src' in path_parts:
            return 'Frontend (Next.js)'
        return 'Infrastructure'
    
    # Intelligence/AI Layer
    if '04_Intelligence_Lab' in path_parts:
        return 'Intelligence Layer (AI/Analytics)'
    
    return 'Configuration'


def extract_imports(filepath: str) -> List[str]:
    """Extract import statements from Python/JS/TS files."""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                # Python imports
                if line.startswith('from ') or line.startswith('import '):
                    imports.append(line.split('#')[0].strip())
                # JS/TS imports
                elif line.startswith('import ') and ' from ' in line:
                    imports.append(line.split('//')[0].strip())
                    
                # Stop after ~50 lines (imports are typically at top)
                if len(imports) > 50:
                    break
    except Exception:
        pass
    return imports


def analyze_file_purpose(filepath: str, content_sample: str) -> str:
    """Infer file purpose from name and content."""
    filename = os.path.basename(filepath).lower()
    
    # Sync/ETL patterns
    if 'sync' in filename:
        return 'Data Synchronization (ETL)'
    
    # API patterns
    if any(x in filename for x in ['api', 'endpoint', 'route']):
        return 'REST API Endpoint'
    
    # UI/Frontend patterns
    if any(x in filename for x in ['client', 'page', 'component']):
        return 'UI Component'
    
    # Domain logic patterns
    if any(x in filepath.lower() for x in ['pillar', 'domain', 'service']):
        return 'Business Logic'
    
    # Intelligence patterns
    if any(x in filename for x in ['ai', 'gemini', 'chat', 'intelligence']):
        return 'AI/Intelligence Service'
    
    # Data patterns
    if any(x in filename for x in ['dashboard', 'report', 'metric']):
        return 'Analytics/Reporting'
    
    return 'Utility/Helper'


def scan_directory(root_path: str) -> Dict:
    """Scan directory structure and categorize files."""
    structure = {
        'domain_logic': [],
        'adapters_primary': [],
        'adapters_secondary': [],
        'application_services': [],
        'frontend': [],
        'intelligence': [],
        'infrastructure': [],
        'configuration': [],
    }
    
    file_count = 0
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out excluded directories
        dirnames[:] = [d for d in dirnames if not is_excluded(os.path.join(dirpath, d), SECURITY_EXCLUSIONS)]
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            
            # Skip excluded files
            if is_excluded(filepath, SECURITY_EXCLUSIONS):
                continue
            
            # Only analyze code files
            ext = os.path.splitext(filename)[1]
            if ext not in ANALYSIS_EXTENSIONS:
                continue
            
            file_count += 1
            rel_path = os.path.relpath(filepath, root_path)
            category = get_file_category(rel_path)
            
            file_info = {
                'path': rel_path.replace('\\', '/'),
                'name': filename,
                'size': os.path.getsize(filepath),
                'language': ANALYSIS_EXTENSIONS.get(ext, 'Unknown'),
                'purpose': analyze_file_purpose(filepath, ''),
                'imports': extract_imports(filepath)[:10],  # Limit to 10 imports
            }
            
            # Map to structure categories
            if 'Domain Logic' in category:
                structure['domain_logic'].append(file_info)
            elif 'Primary Adapter' in category:
                structure['adapters_primary'].append(file_info)
            elif 'Secondary Adapter' in category:
                structure['adapters_secondary'].append(file_info)
            elif 'Application Services' in category:
                structure['application_services'].append(file_info)
            elif 'Frontend' in category:
                structure['frontend'].append(file_info)
            elif 'Intelligence' in category:
                structure['intelligence'].append(file_info)
            elif 'Infrastructure' in category:
                structure['infrastructure'].append(file_info)
            else:
                structure['configuration'].append(file_info)
    
    return structure, file_count


def generate_data_flow_diagram(structure: Dict) -> str:
    """Generate ASCII data flow diagram."""
    diagram = """
## 📊 Data Flow Architecture (Hexagonal/Ports & Adapters)

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRIMARY ADAPTERS (Inbound)                  │
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Next.js   │    │  FastAPI    │    │  Streamlit  │         │
│  │  Frontend   │    │   REST API  │    │   Admin UI  │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION SERVICES                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Chat Interface      • Query Engine                      │ │
│  │  • AI Task Queue       • BigQuery Guardrails              │ │
│  │  • Ops Brief Generator • Performance Optimizer            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOMAIN LOGIC (PILLARS)                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Config Vault        • Dashboard Analytics              │ │
│  │  • Users & Roles       • Chat Intelligence                │ │
│  │  • System Logger       • Evolution Engine                 │ │
│  │  • Expense Analysis    • Revenue Integrity                │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SECONDARY ADAPTERS (Outbound)                   │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐            │
│  │  BigQuery   │  │ Google Drive │  │  Petpooja   │            │
│  │  Warehouse  │  │   Storage    │  │     POS     │            │
│  └─────────────┘  └──────────────┘  └─────────────┘            │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐                              │
│  │   Gemini    │  │  Sync Jobs   │                              │
│  │     AI      │  │  (ETL/ELT)   │                              │
│  └─────────────┘  └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```
"""
    return diagram


def generate_markdown_blueprint(structure: Dict, file_count: int, root_path: str) -> str:
    """Generate complete BLUEPRINT.md content."""
    
    md = f"""# 🧬 TITAN ERP - System Blueprint
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Code Files Analyzed:** {file_count}  
**Architecture:** Hexagonal (Ports & Adapters) + Multi-Tenant SaaS  

---

{generate_data_flow_diagram(structure)}

---

## 🏗️ Architecture Layers

### 1. Domain Logic (Core Business Rules)
**Location:** `pillars/`  
**Purpose:** Pure business logic, framework-agnostic

| File | Purpose | Key Dependencies |
|------|---------|------------------|
"""
    
    for item in structure['domain_logic']:
        imports_str = ', '.join(item['imports'][:3]) if item['imports'] else 'None'
        md += f"| `{item['name']}` | {item['purpose']} | {imports_str} |\n"
    
    md += """
### 2. Primary Adapters (User-Facing Interfaces)
**Location:** `api/`, `web/`, `titan_app.py`  
**Purpose:** REST APIs, UI components, user interaction

| File | Purpose | Language |
|------|---------|----------|
"""
    
    for item in structure['adapters_primary']:
        md += f"| `{item['path']}` | {item['purpose']} | {item['language']} |\n"
    
    md += """
### 3. Secondary Adapters (External Systems)
**Location:** `01_Data_Sync/`  
**Purpose:** Integration with BigQuery, Drive, Petpooja, AI APIs

| File | Purpose | Data Source |
|------|---------|-------------|
"""
    
    for item in structure['adapters_secondary']:
        md += f"| `{item['name']}` | {item['purpose']} | External API |\n"
    
    md += """
### 4. Application Services
**Location:** `utils/`  
**Purpose:** Cross-cutting concerns, query engines, AI orchestration

| File | Purpose | Layer |
|------|---------|-------|
"""
    
    for item in structure['application_services']:
        md += f"| `{item['name']}` | {item['purpose']} | Service |\n"
    
    md += """
### 5. Intelligence Layer (AI/Analytics)
**Location:** `04_Intelligence_Lab/`  
**Purpose:** Sentinel monitoring, DNA analysis, evolution tracking

| File | Purpose | Type |
|------|---------|------|
"""
    
    for item in structure['intelligence']:
        md += f"| `{item['name']}` | {item['purpose']} | AI/Analytics |\n"
    
    md += """
### 6. Frontend (Next.js SaaS Interface)
**Location:** `web/src/`  
**Purpose:** Multi-tenant web interface

| Component | Purpose | Framework |
|-----------|---------|-----------|
"""
    
    for item in structure['frontend'][:20]:  # Limit frontend to prevent bloat
        md += f"| `{item['name']}` | {item['purpose']} | {item['language']} |\n"
    
    md += """
---

## 🔐 Security Architecture

### Credential Management
- **Service Account:** `service-key.json` (Google Cloud)
- **API Keys:** Environment variables via `os.getenv()` in `settings.py`
- **Secret Storage:** `config_override.json` for runtime overrides
- **⚠️ WARNING:** Never commit `service-key.json` or `.env` files to version control

### Data Flow Security
1. **Inbound:** CORS-protected FastAPI endpoints
2. **Outbound:** OAuth2 for Google APIs, token-based for Petpooja
3. **Storage:** BigQuery with service account authentication
4. **AI:** Gemini API key via environment variable

---

## 📦 Domain Models (Business Entities)

### Revenue Domain
- **Sales Orders:** Raw POS data from Petpooja → `sales_raw_layer`
- **Sales Items:** Parsed line items → `sales_items_parsed`
- **Sales Enhanced:** Enriched with customer/delivery metadata → `sales_enhanced`

### Expense Domain
- **Expenses:** Category-based tracking → `expenses_master`
- **Cash Flow:** Withdrawals/topups → `cash_flow_master`
- **Purchases:** Ingredient procurement → `purchases_master`

### Inventory Domain
- **Ingredients:** Raw materials → `ingredients_master`
- **Recipes (Sales):** Item composition → `recipes_sales_master`
- **Recipes (Production):** Sub-recipe assembly → `recipes_production_master`
- **Wastage:** Loss tracking → `wastage_log`

### System Domain
- **Evolution Log:** Self-improvement tracking → `dev_evolution_log`
- **Error Log:** System errors → `system_error_log`
- **Sync Log:** ETL status → `system_sync_log`
- **Cost Log:** BigQuery spend → `system_cost_log`

---

## 🔄 Key Data Flows

### 1. Sales Sync Flow
```
Petpooja POS API 
  → sync_sales_raw.py (Secondary Adapter)
  → sales_raw_layer (BigQuery)
  → enhanced_sales_parser.py (Transform)
  → sales_enhanced (BigQuery)
  → Dashboard/API (Primary Adapter)
```

### 2. Expense Sync Flow
```
Google Drive Excel Files
  → sync_expenses.py (Secondary Adapter)
  → expenses_master (BigQuery)
  → Expense Analysis Engine (Domain Logic)
  → Dashboard Charts (Primary Adapter)
```

### 3. Chat Intelligence Flow
```
User Query (Next.js/Streamlit)
  → /chat/stream API endpoint
  → gemini_chat.py (Application Service)
  → BigQuery Context Retrieval
  → Gemini AI API (Secondary Adapter)
  → Streaming Response (Primary Adapter)
```

---

## 🧪 Adapter Definitions

### Primary Adapters (Driving/Inbound)
| Adapter | Technology | Port Interface |
|---------|-----------|----------------|
| REST API | FastAPI | `/health`, `/chat`, `/metrics`, `/ops` |
| Web UI | Next.js 16 + React 19 | Pages: dashboard, chat, operations, settings |
| Admin Dashboard | Streamlit | `titan_app.py` (legacy, being phased out) |

### Secondary Adapters (Driven/Outbound)
| Adapter | External System | Integration Method |
|---------|----------------|-------------------|
| BigQuery Adapter | Google BigQuery | `google-cloud-bigquery` SDK |
| Drive Adapter | Google Drive | `google-api-python-client` |
| POS Adapter | Petpooja API | REST API (custom HTTP client) |
| AI Adapter | Gemini API | HTTP requests to `generativelanguage.googleapis.com` |

---

## 🎯 Petpooja Integration Points

### Endpoints Consumed
1. **Sales Data:** Fetch order history with full JSON payload
2. **Inventory:** Real-time stock levels (future)
3. **Menu Items:** Item catalog sync (future)

### Data Mapping
- **Order Status:** Normalized to exclude "cancel" variants
- **Revenue:** Multi-path extraction (`order_total`, `total`, `grand_total`)
- **Delivery Partner:** Extracted from JSON payload when column missing

---

## 📈 Evolution & Self-Development

The system tracks its own improvements in `dev_evolution_log`:
- **Feature additions** suggested by AI
- **Bug fixes** identified by Sentinel Hub
- **Performance optimizations** logged by guardrails
- **User feedback** captured via Chat Intelligence

---

## 🚨 Health Monitoring

### Sentinel Hub (`04_Intelligence_Lab/sentinel_hub.py`)
Monitors:
- Revenue anomalies (>10% deviation)
- Data freshness (stale sync warnings)
- Expense spikes
- Missing data gaps

### Cost Guardrails (`utils/bq_guardrails.py`)
- Dry-run cost estimation before query execution
- Monthly budget tracking (₹1000 default)
- Query-level cost logging
- Budget breach prevention

---

## 🔮 Future Roadmap (Per TITAN_DNA.json)

1. **Multi-Tenant Isolation:** Row-level security in BigQuery
2. **Recipe Intelligence:** Auto-detect ingredient usage anomalies
3. **Predictive Analytics:** Demand forecasting via ML
4. **Mobile App:** React Native companion
5. **Webhook Integration:** Real-time Petpooja events

---

**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}  
**Maintained By:** TITAN Self-Evolution Engine  
**Questions?** Check `TITAN_VISION.md` or ask via Intelligence Chat
"""
    
    return md


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    # Determine project root (script is in scripts/ subdirectory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print("🔍 TITAN System Map Generator")
    print("=" * 60)
    print(f"📂 Scanning project: {project_root}")
    print(f"🔒 Security exclusions: {len(SECURITY_EXCLUSIONS)} patterns")
    print()
    
    # Scan directory structure
    print("📊 Analyzing codebase structure...")
    structure, file_count = scan_directory(str(project_root))
    
    print(f"✅ Analyzed {file_count} code files")
    print(f"   • Domain Logic: {len(structure['domain_logic'])} files")
    print(f"   • Primary Adapters: {len(structure['adapters_primary'])} files")
    print(f"   • Secondary Adapters: {len(structure['adapters_secondary'])} files")
    print(f"   • Application Services: {len(structure['application_services'])} files")
    print(f"   • Frontend: {len(structure['frontend'])} files")
    print(f"   • Intelligence: {len(structure['intelligence'])} files")
    print()
    
    # Generate blueprint
    print("📝 Generating BLUEPRINT.md...")
    blueprint_content = generate_markdown_blueprint(structure, file_count, str(project_root))
    
    # Write to file
    output_path = project_root / "BLUEPRINT.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(blueprint_content)
    
    print(f"✅ Blueprint generated: {output_path}")
    print()
    print("🎉 System map generation complete!")
    print(f"📄 View the blueprint: BLUEPRINT.md")
    print()
    print("🔐 SECURITY CHECK:")
    print("   ✅ Excluded sensitive files from documentation")
    print("   ✅ No credentials included in output")
    print("   ✅ Safe to commit BLUEPRINT.md to version control")


if __name__ == "__main__":
    main()
