from pathlib import Path
import json

import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Monsoon Rainfall Intelligence",
    page_icon="🌧️",
    layout="wide",
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

GEOJSON_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "district_regime_corrected_forecast.geojson"
)


@st.cache_data
def load_forecast_data():
    forecast = gpd.read_file(GEOJSON_FILE)

    forecast["date"] = pd.to_datetime(
        forecast["date"]
    )

    forecast["shapeID"] = (
        forecast["shapeID"].astype(str)
    )

    return forecast


forecast_gdf = load_forecast_data()


layer_settings = {
    "Raw GEFS rainfall": {
        "column": "gefs_mean_mm",
        "label": "Raw GEFS rainfall (mm/day)",
        "scale": "Blues",
        "range": (0, 150),
    },
    "Global corrected rainfall": {
        "column": "global_corrected_mean_mm",
        "label": "Global corrected rainfall (mm/day)",
        "scale": "Blues",
        "range": (0, 150),
    },
    "Regime-corrected rainfall": {
        "column": "regime_corrected_mean_mm",
        "label": "Regime-corrected rainfall (mm/day)",
        "scale": "Blues",
        "range": (0, 150),
    },
    "Observed IMERG rainfall": {
        "column": "observed_mean_mm",
        "label": "IMERG observed rainfall (mm/day)",
        "scale": "Blues",
        "range": (0, 150),
    },
    "Heavy-rain probability": {
        "column": "heavy_probability_max",
        "label": "Heavy-rain probability",
        "scale": "YlOrRd",
        "range": (0, 0.60),
    },
}


st.title("Regime-Aware Monsoon Rainfall Intelligence")

st.caption(
    "District-level prototype using GEFS forecasts, "
    "IMERG observations and regime-aware AI correction."
)


available_dates = sorted(
    forecast_gdf["date"].dt.date.unique()
)

with st.sidebar:
    st.header("Forecast controls")

    selected_date = st.selectbox(
        "Forecast date",
        available_dates,
        index=0,
    )

    selected_layer = st.selectbox(
        "Map layer",
        list(layer_settings),
        index=2,
    )

    st.divider()

    st.warning(
        "Research prototype only. Probability signals "
        "are not official weather warnings."
    )


selected_data = forecast_gdf[
    forecast_gdf["date"].dt.date == selected_date
].copy()

settings = layer_settings[selected_layer]
map_column = settings["column"]


watch_count = int(
    (
        selected_data["heavy_probability_max"]
        >= 0.10
    ).sum()
)

maximum_probability = selected_data[
    "heavy_probability_max"
].max()

average_raw = selected_data[
    "gefs_mean_mm"
].mean()

average_corrected = selected_data[
    "regime_corrected_mean_mm"
].mean()


metric_1, metric_2, metric_3, metric_4 = st.columns(4)

metric_1.metric(
    "Districts",
    f"{selected_data['shapeID'].nunique():,}",
)

metric_2.metric(
    "Experimental watches",
    f"{watch_count:,}",
)

metric_3.metric(
    "Maximum heavy probability",
    f"{maximum_probability:.1%}",
)

metric_4.metric(
    "Average corrected rainfall",
    f"{average_corrected:.1f} mm",
    delta=f"{average_corrected - average_raw:.1f} mm",
    delta_color="off",
)


map_geometry = selected_data[
    [
        "shapeID",
        "geometry",
    ]
].copy()

