import os
import time
import pandas as pd
from google import genai

# --------------------------------
# CONFIG
# --------------------------------
INPUT_CSV = "data/datasets--UrvishAhir1--Electric-Vehicle-Specs-Dataset-2025/snapshots/0f0663f5365230357a815f23eb815796bce15b64/electric_vehicles_spec_2025.csv"

OUTPUT_CSV = "data/gemini_ev_prompt_with_responses.csv"

# Using the latest 2.0 Flash (standard for stable automation)
MODEL_NAME = "gemini-2.0-flash" 
REQUEST_SLEEP = 1.0  # Respect rate limits

# Initialize Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --------------------------------
# PROMPT TEMPLATES
# --------------------------------
PROMPT_TEMPLATES = {
  "technical_description": """
Write a concise technical description of the following electric vehicle.
Focus on drivetrain, battery, efficiency, and performance.

Car specs:
Brand: {brand}
Model: {model}
Top speed: {top_speed_kmh} km/h
Battery: {battery_capacity_kWh} kWh
Range: {range_km} km
Acceleration (0–100): {acceleration_0_100_s} s
Drivetrain: {drivetrain}
""",

    "marketing_description": """
Write a marketing-style description of this electric vehicle.
Highlight design, performance, and lifestyle appeal.

Car:
Brand: {brand}
Model: {model}
Body type: {car_body_type}
Segment: {segment}
""",

    "buyer_explanation": """
Explain this electric vehicle to a potential buyer who is new to EVs.
Keep the tone simple and informative.

Car:
Brand: {brand}
Model: {model}
Range: {range_km} km
Battery: {battery_capacity_kWh} kWh
""",

    "urban_usage": """
Analyze how suitable this electric vehicle is for city driving.
Consider size, efficiency, and range.

Car:
Brand: {brand}
Model: {model}
Efficiency: {efficiency_wh_per_km} Wh/km
Range: {range_km} km
""",

    "highway_usage": """
Evaluate this electric vehicle for highway and long-distance driving.
Consider charging speed, range, and comfort.

Car:
Brand: {brand}
Model: {model}
Range: {range_km} km
Fast charging power: {fast_charging_power_kw_dc} kW
""",

}

# --------------------------------
# MAIN PIPELINE
# --------------------------------
def main():
    # 1. Load data
    df = pd.read_csv(INPUT_CSV)
    
    # Check if we already have some results to avoid starting over
    if os.path.exists(OUTPUT_CSV):
        processed_df = pd.read_csv(OUTPUT_CSV)
        # Simple logic: skip rows we've already handled
        start_index = len(processed_df) // len(PROMPT_TEMPLATES)
        print(f"⏩ Resuming from index {start_index}")
        results = processed_df.to_dict('records')
    else:
        results = []
        start_index = 0

    # 2. Iterate through rows
    for idx, row in df.iloc[start_index:].iterrows():
        print(f"🚗 [{idx+1}/{len(df)}] Processing: {row['brand']} {row['model']}")

        for prompt_type, template in PROMPT_TEMPLATES.items():
            try:
                # Format the prompt with data from the current row
                prompt_text = template.format(**row)

                # Call Gemini
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt_text,
                    config={'system_instruction': "You are an expert automotive analyst."}
                )

                # Store result
                results.append({
                    "brand": row["brand"],
                    "model": row["model"],
                    "prompt_type": prompt_type,
                    "gemini_response": response.text.strip()
                })

                # Small delay to prevent hitting rate limits
                time.sleep(REQUEST_SLEEP)

            except Exception as e:
                print(f"❌ Error at {row['brand']} {idx}: {e}")
                continue

        # 3. Save progress every row so you don't lose data if it crashes
        pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)

    print(f"\n✅ DONE! Saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()