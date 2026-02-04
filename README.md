# ⚡ EV Spec Labeler 2025

**Interactive data labeling & exploration tool** for classifying modern electric vehicles according to high-level categories (Economy, Luxury, Sport, Utility) based on technical specifications.

Built with **Streamlit** + **pandas**.

Designed for dataset enrichment, ML preprocessing, human-in-the-loop annotation, and exploratory analysis of 2025-era EV data.

## ✨ Key Features

- Clean, wide-layout browser for EV specifications
- **Rule-based auto-suggestion** for four categories:
  - Economy
  - Luxury
  - Sport
  - Utility
- Fast human-in-the-loop labeling
  - One-click label confirmation
  - "Confirm & Next" navigation
- Persistent labeling — changes are **immediately saved to CSV**
- Sidebar filters: brand + labeled/unlabeled status
- Real-time labeling progress bar
- Colored label badges + responsive styling
- Quick dataset overview table

## 🧠 Auto-labeling Logic

Applied **only to unlabeled vehicles**.  
Manually assigned labels are **never overwritten**.

| Priority | Condition                                              | Label     |
|--------|--------------------------------------------------------|-----------|
| 1      | 0–100 km/h < 5 s **or** top speed > 200 km/h          | Sport     |
| 2      | segment = luxury/premium **or** battery > 75 kWh      | Luxury    |
| 3      | body = SUV / Pickup **or** towing > 500 kg            | Utility   |
| 4      | otherwise                                             | Economy   |

## 📦 Dataset

**File**: `electric_vehicles_spec_2025.csv`  
**Location**: `data/datasets--UrvishAhir1--Electric-Vehicle-Specs-Dataset-2025/.../`

(Assumed to be a Hugging Face dataset snapshot)

**Most important columns used**

- `brand`, `model`
- `segment`, `car_body_type`, `drivetrain`
- `acceleration_0_100_s`, `top_speed_kmh`, `torque_nm`
- `battery_capacity_kWh`, `range_km`, `efficiency_wh_per_km`
- `fast_charging_power_kw_dc`, `towing_capacity_kg`
- `cargo_volume_l`, `seats`
- `length_mm`, `width_mm`, `height_mm`
- `source_url`

## 🤖 LLM-assisted Data Enrichment

The project supports semi-automated data collection & cleaning using:

- OpenAI GPT models
- Google Gemini models

### Typical LLM usage patterns

- Extracting / normalizing specs from semi-structured web pages
- Filling missing numerical values when source URL allows verification
- Generating short standardized descriptions
- Detecting & flagging inconsistencies
- Converting free-text → structured CSV rows

**Important**: LLM outputs are **never blindly trusted**.  
Every enriched or corrected row should be reviewed in the Streamlit labeling interface.

## 🚀 Quick Start

```bash
# 1. Clone
git clone git@github.com:Tasoka123ji/Electrical_vehicl_data_collection_data_labeling_agent_intagration_aws_deployment.git
cd ev-spec-labeler-2025

# 2. Install dependencies
pip install streamlit pandas

# (or if you have a requirements.txt)
# pip install -r requirements.txt

# 3. Launch
streamlit run app.py