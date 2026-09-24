import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from core.logger import get_logger

logger = get_logger(__name__)

def generate_chart(df, chart):
    
    chart_type= chart.get("chart_type", "").lower()
    x_col=chart.get("x_column")
    y_col=chart.get("y_column")
    title=chart.get("title")
    
    if x_col and x_col not in df.columns:
        logger.warning(f"x_column '{x_col}' not in dataframe - skipping chart: {title}")
        return None
    if y_col and y_col not in df.columns:
            logger.warning(f"x_column '{y_col}' not in dataframe - skipping chart: {title}")
            return None
    
    try:
        fig = None
        
        if chart_type=="bar":
            if x_col and y_col:
                agg = df.groupby(x_col)[y_col].mean().reset_index()
                fig = px.bar(agg, x=x_col, y=y_col, title=title)
            elif x_col:
                counts = df[x_col].value_counts().reset_index()
                counts.columns = [x_col, "count"]
                fig = px.bar(counts, x=x_col, y="count", title=title)
            
        elif chart_type=="line":
            fig = px.line(df, x=x_col, y=y_col, title=title)
            
        elif chart_type=="scatter":
            fig = px.scatter(df, x=x_col, y=y_col, title=title, opacity=0.6)
            
        elif chart_type=="histogram":
            col = x_col or y_col
            fig = px.histogram(df, x=col, title=title)
            
        elif chart_type == "box":
            if x_col and y_col:
                fig = px.box(df, x=x_col, y=y_col, title=title)
            else:
                col = y_col or x_col
                fig = px.box(df, y=col, title=title)
                
        elif chart_type == "pie":
            if x_col:
                counts = df[x_col].value_counts().reset_index()
                counts.columns = [x_col, "count"]
                fig = px.pie(counts, names=x_col, values="count", title=title)
                
        elif chart_type == "heatmap":
            numeric_df = df.select_dtypes(include="number")
            corr = numeric_df.corr().round(3)
            fig = go.Figure(data=go.Heatmap(
                    z=corr.values, x=list(corr.columns), y=list(corr.index),
                    colorscale="RdBu", zmid=0,)
            )
            fig.update_layout(title=title)
        
        if fig is None:
            logger.warning(f"Could not generate chart for type {chart_type}: {title}")
            return None
            
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40),
        )
        
        return {
            "chart_type":chart_type,
            "title": title,
            "plotly_json": json.loads(fig.to_json()),
        }

    except Exception as e:
        logger.error(f"Chart generation failed for '{title}': {e}")
        return None


def generate_all_charts(df, visualisations):
    charts=[]
    for chart in visualisations:
        dchart = generate_chart(df,chart)
        if dchart:
            charts.append(dchart)
            logger.info(f"Chart generated: [{chart['chart_type'].upper()}] {chart['title']}")
    logger.info(f"Total charts generated: {len(charts)}/{len(visualisations)} ")
    return charts