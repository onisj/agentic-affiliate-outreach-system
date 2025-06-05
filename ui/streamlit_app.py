import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
import os
from datetime import datetime, timedelta
from io import BytesIO
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
from services.monitoring_service import MonitoringService
from services.scoring_service import ScoringService
from database.session import get_db
from database.models import AffiliateProspect, MessageLog, Alert

# PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# Database
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DB_URL = os.getenv("DATABASE_URL")
HEALTH_PORT = 8502

# Initialize services
monitoring_service = MonitoringService()
scoring_service = ScoringService()
db = next(get_db())

class DatabaseManager:
    """Centralized database management."""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize database engine."""
        try:
            self.engine = create_engine(self.db_url)
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            self.engine = None
    
    def execute_query(self, query: str, params: dict = None) -> pd.DataFrame:
        """Execute query and return DataFrame."""
        try:
            if not self.engine:
                self._initialize_engine()
            
            with self.engine.connect() as conn:
                result = pd.read_sql(text(query), conn, params=params)
                return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return pd.DataFrame()
    
    def get_scalar(self, query: str, params: dict = None) -> int:
        """Execute query and return scalar value."""
        try:
            df = self.execute_query(query, params)
            return df.iloc[0, 0] if not df.empty else 0
        except Exception as e:
            logger.error(f"Scalar query failed: {e}")
            return 0

class AnalyticsEngine:
    """Analytics computation engine."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_response_metrics(self) -> dict:
        """Calculate response rate metrics."""
        try:
            total_messages = self.db.get_scalar(
                "SELECT COUNT(*) FROM message_log WHERE status != 'BOUNCED'"
            )
            replied_messages = self.db.get_scalar(
                "SELECT COUNT(*) FROM message_log WHERE status = 'REPLIED'"
            )
            
            response_rate = (replied_messages / total_messages * 100) if total_messages > 0 else 0
            
            return {
                "total_messages": total_messages,
                "replied_messages": replied_messages,
                "response_rate": response_rate
            }
        except Exception as e:
            logger.error(f"Error calculating response metrics: {e}")
            return {"total_messages": 0, "replied_messages": 0, "response_rate": 0}
    
    def get_conversion_metrics(self) -> dict:
        """Calculate conversion rate metrics."""
        try:
            enrolled_prospects = self.db.get_scalar(
                "SELECT COUNT(*) FROM affiliate_prospects WHERE status = 'ENROLLED'"
            )
            total_prospects = self.db.get_scalar(
                "SELECT COUNT(*) FROM affiliate_prospects"
            )
            
            conversion_rate = (enrolled_prospects / total_prospects * 100) if total_prospects > 0 else 0
            
            return {
                "enrolled_prospects": enrolled_prospects,
                "total_prospects": total_prospects,
                "conversion_rate": conversion_rate
            }
        except Exception as e:
            logger.error(f"Error calculating conversion metrics: {e}")
            return {"enrolled_prospects": 0, "total_prospects": 0, "conversion_rate": 0}
    
    def get_message_status_distribution(self) -> pd.DataFrame:
        """Get message status distribution."""
        query = "SELECT status, COUNT(*) as count FROM message_log GROUP BY status"
        return self.db.execute_query(query)
    
    def get_ab_test_results(self) -> pd.DataFrame:
        """Get A/B test results."""
        query = """
        SELECT 
            a.name,
            r.variant_id,
            r.sent_count,
            r.open_rate,
            r.click_rate,
            r.reply_rate
        FROM ab_tests a 
        JOIN ab_test_results r ON a.id = r.ab_test_id
        """
        return self.db.execute_query(query)
    
    def get_campaign_performance(self) -> pd.DataFrame:
        """Get campaign performance metrics."""
        query = """
        SELECT 
            c.name as campaign_name,
            COUNT(ml.id) as total_messages,
            COUNT(CASE WHEN ml.status = 'REPLIED' THEN 1 END) as replies,
            COUNT(CASE WHEN ml.status = 'OPENED' THEN 1 END) as opens,
            COUNT(CASE WHEN ml.status = 'CLICKED' THEN 1 END) as clicks
        FROM campaigns c
        LEFT JOIN message_log ml ON c.id = ml.campaign_id
        GROUP BY c.id, c.name
        """
        return self.db.execute_query(query)
    
    def get_prospect_trends(self, days: int = 30) -> pd.DataFrame:
        """Get prospect acquisition trends."""
        query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as new_prospects
        FROM affiliate_prospects 
        WHERE created_at >= NOW() - INTERVAL :days DAY
        GROUP BY DATE(created_at)
        ORDER BY date
        """
        return self.db.execute_query(query, {"days": days})
    
    def get_comprehensive_analytics(self) -> dict:
        """Get all analytics data."""
        return {
            "response_metrics": self.get_response_metrics(),
            "conversion_metrics": self.get_conversion_metrics(),
            "status_distribution": self.get_message_status_distribution(),
            "ab_test_results": self.get_ab_test_results(),
            "campaign_performance": self.get_campaign_performance(),
            "prospect_trends": self.get_prospect_trends(),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

class ReportGenerator:
    """Generate reports in various formats."""
    
    def __init__(self, analytics_engine: AnalyticsEngine):
        self.analytics = analytics_engine
    
    def generate_csv_report(self) -> tuple:
        """Generate CSV report."""
        try:
            data = self.analytics.get_comprehensive_analytics()
            
            # Create summary data
            summary_data = [
                ["Metric", "Value"],
                ["Response Rate", f"{data['response_metrics']['response_rate']:.2f}%"],
                ["Conversion Rate", f"{data['conversion_metrics']['conversion_rate']:.2f}%"],
                ["Total Messages", data['response_metrics']['total_messages']],
                ["Total Prospects", data['conversion_metrics']['total_prospects']],
                ["Enrolled Prospects", data['conversion_metrics']['enrolled_prospects']],
                ["Last Updated", data['last_updated']]
            ]
            
            df = pd.DataFrame(summary_data[1:], columns=summary_data[0])
            csv_content = df.to_csv(index=False)
            
            return csv_content, "affiliate_outreach_report.csv"
        except Exception as e:
            logger.error(f"CSV report generation failed: {e}")
            return f"Error: {str(e)}", None
    
    def generate_pdf_report(self) -> tuple:
        """Generate PDF report."""
        try:
            data = self.analytics.get_comprehensive_analytics()
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph("Affiliate Outreach Analytics Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Summary metrics
            summary_title = Paragraph("Key Metrics", styles['Heading2'])
            story.append(summary_title)
            
            metrics_data = [
                ["Metric", "Value"],
                ["Response Rate", f"{data['response_metrics']['response_rate']:.2f}%"],
                ["Conversion Rate", f"{data['conversion_metrics']['conversion_rate']:.2f}%"],
                ["Total Messages", str(data['response_metrics']['total_messages'])],
                ["Total Prospects", str(data['conversion_metrics']['total_prospects'])],
                ["Enrolled Prospects", str(data['conversion_metrics']['enrolled_prospects'])]
            ]
            
            metrics_table = Table(metrics_data)
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 20))
            
            # Footer
            footer = Paragraph(f"Generated on: {data['last_updated']}", styles['Normal'])
            story.append(footer)
            
            # Build PDF
            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content, "affiliate_outreach_report.pdf"
        except Exception as e:
            logger.error(f"PDF report generation failed: {e}")
            return f"Error: {str(e)}", None

class HealthCheckServer:
    """Health check server for Streamlit."""
    
    def __init__(self, port: int, db_manager: DatabaseManager):
        self.port = port
        self.db_manager = db_manager
        self.server = None
    
    def start(self):
        """Start health check server."""
        health_thread = Thread(target=self._run_server, daemon=True)
        health_thread.start()
        logger.info(f"Health check server started on port {self.port}")
    
    def _run_server(self):
        """Run the health server."""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), HealthHandler)
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Health server error: {e}")
    
    def check_health(self) -> dict:
        """Check application health."""
        try:
            # Test database connection
            test_query = "SELECT 1"
            self.db_manager.execute_query(test_query)
            db_healthy = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_healthy = False
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "streamlit",
            "database": "connected" if db_healthy else "disconnected",
            "timestamp": time.time()
        }

class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks."""
    
    def do_GET(self):
        if self.path == '/health':
            health_data = health_server.check_health()
            status_code = 200 if health_data["status"] == "healthy" else 503
            
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

