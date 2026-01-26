"""
Advanced Query Engine - Natural Language to Business Insights
"""
import re
from datetime import datetime
from utils.ai_agent import TitanAIAgent

class AdvancedQueryEngine:
    """Parse natural language queries and execute business logic"""
    
    def __init__(self, client, settings):
        self.agent = TitanAIAgent(client, settings)
        self.client = client
        self.settings = settings
    
    def parse_query(self, query):
        """Parse natural language query and identify intent"""
        query_lower = query.lower()
        
        # Expense queries — always send to Gemini for human-like answers (no raw df dumps)
        if any(word in query_lower for word in ['expense', 'spent', 'cost', 'expenditure']):
            return None
        
        # Revenue/Sales queries
        if any(word in query_lower for word in ['revenue', 'sales', 'income', 'earning']):
            return self._handle_sales_query(query_lower)
        
        # Profit queries
        if any(word in query_lower for word in ['profit', 'loss', 'p&l', 'pnl', 'net']):
            return self._handle_profit_query(query_lower)
        
        # Staff queries — always send to Gemini for human-like answers (no raw df dumps)
        if any(word in query_lower for word in ['staff', 'employee', 'worker', 'salary', 'advance']):
            return None
        
        # Product queries
        if any(word in query_lower for word in ['product', 'item', 'selling', 'stock', 'inventory']):
            return self._handle_product_query(query_lower)
        
        # Default: pass to AI
        return None
    
    def _handle_expense_query(self, query):
        """Handle expense-related queries"""
        date = None
        payment_mode = None
        exclude_categories = []
        
        # Extract date
        if 'yesterday' in query:
            from datetime import datetime, timedelta
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'today' in query:
            date = datetime.now().strftime('%Y-%m-%d')
        elif 'last month' in query:
            from datetime import datetime, timedelta
            date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Extract payment mode
        if 'cash' in query:
            payment_mode = 'cash'
        elif 'bank' in query or 'card' in query:
            payment_mode = 'bank'
        
        # Extract exclusions
        if 'exclude' in query or 'neglect' in query or 'avoid' in query:
            if 'personal' in query:
                exclude_categories.append('personal')
            if 'loan' in query:
                exclude_categories.append('loan')
        
        return {
            'type': 'expense',
            'date': date,
            'payment_mode': payment_mode,
            'exclude_categories': exclude_categories
        }
    
    def _handle_sales_query(self, query):
        """Handle sales-related queries"""
        date = None
        item_name = None
        
        # Extract date
        if 'yesterday' in query:
            from datetime import datetime, timedelta
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Extract item name (basic)
        words = query.split()
        for i, word in enumerate(words):
            if word in ['for', 'of', 'item'] and i + 1 < len(words):
                item_name = words[i + 1]
                break
        
        return {
            'type': 'sales',
            'date': date,
            'item_name': item_name
        }
    
    def _handle_profit_query(self, query):
        """Handle profit & loss queries"""
        exclude_personal = 'personal' in query or 'neglect' in query or 'exclude' in query
        exclude_categories = []
        
        if 'personal' in query:
            exclude_categories.append('personal')
        if 'loan' in query:
            exclude_categories.append('loan')
        
        return {
            'type': 'profit',
            'exclude_personal': exclude_personal,
            'exclude_categories': exclude_categories
        }
    
    def _handle_staff_query(self, query):
        """Handle staff-related queries"""
        staff_name = None
        query_type = None
        
        # Extract staff name
        if 'arun' in query:
            staff_name = 'Arun'
        # Add more staff names as needed
        
        # Determine query type
        if 'advance' in query:
            query_type = 'advance'
        elif 'salary' in query or 'wages' in query or 'paid' in query:
            query_type = 'salary'
        
        return {
            'type': 'staff',
            'staff_name': staff_name,
            'query_type': query_type
        }
    
    def _handle_product_query(self, query):
        """Handle product-related queries"""
        item_name = None
        
        # Extract item name (simplified)
        if 'cheesecake' in query:
            item_name = 'cheesecake'
        elif 'cupcake' in query:
            item_name = 'cupcake'
        elif 'truffle' in query:
            item_name = 'truffle'
        
        return {
            'type': 'product',
            'item_name': item_name
        }
    
    def execute_query(self, parsed_query):
        """Execute parsed query"""
        if parsed_query is None:
            return None
        
        query_type = parsed_query.get('type')
        
        if query_type == 'expense':
            df = self.agent.analyze_expenses(
                date=parsed_query.get('date'),
                payment_mode=parsed_query.get('payment_mode'),
                exclude_categories=parsed_query.get('exclude_categories')
            )
            if not df.empty:
                total = df['amount'].sum()
                return f"Total Expenses: ₹{total:,.2f}\n\n{df.to_string(index=False)}"
            return "No expense data found."
        
        elif query_type == 'sales':
            # Implement sales query
            return "Sales query executed"
        
        elif query_type == 'profit':
            pnl = self.agent.calculate_pnl(
                exclude_personal=parsed_query.get('exclude_personal'),
                exclude_categories=parsed_query.get('exclude_categories')
            )
            return f"""
Profit & Loss Summary:
Revenue: ₹{pnl['revenue']:,.2f}
Expenses: ₹{pnl['expenses']:,.2f}
Net Profit: ₹{pnl['net_profit']:,.2f}
Profit Margin: {pnl['profit_margin']:.2f}%
            """
        
        elif query_type == 'staff':
            staff_name = parsed_query.get('staff_name')
            query_type_staff = parsed_query.get('query_type')
            
            if query_type_staff == 'advance':
                df = self.agent.get_staff_advances(staff_name)
                if not df.empty:
                    total = df['amount'].sum()
                    return f"{staff_name}'s Total Advances: ₹{total:,.2f}\n\n{df.to_string(index=False)}"
                return f"No advance records found for {staff_name}."
            
            elif query_type_staff == 'salary':
                df = self.agent.get_staff_salary_payments(staff_name)
                if not df.empty:
                    return f"{staff_name}'s Salary History:\n\n{df.to_string(index=False)}"
                return f"No salary records found for {staff_name}."
        
        elif query_type == 'product':
            item_name = parsed_query.get('item_name')
            insights = self.agent.detect_product_issues(item_name)
            if insights:
                return "\n".join(insights)
            return f"No insights available for {item_name}."
        
        return None
