import os
import sys

# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def fast_pulse():
    print("\n" + "="*50)
    print("TITAN DNA PULSE: FAST FILE SCAN")
    print("="*50)
    
    # 1. Path Identity
    root_path = os.getcwd()
    print(f"📍 ROOT: {root_path}")
    
    # 2. Scanning for the "DNA" (Settings & Keys)
    essentials = ['settings.py', 'service-key.json', '.env']
    print("\nCORE ASSETS:")
    for e in essentials:
        status = "[OK] Found" if os.path.exists(e) else "[MISSING]"
        print(f" - {e:<20}: {status}")
    
    # 3. ROOT FILE LIST (The "Mess" Audit)
    print("\nFILES CURRENTLY IN ROOT (Potential Mess):")
    all_items = os.listdir('.')
    for item in all_items:
        if os.path.isfile(item):
            # Get file size to see if it's a script or data
            size = os.path.getsize(item) / 1024
            print(f" - [FILE] {item:<30} ({size:.1f} KB)")
        else:
            print(f" - [DIR]  {item}")

    print("\n" + "="*50)
    print("ACTION: Copy and paste this list to Gemini.")

if __name__ == "__main__":
    fast_pulse()