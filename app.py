
import streamlit as st
import pandas as pd
import plotly.express as px
import joblib




st.set_page_config(
    page_title="Nassau Candy Optimizer",
    page_icon="🍬",
    layout="wide"
)

st.title("🍬 Nassau Candy Factory Optimization")
st.caption(
    "Prototype using assumed factory assignments and approximate "
    "region coordinates. Distances are estimates, not actual shipping routes."
)

@st.cache_data
def load_data():
    return pd.read_csv("factory_recommendations.csv")

try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "factory_recommendations.csv was not found. "
        "Place it in the same folder as app.py."
    )
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")

regions = ["All"] + sorted(df["Region"].dropna().unique().tolist())
selected_region = st.sidebar.selectbox("Select region", regions)

products = ["All"] + sorted(df["Product"].dropna().unique().tolist())
selected_product = st.sidebar.selectbox("Select product", products)

min_km = st.sidebar.slider(
    "Minimum potential distance difference (km)",
    min_value=0,
    max_value=3000,
    value=500,
    step=100
)

filtered = df[
    df["Potential Distance Difference (km)"] >= min_km
].copy()

if selected_region != "All":
    filtered = filtered[filtered["Region"] == selected_region]

if selected_product != "All":
    filtered = filtered[filtered["Product"] == selected_product]

# Dashboard metrics
col1, col2, col3 = st.columns(3)

col1.metric("Matching scenarios", len(filtered))
col2.metric(
    "Different nearest factory",
    int(filtered["Factory Change Suggested"].sum())
)

average_difference = (
    filtered["Potential Distance Difference (km)"].mean()
    if not filtered.empty else 0
)
col3.metric(
    "Average potential difference",
    f"{average_difference:,.2f} km"
)

st.warning(
    "These are hypothetical distance comparisons. "
    "Do not use them as operational factory reassignment decisions."
)

# Results table
st.subheader("Factory Scenario Recommendations")

display_columns = [
    "Product",
    "Region",
    "Current Factory",
    "Nearest Candidate Factory",
    "Current Distance (km)",
    "Nearest Distance (km)",
    "Potential Distance Difference (km)",
    "Potential Distance Difference (%)",
    "Factory Change Suggested"
]

if filtered.empty:
    st.info("No scenarios match these filters. Try lowering the minimum distance.")
else:
    st.dataframe(
    filtered[display_columns].round(2),
    use_container_width=True,
    hide_index=True,
    height=400
)
    

    chart = px.bar(
        filtered.head(15).sort_values(
            "Potential Distance Difference (km)"
        ),
        x="Potential Distance Difference (km)",
        y="Product",
        color="Region",
        orientation="h",
        title="Top scenarios by potential distance difference"
    )
    st.plotly_chart(chart, use_container_width=True)

    st.subheader("📊 Current Factory vs Nearest Candidate")

    comparison = filtered.head(10).copy()

    comparison_chart = px.bar(
        comparison,
        x="Product",
        y=["Current Distance (km)", "Nearest Distance (km)"],
        barmode="group",
        title="Distance Comparison by Product"
    )

    st.plotly_chart(
        comparison_chart,
        use_container_width=True
    )

st.divider()

st.divider()

st.header("⚖️ Speed vs Profit Preference")

speed_priority = st.slider(
    "Priority for shorter distance vs profit",
    min_value=0,
    max_value=100,
    value=50,
    step=10,
    help="0 = profit-focused, 100 = distance-focused"
)

st.subheader("📊 Recommendations Based on Your Preference")

ranked = df.copy()

ranked["Distance Improvement (%)"] = (
    ranked["Potential Distance Difference (%)"].clip(lower=0)
)

# Higher slider values give more importance to distance reduction.
ranked["Priority Score"] = (
    ranked["Distance Improvement (%)"] * speed_priority / 100
)

ranked = ranked.sort_values(
    "Priority Score",
    ascending=False
)

st.caption(
    "Ranking uses estimated distance improvement only. "
    "Profit impact is not calculated because transport-cost and "
    "factory-profit data are unavailable."
)

st.dataframe(
    ranked[
        [
            "Product",
            "Region",
            "Current Factory",
            "Nearest Candidate Factory",
            "Potential Distance Difference (km)",
            "Distance Improvement (%)",
            "Priority Score"
        ]
    ].head(10).round(2),
    use_container_width=True,
    hide_index=True
)

st.download_button(
    label="📥 Download Ranked Recommendations",
    data=ranked.to_csv(index=False).encode("utf-8"),
    file_name="ranked_factory_recommendations.csv",
    mime="text/csv"
)

profit_priority = 100 - speed_priority

col1, col2 = st.columns(2)

col1.metric("Distance Priority", f"{speed_priority}%")
col2.metric("Profit Priority", f"{profit_priority}%")

