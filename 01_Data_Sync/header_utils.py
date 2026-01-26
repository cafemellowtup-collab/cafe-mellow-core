"""
Header-agnostic column resolution: find columns by keywords regardless of position.
Used by sync_purchases and sync_recipes for Petpooja/Excel variance.
"""
import pandas as pd


def _col_matches(c, keywords):
    if pd.isna(c):
        return False
    s = str(c).strip().lower()
    return any(kw in s for kw in keywords)


def find_col(df, keywords):
    """Return first column name where header matches any keyword. """
    for col in df.columns:
        if _col_matches(col, keywords):
            return col
    return None


def find_col_index(df, keywords):
    """Return first column index (int) where header matches any keyword."""
    for i, col in enumerate(df.columns):
        if _col_matches(col, keywords):
            return i
    return -1


def get_series(df, keywords, default=0):
    """Get a Series for the first matching column; if missing, return Series of default."""
    c = find_col(df, keywords)
    if c is not None:
        return df[c]
    return pd.Series([default] * len(df))


def find_header_row_purchases(df_raw):
    """
    Find row index where we see supplier+invoice (or item+qty+amount). Returns (header_idx, df_with_headers).
    """
    for i, row in df_raw.iterrows():
        row_str = " ".join(str(x) for x in row.values).lower()
        has_supplier = any(k in row_str for k in ["supplier", "vendor"])
        has_invoice = any(k in row_str for k in ["invoice", "inv no", "inv no"])
        has_item = any(k in row_str for k in ["item", "material", "product"])
        has_qty = any(k in row_str for k in ["qty", "quantity"])
        has_amount = any(k in row_str for k in ["amount", "net", "total", "subtotal", "price"])
        if (has_supplier and has_invoice) or (has_item and has_qty and has_amount):
            df_raw = df_raw.copy()
            df_raw.columns = df_raw.iloc[i]
            return i, df_raw.iloc[i + 1:].reset_index(drop=True)
    return None, None


def find_header_row_recipes(df_raw):
    """
    Find row where ItemName/Item and (RawMaterial or Ingredient or Qty) appear. Returns (header_idx, df).
    """
    for i, row in df_raw.iterrows():
        row_str = " ".join(str(x) for x in row.values).lower()
        has_item = any(k in row_str for k in ["itemname", "item name", "product", "menu item", "item"])
        has_ing = any(k in row_str for k in ["rawmaterial", "raw material", "ingredient", "material"])
        has_qty = "qty" in row_str or "quantity" in row_str
        if has_item and (has_ing or has_qty):
            df_raw = df_raw.copy()
            df_raw.columns = df_raw.iloc[i]
            return i, df_raw.iloc[i + 1:].reset_index(drop=True)
    return None, None


def build_purchases_row_agnostic(df, clean_money):
    """
    Build clean purchase rows using header-agnostic column resolution.
    Returns DataFrame with: supplier_name, invoice_date, invoice_number, item_name, qty, unit,
    unit_price, subtotal, tax, discount, net_amount, po_ref, category, sub_category, description.
    """
    def col(*k): return find_col(df, list(k))
    def idx(*k): return find_col_index(df, list(k))
    def ser(*k, d=0): return get_series(df, list(k), d)

    # Required: at least item and an amount-like column
    item_col = col("item", "item name", "material", "product")
    amt_kw = ["amount", "net", "total", "subtotal", "unit price", "price", "rate"]
    has_amt = any(col(a) is not None for a in amt_kw)
    if not item_col or not has_amt:
        return pd.DataFrame()

    clean = pd.DataFrame()
    clean["supplier_name"] = ser("supplier", "vendor", d="")
    clean["invoice_date"] = pd.to_datetime(ser("date", "invoice date", "inv date", d=""), dayfirst=True, errors="coerce").dt.date
    clean["invoice_number"] = ser("invoice", "inv no", "invoice no", "inv number", d="").astype(str)
    clean["item_name"] = df[item_col].astype(str) if item_col else ser("item", "material", d="")
    clean["qty"] = pd.to_numeric(ser("qty", "quantity", d=0), errors="coerce").fillna(0)
    clean["unit"] = ser("unit", "uom", d="")
    clean["unit_price"] = ser("unit price", "price", "rate", "cost", d=0).apply(clean_money)
    clean["subtotal"] = ser("subtotal", "sub total", d=0).apply(clean_money)
    clean["tax"] = ser("tax", "gst", "vat", d=0).apply(clean_money)
    clean["discount"] = ser("discount", d=0).apply(clean_money)
    # Prefer net/total/amount column; else derive from subtotal+tax-discount
    net_col = find_col(df, ["net", "net amount", "total", "amount", "grand total"])
    if net_col:
        clean["net_amount"] = df[net_col].apply(clean_money)
    else:
        clean["net_amount"] = clean["subtotal"] + clean["tax"] - clean["discount"]
    clean["po_ref"] = ser("po", "order", "po ref", "reference", d="").astype(str)
    clean["category"] = ser("category", "group", d="").astype(str)
    clean["sub_category"] = ser("sub category", "subcategory", "sub", d="").astype(str)
    clean["description"] = ser("description", "notes", "remarks", d="").astype(str)

    clean = clean[clean["item_name"].notna() & (clean["item_name"].astype(str).str.lower() != "nan")]
    return clean


def build_recipes_rows_agnostic(df):
    """
    Header-agnostic recipe parsing. Finds ItemName column and the start of 4‑col blocks
    (ingredient, qty, unit, area). Returns DataFrame with parent_item, ingredient_name, qty, unit, area, recipe_type.
    """
    item_col = find_col(df, ["itemname", "item name", "product", "menu item", "item"])
    if not item_col:
        return pd.DataFrame()

    # Find start of ingredient block: first col with raw/ingredient/material
    start = find_col_index(df, ["rawmaterial", "raw material", "ingredient", "material"])
    if start < 0:
        # Fallback: find "qty" or "unit" and assume block starts one or two cols before
        qidx = find_col_index(df, ["qty", "quantity"])
        uidx = find_col_index(df, ["unit", "uom"])
        if qidx >= 0:
            start = max(0, qidx - 1)  # name before qty
        elif uidx >= 0:
            start = max(0, uidx - 2)
        else:
            return pd.DataFrame()

    cols = list(df.columns)
    total = len(cols)
    rows_out = []
    for _, row in df.iterrows():
        item_name = str(row.get(item_col, "") or "").strip()
        if not item_name or item_name.lower() == "nan":
            continue
        i = start
        while i + 3 < total:
            ing = str(row.iloc[i]).strip() if i < len(row) else ""
            qty = row.iloc[i + 1] if i + 1 < len(row) else 0
            unit = str(row.iloc[i + 2]).strip() if i + 2 < len(row) else ""
            area = str(row.iloc[i + 3]).strip() if i + 3 < len(row) else ""
            if ing and ing.lower() != "nan":
                area = "All" if (not area or area.lower() == "nan") else area
                rows_out.append({
                    "parent_item": item_name,
                    "ingredient_name": ing,
                    "qty": pd.to_numeric(qty, errors="coerce") or 0,
                    "unit": unit,
                    "area": area,
                    "recipe_type": "SALES_LINK",
                })
            i += 4
    return pd.DataFrame(rows_out)
