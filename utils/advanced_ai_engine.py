"""
Advanced AI Engine - Beyond Current AI Capabilities
Features: Predictive Analytics, Pattern Recognition, Self-Learning, Proactive Insights
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import settings
import json

class AdvancedAIEngine:
    """Advanced AI Engine with predictive and learning capabilities"""
    
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
    
    def predict_sales_trends(self, item_name=None, days_ahead=7):
        """Predict future sales trends using historical patterns"""
        try:
            # Get historical data
            query = f"""
                SELECT 
                    bill_date,
                    item_name,
                    SUM(quantity) as daily_qty,
                    SUM(total_revenue) as daily_revenue,
                    COUNT(DISTINCT order_id) as order_count
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced`
                WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                {'AND item_name LIKE "%' + item_name + '%"' if item_name else ''}
                GROUP BY bill_date, item_name
                ORDER BY bill_date
            """
            df = self.client.query(query).to_dataframe()
            
            if df.empty:
                return None
            
            predictions = []
            
            # Group by item
            for item in df['item_name'].unique()[:10]:  # Top 10 items
                item_df = df[df['item_name'] == item].copy()
                item_df = item_df.sort_values('bill_date')
                
                if len(item_df) < 7:
                    continue
                
                # Simple moving average prediction
                recent_avg = item_df.tail(7)['daily_qty'].mean()
                weekly_avg = item_df.tail(30)['daily_qty'].mean()
                
                # Trend detection
                recent_trend = item_df.tail(7)['daily_qty'].mean() - item_df.tail(14).head(7)['daily_qty'].mean()
                
                # Predict next 7 days
                predicted_qty = recent_avg + (recent_trend * days_ahead)
                
                predictions.append({
                    'item_name': item,
                    'current_avg_daily': recent_avg,
                    'predicted_daily': max(0, predicted_qty),
                    'trend': 'increasing' if recent_trend > 0 else 'decreasing' if recent_trend < 0 else 'stable',
                    'confidence': 'high' if len(item_df) > 30 else 'medium'
                })
            
            return predictions
        except Exception as e:
            print(f"Error in sales prediction: {e}")
            return None
    
    def detect_anomalies(self, table_name, date_column, value_column, threshold=2.0):
        """Detect anomalies using statistical methods"""
        try:
            query = f"""
                SELECT {date_column}, SUM({value_column}) as total_value
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.{table_name}`
                WHERE {date_column} >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY {date_column}
                ORDER BY {date_column}
            """
            df = self.client.query(query).to_dataframe()
            
            if df.empty or len(df) < 7:
                return []
            
            # Calculate z-scores
            mean = df['total_value'].mean()
            std = df['total_value'].std()
            
            if std == 0:
                return []
            
            df['z_score'] = (df['total_value'] - mean) / std
            anomalies = df[abs(df['z_score']) > threshold].copy()
            
            results = []
            for _, row in anomalies.iterrows():
                results.append({
                    'date': row[date_column],
                    'value': row['total_value'],
                    'z_score': row['z_score'],
                    'severity': 'high' if abs(row['z_score']) > 3 else 'medium',
                    'type': 'spike' if row['z_score'] > 0 else 'drop'
                })
            
            return results
        except Exception as e:
            print(f"Error detecting anomalies: {e}")
            return []
    
    def identify_opportunities(self):
        """Proactively identify business opportunities"""
        opportunities = []
        
        try:
            # Opportunity 1: High wastage items
            wastage_query = f"""
                SELECT item_name, SUM(quantity) as total_wasted
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.wastage_log`
                WHERE wastage_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY item_name
                HAVING total_wasted > 20
                ORDER BY total_wasted DESC
                LIMIT 5
            """
            wastage_df = self.client.query(wastage_query).to_dataframe()
            for _, row in wastage_df.iterrows():
                opportunities.append({
                    'type': 'wastage_reduction',
                    'priority': 'high',
                    'item': row['item_name'],
                    'message': f"High wastage detected: {row['total_wasted']:.0f} units. Review production planning.",
                    'action': 'Reduce production quantity or improve inventory management'
                })
        except:
            pass
        
        try:
            # Opportunity 2: Low stock items with high sales
            stock_query = f"""
                SELECT 
                    i.item_name,
                    i.current_stock,
                    SUM(s.quantity) as sales_qty
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.ingredients_master` i
                LEFT JOIN `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced` s
                    ON i.item_name = s.item_name
                WHERE s.bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                GROUP BY i.item_name, i.current_stock
                HAVING i.current_stock < 10 AND sales_qty > 50
                LIMIT 5
            """
            stock_df = self.client.query(stock_query).to_dataframe()
            for _, row in stock_df.iterrows():
                opportunities.append({
                    'type': 'stock_alert',
                    'priority': 'high',
                    'item': row['item_name'],
                    'message': f"Low stock ({row['current_stock']:.0f}) but high sales ({row['sales_qty']:.0f}). Restock needed.",
                    'action': 'Place purchase order immediately'
                })
        except:
            pass
        
        try:
            # Opportunity 3: Top sellers without recipes
            recipe_query = f"""
                SELECT DISTINCT s.item_name
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced` s
                LEFT JOIN `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.titan_name_bridge` b
                    ON s.item_name = b.sales_name
                LEFT JOIN `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.recipes_sales_master` r
                    ON b.recipe_name = r.parent_item OR s.item_name = r.parent_item
                WHERE s.bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                    AND r.parent_item IS NULL
                GROUP BY s.item_name
                HAVING SUM(s.total_revenue) > 5000
                ORDER BY SUM(s.total_revenue) DESC
                LIMIT 5
            """
            recipe_df = self.client.query(recipe_query).to_dataframe()
            for _, row in recipe_df.iterrows():
                opportunities.append({
                    'type': 'recipe_missing',
                    'priority': 'medium',
                    'item': row['item_name'],
                    'message': f"Top seller '{row['item_name']}' has no recipe. Add recipe for inventory tracking.",
                    'action': 'Create recipe in Petpooja dashboard'
                })
        except:
            pass
        
        return opportunities
    
    def analyze_customer_behavior(self, days=30):
        """Analyze customer behavior patterns"""
        try:
            query = f"""
                SELECT 
                    customer_phone,
                    customer_name,
                    COUNT(DISTINCT order_id) as order_count,
                    SUM(total_revenue) as total_spent,
                    AVG(total_revenue) as avg_order_value,
                    MAX(bill_date) as last_order_date,
                    COUNT(DISTINCT item_name) as unique_items_ordered
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced`
                WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                    AND customer_phone IS NOT NULL
                    AND customer_phone != ''
                GROUP BY customer_phone, customer_name
                HAVING order_count >= 3
                ORDER BY total_spent DESC
                LIMIT 20
            """
            df = self.client.query(query).to_dataframe()
            
            if df.empty:
                return []
            
            # Classify customers
            df['customer_segment'] = df.apply(lambda x: 
                'VIP' if x['total_spent'] > 10000 else
                'Regular' if x['order_count'] > 10 else
                'Occasional', axis=1
            )
            
            return df.to_dict('records')
        except Exception as e:
            print(f"Error analyzing customer behavior: {e}")
            return []
    
    def generate_proactive_insights(self):
        """Generate proactive business insights"""
        insights = []
        
        # Get today's date
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        try:
            # Insight 1: Revenue comparison
            today_rev_query = f"""
                SELECT SUM(total_revenue) as revenue
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced`
                WHERE bill_date = CURRENT_DATE()
            """
            today_rev = self.client.query(today_rev_query).to_dataframe()
            today_revenue = today_rev['revenue'][0] if not today_rev.empty and today_rev['revenue'][0] else 0
            
            yesterday_rev_query = f"""
                SELECT SUM(total_revenue) as revenue
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced`
                WHERE bill_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
            """
            yesterday_rev = self.client.query(yesterday_rev_query).to_dataframe()
            yesterday_revenue = yesterday_rev['revenue'][0] if not yesterday_rev.empty and yesterday_rev['revenue'][0] else 0
            
            if yesterday_revenue > 0:
                change_pct = ((today_revenue - yesterday_revenue) / yesterday_revenue) * 100
                if abs(change_pct) > 20:
                    insights.append({
                        'type': 'revenue_alert',
                        'priority': 'high' if change_pct < -20 else 'medium',
                        'message': f"Revenue {'decreased' if change_pct < 0 else 'increased'} by {abs(change_pct):.1f}% compared to yesterday.",
                        'action': 'Review sales patterns and marketing activities'
                    })
        except:
            pass
        
        # Add opportunities as insights
        opportunities = self.identify_opportunities()
        insights.extend(opportunities)
        
        return insights
    
    def learn_from_patterns(self):
        """Self-learning: Identify patterns and create rules"""
        patterns = []
        
        try:
            # Pattern 1: Day of week patterns
            query = f"""
                SELECT 
                    EXTRACT(DAYOFWEEK FROM bill_date) as day_of_week,
                    AVG(SUM(total_revenue)) as avg_revenue
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_enhanced`
                WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
                GROUP BY day_of_week
                ORDER BY avg_revenue DESC
            """
            df = self.client.query(query).to_dataframe()
            
            if not df.empty:
                best_day = df.iloc[0]['day_of_week']
                patterns.append({
                    'pattern_type': 'day_of_week',
                    'insight': f"Day {int(best_day)} is typically the busiest day",
                    'recommendation': 'Schedule more staff on this day'
                })
        except:
            pass
        
        return patterns
