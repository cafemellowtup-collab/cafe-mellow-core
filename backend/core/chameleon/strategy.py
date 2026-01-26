"""
Adaptive Strategy Selector
Chooses calculation strategy based on data quality tier
"""
from enum import Enum
from typing import Optional
from .data_quality import QualityTier, DataQualityScore


class AdaptiveStrategy(str, Enum):
    """Calculation Strategies"""
    RED_TIER_ESTIMATION = "red_estimation"        # Sales - Purchase approximation
    YELLOW_TIER_HYBRID = "yellow_hybrid"          # Partial COGS with estimation
    GREEN_TIER_AUDIT = "green_audit"              # Full COGS, audit-grade


class StrategySelector:
    """
    Selects appropriate calculation strategy based on data quality
    This is the "Chameleon" brain - adapts to data quality
    """
    
    @staticmethod
    def select_profit_strategy(quality_score: DataQualityScore) -> AdaptiveStrategy:
        """
        Select profit calculation strategy
        
        RED (< 50): Profit ≈ Sales - Purchases (rough estimation)
        YELLOW (50-90): Profit = Sales - COGS (where COGS available) - Purchases (fallback)
        GREEN (> 90): Profit = Sales - COGS (audit-grade, full recipe costing)
        """
        if quality_score.tier == QualityTier.RED:
            return AdaptiveStrategy.RED_TIER_ESTIMATION
        elif quality_score.tier == QualityTier.YELLOW:
            return AdaptiveStrategy.YELLOW_TIER_HYBRID
        else:
            return AdaptiveStrategy.GREEN_TIER_AUDIT
    
    @staticmethod
    def get_strategy_sql(strategy: AdaptiveStrategy, project_id: str, dataset_id: str, org_id: str, location_id: str, start_date: str, end_date: str) -> str:
        """
        Get SQL query for the selected strategy
        """
        if strategy == AdaptiveStrategy.RED_TIER_ESTIMATION:
            return f"""
            -- RED TIER: Estimation via Sales - Purchase
            WITH sales AS (
                SELECT SUM(total_revenue) as revenue
                FROM `{project_id}.{dataset_id}.sales_items_parsed`
                WHERE org_id = '{org_id}' 
                    AND location_id = '{location_id}'
                    AND bill_date BETWEEN '{start_date}' AND '{end_date}'
            ),
            purchases AS (
                SELECT SUM(amount) as cost
                FROM `{project_id}.{dataset_id}.purchases_master`
                WHERE org_id = '{org_id}' 
                    AND location_id = '{location_id}'
                    AND purchase_date BETWEEN '{start_date}' AND '{end_date}'
            )
            SELECT 
                sales.revenue,
                purchases.cost,
                sales.revenue - purchases.cost as estimated_profit,
                'RED_TIER_ESTIMATION' as strategy
            FROM sales, purchases
            """
        
        elif strategy == AdaptiveStrategy.YELLOW_TIER_HYBRID:
            return f"""
            -- YELLOW TIER: Hybrid COGS + Purchase Fallback
            WITH sales AS (
                SELECT 
                    item_name,
                    SUM(total_revenue) as revenue,
                    SUM(quantity) as qty
                FROM `{project_id}.{dataset_id}.sales_items_parsed`
                WHERE org_id = '{org_id}' 
                    AND location_id = '{location_id}'
                    AND bill_date BETWEEN '{start_date}' AND '{end_date}'
                GROUP BY item_name
            ),
            recipes AS (
                SELECT item_name, ingredient_name, quantity_per_unit
                FROM `{project_id}.{dataset_id}.recipes_sales_master`
                WHERE org_id = '{org_id}' AND location_id = '{location_id}'
            ),
            cogs_available AS (
                SELECT 
                    s.item_name,
                    s.revenue,
                    SUM(r.quantity_per_unit * s.qty) as cogs
                FROM sales s
                LEFT JOIN recipes r ON s.item_name = r.item_name
                WHERE r.item_name IS NOT NULL
                GROUP BY s.item_name, s.revenue
            ),
            purchases AS (
                SELECT SUM(amount) as purchase_fallback
                FROM `{project_id}.{dataset_id}.purchases_master`
                WHERE org_id = '{org_id}' 
                    AND location_id = '{location_id}'
                    AND purchase_date BETWEEN '{start_date}' AND '{end_date}'
            )
            SELECT 
                SUM(revenue) as total_revenue,
                COALESCE(SUM(cogs), 0) + COALESCE(purchases.purchase_fallback, 0) as total_cost,
                SUM(revenue) - (COALESCE(SUM(cogs), 0) + COALESCE(purchases.purchase_fallback, 0)) as profit,
                'YELLOW_TIER_HYBRID' as strategy
            FROM cogs_available, purchases
            """
        
        else:  # GREEN_TIER_AUDIT
            return f"""
            -- GREEN TIER: Full Audit-Grade COGS
            WITH sales AS (
                SELECT 
                    item_name,
                    SUM(total_revenue) as revenue,
                    SUM(quantity) as qty
                FROM `{project_id}.{dataset_id}.sales_items_parsed`
                WHERE org_id = '{org_id}' 
                    AND location_id = '{location_id}'
                    AND bill_date BETWEEN '{start_date}' AND '{end_date}'
                GROUP BY item_name
            ),
            recipes AS (
                SELECT item_name, ingredient_name, quantity_per_unit
                FROM `{project_id}.{dataset_id}.recipes_sales_master`
                WHERE org_id = '{org_id}' AND location_id = '{location_id}'
            ),
            ingredient_costs AS (
                SELECT 
                    ingredient_name,
                    AVG(unit_price) as avg_cost
                FROM `{project_id}.{dataset_id}.purchases_master`
                WHERE org_id = '{org_id}' 
                    AND location_id = '{location_id}'
                    AND purchase_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                GROUP BY ingredient_name
            ),
            cogs AS (
                SELECT 
                    s.item_name,
                    s.revenue,
                    SUM(r.quantity_per_unit * s.qty * ic.avg_cost) as cogs
                FROM sales s
                JOIN recipes r ON s.item_name = r.item_name
                JOIN ingredient_costs ic ON r.ingredient_name = ic.ingredient_name
                GROUP BY s.item_name, s.revenue
            )
            SELECT 
                SUM(revenue) as total_revenue,
                SUM(cogs) as total_cogs,
                SUM(revenue - cogs) as profit,
                'GREEN_TIER_AUDIT' as strategy
            FROM cogs
            """
