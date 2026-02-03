"""
Phase 2D Verification: Structure Detective Upgrades
====================================================
Tests:
1. Golden Path - Simple file returns Row 0 instantly
2. Golden Path - Row 1 header detection
3. Deep Scan - Messy file with logo rows
4. Deep Scan - Header buried at Row 200
5. Multi-Table - Summary vs Detail scoring
"""

import sys
import io

# Windows console encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import pandas as pd

sys.path.insert(0, r"c:\Users\USER\OneDrive\Desktop\Cafe_AI")

from backend.universal_adapter.structure_detective import StructureDetective

def test_golden_path_row0():
    """TEST 1: Simple file with header at Row 0 - should return instantly"""
    print("\n" + "=" * 60)
    print("TEST 1: Golden Path - Header at Row 0")
    print("=" * 60)
    
    csv_data = """Date,Item,Qty,Amount
2024-01-15,Coffee,5,250
2024-01-16,Tea,3,150
2024-01-17,Sandwich,2,400"""
    
    df = pd.read_csv(io.StringIO(csv_data), header=None)
    idx = StructureDetective.find_header_row(df)
    
    print(f"Input: Clean CSV with header at Row 0")
    print(f"Result: Header detected at Row {idx}")
    
    if idx == 0:
        print("✅ PASS: Golden Path short-circuited at Row 0!")
        return True
    else:
        print(f"❌ FAIL: Expected Row 0, got Row {idx}")
        return False


def test_golden_path_row1():
    """TEST 2: File with header at Row 1 - should detect quickly"""
    print("\n" + "=" * 60)
    print("TEST 2: Golden Path - Header at Row 1")
    print("=" * 60)
    
    csv_data = """Report Title,,,
Date,Item,Qty,Amount
2024-01-15,Coffee,5,250
2024-01-16,Tea,3,150"""
    
    df = pd.read_csv(io.StringIO(csv_data), header=None)
    idx = StructureDetective.find_header_row(df)
    
    print(f"Input: CSV with title row, header at Row 1")
    print(f"Result: Header detected at Row {idx}")
    
    if idx == 1:
        print("✅ PASS: Golden Path detected header at Row 1!")
        return True
    else:
        print(f"❌ FAIL: Expected Row 1, got Row {idx}")
        return False


def test_deep_scan_logo_rows():
    """TEST 3: Messy file with logo/title rows"""
    print("\n" + "=" * 60)
    print("TEST 3: Deep Scan - Logo/Title Rows")
    print("=" * 60)
    
    csv_data = """Company Logo,,,
PetPooja Export,,,
Generated: 2024-01-30,,,
,,,
Date,Item,Qty,Amount
2024-01-15,Coffee,5,250
2024-01-16,Tea,3,150"""
    
    df = pd.read_csv(io.StringIO(csv_data), header=None)
    idx = StructureDetective.find_header_row(df)
    
    print(f"Input: CSV with 4 junk rows before header")
    print(f"Result: Header detected at Row {idx}")
    
    if idx == 4:
        print("✅ PASS: Deep Scan found header at Row 4!")
        return True
    else:
        print(f"❌ FAIL: Expected Row 4, got Row {idx}")
        return False


def test_deep_scan_buried_header():
    """TEST 4: Header buried deep in file"""
    print("\n" + "=" * 60)
    print("TEST 4: Deep Scan - Header at Row 50")
    print("=" * 60)
    
    # Create 50 junk rows
    rows = ["Junk Row,,,"] * 50
    rows.append("Date,Item,Qty,Amount,Invoice,Total")
    rows.append("2024-01-15,Coffee,5,250,INV001,1250")
    rows.append("2024-01-16,Tea,3,150,INV002,450")
    
    csv_data = "\n".join(rows)
    df = pd.read_csv(io.StringIO(csv_data), header=None)
    idx = StructureDetective.find_header_row(df)
    
    print(f"Input: CSV with 50 junk rows, header at Row 50")
    print(f"Result: Header detected at Row {idx}")
    
    if idx == 50:
        print("✅ PASS: Deep Scan found buried header at Row 50!")
        return True
    else:
        print(f"❌ FAIL: Expected Row 50, got Row {idx}")
        return False


def test_transactional_bonus():
    """TEST 5: Transactional keywords get bonus scoring"""
    print("\n" + "=" * 60)
    print("TEST 5: Transactional Bonus Scoring")
    print("=" * 60)
    
    # Row 2 has transactional keywords (Date + Amount + Invoice)
    # Row 5 has generic keywords (Name + Code)
    csv_data = """Title,,,,,
Summary,,,,,
Category,Name,Code,Count
Cat1,Item1,C001,10
,,,
Date,Item,Qty,Amount,Invoice,Total
2024-01-15,Coffee,5,250,INV001,1250"""
    
    df = pd.read_csv(io.StringIO(csv_data), header=None)
    candidates = StructureDetective.get_all_candidates(df)
    
    print("Candidates found:")
    for c in candidates[:3]:
        print(f"  Row {c['row_idx']}: base={c['base_score']}, final={c['final_score']}, trans={c['has_transactional']}")
    
    idx = StructureDetective.find_header_row(df)
    print(f"Result: Header detected at Row {idx}")
    
    # Row 5 should win due to transactional bonus
    if idx == 5:
        print("✅ PASS: Transactional header (Row 5) scored higher!")
        return True
    else:
        print(f"❌ FAIL: Expected Row 5 (transactional), got Row {idx}")
        return False


def test_data_below_bonus():
    """TEST 6: Rows followed by data get bonus"""
    print("\n" + "=" * 60)
    print("TEST 6: Data-Below Bonus Scoring")
    print("=" * 60)
    
    csv_data = """Title,,,
Date,Item,Amount
2024-01-15,Coffee,250
2024-01-16,Tea,150"""
    
    df = pd.read_csv(io.StringIO(csv_data), header=None)
    candidates = StructureDetective.get_all_candidates(df, min_score=2)
    
    print("Candidates found:")
    for c in candidates:
        print(f"  Row {c['row_idx']}: base={c['base_score']}, final={c['final_score']}, data_below={c['has_data_below']}")
    
    # Check that the header row has data_below=True
    header_candidate = next((c for c in candidates if c['row_idx'] == 1), None)
    if header_candidate and header_candidate['has_data_below']:
        print("✅ PASS: Header row correctly detected data below!")
        return True
    else:
        print("❌ FAIL: Data-below detection failed")
        return False


def main():
    print("#" * 70)
    print("#  PHASE 2D VERIFICATION: Structure Detective Upgrades")
    print("#" * 70)
    
    results = []
    results.append(("Golden Path Row 0", test_golden_path_row0()))
    results.append(("Golden Path Row 1", test_golden_path_row1()))
    results.append(("Deep Scan Logo Rows", test_deep_scan_logo_rows()))
    results.append(("Deep Scan Buried Header", test_deep_scan_buried_header()))
    results.append(("Transactional Bonus", test_transactional_bonus()))
    results.append(("Data Below Bonus", test_data_below_bonus()))
    
    print("\n" + "=" * 70)
    print("PHASE 2D SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {name}")
    
    print("-" * 70)
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL PHASE 2D TESTS PASSED! No regression risk detected.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review required.")
    
    print("=" * 70)
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
