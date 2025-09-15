"""
API Status Dashboard Component for Streamlit Frontend
Real-time connection indicators and health monitoring
"""
import streamlit as st
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd


class APIStatusDashboard:
    """Real-time API status dashboard component"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.api_endpoints = {
            "system_health": f"{backend_url}/api/v1/system/health",
            "api_health": f"{backend_url}/api/v1/system/health/{{provider}}",
            "rate_limits": f"{backend_url}/api/v1/system/rate-limits"
        }
    
    def render_status_strip(self):
        """Render hardware status strip with API indicators"""
        try:
            # Get system health data
            health_data = self._get_system_health()
            
            if not health_data:
                st.error("❌ Unable to connect to backend services")
                return
            
            # Create status indicators
            api_count = health_data.get("total_apis", 0)
            healthy_count = health_data.get("healthy_apis", 0)
            
            # Determine overall status
            if healthy_count == api_count:
                status_icon = "🟢"
                status_text = "ALL UP"
            elif healthy_count > 0:
                status_icon = "🟡"
                status_text = f"{healthy_count}/{api_count}"
            else:
                status_icon = "🔴"
                status_text = "DOWN"
            
            # Render status strip
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("🧠NPU", "85%", "2%")
            
            with col2:
                st.metric("📊GPU", "45%", "-5%")
            
            with col3:
                st.metric("💾RAM", "12GB", "1GB")
            
            with col4:
                st.metric("⚡APIs", status_text, status_icon)
            
            with col5:
                st.metric("📚F&O", "23%", "5%")
            
        except Exception as e:
            st.error(f"Error rendering status strip: {e}")
    
    def render_detailed_dashboard(self):
        """Render detailed API status dashboard"""
        st.subheader("🔌 API Connection Status")
        
        try:
            health_data = self._get_system_health()
            
            if not health_data:
                st.error("❌ Unable to retrieve API health data")
                return
            
            api_statuses = health_data.get("api_statuses", [])
            
            if not api_statuses:
                st.warning("No API connections configured")
                return
            
            # Create status cards
            cols = st.columns(len(api_statuses))
            
            for i, api_status in enumerate(api_statuses):
                with cols[i]:
                    self._render_api_status_card(api_status)
            
            # Detailed metrics table
            st.subheader("📊 Detailed Metrics")
            self._render_metrics_table(api_statuses)
            
            # Rate limits section
            st.subheader("🚦 Rate Limits")
            self._render_rate_limits()
            
        except Exception as e:
            st.error(f"Error rendering detailed dashboard: {e}")
    
    def _render_api_status_card(self, api_status: Dict):
        """Render individual API status card"""
        provider = api_status.get("provider", "unknown")
        status = api_status.get("status", "unknown")
        last_check = api_status.get("last_check", "")
        rate_limit = api_status.get("rate_limit_remaining", 0)
        
        # Status color and icon
        if status == "healthy":
            color = "🟢"
            status_text = "HEALTHY"
        elif status == "unhealthy":
            color = "🔴"
            status_text = "UNHEALTHY"
        else:
            color = "🟡"
            status_text = "UNKNOWN"
        
        # Format last check time
        try:
            if last_check:
                last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                time_diff = datetime.now() - last_check_dt.replace(tzinfo=None)
                last_check_str = f"{int(time_diff.total_seconds())}s ago"
            else:
                last_check_str = "Never"
        except:
            last_check_str = "Unknown"
        
        # Create card
        with st.container():
            st.markdown(f"""
            <div style="
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 16px;
                margin: 8px 0;
                background-color: {'#f0f9ff' if status == 'healthy' else '#fef2f2' if status == 'unhealthy' else '#fffbeb'}
            ">
                <h4 style="margin: 0; color: #333;">{color} {provider.upper()}</h4>
                <p style="margin: 4px 0; font-size: 14px; color: #666;">
                    Status: <strong>{status_text}</strong><br>
                    Last Check: {last_check_str}<br>
                    Rate Limit: {rate_limit}/sec
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_metrics_table(self, api_statuses: List[Dict]):
        """Render detailed metrics table"""
        if not api_statuses:
            return
        
        # Prepare data for table
        table_data = []
        for api_status in api_statuses:
            table_data.append({
                "Provider": api_status.get("provider", "").upper(),
                "Status": api_status.get("status", "").upper(),
                "Last Check": api_status.get("last_check", ""),
                "Rate Limit": api_status.get("rate_limit_remaining", 0),
                "Failures": api_status.get("consecutive_failures", 0)
            })
        
        # Create DataFrame and display
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
    
    def _render_rate_limits(self):
        """Render rate limits information"""
        try:
            rate_limits_data = self._get_rate_limits()
            
            if not rate_limits_data:
                st.warning("Unable to retrieve rate limits data")
                return
            
            rate_limits = rate_limits_data.get("rate_limits", {})
            
            if not rate_limits:
                st.info("No rate limits data available")
                return
            
            # Create rate limits table
            rate_table_data = []
            for provider, limits in rate_limits.items():
                rate_table_data.append({
                    "Provider": provider.upper(),
                    "Per Second": limits.get("requests_per_second", 0),
                    "Per Minute": limits.get("requests_per_minute", 0),
                    "Current/Second": limits.get("current_second", 0),
                    "Current/Minute": limits.get("current_minute", 0)
                })
            
            df = pd.DataFrame(rate_table_data)
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering rate limits: {e}")
    
    def _get_system_health(self) -> Optional[Dict]:
        """Get system health data from backend"""
        try:
            response = requests.get(self.api_endpoints["system_health"], timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                st.warning(f"Backend returned status code: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            st.warning(f"Failed to connect to backend: {e}")
            return None
    
    def _get_rate_limits(self) -> Optional[Dict]:
        """Get rate limits data from backend"""
        try:
            response = requests.get(self.api_endpoints["rate_limits"], timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except requests.exceptions.RequestException:
            return None
    
    def render_auto_refresh_dashboard(self, refresh_interval: int = 30):
        """Render dashboard with auto-refresh"""
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
        
        # Check if we need to refresh
        now = datetime.now()
        if (now - st.session_state.last_refresh).total_seconds() >= refresh_interval:
            st.rerun()
            st.session_state.last_refresh = now
        
        # Render dashboard
        self.render_detailed_dashboard()
        
        # Show refresh info
        time_until_refresh = refresh_interval - (now - st.session_state.last_refresh).total_seconds()
        st.caption(f"Auto-refresh in {int(time_until_refresh)} seconds")


# Example usage in Streamlit app
def main():
    """Example usage of API Status Dashboard"""
    st.set_page_config(
        page_title="AI Trading Engine - API Status",
        page_icon="🔌",
        layout="wide"
    )
    
    st.title("🔌 API Status Dashboard")
    
    # Initialize dashboard
    dashboard = APIStatusDashboard()
    
    # Render status strip
    dashboard.render_status_strip()
    
    st.divider()
    
    # Render detailed dashboard with auto-refresh
    dashboard.render_auto_refresh_dashboard(refresh_interval=30)
    
    # Manual refresh button
    if st.button("🔄 Refresh Now"):
        st.rerun()


if __name__ == "__main__":
    main()

