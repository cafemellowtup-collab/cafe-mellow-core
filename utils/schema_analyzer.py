"""
Comprehensive BigQuery Schema Analyzer
Fetches all tables, columns, and sample data for AI analysis
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import pandas as pd
import json
import settings

def analyze_all_tables(client, settings):
    """Analyze all tables in the dataset"""
    results = {
        'tables': {},
        'summary': {}
    }
    
    dataset_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}"
    
    try:
        dataset = client.get_dataset(dataset_id)
        tables = list(client.list_tables(dataset))
        
        print(f"Found {len(tables)} tables in {dataset_id}")
        
        for table_ref in tables:
            table_id = f"{dataset_id}.{table_ref.table_id}"
            table_name = table_ref.table_id
            
            try:
                table = client.get_table(table_id)
                
                # Get schema
                schema_info = []
                for field in table.schema:
                    schema_info.append({
                        'name': field.name,
                        'type': field.field_type,
                        'mode': field.mode or 'NULLABLE',
                        'description': field.description or ''
                    })
                
                # Get row count
                count_query = f"SELECT COUNT(*) as cnt FROM `{table_id}`"
                count_result = client.query(count_query).result()
                row_count = list(count_result)[0].cnt
                
                # Get sample data (first 5 rows)
                sample_query = f"SELECT * FROM `{table_id}` LIMIT 5"
                try:
                    sample_df = client.query(sample_query).to_dataframe()
                    sample_data = sample_df.to_dict('records') if not sample_df.empty else []
                except Exception as e:
                    sample_data = []
                    print(f"Error getting sample for {table_name}: {e}")
                
                # Get column statistics for numeric columns
                stats = {}
                numeric_cols = [f.name for f in table.schema if f.field_type in ['INTEGER', 'FLOAT', 'NUMERIC']]
                if numeric_cols and row_count > 0:
                    for col in numeric_cols[:5]:  # Limit to 5 columns
                        try:
                            stat_query = f"""
                                SELECT 
                                    MIN({col}) as min_val,
                                    MAX({col}) as max_val,
                                    AVG({col}) as avg_val,
                                    COUNT(*) as count_val
                                FROM `{table_id}`
                                WHERE {col} IS NOT NULL
                            """
                            stat_df = client.query(stat_query).to_dataframe()
                            if not stat_df.empty:
                                stats[col] = stat_df.iloc[0].to_dict()
                        except:
                            pass
                
                results['tables'][table_name] = {
                    'schema': schema_info,
                    'row_count': row_count,
                    'sample_data': sample_data,
                    'statistics': stats,
                    'size_bytes': table.num_bytes if hasattr(table, 'num_bytes') else 0
                }
                
                print(f"[OK] Analyzed {table_name}: {row_count} rows, {len(schema_info)} columns")
                
            except Exception as e:
                print(f"[ERROR] Error analyzing {table_name}: {e}")
                results['tables'][table_name] = {'error': str(e)}
        
        # Create summary
        results['summary'] = {
            'total_tables': len(tables),
            'total_columns': sum(len(t['schema']) for t in results['tables'].values() if 'schema' in t),
            'total_rows': sum(t.get('row_count', 0) for t in results['tables'].values())
        }
        
    except Exception as e:
        print(f"Error accessing dataset: {e}")
        results['error'] = str(e)
    
    return results

def get_schema_summary(client, settings):
    """Get a concise schema summary for AI"""
    analysis = analyze_all_tables(client, settings)
    
    summary_text = "BIGQUERY DATABASE SCHEMA:\n"
    summary_text += "=" * 60 + "\n\n"
    
    for table_name, table_info in analysis['tables'].items():
        if 'error' in table_info:
            continue
            
        summary_text += f"TABLE: {table_name}\n"
        summary_text += f"  Rows: {table_info.get('row_count', 0)}\n"
        summary_text += f"  Columns:\n"
        
        for col in table_info.get('schema', []):
            summary_text += f"    - {col['name']} ({col['type']}): {col.get('description', 'No description')}\n"
        
        summary_text += "\n"
    
    return summary_text, analysis

if __name__ == "__main__":
    from google.cloud import bigquery
    import settings
    
    client = bigquery.Client.from_service_account_json(settings.KEY_FILE)
    results = analyze_all_tables(client, settings)
    
    # Save to file
    with open('schema_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n" + "="*60)
    print("Schema analysis complete!")
    print(f"Total tables: {results['summary'].get('total_tables', 0)}")
    print(f"Total columns: {results['summary'].get('total_columns', 0)}")
    print(f"Total rows: {results['summary'].get('total_rows', 0)}")
    print("\nResults saved to schema_analysis.json")
