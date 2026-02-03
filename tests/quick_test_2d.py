import sys
sys.path.insert(0, r"c:\Users\USER\OneDrive\Desktop\Cafe_AI")
import pandas as pd
import io
from backend.universal_adapter.structure_detective import StructureDetective

# Test 1: Golden Path Row 0
df1 = pd.read_csv(io.StringIO("Date,Item,Qty,Amount\n2024-01-15,Coffee,5,250"), header=None)
r1 = StructureDetective.find_header_row(df1)
print(f"Test 1 (Row 0): {r1} - {'PASS' if r1==0 else 'FAIL'}")

# Test 2: Row 1
df2 = pd.read_csv(io.StringIO("Title,,,\nDate,Item,Qty,Amount\n2024-01-15,Coffee,5,250"), header=None)
r2 = StructureDetective.find_header_row(df2)
print(f"Test 2 (Row 1): {r2} - {'PASS' if r2==1 else 'FAIL'}")

# Test 3: Deep Scan Row 4
df3 = pd.read_csv(io.StringIO("Logo,,,\nTitle,,,\nGen,,,\n,,,\nDate,Item,Qty,Amount\n2024-01-15,Coffee,5,250"), header=None)
r3 = StructureDetective.find_header_row(df3)
print(f"Test 3 (Row 4): {r3} - {'PASS' if r3==4 else 'FAIL'}")

# Test 4: Buried header
rows = ["Junk,,,"] * 50 + ["Date,Item,Qty,Amount\n2024-01-15,Coffee,5,250"]
df4 = pd.read_csv(io.StringIO("\n".join(rows)), header=None)
r4 = StructureDetective.find_header_row(df4)
print(f"Test 4 (Row 50): {r4} - {'PASS' if r4==50 else 'FAIL'}")

passed = sum([r1==0, r2==1, r3==4, r4==50])
print(f"\nTotal: {passed}/4 passed")
