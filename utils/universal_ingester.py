"""
Universal Ingester: Multi-Modal ETL Pipeline for Excel, CSV, PDF, and Images
Hybrid parser: First 50 rows to LLM for schema mapping, rest with Pandas
"""
import os
import io
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from google.cloud import bigquery
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import base64

class UniversalIngester:
    """
    Multi-modal data ingester with AI-powered schema mapping.
    Supports: Excel (.xlsx, .xls), CSV, PDF, Images (via Gemini Vision)
    """
    
    def __init__(self, settings, bq_client: bigquery.Client):
        self.settings = settings
        self.bq_client = bq_client
        self.gemini_api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.project_id = getattr(settings, "PROJECT_ID", "")
        self.dataset_id = getattr(settings, "DATASET_ID", "")
        
        # Initialize Drive API
        key_file = getattr(settings, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        self.credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
    
    def get_service_account_email(self) -> str:
        """Return the service account email for Drive sharing instructions"""
        return self.credentials.service_account_email
    
    def ingest_from_folder(
        self, 
        folder_id: str, 
        master_category: str,
        sub_tag: Optional[str] = None,
        archive_folder_id: Optional[str] = None,
        failed_folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest all files from a Google Drive folder.
        
        Args:
            folder_id: Google Drive folder ID
            master_category: Category for all files (e.g., "expenses", "sales", "inventory")
            sub_tag: Optional sub-categorization
            archive_folder_id: Folder to move successfully processed files
            failed_folder_id: Folder to move failed files
        
        Returns:
            Summary with success/failure counts
        """
        results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "files": []
        }
        
        try:
            # List all files in folder
            query = f"'{folder_id}' in parents and trashed=false"
            response = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime)",
                pageSize=100
            ).execute()
            
            files = response.get('files', [])
            results["total"] = len(files)
            
            for file_info in files:
                file_id = file_info['id']
                file_name = file_info['name']
                mime_type = file_info['mimeType']
                
                try:
                    # Process file based on type
                    if self._is_spreadsheet(mime_type, file_name):
                        self._process_spreadsheet(file_id, file_name, master_category, sub_tag)
                    elif self._is_pdf(mime_type, file_name):
                        self._process_pdf(file_id, file_name, master_category, sub_tag)
                    elif self._is_image(mime_type, file_name):
                        self._process_image(file_id, file_name, master_category, sub_tag)
                    else:
                        raise ValueError(f"Unsupported file type: {mime_type}")
                    
                    results["success"] += 1
                    results["files"].append({
                        "name": file_name,
                        "status": "success",
                        "category": master_category
                    })
                    
                    # Move to archive folder if specified
                    if archive_folder_id:
                        self._move_file(file_id, folder_id, archive_folder_id)
                    
                except Exception as e:
                    results["failed"] += 1
                    results["files"].append({
                        "name": file_name,
                        "status": "failed",
                        "error": str(e)
                    })
                    
                    # Move to failed folder if specified
                    if failed_folder_id:
                        self._move_file(file_id, folder_id, failed_folder_id)
            
            return results
            
        except Exception as e:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "error": str(e)
            }
    
    def _is_spreadsheet(self, mime_type: str, filename: str) -> bool:
        """Check if file is a spreadsheet"""
        spreadsheet_mimes = [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv',
            'application/vnd.google-apps.spreadsheet'
        ]
        spreadsheet_exts = ['.xlsx', '.xls', '.csv']
        
        return mime_type in spreadsheet_mimes or any(filename.lower().endswith(ext) for ext in spreadsheet_exts)
    
    def _is_pdf(self, mime_type: str, filename: str) -> bool:
        """Check if file is a PDF"""
        return mime_type == 'application/pdf' or filename.lower().endswith('.pdf')
    
    def _is_image(self, mime_type: str, filename: str) -> bool:
        """Check if file is an image"""
        image_mimes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        return mime_type in image_mimes or any(filename.lower().endswith(ext) for ext in image_exts)
    
    def _process_spreadsheet(
        self, 
        file_id: str, 
        filename: str, 
        master_category: str,
        sub_tag: Optional[str]
    ):
        """
        Process Excel/CSV with hybrid approach:
        1. Send first 50 rows to LLM for schema mapping
        2. Parse rest with Pandas using mapped schema
        """
        # Download file
        request = self.drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file_buffer.seek(0)
        
        # Read with pandas
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(file_buffer)
        else:
            df = pd.read_excel(file_buffer)
        
        # Drop completely empty rows
        df = df.dropna(how='all')
        
        if df.empty:
            raise ValueError("File is empty after removing blank rows")
        
        # HYBRID PARSER: Send first 50 rows to LLM for schema mapping
        sample_df = df.head(50)
        schema_mapping = self._ai_schema_mapper(sample_df, master_category, filename)
        
        # Apply schema mapping to full dataset
        df_mapped = self._apply_schema_mapping(df, schema_mapping)
        
        # Add metadata
        df_mapped['_source_file'] = filename
        df_mapped['_ingested_at'] = datetime.now()
        df_mapped['_master_category'] = master_category
        if sub_tag:
            df_mapped['_sub_tag'] = sub_tag
        
        # Insert into BigQuery
        table_name = self._get_table_name(master_category)
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        # Create table if not exists (with schema from mapping)
        self._ensure_table_exists(table_id, schema_mapping)
        
        # Insert data
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        job = self.bq_client.load_table_from_dataframe(df_mapped, table_id, job_config=job_config)
        job.result()
    
    def _process_pdf(
        self, 
        file_id: str, 
        filename: str, 
        master_category: str,
        sub_tag: Optional[str]
    ):
        """
        Process PDF using Gemini Vision to extract tables.
        Convert PDF pages to images and use Vision API.
        """
        # Download PDF
        request = self.drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file_buffer.seek(0)
        
        # Convert PDF to images (requires pdf2image library)
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(file_buffer.read(), dpi=200, fmt='jpeg')
        except ImportError:
            raise ImportError("pdf2image library required for PDF processing. Install: pip install pdf2image")
        
        # Process each page with Vision API
        all_extracted_data = []
        for idx, image in enumerate(images):
            extracted_data = self._vision_extract_table(image, master_category, filename, page=idx+1)
            if extracted_data:
                all_extracted_data.extend(extracted_data)
        
        if not all_extracted_data:
            raise ValueError("No data extracted from PDF")
        
        # Convert to DataFrame and insert
        df = pd.DataFrame(all_extracted_data)
        df['_source_file'] = filename
        df['_ingested_at'] = datetime.now()
        df['_master_category'] = master_category
        if sub_tag:
            df['_sub_tag'] = sub_tag
        
        table_name = self._get_table_name(master_category)
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
    
    def _process_image(
        self, 
        file_id: str, 
        filename: str, 
        master_category: str,
        sub_tag: Optional[str]
    ):
        """Process image using Gemini Vision"""
        # Download image
        request = self.drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file_buffer.seek(0)
        
        # Process with Vision API
        from PIL import Image
        image = Image.open(file_buffer)
        extracted_data = self._vision_extract_table(image, master_category, filename)
        
        if not extracted_data:
            raise ValueError("No data extracted from image")
        
        # Convert to DataFrame and insert
        df = pd.DataFrame(extracted_data)
        df['_source_file'] = filename
        df['_ingested_at'] = datetime.now()
        df['_master_category'] = master_category
        if sub_tag:
            df['_sub_tag'] = sub_tag
        
        table_name = self._get_table_name(master_category)
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
    
    def _ai_schema_mapper(self, sample_df: pd.DataFrame, category: str, filename: str) -> Dict[str, Any]:
        """
        Use Gemini to intelligently map columns to standard schema.
        Returns mapping of original columns to target schema.
        """
        import requests
        
        # Get sample data as string
        sample_str = sample_df.head(10).to_string()
        
        prompt = f"""You are a data schema mapper for a restaurant ERP system.

File: {filename}
Category: {category}

Sample Data (first 10 rows):
{sample_str}

Task: Map the columns to a standardized schema. Return ONLY a JSON object with this structure:
{{
    "column_mapping": {{
        "original_column_name": "standard_field_name"
    }},
    "data_types": {{
        "standard_field_name": "string|float|date|integer"
    }}
}}

Standard fields by category:
- expenses: date, item_name, amount, category, vendor, payment_mode
- sales: date, item_name, quantity, price, total, customer
- inventory: date, item_name, quantity, unit, cost
- purchases: date, item_name, quantity, unit_cost, vendor

Return ONLY the JSON, no explanation."""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024}
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            text = data['candidates'][0]['content']['parts'][0]['text']
            # Extract JSON from response
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            return json.loads(text)
        else:
            # Fallback: Use column names as-is
            return {
                "column_mapping": {col: col.lower().replace(" ", "_") for col in sample_df.columns},
                "data_types": {col.lower().replace(" ", "_"): "string" for col in sample_df.columns}
            }
    
    def _apply_schema_mapping(self, df: pd.DataFrame, schema_mapping: Dict[str, Any]) -> pd.DataFrame:
        """Apply the AI-generated schema mapping to the full dataset"""
        column_mapping = schema_mapping.get("column_mapping", {})
        data_types = schema_mapping.get("data_types", {})
        
        # Rename columns
        df_renamed = df.rename(columns=column_mapping)
        
        # Apply data types
        for col, dtype in data_types.items():
            if col in df_renamed.columns:
                try:
                    if dtype == "float":
                        df_renamed[col] = pd.to_numeric(df_renamed[col], errors='coerce')
                    elif dtype == "integer":
                        df_renamed[col] = pd.to_numeric(df_renamed[col], errors='coerce').astype('Int64')
                    elif dtype == "date":
                        df_renamed[col] = pd.to_datetime(df_renamed[col], errors='coerce')
                except:
                    pass  # Keep original if conversion fails
        
        return df_renamed
    
    def _vision_extract_table(self, image, category: str, filename: str, page: int = 1) -> List[Dict]:
        """Use Gemini Vision to extract table data from image"""
        import requests
        
        # Convert image to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        image_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        prompt = f"""Extract ALL data from this table/document image.

Category: {category}
File: {filename}, Page: {page}

Return a JSON array of objects, where each object represents a row.
Example: [{{"date": "2024-01-15", "item": "Coffee", "amount": "150"}}, ...]

Return ONLY the JSON array, no explanation."""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}
                ]
            }],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048}
        }
        
        response = requests.post(url, json=payload, timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            text = data['candidates'][0]['content']['parts'][0]['text']
            # Extract JSON
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            return json.loads(text)
        
        return []
    
    def _get_table_name(self, master_category: str) -> str:
        """Get target table name based on category"""
        category_tables = {
            "expenses": "expenses_master",
            "sales": "sales_universal_ingested",
            "inventory": "inventory_universal",
            "purchases": "purchases_master",
            "wastage": "wastage_log",
        }
        
        return category_tables.get(master_category.lower(), f"{master_category.lower()}_ingested")
    
    def _ensure_table_exists(self, table_id: str, schema_mapping: Dict[str, Any]):
        """Ensure target table exists with proper schema"""
        try:
            self.bq_client.get_table(table_id)
        except:
            # Create table with schema
            data_types = schema_mapping.get("data_types", {})
            
            bq_schema = []
            for field, dtype in data_types.items():
                bq_type = "STRING"
                if dtype == "float":
                    bq_type = "FLOAT64"
                elif dtype == "integer":
                    bq_type = "INT64"
                elif dtype == "date":
                    bq_type = "DATE"
                
                bq_schema.append(bigquery.SchemaField(field, bq_type, mode="NULLABLE"))
            
            # Add metadata fields
            bq_schema.extend([
                bigquery.SchemaField("_source_file", "STRING"),
                bigquery.SchemaField("_ingested_at", "TIMESTAMP"),
                bigquery.SchemaField("_master_category", "STRING"),
                bigquery.SchemaField("_sub_tag", "STRING"),
            ])
            
            table = bigquery.Table(table_id, schema=bq_schema)
            self.bq_client.create_table(table)
    
    def _move_file(self, file_id: str, source_folder_id: str, target_folder_id: str):
        """Move file from source folder to target folder"""
        try:
            # Remove from source parent
            self.drive_service.files().update(
                fileId=file_id,
                addParents=target_folder_id,
                removeParents=source_folder_id,
                fields='id, parents'
            ).execute()
        except Exception as e:
            print(f"Failed to move file {file_id}: {e}")
