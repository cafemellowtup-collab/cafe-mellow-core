"""
Performance Optimizer - Caching, Lazy Loading, Query Optimization
"""
import streamlit as st
from functools import lru_cache
import time
from datetime import datetime, timedelta
from google.cloud import bigquery
import settings

class PerformanceOptimizer:
    """Optimize app performance with caching and lazy loading"""
    
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
        self.cache_ttl = 300  # 5 minutes
    
    @staticmethod
    def cache_key(table_name, query_params):
        """Generate cache key"""
        return f"{table_name}_{hash(str(query_params))}"
    
    def get_cached_query(self, cache_key, query_func, *args, **kwargs):
        """Get query result from cache or execute"""
        if cache_key not in st.session_state:
            st.session_state[cache_key] = {
                'data': None,
                'timestamp': None
            }
        
        cache_entry = st.session_state[cache_key]
        
        # Check if cache is valid
        if cache_entry['data'] is not None and cache_entry['timestamp'] is not None:
            age = (datetime.now() - cache_entry['timestamp']).total_seconds()
            if age < self.cache_ttl:
                return cache_entry['data']
        
        # Execute query and cache
        result = query_func(*args, **kwargs)
        st.session_state[cache_key] = {
            'data': result,
            'timestamp': datetime.now()
        }
        
        return result
    
    def get_financial_summary_cached(self):
        """Get cached financial summary"""
        cache_key = "financial_summary"
        
        def fetch_summary():
            try:
                query = f"""
                    SELECT 
                        (SELECT SUM(total_revenue) FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced` WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as week_revenue,
                        (SELECT SUM(amount) FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.expenses_master` WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as week_expenses,
                        (SELECT COUNT(*) FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.ai_task_queue` WHERE status = 'Pending') as pending_tasks
                """
                df = self.client.query(query).to_dataframe()
                return df.iloc[0].to_dict() if not df.empty else {}
            except:
                return {}
        
        return self.get_cached_query(cache_key, fetch_summary)
    
    def get_top_items_cached(self, limit=5):
        """Get cached top items"""
        cache_key = f"top_items_{limit}"
        
        def fetch_top_items():
            try:
                query = f"""
                    SELECT 
                        item_name,
                        SUM(total_revenue) as revenue,
                        SUM(quantity) as qty
                    FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced`
                    WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                    GROUP BY item_name
                    ORDER BY revenue DESC
                    LIMIT {limit}
                """
                df = self.client.query(query).to_dataframe()
                return df.to_dict('records') if not df.empty else []
            except:
                return []
        
        return self.get_cached_query(cache_key, fetch_top_items)
    
    def clear_cache(self, pattern=None):
        """Clear cache entries"""
        if pattern:
            keys_to_remove = [k for k in st.session_state.keys() if pattern in k]
            for key in keys_to_remove:
                if key.startswith(('financial_', 'top_', 'customer_')):
                    del st.session_state[key]
        else:
            # Clear all cache
            keys_to_remove = [k for k in st.session_state.keys() if k.startswith(('financial_', 'top_', 'customer_'))]
            for key in keys_to_remove:
                del st.session_state[key]
