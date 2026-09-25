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


st.markdown(
    """
    <style>
    /* Keep the dashboard comfortable on laptops without wasting space. */
    .block-container {
        max-width: 1500px;
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        padding: 0.75rem 0.9rem;
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 0.75rem;
        background: rgba(128, 128, 128, 0.04);
        min-height: 7.25rem;
    }

    [data-testid="stMetricLabel"] {
        min-height: 2.7rem;
        align-items: flex-start;
    }

    [data-testid="stMetricValue"] {
        font-size: clamp(1.55rem, 2.3vw, 2.35rem);
    }

    /* Let wide dataframes scroll instead of squeezing their contents. */
    [data-testid="stDataFrame"] {
        overflow-x: auto;
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 0.75rem 0.8rem 1.5rem;
        }

        h1 {
            font-size: 1.75rem !important;
            line-height: 1.15 !important;
        }

        h2, h3 {
            font-size: 1.35rem !important;
            line-height: 1.2 !important;
        }

        div[data-testid="stAlert"] {
            padding: 0.75rem;
        }

        .st-key-primary_metrics [data-testid="stHorizontalBlock"],
        .st-key-trust_metrics [data-testid="stHorizontalBlock"] {
            display: flex;
            flex-direction: row;
            flex-wrap: wrap;
            gap: 0.55rem;
        }

        .st-key-primary_metrics [data-testid="column"],
        .st-key-trust_metrics [data-testid="column"] {
            flex: 1 1 calc(50% - 0.55rem) !important;
            width: calc(50% - 0.55rem) !important;
            min-width: 0 !important;
        }

        [data-testid="stMetric"] {
            padding: 0.65rem 0.7rem;
            min-height: 6.4rem;
        }

        [data-testid="stMetricLabel"] {
            min-height: 2.35rem;
            font-size: 0.82rem;
            line-height: 1.15;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.45rem;
        }

        [data-testid="stMetricDelta"] {
            font-size: 0.75rem;
        }

        /* Avoid an oversized gap above Plotly charts on narrow screens. */
        [data-testid="stPlotlyChart"] {
            margin-top: -0.25rem;
        }

        .stDownloadButton button {
            width: 100%;
        }
    }

    @media (max-width: 390px) {
        .st-key-primary_metrics [data-testid="column"],
        .st-key-trust_metrics [data-testid="column"] {
            flex-basis: 100% !important;
            width: 100% !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BOUNDARY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "india_districts_simplified.geojson"
)

FORECAST_CANDIDATES = [
    (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "district_rainfall_forecast_trust_20180727_20180731.csv"
    ),
    (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "district_regime_corrected_forecast_20180727_20180731.csv"
    ),
    (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "district_rainfall_forecast_20180727_20180731.csv"
    ),
]

FORECAST_FILE = next(
    (
        candidate
        for candidate in FORECAST_CANDIDATES
        if candidate.exists()
    ),
    FORECAST_CANDIDATES[0],
)


if not BOUNDARY_FILE.exists():
    st.error(
        f"District boundary file not found:\n{BOUNDARY_FILE}"
    )
    st.stop()

if not FORECAST_FILE.exists():
    st.error(
        "No supported forecast file was found. "
        "Generate the Stage 6A trust dataset or the legacy "
        "deployment dataset first. Checked:\n"
        + "\n".join(
            str(path)
            for path in FORECAST_CANDIDATES
        )
    )
    st.stop()


@st.cache_data
def load_forecast_data():
    boundaries = gpd.read_file(
        BOUNDARY_FILE
    )

    forecast = pd.read_csv(
        FORECAST_FILE,
        parse_dates=["date"],
    )

    boundaries["shapeID"] = (
        boundaries["shapeID"].astype(str)
    )

    forecast["shapeID"] = (
        forecast["shapeID"].astype(str)
    )

    boundaries = boundaries[
        [
            "shapeID",
            "shapeName",
            "geometry",
        ]
    ].copy()

    return boundaries, forecast


districts_gdf, forecast_df = (
    load_forecast_data()
)


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


optional_layer_settings = {
    "Observation confidence": {
        "column": "observation_confidence_mean",
        "label": "Observation confidence",
        "scale": "RdYlGn",
        "range": (0, 1),
    },
    "Low-confidence cell fraction": {
        "column": "low_confidence_cell_fraction",
        "label": "Low-confidence grid-cell fraction",
        "scale": "YlOrRd",
        "range": (0, 1),
    },
    "Observation reliability signal": {
        "column": "observation_reliability_signal",
        "label": "Observation reliability signal",
        "kind": "categorical",
        "colors": {
            "Higher observation agreement": "#2ca25f",
            "Mixed observation agreement": "#fec44f",
            "Elevated observation disagreement": "#de2d26",
        },
    },
    "Geographic regime": {
        "column": "dominant_geographic_regime",
        "label": "Dominant geographic regime",
        "kind": "categorical",
        "colors": {
            "Interior plain": "#74a9cf",
            "Coastal plain": "#2b8cbe",
            "Interior orographic": "#a1d99b",
            "Coastal orographic": "#31a354",
        },
    },
    "Experimental selective-trust rainfall": {
        "column": "selective_trust_raw_mean_mm",
        "label": (
            "Experimental selective-trust raw blend "
            "(mm/day)"
        ),
        "scale": "Blues",
        "range": (0, 150),
    },
}


for layer_name, layer_config in (
    optional_layer_settings.items()
):
    if layer_config["column"] in forecast_df.columns:
        layer_settings[layer_name] = layer_config


trust_columns_available = {
    "observation_confidence_mean",
    "low_confidence_cell_fraction",
    "observation_reliability_signal",
}.issubset(forecast_df.columns)


st.title(
    "Regime-Aware Monsoon Rainfall Intelligence"
)

st.caption(
    "District-level prototype using GEFS forecasts, "
    "IMERG observations, independent IMD validation, "
    "geographic context and regime-aware AI correction."
)

st.info(
    "Scope: the research evaluation uses all 31 days of "
    "July 2018 at grid level. This dashboard packages only "
    "27–31 July 2018 as a five-day, district-level MVP "
    "demonstration. The dashboard dates are not presented "
    "as an independent test set."
)


available_dates = sorted(
    forecast_df["date"].dt.date.unique()
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
        list(layer_settings.keys()),
        index=2,
    )

    st.divider()

    st.warning(
        "Research prototype only. Probability signals "
        "are not official weather warnings."
    )

    if trust_columns_available:
        st.success(
            "RAIN-Trust reliability layers are available."
        )
    else:
        st.info(
            "Legacy forecast dataset loaded. Generate the "
            "Stage 6A trust CSV to enable observation-"
            "reliability layers."
        )


selected_attributes = forecast_df[
    forecast_df["date"].dt.date
    == selected_date
].copy()

selected_attributes = selected_attributes.drop(
    columns=["shapeName"],
    errors="ignore",
)

selected_data = districts_gdf.merge(
    selected_attributes,
    on="shapeID",
    how="inner",
    validate="one_to_one",
)


if selected_data.empty:
    st.error(
        "No district forecast data are available "
        "for the selected date."
    )
    st.stop()


settings = layer_settings[selected_layer]
map_column = settings["column"]


watch_count = int(
    (
        selected_data["heavy_probability_max"]
        >= 0.10
    ).sum()
)

maximum_probability = float(
    selected_data[
        "heavy_probability_max"
    ].max()
)

average_raw = float(
    selected_data[
        "gefs_mean_mm"
    ].mean()
)

average_corrected = float(
    selected_data[
        "regime_corrected_mean_mm"
    ].mean()
)


with st.container(key="primary_metrics"):
    metric_1, metric_2, metric_3, metric_4 = (
        st.columns(4, gap="small")
    )

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
        delta=(
            f"{average_corrected - average_raw:.1f} mm"
        ),
        delta_color="off",
    )


if trust_columns_available:
    elevated_count = int(
        (
            selected_data[
                "observation_reliability_signal"
            ]
            == "Elevated observation disagreement"
        ).sum()
    )

    mean_observation_confidence = float(
        selected_data[
            "observation_confidence_mean"
        ].mean()
    )

    mean_low_confidence_fraction = float(
        selected_data[
            "low_confidence_cell_fraction"
        ].mean()
    )

    with st.container(key="trust_metrics"):
        trust_metric_1, trust_metric_2, trust_metric_3 = (
            st.columns(3, gap="small")
        )

        trust_metric_1.metric(
            "Elevated-disagreement districts",
            f"{elevated_count:,}",
        )

        trust_metric_2.metric(
            "Mean observation confidence",
            f"{mean_observation_confidence:.1%}",
        )

        trust_metric_3.metric(
            "Mean low-confidence fraction",
            f"{mean_low_confidence_fraction:.1%}",
        )


st.subheader("District forecast map")


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

    geojson_data = json.loads(
        map_geometry.to_json()
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

    hover_formats = {
        "shapeID": False,
        "date": True,
        "gefs_mean_mm": ":.1f",
        "global_corrected_mean_mm": ":.1f",
        "regime_corrected_mean_mm": ":.1f",
        "observed_mean_mm": ":.1f",
        "heavy_probability_max": ":.1%",
        "risk_level": True,
        "observation_confidence_mean": ":.1%",
        "low_confidence_cell_fraction": ":.1%",
        "low_confidence_risk_mean": ":.1%",
        "observation_reliability_signal": True,
        "dominant_geographic_regime": True,
        "selective_trust_raw_mean_mm": ":.1f",
        "selective_adjustment_mean_mm": ":.1f",
    }

    hover_data = {
        column: value
        for column, value in hover_formats.items()
        if column in plot_data.columns
    }

    labels = {
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
        "observation_confidence_mean": (
            "Observation confidence"
        ),
        "low_confidence_cell_fraction": (
            "Low-confidence cell fraction"
        ),
        "low_confidence_risk_mean": (
            "Low-confidence risk"
        ),
        "observation_reliability_signal": (
            "Reliability signal"
        ),
        "dominant_geographic_regime": (
            "Geographic regime"
        ),
        "selective_trust_raw_mean_mm": (
            "Experimental selective trust (mm)"
        ),
        "selective_adjustment_mean_mm": (
            "Experimental adjustment (mm)"
        ),
        map_column: settings["label"],
    }

    map_arguments = {
        "data_frame": plot_data,
        "geojson": geojson_data,
        "locations": "shapeID",
        "featureidkey": "properties.shapeID",
        "color": map_column,
        "hover_name": "shapeName",
        "hover_data": hover_data,
        "labels": labels,
        "center": {
            "lat": 22.5,
            "lon": 79.0,
        },
        "zoom": 3.0,
        "opacity": 0.80,
        "map_style": "carto-positron",
        "height": 680,
    }

    if settings.get("kind") == "categorical":
        map_arguments["color_discrete_map"] = (
            settings["colors"]
        )
    else:
        map_arguments["color_continuous_scale"] = (
            settings["scale"]
        )
        map_arguments["range_color"] = settings["range"]

    figure = px.choropleth_map(**map_arguments)

    figure.update_traces(
        marker_line_width=0.25,
        marker_line_color="#6b7280",
    )

    figure.update_layout(
        margin={
            "l": 0,
            "r": 0,
            "t": 8,
            "b": 86,
        },
        coloraxis_colorbar={
            "orientation": "h",
            "x": 0.5,
            "xanchor": "center",
            "y": -0.08,
            "yanchor": "top",
            "len": 0.82,
            "thickness": 14,
            "title": {
                "side": "top",
                "text": settings["label"],
            },
        },
        legend={
            "orientation": "h",
            "x": 0.0,
            "xanchor": "left",
            "y": -0.08,
            "yanchor": "top",
            "title": {"text": ""},
        },
    )


st.caption(
    f"{selected_layer} — "
    f"{selected_date:%d %B %Y}"
)

st.plotly_chart(
    figure,
    width="stretch",
    theme=None,
    config={
        "displaylogo": False,
        "displayModeBar": False,
        "scrollZoom": False,
        "responsive": True,
    },
)


left_column, right_column = st.columns(
    [1, 1],
    gap="large",
)


with left_column:
    st.subheader(
        "Highest heavy-rain signals"
    )

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
        .copy()
    )

    highest_risk[
        "heavy_probability_percent"
    ] = (
        highest_risk[
            "heavy_probability_max"
        ]
        * 100
    )

    highest_risk = highest_risk.drop(
        columns=["heavy_probability_max"]
    )

    highest_risk = highest_risk.rename(
        columns={
            "shapeName": "District",
            "regime_corrected_mean_mm": (
                "Corrected rainfall (mm)"
            ),
            "observed_mean_mm": (
                "Observed rainfall (mm)"
            ),
            "heavy_probability_percent": (
                "Heavy probability (%)"
            ),
            "risk_level": "Signal",
        }
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
            "Heavy probability (%)": (
                st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=100,
                    format="%.1f%%",
                )
            ),
        },
    )


with right_column:
    st.subheader(
        "Forecast comparison"
    )

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
                "observed_mean_mm": (
                    "IMERG observed"
                ),
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
        margin={
            "l": 0,
            "r": 0,
            "t": 20,
            "b": 0,
        },
    )

    st.plotly_chart(
        comparison_figure,
        width="stretch",
    )


if trust_columns_available:
    st.subheader("Observation reliability diagnostics")

    st.caption(
        "These diagnostics compare independent IMERG and "
        "IMD rainfall products. Elevated disagreement means "
        "the observational reference is less certain; it is "
        "not an official warning and does not by itself prove "
        "that the forecast is incorrect."
    )

    reliability_left, reliability_right = st.columns(
        [1, 2],
        gap="large",
    )

    with reliability_left:
        reliability_summary = (
            selected_data.groupby(
                "observation_reliability_signal",
                dropna=False,
            )
            .agg(
                Districts=("shapeID", "nunique"),
                **{
                    "Mean confidence": (
                        "observation_confidence_mean",
                        "mean",
                    ),
                    "Mean low-confidence fraction": (
                        "low_confidence_cell_fraction",
                        "mean",
                    ),
                },
            )
            .reset_index()
            .rename(
                columns={
                    "observation_reliability_signal": (
                        "Reliability signal"
                    )
                }
            )
        )

        st.markdown("**Districts by reliability signal**")
        st.dataframe(
            reliability_summary,
            width="stretch",
            hide_index=True,
            column_config={
                "Mean confidence": (
                    st.column_config.NumberColumn(
                        format="percent"
                    )
                ),
                "Mean low-confidence fraction": (
                    st.column_config.NumberColumn(
                        format="percent"
                    )
                ),
            },
        )

    with reliability_right:
        reliability_columns = [
            "shapeName",
            "observation_confidence_mean",
            "low_confidence_cell_fraction",
            "observation_reliability_signal",
        ]

        for optional_column in [
            "low_confidence_risk_mean",
            "selective_adjustment_mean_mm",
            "dominant_geographic_regime",
        ]:
            if optional_column in selected_data.columns:
                reliability_columns.append(optional_column)

        lowest_confidence = (
            selected_data[reliability_columns]
            .sort_values(
                [
                    "low_confidence_cell_fraction",
                    "observation_confidence_mean",
                ],
                ascending=[False, True],
            )
            .head(15)
            .rename(
                columns={
                    "shapeName": "District",
                    "observation_confidence_mean": (
                        "Observation confidence"
                    ),
                    "low_confidence_cell_fraction": (
                        "Low-confidence fraction"
                    ),
                    "low_confidence_risk_mean": (
                        "Low-confidence risk"
                    ),
                    "observation_reliability_signal": (
                        "Reliability signal"
                    ),
                    "selective_adjustment_mean_mm": (
                        "Experimental adjustment (mm)"
                    ),
                    "dominant_geographic_regime": (
                        "Geographic regime"
                    ),
                }
            )
        )

        st.markdown("**Highest observation-disagreement districts**")
        st.dataframe(
            lowest_confidence,
            width="stretch",
            hide_index=True,
            column_config={
                "Observation confidence": (
                    st.column_config.NumberColumn(
                        format="percent"
                    )
                ),
                "Low-confidence fraction": (
                    st.column_config.NumberColumn(
                        format="percent"
                    )
                ),
                "Low-confidence risk": (
                    st.column_config.NumberColumn(
                        format="percent"
                    )
                ),
                "Experimental adjustment (mm)": (
                    st.column_config.NumberColumn(
                        format="%.1f"
                    )
                ),
            },
        )


st.subheader("District forecast table")

forecast_table_columns = [
    "shapeName",
    "gefs_mean_mm",
    "global_corrected_mean_mm",
    "regime_corrected_mean_mm",
    "observed_mean_mm",
    "heavy_probability_max",
    "very_heavy_probability_max",
    "risk_level",
]

for optional_column in [
    "observation_confidence_mean",
    "low_confidence_cell_fraction",
    "observation_reliability_signal",
    "dominant_geographic_regime",
    "selective_trust_raw_mean_mm",
    "selective_adjustment_mean_mm",
]:
    if optional_column in selected_data.columns:
        forecast_table_columns.append(optional_column)

forecast_table = selected_data[
    forecast_table_columns
].copy()

forecast_table[
    "heavy_probability_max"
] *= 100

forecast_table[
    "very_heavy_probability_max"
] *= 100

for percentage_column in [
    "observation_confidence_mean",
    "low_confidence_cell_fraction",
]:
    if percentage_column in forecast_table.columns:
        forecast_table[percentage_column] *= 100

forecast_table = forecast_table.rename(
    columns={
        "shapeName": "District",
        "gefs_mean_mm": "Raw GEFS (mm)",
        "global_corrected_mean_mm": (
            "Global corrected (mm)"
        ),
        "regime_corrected_mean_mm": (
            "Regime corrected (mm)"
        ),
        "observed_mean_mm": (
            "IMERG observed (mm)"
        ),
        "heavy_probability_max": (
            "Heavy probability (%)"
        ),
        "very_heavy_probability_max": (
            "Very-heavy probability (%)"
        ),
        "risk_level": "Signal",
        "observation_confidence_mean": (
            "Observation confidence (%)"
        ),
        "low_confidence_cell_fraction": (
            "Low-confidence fraction (%)"
        ),
        "observation_reliability_signal": (
            "Observation reliability"
        ),
        "dominant_geographic_regime": (
            "Geographic regime"
        ),
        "selective_trust_raw_mean_mm": (
            "Experimental selective trust (mm)"
        ),
        "selective_adjustment_mean_mm": (
            "Experimental adjustment (mm)"
        ),
    }
)

forecast_table = forecast_table.sort_values(
    "Heavy probability (%)",
    ascending=False,
)

forecast_column_config = {}

for percentage_column in [
    "Observation confidence (%)",
    "Low-confidence fraction (%)",
]:
    if percentage_column in forecast_table.columns:
        forecast_column_config[percentage_column] = (
            st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%.1f%%",
            )
        )

for rainfall_column in [
    "Experimental selective trust (mm)",
    "Experimental adjustment (mm)",
]:
    if rainfall_column in forecast_table.columns:
        forecast_column_config[rainfall_column] = (
            st.column_config.NumberColumn(
                format="%.1f"
            )
        )

st.dataframe(
    forecast_table,
    width="stretch",
    hide_index=True,
    column_config=forecast_column_config,
)


download_csv = forecast_table.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download selected district forecast",
    data=download_csv,
    file_name=(
        f"district_forecast_"
        f"{selected_date:%Y%m%d}.csv"
    ),
    mime="text/csv",
)


if trust_columns_available:
    with st.expander(
        "Study-wide RAIN-Trust findings — July 2018"
    ):
        st.markdown(
            """
- **Observation reliability is geographically structured.** Independent IMERG–IMD disagreement was highest in the coastal-orographic regime.
- At the selected stabilization floor, coastal-orographic agreement was **0.0929 lower** than the interior-plain reference; its 95% bootstrap interval was **−0.1151 to −0.0702**.
- A model using rainfall intensity plus geographic features improved spatial-block cross-validation MAE from **0.17596 to 0.16803** and R² from **0.33013 to 0.34375**.
- **Regime correction remains the primary forecast.** Direct trust blending did not improve performance across India.
- Selective raw blending is retained only as an **experimental coastal-orographic diagnostic**. It improved daily coastal-orographic RMSE by **0.2943 mm/day** in paired bootstrap evaluation, but degraded overall performance.
- The confidence layer describes agreement between two observation products. It is not a calibrated probability that either product—or the forecast—is correct.
            """
        )


with st.expander(
    "Study-wide model verification and limitations"
):
    st.markdown(
        """
- Regime-classifier balanced accuracy: **0.6089**
- Regime-aware 31-day RMSE: **19.2833 mm/day**
- Raw GEFS 31-day RMSE: **20.3831 mm/day**
- Heavy-rain ROC-AUC: **0.9099**
- Heavy-rain CSI: **0.0945**
- Heavy-rain POD: **0.2074**
- Heavy-rain FAR: **0.8521**
- The current prototype is trained and evaluated using July 2018 data.
- IMD and IMERG are independent observation products; neither is treated as perfect ground truth.
- Observation confidence and geographic reliability results are prototype evidence, not a climatology.
- Regime correction is the default forecast layer. Selective-trust rainfall is experimental and must not replace it operationally.
- Very-heavy rainfall probabilities are experimental.
- Bias correction improves rainfall magnitude but does not fully correct spatial displacement.
- The dashboard does not provide official operational warnings.
        """
    )
