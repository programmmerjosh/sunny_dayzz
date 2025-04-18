import altair as alt
import pandas as pd

def build_time_chart(df, facet_by_date=False, height=300):
    """
    Build a line chart (optionally faceted by date) showing cloud cover over time.

    Args:
        df (pd.DataFrame): DataFrame containing 'Time', 'Cloud Cover (%)', 'Source', and optionally 'Date'
        facet_by_date (bool): If True, create a separate chart per date
        height (int): Chart height

    Returns:
        alt.Chart: The configured Altair chart
    """

    base = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("Time:O", title="Time (UTC)"),
        y=alt.Y("Cloud Cover (%):Q", scale=alt.Scale(domain=[0, 100])),
        text=alt.condition(
        alt.datum["Cloud Cover (%)"] == None,
        alt.value("—"),
        alt.value("")),
        color=alt.Color("Source:N"),
        tooltip=["Date", "Time", "Source", "Cloud Cover (%)"] if "Date" in df.columns else ["Time", "Source", "Cloud Cover (%)"]
    ).properties(
        height=height
    )

    if facet_by_date and "Date" in df.columns:
        return base.facet(
            column=alt.Column("Date:T", title="Forecast Date")
        ).resolve_scale(
            y="shared"
        )

    return base

# Pie chart helper
def build_pie_chart(sunny, cloudy, use_len=False):
    df = pd.DataFrame({
        "Type": ["Sunny", "Cloudy"],
        "Count": [len(sunny), len(cloudy)] if use_len else [sunny, cloudy]
    })
    return alt.Chart(df).mark_arc(innerRadius=50).encode(
        theta="Count:Q",
        color="Type:N"
    ).properties(width=300, height=300)