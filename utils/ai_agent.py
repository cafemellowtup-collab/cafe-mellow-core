"""
Advanced AI Agent with Deep Business Intelligence
"""
import requests
import json
import settings
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import pandas as pd

class TitanAIAgent:
    """Advanced AI Agent for Business Intelligence"""
    
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
        self.city = "Tiruppur"
        self.state = "Tamil Nadu"
        self.country = "India"
    
    def get_market_context(self):
        """Get market context for Tiruppur, Tamil Nadu"""
        # This would integrate with market data APIs in the future
        return f"Business Location: {self.city}, {self.state}, {self.country}"
    
    def analyze_expenses(self, date=None, payment_mode=None, exclude_categories=None, include_categories=None):
        """Advanced expense analysis with filtering"""
        try:
            query = f"""
                SELECT expense_date, item_name, amount, payment_mode, category
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.expenses_master`
                WHERE 1=1
            """
            
            if date:
                query += f" AND expense_date = '{date}'"
            else:
                query += " AND expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
            
            if payment_mode:
                query += f" AND payment_mode LIKE '%{payment_mode}%'"
            
            if exclude_categories:
                for cat in exclude_categories:
                    query += f" AND item_name NOT LIKE '%{cat}%'"
            
            if include_categories:
                conditions = " OR ".join([f"item_name LIKE '%{cat}%'" for cat in include_categories])
                query += f" AND ({conditions})"
            
            df = self.client.query(query).to_dataframe()
            return df
        except Exception as e:
            print(f"Error analyzing expenses: {e}")
            return pd.DataFrame()
    
    def calculate_pnl(self, start_date=None, end_date=None, exclude_personal=True, exclude_categories=None):
        """Calculate Profit & Loss with custom rules"""
        try:
            # Revenue - Try enhanced table first, fallback to parsed
            try:
                rev_query = f"""
                    SELECT SUM(total_revenue) as revenue
                    FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced`
                    WHERE 1=1
                """
                if start_date:
                    rev_query += f" AND bill_date >= '{start_date}'"
                if end_date:
                    rev_query += f" AND bill_date <= '{end_date}'"
                
                rev_df = self.client.query(rev_query).to_dataframe()
                revenue = rev_df['revenue'][0] if not rev_df.empty and rev_df['revenue'][0] else 0
            except:
                # Fallback to basic parsed table
                rev_query = f"""
                    SELECT SUM(total_revenue) as revenue
                    FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_items_parsed`
                    WHERE 1=1
                """
                if start_date:
                    rev_query += f" AND bill_date >= '{start_date}'"
                if end_date:
                    rev_query += f" AND bill_date <= '{end_date}'"
                
                rev_df = self.client.query(rev_query).to_dataframe()
                revenue = rev_df['revenue'][0] if not rev_df.empty and rev_df['revenue'][0] else 0
            
            # Expenses
            exp_query = f"""
                SELECT SUM(amount) as expenses
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.expenses_master`
                WHERE 1=1
            """
            if start_date:
                exp_query += f" AND expense_date >= '{start_date}'"
            if end_date:
                exp_query += f" AND expense_date <= '{end_date}'"
            
            if exclude_personal:
                exp_query += " AND item_name NOT LIKE '%personal%' AND item_name NOT LIKE '%loan%'"
            
            if exclude_categories:
                for cat in exclude_categories:
                    exp_query += f" AND item_name NOT LIKE '%{cat}%'"
            
            exp_df = self.client.query(exp_query).to_dataframe()
            expenses = exp_df['expenses'][0] if not exp_df.empty and exp_df['expenses'][0] else 0
            
            return {
                'revenue': revenue,
                'expenses': expenses,
                'net_profit': revenue - expenses,
                'profit_margin': ((revenue - expenses) / revenue * 100) if revenue > 0 else 0
            }
        except Exception as e:
            print(f"Error calculating P&L: {e}")
            return {'revenue': 0, 'expenses': 0, 'net_profit': 0, 'profit_margin': 0}
    
    def get_staff_advances(self, staff_name, start_date=None, end_date=None):
        """Get staff advance payments"""
        try:
            query = f"""
                SELECT expense_date, item_name, amount, payment_mode
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.expenses_master`
                WHERE item_name LIKE '%{staff_name}%'
                AND (item_name LIKE '%advance%' OR item_name LIKE '%Advance%')
            """
            
            if start_date:
                query += f" AND expense_date >= '{start_date}'"
            if end_date:
                query += f" AND expense_date <= '{end_date}'"
            
            df = self.client.query(query).to_dataframe()
            return df
        except:
            return pd.DataFrame()
    
    def get_staff_salary_payments(self, staff_name):
        """Get staff salary payment history"""
        try:
            query = f"""
                SELECT expense_date, amount, payment_mode
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.expenses_master`
                WHERE item_name LIKE '%{staff_name}%'
                AND (item_name LIKE '%salary%' OR item_name LIKE '%Salary%' OR item_name LIKE '%wages%')
                ORDER BY expense_date DESC
            """
            df = self.client.query(query).to_dataframe()
            return df
        except:
            return pd.DataFrame()
    
    def analyze_sales_patterns(self, days=30):
        """Deep sales pattern analysis using enhanced data"""
        try:
            # Use enhanced table for more detailed analysis
            query = f"""
                SELECT 
                    bill_date,
                    item_name,
                    order_type,
                    delivery_partner,
                    payment_mode,
                    SUM(quantity) as total_qty,
                    SUM(total_revenue) as total_revenue,
                    COUNT(DISTINCT order_id) as order_count,
                    COUNT(DISTINCT customer_phone) as unique_customers
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced`
                WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                GROUP BY bill_date, item_name, order_type, delivery_partner, payment_mode
                ORDER BY bill_date DESC, total_revenue DESC
            """
            df = self.client.query(query).to_dataframe()
            return df
        except:
            # Fallback to basic parsed table
            try:
                query = f"""
                    SELECT 
                        bill_date,
                        item_name,
                        SUM(quantity) as total_qty,
                        SUM(total_revenue) as total_revenue,
                        COUNT(DISTINCT order_id) as order_count
                    FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_items_parsed`
                    WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                    GROUP BY bill_date, item_name
                    ORDER BY bill_date DESC, total_revenue DESC
                """
                df = self.client.query(query).to_dataframe()
                return df
            except:
                return pd.DataFrame()
    
    def detect_product_issues(self, item_name):
        """Detect issues with specific products (stock-outs, quality, etc.)"""
        insights = []
        try:
            # Analyze sales trend
            query = f"""
                SELECT 
                    bill_date,
                    SUM(quantity) as daily_qty,
                    SUM(total_revenue) as daily_revenue
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_items_parsed`
                WHERE item_name LIKE '%{item_name}%'
                AND bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY bill_date
                ORDER BY bill_date DESC
            """
            df = self.client.query(query).to_dataframe()
            
            if not df.empty:
                # Detect sudden drops
                if len(df) >= 3:
                    recent_avg = df.head(3)['daily_qty'].mean()
                    older_avg = df.tail(7)['daily_qty'].mean() if len(df) > 7 else recent_avg
                    
                    if recent_avg < (older_avg * 0.5):  # 50% drop
                        insights.append(f"⚠️ {item_name} sales dropped {((1 - recent_avg/older_avg)*100):.0f}% recently. Possible stock-out or quality issue.")
                
                # Check for zero sales days
                zero_days = df[df['daily_qty'] == 0]
                if len(zero_days) > 0:
                    insights.append(f"⚠️ {item_name} had {len(zero_days)} days with zero sales in the last 30 days.")
                
                # Top selling days
                top_day = df.loc[df['daily_qty'].idxmax()]
                insights.append(f"📊 {item_name} sells best on {top_day['bill_date']} - Average {top_day['daily_qty']:.0f} units.")
            
        except Exception as e:
            print(f"Error detecting product issues: {e}")
        
        return insights
    
    def get_daily_recommendations(self):
        """Generate daily recommendations"""
        recommendations = []
        try:
            # Check top sellers
            query = f"""
                SELECT item_name, SUM(total_revenue) as revenue, SUM(quantity) as qty
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_items_parsed`
                WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                GROUP BY item_name
                ORDER BY revenue DESC
                LIMIT 5
            """
            top_items = self.client.query(query).to_dataframe()
            
            if not top_items.empty:
                for _, row in top_items.iterrows():
                    recommendations.append({
                        'type': 'stock_alert',
                        'priority': 'High',
                        'message': f"🔥 {row['item_name']} is top seller (₹{row['revenue']:,.0f}/week). Keep well-stocked!",
                        'item': row['item_name']
                    })
            
            # Check wastage (if table exists)
            try:
                wastage_query = f"""
                    SELECT item_name, SUM(quantity) as wasted
                    FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.wastage_log`
                    WHERE wastage_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                    GROUP BY item_name
                    ORDER BY wasted DESC
                    LIMIT 3
                """
                wastage_df = self.client.query(wastage_query).to_dataframe()
                for _, row in wastage_df.iterrows():
                    recommendations.append({
                        'type': 'wastage_alert',
                        'priority': 'Medium',
                        'message': f"⚠️ High wastage detected for {row['item_name']}. Review production quantities.",
                        'item': row['item_name']
                    })
            except:
                pass
                
        except Exception as e:
            print(f"Error generating recommendations: {e}")
        
        return recommendations
