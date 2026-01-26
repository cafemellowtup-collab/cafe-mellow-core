-- GENESIS PROTOCOL - BigQuery Schema Definitions
-- Universal Ledger & Hexagonal Architecture Tables

-- =============================================================================
-- SECTION 1: CITADEL (Security & RBAC)
-- =============================================================================

-- Users Table
CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.users` (
    id STRING NOT NULL,
    username STRING NOT NULL,
    email STRING NOT NULL,
    phone STRING,
    password_hash STRING NOT NULL,
    pin_hash STRING,
    
    role_ids ARRAY<STRING>,
    permissions ARRAY<STRING>,
    
    org_id STRING NOT NULL,
    location_ids ARRAY<STRING>,
    
    is_active BOOL DEFAULT TRUE,
    is_verified BOOL DEFAULT FALSE,
    last_login TIMESTAMP,
    
    metadata JSON,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY org_id, email;

-- Roles Table
CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.roles` (
    id STRING NOT NULL,
    name STRING NOT NULL,
    description STRING,
    permissions ARRAY<STRING>,
    is_system_role BOOL DEFAULT FALSE,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

-- Entities Table (Employees/Vendors)
CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.entities` (
    id STRING NOT NULL,
    entity_type STRING NOT NULL,
    name STRING NOT NULL,
    
    org_id STRING NOT NULL,
    location_id STRING,
    
    contact_phone STRING,
    contact_email STRING,
    
    employee_id STRING,
    vendor_code STRING,
    
    payment_details JSON,
    tax_details JSON,
    
    linked_user_id STRING,
    
    is_active BOOL DEFAULT TRUE,
    metadata JSON,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY org_id, location_id, entity_type;

-- =============================================================================
-- SECTION 2: UNIVERSAL LEDGER
-- =============================================================================

CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.ledger_universal` (
    id STRING NOT NULL,
    org_id STRING NOT NULL,
    location_id STRING NOT NULL,
    
    timestamp TIMESTAMP NOT NULL,
    entry_date DATE NOT NULL,
    
    type STRING NOT NULL,
    amount NUMERIC NOT NULL,
    
    entry_source STRING NOT NULL,
    source_id STRING,
    
    entity_id STRING,
    entity_name STRING,
    
    category STRING,
    subcategory STRING,
    
    description STRING,
    
    metadata JSON,
    
    is_verified BOOL DEFAULT FALSE,
    is_locked BOOL DEFAULT FALSE,
    
    created_by STRING,
    verified_by STRING,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY entry_date
CLUSTER BY org_id, location_id, type;

-- =============================================================================
-- SECTION 3: CHAMELEON BRAIN (Data Quality)
-- =============================================================================

CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.data_quality_scores` (
    id STRING NOT NULL,
    org_id STRING NOT NULL,
    location_id STRING NOT NULL,
    
    score FLOAT64 NOT NULL,
    tier STRING NOT NULL,
    
    completeness_score FLOAT64,
    freshness_score FLOAT64,
    consistency_score FLOAT64,
    accuracy_score FLOAT64,
    
    recommendations ARRAY<STRING>,
    
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(calculated_at)
CLUSTER BY org_id, location_id;

-- =============================================================================
-- SECTION 4: META-COGNITIVE LAYER
-- =============================================================================

-- System Knowledge Base
CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.system_knowledge_base` (
    id STRING NOT NULL,
    type STRING NOT NULL,
    title STRING NOT NULL,
    content STRING NOT NULL,
    
    tags ARRAY<STRING>,
    category STRING,
    
    related_entries ARRAY<STRING>,
    
    version STRING DEFAULT '1.0',
    language STRING DEFAULT 'en',
    
    auto_generated BOOL DEFAULT FALSE,
    verified BOOL DEFAULT FALSE,
    
    metadata JSON,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY type, category;

-- Learned Strategies
CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.learned_strategies` (
    id STRING NOT NULL,
    org_id STRING NOT NULL,
    location_id STRING,
    
    type STRING NOT NULL,
    name STRING NOT NULL,
    description STRING,
    
    rule_json JSON NOT NULL,
    
    confidence_score FLOAT64,
    
    learned_from STRING,
    
    is_active BOOL DEFAULT TRUE,
    requires_approval BOOL DEFAULT TRUE,
    approved_by STRING,
    
    metadata JSON,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY org_id, location_id, type;

-- =============================================================================
-- SECTION 5: USER ACTIVITY LOG (DPDP Compliance)
-- =============================================================================

CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.user_activity_log` (
    id STRING NOT NULL,
    user_id STRING NOT NULL,
    org_id STRING NOT NULL,
    
    activity_type STRING NOT NULL,
    activity_description STRING,
    
    ip_address STRING,
    user_agent STRING,
    
    resource_type STRING,
    resource_id STRING,
    
    metadata JSON,
    
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY user_id, org_id;

-- =============================================================================
-- INDEXES & VIEWS
-- =============================================================================

-- View: Daily Revenue by Org/Location (Chameleon-Compatible)
CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.v_daily_revenue` AS
SELECT 
    org_id,
    location_id,
    entry_date,
    SUM(amount) as revenue,
    COUNT(*) as transaction_count
FROM `{PROJECT_ID}.{DATASET_ID}.ledger_universal`
WHERE type = 'SALE'
GROUP BY org_id, location_id, entry_date;

-- View: Daily Expenses by Category
CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.v_daily_expenses` AS
SELECT 
    org_id,
    location_id,
    entry_date,
    category,
    SUM(amount) as total_amount,
    COUNT(*) as expense_count
FROM `{PROJECT_ID}.{DATASET_ID}.ledger_universal`
WHERE type = 'EXPENSE'
GROUP BY org_id, location_id, entry_date, category;

-- View: Profit Summary (Adaptive Strategy Ready)
CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.v_profit_summary` AS
WITH revenue AS (
    SELECT org_id, location_id, entry_date, SUM(amount) as revenue
    FROM `{PROJECT_ID}.{DATASET_ID}.ledger_universal`
    WHERE type = 'SALE'
    GROUP BY org_id, location_id, entry_date
),
expenses AS (
    SELECT org_id, location_id, entry_date, SUM(amount) as expenses
    FROM `{PROJECT_ID}.{DATASET_ID}.ledger_universal`
    WHERE type IN ('EXPENSE', 'PURCHASE')
    GROUP BY org_id, location_id, entry_date
)
SELECT 
    COALESCE(r.org_id, e.org_id) as org_id,
    COALESCE(r.location_id, e.location_id) as location_id,
    COALESCE(r.entry_date, e.entry_date) as entry_date,
    COALESCE(r.revenue, 0) as revenue,
    COALESCE(e.expenses, 0) as expenses,
    COALESCE(r.revenue, 0) - COALESCE(e.expenses, 0) as profit
FROM revenue r
FULL OUTER JOIN expenses e 
    ON r.org_id = e.org_id 
    AND r.location_id = e.location_id 
    AND r.entry_date = e.entry_date;
