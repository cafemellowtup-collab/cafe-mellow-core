"""
CAFE_AI Startup Script - Runs all necessary scripts to make the app live
"""
import sys
import os
import subprocess

# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def run_script(script_path, description):
    """Run a Python script and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Script: {script_path}")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.getcwd(),
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print(f"\n[SUCCESS] {description} completed successfully!")
            return True
        else:
            print(f"\n[ERROR] {description} failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"\n[ERROR] Failed to run {description}: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("CAFE_AI STARTUP - Making the app live")
    print("="*60)
    
    scripts = [
        ("04_Intelligence_Lab/titan_dna.py", "Generate System DNA"),
        ("01_Data_Sync/sync_sales_raw.py", "Sync Sales Data (Raw)"),
        ("01_Data_Sync/titan_sales_parser.py", "Parse Sales Data"),
        ("04_Intelligence_Lab/sentinel_hub.py", "Run Intelligence Scan"),
    ]
    
    # Optional scripts (may fail if dependencies missing)
    optional_scripts = [
        ("01_Data_Sync/sync_expenses.py", "Sync Expenses"),
        ("01_Data_Sync/sync_recipes.py", "Sync Recipes"),
    ]
    
    results = []
    
    # Run required scripts
    for script_path, description in scripts:
        success = run_script(script_path, description)
        results.append((description, success))
    
    # Run optional scripts
    print("\n" + "="*60)
    print("Running Optional Scripts (may require additional setup)")
    print("="*60)
    
    for script_path, description in optional_scripts:
        success = run_script(script_path, description)
        results.append((description, success))
    
    # Summary
    print("\n" + "="*60)
    print("STARTUP SUMMARY")
    print("="*60)
    
    for description, success in results:
        status = "[OK]" if success else "[FAILED]"
        print(f"{status} {description}")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("1. Launch dashboard: streamlit run titan_app.py")
    print("2. Check BigQuery tables to verify data")
    print("3. Review ai_task_queue for alerts")
    print("="*60)

if __name__ == "__main__":
    main()
