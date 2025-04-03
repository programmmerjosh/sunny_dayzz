import altair as alt
import pandas as pd

def build_timeline_chart(df_timeline, color_scheme):
    return alt.Chart(df_timeline).mark_line(point=True).encode(
    x=alt.X("Date:T", title="Date"),
    y=alt.Y("Cloud Cover (%):Q"),
    color=alt.Color("Time of Day:N",
                    sort=list(color_scheme.keys()),
                    scale=alt.Scale(
                        domain=list(color_scheme.keys()),
                        range=list(color_scheme.values())
                    )),
    tooltip=["Date", "Time of Day", "Cloud Cover (%)"],
    detail="Time of Day:N"  # 👈 Ensures each time-of-day series gets its own line
).properties(
    width="container",
    height=300
)


def build_pie_chart(sunny_days, cloudy_days):
    summary_df = pd.DataFrame({
    "Type": ["Sunny", "Cloudy"],
    "Count": [len(sunny_days), len(cloudy_days)]
})
    return alt.Chart(summary_df).mark_arc(innerRadius=50).encode(
    theta="Count:Q",
    color="Type:N"
).properties(
    width=300,
    height=300
)