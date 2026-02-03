# ⚡ EV Spec Labeler 2025

**Interactive tool for viewing, exploring and manually/semi-automatically labeling electric vehicles** based on technical specifications (range, acceleration, battery size, body type, etc.).

Built with **Streamlit** + **pandas**.

https://github.com/<your-username>/ev-spec-labeler-2025   (replace with real link)

## ✨ Features

- Browse 2025-era electric vehicles with key specs in a clean, wide-layout view
- Rule-based **auto-suggestion** of four categories:
  - **Economy**
  - **Luxury**
  - **Sport**
  - **Utility**
- Manual label assignment with one-click **Confirm & Next** navigation
- Persistent labeling — labels are saved directly back to the CSV file
- Sidebar filters: brand, labeled/unlabeled status
- Progress bar showing labeling completion
- Responsive styling + colored label badges
- Quick dataset overview table at the bottom

## Labeling Rules (auto-suggestion logic)

| Priority | Condition                                                | Suggested Label |
|--------|-----------------------------------------------------------|-----------------|
| 1      | 0–100 km/h < 5 s **or** top speed > 200 km/h             | Sport           |
| 2      | Segment = luxury/premium **or** battery > 75 kWh         | Luxury          |
| 3      | Body = SUV / Pickup **or** towing capacity > 500 kg      | Utility         |
| 4      | Otherwise                                                | Economy         |

→ Already manually labeled vehicles keep their label (auto-label only runs on "Unlabeled" entries)

## 📦 Dataset

**Source**: `data/datasets--UrvishAhir1--Electric-Vehicle-Specs-Dataset-2025/.../electric_vehicles_spec_2025.csv`

(Assumed to be from a Hugging Face dataset snapshot)

**Important columns used**:

- `brand`, `model`
- `segment`, `car_body_type`, `drivetrain`
- `acceleration_0_100_s`, `top_speed_kmh`
- `battery_capacity_kWh`, `range_km`, `efficiency_wh_per_km`
- `torque_nm`, `fast_charging_power_kw_dc`, `towing_capacity_kg`
- `length_mm`, `width_mm`, `height_mm`, `cargo_volume_l`, `seats`
- `source_url`

## 🚀 Quick Start

### 1. Clone repository

```bash
git clone https://github.com/<your-username>/ev-spec-labeler-2025.git
cd ev-spec-labeler-2025