if speed_priority >= 70:
    st.info("Preference: prioritize shorter estimated distances.")
elif speed_priority <= 30:
    st.info("Preference: prioritize profitability, subject to cost data.")
else:
    st.info("Preference: balance distance and profitability.")

st.header("🏭 Factory Reassignment Simulator")

st.write(
    "Choose a product and region to explore a hypothetical "
    "alternative factory assignment."
)

if not df.empty:
    selected_scenario = st.selectbox(
        "Choose a scenario",
        df.index,
        format_func=lambda i: (
            f"{df.loc[i, 'Product']} | "
            f"{df.loc[i, 'Region']}"
        ),
        key="simulator_scenario"
    )

    scenario = df.loc[selected_scenario]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Current Assignment")
        st.write("Factory:", scenario["Current Factory"])
        st.metric(
            "Estimated distance",
            f"{scenario['Current Distance (km)']:,.2f} km"
        )

    with col2:
        st.subheader("Alternative Assignment")
        st.write(
            "Factory:",
            scenario["Nearest Candidate Factory"]
        )
        st.metric(
            "Estimated distance",
            f"{scenario['Nearest Distance (km)']:,.2f} km",
            delta=(
                f"-{scenario['Potential Distance Difference (km)']:,.2f} km"
            )
        )

    st.info(
        "This is a hypothetical comparison. "
        "Check factory capacity, product compatibility, "
        "transport costs, and actual routes before making decisions."
    )

st.divider()

st.header("📋 Executive Summary")

st.write(
    "This dashboard compares hypothetical factory assignments "
    "using approximate straight-line distances between factory "
    "locations and region centres."
)

summary_col1, summary_col2 = st.columns(2)

summary_col1.metric(
    "Scenarios Analysed",
    len(df)
)

summary_col2.metric(
    "Scenarios Matching Filters",
    len(filtered)
)

if not filtered.empty:
    best_scenario = filtered.loc[
        filtered["Potential Distance Difference (km)"].idxmax()
    ]

    st.subheader("Largest Estimated Distance Difference")

    st.write("Product:", best_scenario["Product"])
    st.write("Region:", best_scenario["Region"])
    st.write("Current factory:", best_scenario["Current Factory"])
    st.write(
        "Alternative factory:",
        best_scenario["Nearest Candidate Factory"]
    )
    st.write(
        "Estimated distance difference:",
        f"{best_scenario['Potential Distance Difference (km)']:,.2f} km"
    )

st.warning(
    "These results are exploratory estimates, not verified savings. "
    "Actual shipping time, transport costs, factory capacity, "
    "product compatibility, and profit impact require validation."
)

st.caption(
    "Before using this for real decisions, validate factory assignments, "
    "product compatibility, road routes, capacity, and shipping data."
)

# Gross Profit Prediction Section

st.divider()
st.header("💰 Gross Profit Prediction")

st.write(
    "Estimate gross profit using historical product, region, "
    "shipping mode, and unit patterns."
)

try:
    profit_model = joblib.load("gross_profit_model.pkl")

    # Get the exact categories supported by the trained model
    preprocessor = profit_model.named_steps["preprocessor"]
    encoder = preprocessor.named_transformers_["cat"]
    categories = encoder.categories_

    product_options = sorted(categories[0].tolist())
    region_options = sorted(categories[1].tolist())
    ship_modes = sorted(categories[2].tolist())

    col1, col2 = st.columns(2)

    with col1:
        chosen_product = st.selectbox(
            "Choose product",
            product_options,
            key="profit_product"
        )

        chosen_region = st.selectbox(
            "Choose region",
            region_options,
            key="profit_region"
        )

    with col2:
        chosen_ship_mode = st.selectbox(
            "Choose shipping mode",
            ship_modes,
            key="profit_ship_mode"
        )

        chosen_units = st.number_input(
            "Number of units",
            min_value=1,
            max_value=1000,
            value=2,
            step=1,
            key="profit_units"
        )

    if st.button("🔮 Predict Gross Profit"):
        input_data = pd.DataFrame({
            "Product Name": [chosen_product],
            "Region": [chosen_region],
            "Ship Mode": [chosen_ship_mode],
            "Units": [chosen_units]
        })

        prediction = profit_model.predict(input_data)[0]

        st.metric(
            "Estimated Gross Profit",
            f"{prediction:,.2f}"
        )

        st.caption(
            "This is a model estimate based on historical patterns, "
            "not a guaranteed profit. Predictions may be unreliable "
            "for unit quantities outside the training data range."
        )

except FileNotFoundError:
    st.error(
        "gross_profit_model.pkl not found. "
        "Place it in the same folder as app.py."
    )

except Exception as e:
    st.error(f"Could not load or run the profit model: {e}")
