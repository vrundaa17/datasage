import streamlit as st
import plotly.graph_objects as go


def render_chart(chart: dict):
    plotly_json = chart.get("plotly_json")
    title = chart.get("title", "Chart")
    
    if not plotly_json:
        st.warning(f"No chart data for: {title}")
        return
    
    try:
        fig = go.Figure(plotly_json)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not render chart '{title}': {e}")


def render_all_charts(charts: list):
    if not charts:
        st.info("No charts generated for this dataset.")
        return
    cols = st.columns(2)
    for i, chart in enumerate(charts):
        with cols[i % 2]:
            st.caption(chart.get("title", ""))
            render_chart(chart)