import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="EV Spec Labeler 2025", page_icon="⚡", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 22px; color: #007bff; font-weight: bold; }
.stButton>button { border-radius: 20px; background-color: #007bff; color: white; border: none; font-weight: bold; padding: 8px 16px; }
.stButton>button:hover { background-color: #0056b3; color: white; }
.status-box { padding: 15px; border-radius: 10px; border-left: 5px solid #007bff; background-color: #f0f2f6; margin-bottom: 20px; }
.label-badge { padding: 4px 10px; border-radius: 5px; color: white; font-weight: bold; }
.label-Economy { background-color: #28a745; }
.label-Luxury { background-color: #6f42c1; }
.label-Sport { background-color: #dc3545; }
.label-Utility { background-color: #fd7e14; }
.details-table th { text-align: left; }
</style>
""", unsafe_allow_html=True)

# --- DATA PATH & LOADING ---
DATA_PATH = "data/datasets--UrvishAhir1--Electric-Vehicle-Specs-Dataset-2025/snapshots/0f0663f5365230357a815f23eb815796bce15b64/electric_vehicles_spec_2025.csv"

def get_data():
    if 'df' not in st.session_state:
        df = pd.read_csv(DATA_PATH)
        df['brand'] = df['brand'].astype(str).str.strip().str.title()  # Normalize
        if 'label' not in df.columns:
            df['label'] = "Unlabeled"
        st.session_state.df = df
    return st.session_state.df

df = get_data()

# --- AUTO-LABELING LOGIC ---
def auto_label(row):
    if row['label'] != "Unlabeled":
        return row['label']
    if row.get('acceleration_0_100_s', 100) < 5 or row.get('top_speed_kmh', 0) > 200:
        return "Sport"
    if row.get('segment', '').lower() in ['luxury', 'premium'] or row.get('battery_capacity_kWh', 0) > 75:
        return "Luxury"
    if row.get('car_body_type', '').lower() in ['suv', 'pickup'] or row.get('towing_capacity_kg', 0) > 500:
        return "Utility"
    return "Economy"

df['suggested_label'] = df.apply(auto_label, axis=1)

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.title("🛠️ Labeling Status")
    labeled_count = len(df[df['label'] != "Unlabeled"])
    st.write(f"**Labeled:** {labeled_count} / {len(df)}")
    st.progress(labeled_count / len(df))

    st.divider()
    brands_list = ["All"] + sorted(df['brand'].dropna().unique().tolist())
    selected_brand = st.selectbox("Filter by Brand", brands_list)

    filter_label = st.selectbox("Show", ["All", "Labeled", "Unlabeled"])

# Apply filters safely
filtered_df = df.copy()
if selected_brand != "All":
    filtered_df = filtered_df[filtered_df['brand'].str.lower() == selected_brand.strip().lower()]

if filter_label == "Labeled":
    filtered_df = filtered_df[filtered_df['label'] != "Unlabeled"]
elif filter_label == "Unlabeled":
    filtered_df = filtered_df[filtered_df['label'] == "Unlabeled"]

filtered_indices = filtered_df.index.tolist()

if 'pos' not in st.session_state:
    st.session_state.pos = 0
st.session_state.pos = min(st.session_state.pos, max(len(filtered_indices) - 1, 0))
current_idx = filtered_indices[st.session_state.pos] if filtered_indices else None

# --- MAIN UI ---
st.title("⚡ Electric Vehicle Labeler & Explorer")

if current_idx is not None:
    car = df.loc[current_idx]

    # Hero
    with st.container():
        st.markdown(f"""
        <div class="status-box">
            <h2>{car['brand']} {car['model']}</h2>
            <p style='color:gray;'>Segment: {car.get('segment','N/A')} • Drivetrain: {car.get('drivetrain','N/A')} • Body: {car.get('car_body_type','N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

    # Detailed Table
    specs = {
        "Top Speed (km/h)": car.get('top_speed_kmh'),
        "Battery (kWh)": car.get('battery_capacity_kWh'),
        "Battery Type": car.get('battery_type'),
        "Number of Cells": car.get('number_of_cells'),
        "Torque (Nm)": car.get('torque_nm'),
        "Efficiency (Wh/km)": car.get('efficiency_wh_per_km'),
        "Range (km)": car.get('range_km'),
        "0–100 km/h (s)": car.get('acceleration_0_100_s'),
        "Fast Charging (kW DC)": car.get('fast_charging_power_kw_dc'),
        "Charging Port": car.get('fast_charge_port'),
        "Towing (kg)": car.get('towing_capacity_kg'),
        "Cargo Volume (L)": car.get('cargo_volume_l'),
        "Seats": car.get('seats'),
        "Dimensions (L×W×H mm)": f"{car.get('length_mm')} × {car.get('width_mm')} × {car.get('height_mm')}",
        "Source URL": f"[Link]({car.get('source_url')})"
    }

    st.table(specs)

    st.divider()

    # Label Selector + Navigation
    left, right = st.columns([2,1])

    with left:
        st.subheader("🏷️ Assign or Confirm Label")
        label_options = ["Economy", "Luxury", "Sport", "Utility"]
        default_label = car['label'] if car['label'] != "Unlabeled" else car['suggested_label']
        new_label = st.selectbox("Choose label:", label_options, index=label_options.index(default_label))

        if car['label'] != "Unlabeled":
            st.markdown(f"<span class='label-badge label-{car['label']}'>{car['label']}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color: gray;'>Suggested: <span class='label-badge label-{car['suggested_label']}'>{car['suggested_label']}</span></span>", unsafe_allow_html=True)

    with right:
        if st.button("⬅️ Previous"):
            if st.session_state.pos > 0:
                st.session_state.pos -= 1
                st.rerun()
        if st.button("Confirm & Next ➡️"):
            st.session_state.df.at[current_idx, 'label'] = new_label
            st.session_state.df.to_csv(DATA_PATH, index=False)
            if st.session_state.pos < len(filtered_indices) - 1:
                st.session_state.pos += 1
                st.rerun()
            else:
                st.balloons()
                st.success("All filtered vehicles labeled!")

else:
    st.warning("No cars found for this filter combination.")

# --- DATA OVERVIEW ---
st.subheader("📊 EV Dataset Snapshot")
st.dataframe(
    st.session_state.df[['brand','model','range_km','top_speed_kmh','battery_capacity_kWh','label','suggested_label','source_url']].fillna("N/A"),
    width='stretch',
    height=400,
    hide_index=True
)
