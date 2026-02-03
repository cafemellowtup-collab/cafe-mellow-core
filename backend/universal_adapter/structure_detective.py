"""
Structure Detective (Header Hunter)
====================================
Phase 2C: Auto-detect header rows in messy Excel/CSV files.
Phase 2D: Golden Path short-circuit + Deep Scan with Multi-Table Intelligence.

Problem: Many business exports (PetPooja, Tally, etc.) have:
- Logo rows at the top
- Empty rows
- Report title rows
- Summary tables BEFORE detail tables
- THEN the actual data headers

Solution: 
- Golden Path: Check Row 0/1 first for instant success
- Deep Scan: Scan up to Row 500 for complex files
- AI Judge: Resolve ambiguous multi-table scenarios
"""

from typing import List, Optional, Tuple, Dict, Callable
import pandas as pd


class StructureDetective:
    """
    Detects the true header row in messy spreadsheets.
    
    Phase 2D Features:
    - Golden Path: Instant return for clean files (Row 0/1 with high confidence)
    - Deep Scan: Finds headers buried deep in messy files
    - Multi-Table Intelligence: Scores candidates with transactional bonuses
    - AI Judge Integration: Resolves ambiguous cases
    
    Usage:
        detective = StructureDetective()
        header_idx = detective.find_header_row(df)
        if header_idx > 0:
            df = pd.read_excel(file, header=header_idx)
    """
    
    ANCHOR_KEYWORDS = {
        "date", "item", "qty", "quantity", "amount", "total", 
        "bill", "price", "sku", "tax", "invoice", "order",
        "name", "description", "product", "customer", "vendor",
        "rate", "unit", "discount", "net", "gross", "gst",
        "sr", "sno", "sl", "no", "id", "code"
    }
    
    TRANSACTIONAL_KEYWORDS = {"date", "amount", "total", "invoice", "order", "bill"}
    
    MIN_MATCHES_THRESHOLD = 2
    HIGH_CONFIDENCE_THRESHOLD = 3
    DEEP_SCAN_MAX = 500
    
    @classmethod
    def find_header_row(
        cls,
        df: pd.DataFrame,
        max_scan: int = 500,
        ai_judge: Optional[Callable] = None
    ) -> int:
        """
        Find the most likely header row in a DataFrame.
        
        Uses a two-phase approach:
        1. Golden Path: Check Row 0/1 for instant success
        2. Deep Scan: Full scan with enhanced scoring
        
        Args:
            df: DataFrame loaded with header=None (raw data)
            max_scan: Maximum rows to scan (default 500)
            ai_judge: Optional callback for AI disambiguation
            
        Returns:
            int: Index of the header row (0 if no clear header found)
        """
        if df.empty:
            return 0
        
        # ============================================
        # STEP A: Golden Path (Instant Check)
        # ============================================
        # Check Row 0 and Row 1 first - protect simple files
        for row_idx in range(min(2, len(df))):
            score, _ = cls._score_row(df, row_idx)
            if score >= cls.HIGH_CONFIDENCE_THRESHOLD:
                return row_idx
        
        # ============================================
        # STEP B: Deep Scan (For Messy Files)
        # ============================================
        scan_limit = min(max_scan, len(df))
        candidates: List[Tuple[int, int, bool]] = []  # (row_idx, score, has_data_below)
        
        for row_idx in range(scan_limit):
            score, has_transactional = cls._score_row(df, row_idx)
            
            if score >= cls.MIN_MATCHES_THRESHOLD:
                # Check if followed by data (numbers in next row)
                has_data_below = cls._has_data_below(df, row_idx)
                
                # Apply bonuses
                final_score = score
                if has_transactional:
                    final_score += 2  # Transactional indicator bonus
                if has_data_below:
                    final_score += 1  # Data follows bonus
                
                candidates.append((row_idx, final_score, has_data_below))
        
        if not candidates:
            return 0
        
        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Check for ambiguous case (two candidates with similar scores)
        if len(candidates) >= 2 and ai_judge is not None:
            top_score = candidates[0][1]
            second_score = candidates[1][1]
            
            # If scores are within 2 points, use AI to decide
            if abs(top_score - second_score) <= 2:
                ai_choice = cls._invoke_ai_judge(
                    df, 
                    candidates[0][0], 
                    candidates[1][0], 
                    ai_judge
                )
                if ai_choice is not None:
                    return ai_choice
        
        # Return highest scoring candidate
        return candidates[0][0]
    
    @classmethod
    def _score_row(cls, df: pd.DataFrame, row_idx: int) -> Tuple[int, bool]:
        """
        Score a row for header likelihood.
        
        Returns:
            Tuple[int, bool]: (base_score, has_transactional_keywords)
        """
        row_values = df.iloc[row_idx].astype(str).str.lower().tolist()
        
        matches = 0
        has_transactional = False
        matched_keywords = set()
        
        for keyword in cls.ANCHOR_KEYWORDS:
            for cell in row_values:
                cell_clean = cell.strip()
                cell_words = cell_clean.split()
                
                if cell_clean == keyword or keyword in cell_words:
                    matches += 1
                    matched_keywords.add(keyword)
                    break
        
        # Check for transactional keywords (Date + Amount pattern)
        transactional_matches = matched_keywords & cls.TRANSACTIONAL_KEYWORDS
        if len(transactional_matches) >= 2:
            has_transactional = True
        
        return matches, has_transactional
    
    @classmethod
    def _has_data_below(cls, df: pd.DataFrame, row_idx: int) -> bool:
        """
        Check if the row is followed by actual data (numbers).
        """
        if row_idx + 1 >= len(df):
            return False
        
        next_row = df.iloc[row_idx + 1]
        numeric_count = 0
        
        for val in next_row:
            try:
                str_val = str(val).strip()
                if str_val and str_val not in ['nan', 'None', '']:
                    float(str_val.replace(',', ''))
                    numeric_count += 1
            except (ValueError, TypeError):
                pass
        
        # At least one numeric value indicates data row
        return numeric_count >= 1
    
    @classmethod
    def _invoke_ai_judge(
        cls,
        df: pd.DataFrame,
        candidate1_idx: int,
        candidate2_idx: int,
        ai_judge: Callable
    ) -> Optional[int]:
        """
        Invoke AI to decide between two ambiguous header candidates.
        """
        try:
            row1 = df.iloc[candidate1_idx].astype(str).tolist()
            row2 = df.iloc[candidate2_idx].astype(str).tolist()
            
            sample_rows = {
                "candidate1": {"row_idx": candidate1_idx, "headers": row1},
                "candidate2": {"row_idx": candidate2_idx, "headers": row2}
            }
            
            result = ai_judge(sample_rows)
            
            if result == 1:
                return candidate1_idx
            elif result == 2:
                return candidate2_idx
            else:
                return None
                
        except Exception as e:
            print(f"[DETECTIVE] AI Judge failed: {e}")
            return None
    
    @classmethod
    def _count_anchor_matches(cls, row_text: str, row_values: List[str]) -> int:
        """
        Count how many anchor keywords appear in a row.
        (Legacy method for backward compatibility)
        """
        score, _ = cls._score_row_from_values(row_values)
        return score
    
    @classmethod
    def _score_row_from_values(cls, row_values: List[str]) -> Tuple[int, bool]:
        """
        Score a row from pre-extracted values.
        """
        matches = 0
        matched_keywords = set()
        
        for keyword in cls.ANCHOR_KEYWORDS:
            for cell in row_values:
                cell_clean = cell.strip().lower()
                cell_words = cell_clean.split()
                
                if cell_clean == keyword or keyword in cell_words:
                    matches += 1
                    matched_keywords.add(keyword)
                    break
        
        transactional_matches = matched_keywords & cls.TRANSACTIONAL_KEYWORDS
        has_transactional = len(transactional_matches) >= 2
        
        return matches, has_transactional
    
    @classmethod
    def get_all_candidates(
        cls,
        df: pd.DataFrame,
        max_scan: int = 500,
        min_score: int = 2
    ) -> List[Dict]:
        """
        Get all header candidates with their scores.
        Useful for debugging and AI analysis.
        
        Returns:
            List of candidate dictionaries with row_idx, score, headers, etc.
        """
        if df.empty:
            return []
        
        scan_limit = min(max_scan, len(df))
        candidates = []
        
        for row_idx in range(scan_limit):
            score, has_transactional = cls._score_row(df, row_idx)
            
            if score >= min_score:
                has_data_below = cls._has_data_below(df, row_idx)
                final_score = score
                if has_transactional:
                    final_score += 2
                if has_data_below:
                    final_score += 1
                
                candidates.append({
                    "row_idx": row_idx,
                    "base_score": score,
                    "final_score": final_score,
                    "has_transactional": has_transactional,
                    "has_data_below": has_data_below,
                    "headers": df.iloc[row_idx].astype(str).tolist()
                })
        
        candidates.sort(key=lambda x: x["final_score"], reverse=True)
        return candidates
    
    @classmethod
    def analyze_structure(
        cls,
        df: pd.DataFrame,
        max_scan: int = 50
    ) -> dict:
        """
        Analyze the structure of a DataFrame and return detailed info.
        
        Args:
            df: DataFrame loaded with header=None
            max_scan: Maximum rows to scan
            
        Returns:
            dict: Structure analysis results
        """
        header_row = cls.find_header_row(df, max_scan)
        
        result = {
            "header_row": header_row,
            "rows_to_skip": header_row,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "detected_headers": [],
            "confidence": "low"
        }
        
        if header_row >= 0 and header_row < len(df):
            headers = df.iloc[header_row].astype(str).tolist()
            result["detected_headers"] = headers
            
            row_values = [h.lower() for h in headers]
            row_text = " ".join(row_values)
            score = cls._count_anchor_matches(row_text, row_values)
            
            if score >= 5:
                result["confidence"] = "high"
            elif score >= 3:
                result["confidence"] = "medium"
            else:
                result["confidence"] = "low"
        
        return result