# Initialize components
if DB_URL:
    db_manager = DatabaseManager(DB_URL)
    analytics_engine = AnalyticsEngine(db_manager)
    report_generator = ReportGenerator(analytics_engine)
    health_server = HealthCheckServer(HEALTH_PORT, db_manager)
    health_server.start()
else:
    st.error("❌ Database URL not configured. Please set DATABASE_URL environment variable.")
    st.stop()

# Streamlit configuration
st.set_page_config(
    page_title="Affiliate Outreach Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stTab > div {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def load_prospect_data():
    """Load and process prospect data."""
    prospects = db.query(AffiliateProspect).all()
    data = []
    for p in prospects:
        data.append({
            "ID": str(p.id),
            "Name": f"{p.first_name} {p.last_name}",
            "Email": p.email,
            "Platform": p.platform,
            "Status": p.status,
            "Score": p.qualification_score,
            "Last Contact": p.last_contact_date,
            "Created At": p.created_at
        })
    return pd.DataFrame(data)

def load_message_data():
    """Load and process message data."""
    messages = db.query(MessageLog).all()
    data = []
    for m in messages:
        data.append({
            "ID": str(m.id),
            "Prospect ID": str(m.prospect_id),
            "Type": m.message_type,
            "Status": m.status,
            "Sent At": m.sent_at,
            "Response Time": m.response_time,
            "Content": m.content[:100] + "..." if len(m.content) > 100 else m.content
        })
    return pd.DataFrame(data)

def load_alert_data():
    """Load and process alert data."""
    alerts = db.query(Alert).filter(Alert.status == "active").all()
    data = []
    for a in alerts:
        data.append({
            "ID": str(a.id),
            "Type": a.alert_type,
            "Severity": a.severity,
            "Message": a.message,
            "Created At": a.created_at,
            "Details": json.dumps(a.details)
        })
    return pd.DataFrame(data)

def create_prospect_metrics(df):
    """Create prospect-related metrics and visualizations."""
    st.subheader("Prospect Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Prospects", len(df))
    with col2:
        st.metric("Active Prospects", len(df[df["Status"] == "ACTIVE"]))
    with col3:
        st.metric("Average Score", round(df["Score"].mean(), 2))
    with col4:
        st.metric("Response Rate", 
                 f"{len(df[df['Status'] == 'RESPONDED'])/len(df)*100:.1f}%")
    
    # Status Distribution
    status_counts = df["Status"].value_counts()
    fig_status = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Prospect Status Distribution"
    )
    st.plotly_chart(fig_status)
    
    # Score Distribution
    fig_score = px.histogram(
        df,
        x="Score",
        title="Qualification Score Distribution",
        nbins=20
    )
    st.plotly_chart(fig_score)

