import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from config import settings
import logging
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = settings.DATABASE_URL

def get_analytics():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            total_messages = pd.read_sql("SELECT COUNT(*) FROM message_log WHERE status != 'BOUNCED'", conn).iloc[0, 0]
            replied_messages = pd.read_sql("SELECT COUNT(*) FROM message_log WHERE status = 'REPLIED'", conn).iloc[0, 0]
            response_rate = (replied_messages / total_messages * 100) if total_messages > 0 else 0
            
            enrolled_prospects = pd.read_sql("SELECT COUNT(*) FROM affiliate_prospects WHERE status = 'ENROLLED'", conn).iloc[0, 0]
            total_prospects = pd.read_sql("SELECT COUNT(*) FROM affiliate_prospects", conn).iloc[0, 0]
            conversion_rate = (enrolled_prospects / total_prospects * 100) if total_prospects > 0 else 0
            
            status_counts = pd.read_sql("SELECT status, COUNT(*) as count FROM message_log GROUP BY status", conn)
            
            ab_tests = pd.read_sql("SELECT a.name, r.variant_id, r.sent_count, r.open_rate, r.click_rate, r.reply_rate FROM ab_tests a JOIN ab_test_results r ON a.id = r.ab_test_id", conn)
            
            return {
                "response_rate": f"{response_rate:.2f}%",
                "conversion_rate": f"{conversion_rate:.2f}%",
                "status_counts": status_counts,
                "ab_tests": ab_tests
            }
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        return {"error": str(e)}

def export_report(format_type):
    analytics = get_analytics()
    if "error" in analytics:
        return analytics["error"], None
    
    df = pd.DataFrame({
        "Metric": ["Response Rate", "Conversion Rate"],
        "Value": [analytics["response_rate"], analytics["conversion_rate"]]
    })
    
    if format_type == "CSV":
        return df.to_csv(index=False), "report.csv"
    elif format_type == "PDF":
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "Affiliate Outreach Report")
        for i, row in df.iterrows():
            c.drawString(100, 700 - i * 20, f"{row['Metric']}: {row['Value']}")
        c.save()
        pdf = buffer.getvalue()
        buffer.close()
        return pdf, "report.pdf"
    return "Unsupported format", None

st.set_page_config(page_title="Affiliate Outreach Analytics", layout="wide")
st.title("Agentic Affiliate Outreach System - Analytics (Phase 4)")

st.header("System KPIs")
if st.button("Refresh Analytics"):
    analytics = get_analytics()
    if "error" not in analytics:
        st.metric("Response Rate", analytics["response_rate"])
        st.metric("Conversion Rate", analytics["conversion_rate"])
        
        st.subheader("Message Status Distribution")
        status_df = analytics["status_counts"]
        fig = px.bar(status_df, x="status", y="count", title="Message Status Counts", color="status")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("A/B Test Results")
        ab_test_df = analytics["ab_tests"]
        st.dataframe(ab_test_df)
        
        # Bar chart for A/B test metrics
        if not ab_test_df.empty:
            metrics = ["open_rate", "click_rate", "reply_rate"]
            for metric in metrics:
                fig = px.bar(
                    ab_test_df,
                    x="name",
                    y=metric,
                    color="variant_id",
                    barmode="group",
                    title=f"A/B Test {metric.replace('_', ' ').title()} by Campaign"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Export Report")
        format_type = st.selectbox("Format", ["CSV", "PDF"])
        if st.button("Generate Report"):
            report, filename = export_report(format_type)
            if filename:
                st.download_button(
                    label="Download Report",
                    data=report,
                    file_name=filename,
                    mime="text/csv" if format_type == "CSV" else "application/pdf"
                )
            else:
                st.error("Failed to generate report")
    else:
        st.error(analytics["error"])