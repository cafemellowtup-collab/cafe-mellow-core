"""
Data Optimizer - High-level insights and optimization
"""
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import settings

class DataOptimizer:
    """Analyze data for optimization opportunities"""
    
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
    
    def check_recipe_completeness(self):
        """Check for missing or incomplete recipes"""
        issues = []
        try:
            # Find sales items without recipes
            query = f"""
                SELECT DISTINCT s.item_name
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_items_parsed` s
                LEFT JOIN `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.titan_name_bridge` b
                  ON s.item_name = b.sales_name
                LEFT JOIN `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.recipes_sales_master` r
                  ON b.recipe_name = r.parent_item OR s.item_name = r.parent_item
                WHERE r.parent_item IS NULL
                GROUP BY s.item_name
                LIMIT 20
            """
            df = self.client.query(query).to_dataframe()
            
            if not df.empty:
                for _, row in df.iterrows():
                    issues.append({
                        'type': 'missing_recipe',
                        'severity': 'High',
                        'item': row['item_name'],
                        'message': f"Recipe missing for '{row['item_name']}'. Add recipe in Petpooja dashboard."
                    })
        except Exception as e:
            print(f"Error checking recipes: {e}")
        
        return issues
    
    def check_inventory_mismatches(self):
        """Check for inventory mismatches"""
        issues = []
        try:
            # This would compare sales with inventory
            # Placeholder for now
            pass
        except Exception as e:
            print(f"Error checking inventory: {e}")
        
        return issues
    
    def analyze_wastage(self):
        """Analyze wastage patterns"""
        issues = []
        try:
            query = f"""
                SELECT item_name, SUM(quantity) as total_wasted
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.wastage_log`
                WHERE wastage_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY item_name
                HAVING total_wasted > 10
                ORDER BY total_wasted DESC
                LIMIT 10
            """
            df = self.client.query(query).to_dataframe()
            
            if not df.empty:
                for _, row in df.iterrows():
                    issues.append({
                        'type': 'high_wastage',
                        'severity': 'Medium',
                        'item': row['item_name'],
                        'message': f"High wastage detected for '{row['item_name']}': {row['total_wasted']:.0f} units in last 30 days. Review production quantities."
                    })
        except:
            pass
        
        return issues
    
    def get_all_optimizations(self):
        """Get all optimization recommendations"""
        optimizations = []
        optimizations.extend(self.check_recipe_completeness())
        optimizations.extend(self.analyze_wastage())
        optimizations.extend(self.check_inventory_mismatches())
        return optimizations