def create_message_metrics(df):
    """Create message-related metrics and visualizations."""
    st.subheader("Message Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Messages", len(df))
    with col2:
        st.metric("Success Rate", 
                 f"{len(df[df['Status'] == 'SENT'])/len(df)*100:.1f}%")
    with col3:
        st.metric("Avg Response Time", 
                 f"{df['Response Time'].mean():.1f}s")
    
    # Message Type Distribution
    type_counts = df["Type"].value_counts()
    fig_type = px.pie(
        values=type_counts.values,
        names=type_counts.index,
        title="Message Type Distribution"
    )
    st.plotly_chart(fig_type)
    
    # Response Time Over Time
    df["Sent At"] = pd.to_datetime(df["Sent At"])
    fig_time = px.scatter(
        df,
        x="Sent At",
        y="Response Time",
        color="Type",
        title="Response Time Over Time"
    )
    st.plotly_chart(fig_time)

def create_alert_metrics(df):
    """Create alert-related metrics and visualizations."""
    st.subheader("Alert Metrics")
    
    if len(df) == 0:
        st.info("No active alerts")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Active Alerts", len(df))
    with col2:
        st.metric("High Severity Alerts", 
                 len(df[df["Severity"] == "HIGH"]))
    
    # Alert Severity Distribution
    severity_counts = df["Severity"].value_counts()
    fig_severity = px.pie(
        values=severity_counts.values,
        names=severity_counts.index,
        title="Alert Severity Distribution"
    )
    st.plotly_chart(fig_severity)
    
    # Alert Timeline
    df["Created At"] = pd.to_datetime(df["Created At"])
    fig_timeline = px.scatter(
        df,
        x="Created At",
        y="Severity",
        color="Type",
        title="Alert Timeline"
    )
    st.plotly_chart(fig_timeline)

