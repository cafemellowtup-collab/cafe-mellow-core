# TITAN Master Dashboard Setup Guide

## Required Configuration Fields

### 1. **System Configuration**
```json
{
  "project_id": "cafe-mellow-core-2026",
  "dataset_id": "cafe_operations", 
  "environment": "production",
  "api_version": "v1"
}
```

### 2. **Tenant Creation (Required Fields)**
- **Name**: Business name (e.g., "Cafe Mellow Tiruppur")
- **Email**: Owner email (e.g., "owner@cafemellow.com") 
- **Phone**: Contact number
- **Plan**: free/pro/enterprise
- **Location**: Business address
- **Timezone**: "Asia/Kolkata"

### 3. **Tenant Credentials (Per Tenant)**
```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY",
  "petpooja_app_key": "YOUR_PETPOOJA_KEY", 
  "petpooja_app_secret": "YOUR_PETPOOJA_SECRET",
  "drive_folder_expenses": "Google_Drive_Folder_ID",
  "drive_folder_purchases": "Google_Drive_Folder_ID",
  "bigquery_dataset": "tenant_specific_dataset"
}
```

### 4. **Feature Flags (Per Plan)**
- **Free Plan**: Basic dashboard, reports, chat (50 AI calls/day)
- **Pro Plan**: Advanced reports, API access, tasks (500 AI calls/day) 
- **Enterprise**: All features, multi-location, custom branding (5000 AI calls/day)

## Master Dashboard Functions

### **Tenant Management**
- Create/Update/Suspend tenants
- Monitor usage and costs
- Manage feature access
- Health monitoring

### **System Monitoring** 
- Overall system health
- Cost breakdown across tenants
- Usage analytics
- Performance metrics

### **AI Insights**
- Tenant behavior analysis
- Churn prediction
- Growth opportunities  
- Automated recommendations

## Database Tables Created
- `tenant_registry` - Tenant information
- `tenant_usage` - Usage tracking
- `tenant_features` - Feature overrides
- `health_alerts` - System alerts
- `ai_insights` - AI recommendations
