"""
Factory Reset Tool - The Nuke Button
====================================
Phase 6.5: Clears test data while preserving intelligence.

This tool:
- Deletes transactional/test data files
- Preserves learned intelligence (brain_cache, global_rules)
- Re-creates empty placeholder files to prevent crashes
- Provides a clean slate for production deployment
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Files to DELETE (test/transactional data)
FILES_TO_DELETE = [
    "universal_ledger.jsonl",
    "system_evolution_log.json",
    "tenant_configs.json",
    "user_preferences.json",
    "quarantine_queue.json",
]

# Files to KEEP (learned intelligence)
FILES_TO_KEEP = [
    "brain_cache.json",      # Learned semantic mappings
    "global_rules.json",     # Master's rules
]

# Empty file templates for re-creation
EMPTY_TEMPLATES = {
    "universal_ledger.jsonl": "",  # Empty JSONL
    "system_evolution_log.json": "[]",  # Empty array
    "tenant_configs.json": "{}",  # Empty object
    "user_preferences.json": "{}",  # Empty object
    "quarantine_queue.json": "[]",  # Empty array
}


# =============================================================================
# Factory Reset Functions
# =============================================================================

def print_banner():
    """Print the factory reset banner."""
    print("\n" + "=" * 70)
    print("  ████████╗██╗████████╗ █████╗ ███╗   ██╗")
    print("  ╚══██╔══╝██║╚══██╔══╝██╔══██╗████╗  ██║")
    print("     ██║   ██║   ██║   ███████║██╔██╗ ██║")
    print("     ██║   ██║   ██║   ██╔══██║██║╚██╗██║")
    print("     ██║   ██║   ██║   ██║  ██║██║ ╚████║")
    print("     ╚═╝   ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝")
    print("              FACTORY RESET")
    print("=" * 70)


def show_status():
    """Show current data directory status."""
    print("\n📁 DATA DIRECTORY STATUS")
    print("-" * 50)
    
    if not DATA_DIR.exists():
        print(f"  ⚠️  Data directory does not exist: {DATA_DIR}")
        return
    
    print(f"  Location: {DATA_DIR}\n")
    
    # Files to delete
    print("  🗑️  FILES TO DELETE (Test Data):")
    for filename in FILES_TO_DELETE:
        filepath = DATA_DIR / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"      ✓ {filename} ({size:,} bytes)")
        else:
            print(f"      ○ {filename} (not found)")
    
    # Files to keep
    print("\n  🧠 FILES TO KEEP (Intelligence):")
    for filename in FILES_TO_KEEP:
        filepath = DATA_DIR / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"      ✓ {filename} ({size:,} bytes) - PRESERVED")
        else:
            print(f"      ○ {filename} (not found)")
    
    print()


def delete_files():
    """Delete test data files."""
    deleted = []
    skipped = []
    
    for filename in FILES_TO_DELETE:
        filepath = DATA_DIR / filename
        if filepath.exists():
            try:
                os.remove(filepath)
                deleted.append(filename)
                print(f"  🗑️  Deleted: {filename}")
            except Exception as e:
                print(f"  ❌ Error deleting {filename}: {e}")
                skipped.append(filename)
        else:
            skipped.append(filename)
    
    return deleted, skipped


def recreate_placeholders():
    """Re-create empty placeholder files."""
    created = []
    
    for filename, content in EMPTY_TEMPLATES.items():
        filepath = DATA_DIR / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            created.append(filename)
            print(f"  📄 Created: {filename}")
        except Exception as e:
            print(f"  ❌ Error creating {filename}: {e}")
    
    return created


def verify_intelligence():
    """Verify intelligence files are intact."""
    print("\n🧠 VERIFYING INTELLIGENCE FILES")
    print("-" * 50)
    
    all_intact = True
    for filename in FILES_TO_KEEP:
        filepath = DATA_DIR / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  ✅ {filename} - INTACT ({size:,} bytes)")
        else:
            print(f"  ⚠️  {filename} - NOT FOUND (will be created on first use)")
            all_intact = False
    
    return all_intact


def factory_reset(force: bool = False):
    """
    Execute factory reset.
    
    Args:
        force: If True, skip confirmation prompt
    """
    print_banner()
    show_status()
    
    # Confirmation
    if not force:
        print("⚠️  WARNING: This will delete all test/transactional data!")
        print("   Intelligence files (brain_cache, global_rules) will be preserved.\n")
        
        confirmation = input("   Type 'RESET' to confirm: ").strip()
        
        if confirmation != "RESET":
            print("\n❌ Reset cancelled. No files were modified.")
            return False
    
    print("\n" + "=" * 50)
    print("🚀 EXECUTING FACTORY RESET")
    print("=" * 50)
    
    # Step 1: Delete files
    print("\n📤 DELETING TEST DATA...")
    deleted, skipped = delete_files()
    
    # Step 2: Re-create placeholders
    print("\n📥 CREATING EMPTY PLACEHOLDERS...")
    created = recreate_placeholders()
    
    # Step 3: Verify intelligence
    verify_intelligence()
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ FACTORY RESET COMPLETE")
    print("=" * 70)
    print(f"""
   📊 SUMMARY
   ─────────────────────────────────
   Files Deleted:  {len(deleted)}
   Files Created:  {len(created)}
   Intelligence:   PRESERVED
   
   🎯 System Clean. Intelligence Preserved. Ready for Production.
   
   Next Steps:
   1. Start the API server: uvicorn api.main:app --reload
   2. Ingest fresh data via /api/v1/adapter/ingest
   3. The Semantic Brain will use preserved learnings
""")
    
    return True


def quick_reset():
    """Quick reset without banner (for scripts)."""
    print("[FACTORY RESET] Starting quick reset...")
    
    # Delete
    for filename in FILES_TO_DELETE:
        filepath = DATA_DIR / filename
        if filepath.exists():
            os.remove(filepath)
            print(f"  Deleted: {filename}")
    
    # Recreate
    for filename, content in EMPTY_TEMPLATES.items():
        filepath = DATA_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Created: {filename}")
    
    print("[FACTORY RESET] Complete. Intelligence preserved.")
    return True


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="TITAN Factory Reset - Clear test data, preserve intelligence"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick reset without banner (for scripts)"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show status only, don't reset"
    )
    
    args = parser.parse_args()
    
    if args.status:
        print_banner()
        show_status()
        verify_intelligence()
        return
    
    if args.quick:
        quick_reset()
    else:
        factory_reset(force=args.force)


if __name__ == "__main__":
    main()