def main():
    """Main Streamlit application."""
    
    st.title("📊 Affiliate Outreach Analytics Dashboard")
    st.markdown("Real-time insights into your affiliate outreach performance")
    
    # Sidebar
    with st.sidebar:
        st.header("Dashboard Controls")
        
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        # Date range filter
        date_range = st.selectbox(
            "📅 Time Range",
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time"]
        )
        
        # Health status
        st.markdown("### System Health")
        health = health_server.check_health()
        health_emoji = "✅" if health["status"] == "healthy" else "❌"
        st.markdown(f"{health_emoji} **{health['status'].title()}**")
        st.markdown(f"Database: {health['database']}")
    
    # Cache analytics data
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_analytics_data():
        return analytics_engine.get_comprehensive_analytics()
    
    try:
        # Load data
        with st.spinner("Loading analytics data..."):
            data = get_analytics_data()
        
        # Key Metrics Row
        st.header("📈 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Response Rate",
                f"{data['response_metrics']['response_rate']:.2f}%",
                delta=None
            )
        
        with col2:
            st.metric(
                "Conversion Rate",
                f"{data['conversion_metrics']['conversion_rate']:.2f}%",
                delta=None
            )
        
        with col3:
            st.metric(
                "Total Messages",
                f"{data['response_metrics']['total_messages']:,}",
                delta=None
            )
        
        with col4:
            st.metric(
                "Total Prospects",
                f"{data['conversion_metrics']['total_prospects']:,}",
                delta=None
            )
        
        # Main Dashboard Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Campaigns", "🧪 A/B Tests", "📋 Reports"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Message Status Distribution")
                if not data['status_distribution'].empty:
                    fig_pie = px.pie(
                        data['status_distribution'], 
                        values='count', 
                        names='status',
                        title="Message Status Breakdown"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No message status data available")
            
            with col2:
                st.subheader("Prospect Acquisition Trend")
                if not data['prospect_trends'].empty:
                    fig_line = px.line(
                        data['prospect_trends'],
                        x='date',
                        y='new_prospects',
                        title="Daily New Prospects"
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("No prospect trend data available")
        
        with tab2:
            st.subheader("Campaign Performance")
            if not data['campaign_performance'].empty:
                # Calculate rates
                campaign_df = data['campaign_performance'].copy()
                campaign_df['reply_rate'] = (campaign_df['replies'] / campaign_df['total_messages'] * 100).fillna(0)
                campaign_df['open_rate'] = (campaign_df['opens'] / campaign_df['total_messages'] * 100).fillna(0)
                
                # Display metrics
                st.dataframe(
                    campaign_df[['campaign_name', 'total_messages', 'replies', 'reply_rate', 'open_rate']],
                    use_container_width=True
                )
                
                # Visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_bar = px.bar(
                        campaign_df,
                        x='campaign_name',
                        y='reply_rate',
                        title="Reply Rate by Campaign"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    fig_scatter = px.scatter(
                        campaign_df,
                        x='total_messages',
                        y='reply_rate',
                        size='replies',
                        hover_name='campaign_name',
                        title="Messages vs Reply Rate"
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("No campaign performance data available")
        
        with tab3:
            st.subheader("A/B Test Results")
            if not data['ab_test_results'].empty:
                ab_test_df = data['ab_test_results']
                
                # Display results table
                st.dataframe(ab_test_df, use_container_width=True)
                
                # Visualizations
                metrics = ['open_rate', 'click_rate', 'reply_rate']
                for metric in metrics:
                    if metric in ab_test_df.columns:
                        fig = px.bar(
                            ab_test_df,
                            x='name',
                            y=metric,
                            color='variant_id',
                            barmode='group',
                            title=f"A/B Test {metric.replace('_', ' ').title()} Comparison"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No A/B test data available")
        
        with tab4:
            st.subheader("Generate Reports")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📄 CSV Report")
                if st.button("Generate CSV Report", key="csv_btn"):
                    with st.spinner("Generating CSV report..."):
                        csv_content, filename = report_generator.generate_csv_report()
                        if filename:
                            st.download_button(
                                label="📥 Download CSV Report",
                                data=csv_content,
                                file_name=filename,
                                mime="text/csv"
                            )
                        else:
                            st.error(csv_content)
            
            with col2:
                st.markdown("### 📑 PDF Report")
                if st.button("Generate PDF Report", key="pdf_btn"):
                    with st.spinner("Generating PDF report..."):
                        pdf_content, filename = report_generator.generate_pdf_report()
                        if filename:
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=pdf_content,
                                file_name=filename,
                                mime="application/pdf"
                            )
                        else:
                            st.error(pdf_content)
        
        # Footer
        st.markdown("---")
        st.markdown(f"*Last updated: {data['last_updated']}*")
        
    except Exception as e:
        st.error(f"❌ Error loading analytics data: {str(e)}")
        logger.error(f"Streamlit app error: {e}")

if __name__ == "__main__":
    main()