with st.spinner("Preparing district map..."):
    map_geometry = selected_data[
        [
            "shapeID",
            "geometry",
        ]
    ].copy()

    map_geometry["shapeID"] = (
        map_geometry["shapeID"].astype(str)
    )

    map_geometry["geometry"] = (
        map_geometry.geometry.simplify(
            tolerance=0.02,
            preserve_topology=True,
        )
    )

    geojson_data = json.loads(
        map_geometry.to_json(
            drop_id=True
        )
    )

    plot_data = pd.DataFrame(
        selected_data.drop(
            columns=["geometry"]
        )
    )

    plot_data["shapeID"] = (
        plot_data["shapeID"].astype(str)
    )

    plot_data["date"] = (
        pd.to_datetime(plot_data["date"])
        .dt.strftime("%Y-%m-%d")
    )

    figure = px.choropleth_map(
        plot_data,
        geojson=geojson_data,
        locations="shapeID",
        featureidkey="properties.shapeID",
        color=map_column,
        hover_name="shapeName",
        hover_data={
            "shapeID": False,
            "date": True,
            "gefs_mean_mm": ":.1f",
            "global_corrected_mean_mm": ":.1f",
            "regime_corrected_mean_mm": ":.1f",
            "observed_mean_mm": ":.1f",
            "heavy_probability_max": ":.1%",
            "risk_level": True,
        },
        labels={
            "date": "Date",
            "gefs_mean_mm": "Raw GEFS (mm)",
            "global_corrected_mean_mm": (
                "Global corrected (mm)"
            ),
            "regime_corrected_mean_mm": (
                "Regime corrected (mm)"
            ),
            "observed_mean_mm": "IMERG observed (mm)",
            "heavy_probability_max": (
                "Heavy-rain probability"
            ),
            "risk_level": "Risk category",
            map_column: settings["label"],
        },
        color_continuous_scale=settings["scale"],
        range_color=settings["range"],
        center={
            "lat": 22.5,
            "lon": 79.0,
        },
        zoom=3.3,
        opacity=0.8,
        map_style="carto-positron",
        title=(
            f"{selected_layer} — "
            f"{selected_date:%d %B %Y}"
        ),
        height=720,
    )

    figure.update_traces(
        marker_line_width=0.25,
        marker_line_color="#6b7280",
    )

    figure.update_layout(
        margin={
            "l": 0,
            "r": 0,
            "t": 50,
            "b": 0,
        },
    )

st.plotly_chart(
    figure,
    width="stretch",
    theme=None,
    config={
        "displaylogo": False,
        "scrollZoom": True,
    },
)


left_column, right_column = st.columns([1, 1])

with left_column:
    st.subheader("Highest heavy-rain signals")

    highest_risk = (
        selected_data[
            [
                "shapeName",
                "regime_corrected_mean_mm",
                "observed_mean_mm",
                "heavy_probability_max",
                "risk_level",
            ]
        ]
        .sort_values(
            "heavy_probability_max",
            ascending=False,
        )
        .head(10)
        .rename(
            columns={
                "shapeName": "District",
                "regime_corrected_mean_mm": (
                    "Corrected rainfall (mm)"
                ),
                "observed_mean_mm": (
                    "Observed rainfall (mm)"
                ),
                "heavy_probability_max": (
                    "Heavy probability"
                ),
                "risk_level": "Signal",
            }
        )
    )

    st.dataframe(
        highest_risk,
        width="stretch",
        hide_index=True,
        column_config={
            "Corrected rainfall (mm)": (
                st.column_config.NumberColumn(
                    format="%.1f"
                )
            ),
            "Observed rainfall (mm)": (
                st.column_config.NumberColumn(
                    format="%.1f"
                )
            ),
            "Heavy probability": (
                st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=1,
                    format="%.1%%",
                )
            ),
        },
    )


with right_column:
    st.subheader("Forecast comparison")

    comparison = (
        selected_data[
            [
                "gefs_mean_mm",
                "global_corrected_mean_mm",
                "regime_corrected_mean_mm",
                "observed_mean_mm",
            ]
        ]
        .mean()
        .rename(
            {
                "gefs_mean_mm": "Raw GEFS",
                "global_corrected_mean_mm": (
                    "Global corrected"
                ),
                "regime_corrected_mean_mm": (
                    "Regime corrected"
                ),
                "observed_mean_mm": "IMERG observed",
            }
        )
        .reset_index()
    )

    comparison.columns = [
        "Product",
        "Mean rainfall",
    ]

    comparison_figure = px.bar(
        comparison,
        x="Product",
        y="Mean rainfall",
        color="Product",
        text_auto=".1f",
        labels={
            "Mean rainfall": (
                "Mean district rainfall (mm/day)"
            )
        },
    )

    comparison_figure.update_layout(
        showlegend=False,
        height=420,
    )

    st.plotly_chart(
        comparison_figure,
        width="stretch",
    )


with st.expander("Model verification and limitations"):
    st.markdown(
        """
- Regime-classifier balanced accuracy: **0.6089**
- Regime-aware 31-day RMSE: **19.2833 mm/day**
- Raw GEFS 31-day RMSE: **20.3831 mm/day**
- Heavy-rain ROC-AUC: **0.9099**
- Heavy-rain CSI: **0.0945**
- Heavy-rain POD: **0.2074**
- Heavy-rain FAR: **0.8521**
- Training period is limited to July 2018.
- Very-heavy rainfall probabilities are experimental.
- Bias correction improves rainfall magnitude but does not fully correct spatial displacement.
        """
    )