"""
Daily Report Generator and Task Manager
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from google.cloud import bigquery
import settings

class DailyReporter:
    """Generate and send daily reports"""
    
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
    
    def generate_daily_report(self):
        """Generate comprehensive daily report"""
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'financial_summary': self._get_financial_summary(),
            'sales_insights': self._get_sales_insights(),
            'alerts': self._get_alerts(),
            'recommendations': self._get_recommendations(),
            'tasks': self._generate_tasks()
        }
        return report
    
    def _get_financial_summary(self):
        """Get financial summary"""
        try:
            # Yesterday's data
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            rev_query = f"""
                SELECT SUM(total_revenue) as revenue
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_items_parsed`
                WHERE bill_date = '{yesterday}'
            """
            rev_df = self.client.query(rev_query).to_dataframe()
            revenue = rev_df['revenue'][0] if not rev_df.empty and rev_df['revenue'][0] else 0
            
            exp_query = f"""
                SELECT SUM(amount) as expenses
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.expenses_master`
                WHERE expense_date = '{yesterday}'
            """
            exp_df = self.client.query(exp_query).to_dataframe()
            expenses = exp_df['expenses'][0] if not exp_df.empty and exp_df['expenses'][0] else 0
            
            return {
                'revenue': revenue,
                'expenses': expenses,
                'net_profit': revenue - expenses
            }
        except:
            return {'revenue': 0, 'expenses': 0, 'net_profit': 0}
    
    def _get_sales_insights(self):
        """Get sales insights"""
        try:
            query = f"""
                SELECT item_name, SUM(quantity) as qty, SUM(total_revenue) as revenue
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.sales_items_parsed`
                WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                GROUP BY item_name
                ORDER BY revenue DESC
                LIMIT 5
            """
            df = self.client.query(query).to_dataframe()
            return df.to_dict('records') if not df.empty else []
        except:
            return []
    
    def _get_alerts(self):
        """Get active alerts"""
        try:
            query = f"""
                SELECT task_type, item_involved, description, priority
                FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.ai_task_queue`
                WHERE status = 'Pending'
                ORDER BY priority DESC, created_at DESC
                LIMIT 10
            """
            df = self.client.query(query).to_dataframe()
            return df.to_dict('records') if not df.empty else []
        except:
            return []
    
    def _get_recommendations(self):
        """Get AI recommendations"""
        from utils.ai_agent import TitanAIAgent
        agent = TitanAIAgent(self.client, self.settings)
        return agent.get_daily_recommendations()
    
    def _generate_tasks(self):
        """Generate actionable tasks for the day"""
        tasks = []
        
        # Add tasks based on alerts
        alerts = self._get_alerts()
        for alert in alerts[:5]:  # Top 5
            tasks.append({
                'task': alert['description'],
                'priority': alert['priority'],
                'type': alert['task_type']
            })
        
        return tasks
    
    def format_report_text(self, report):
        """Format report as text"""
        text = f"""
╔══════════════════════════════════════════╗
║     TITAN ERP - DAILY REPORT             ║
║     {report['date']}                        ║
╚══════════════════════════════════════════╝

📊 FINANCIAL SUMMARY
Revenue: ₹{report['financial_summary']['revenue']:,.2f}
Expenses: ₹{report['financial_summary']['expenses']:,.2f}
Net Profit: ₹{report['financial_summary']['net_profit']:,.2f}

📈 TOP SELLING ITEMS (Last 7 Days)
"""
        for item in report['sales_insights'][:5]:
            text += f"- {item['item_name']}: ₹{item['revenue']:,.2f}\n"
        
        text += "\n⚠️ ACTIVE ALERTS\n"
        for alert in report['alerts'][:5]:
            text += f"- [{alert['priority']}] {alert['task_type']}: {alert['description']}\n"
        
        text += "\n✅ TODAY'S TASKS\n"
        for i, task in enumerate(report['tasks'][:5], 1):
            text += f"{i}. [{task['priority']}] {task['task']}\n"
        
        text += "\n💡 RECOMMENDATIONS\n"
        for rec in report['recommendations'][:5]:
            text += f"- {rec['message']}\n"
        
        return text
