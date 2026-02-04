import os
import time
import pandas as pd
from openai import OpenAI

# --------------------------------
# CONFIG
# --------------------------------
INPUT_CSV = "data/datasets--UrvishAhir1--Electric-Vehicle-Specs-Dataset-2025/snapshots/0f0663f5365230357a815f23eb815796bce15b64/electric_vehicles_spec_2025.csv"
OUTPUT_CSV = "data/gpt_ev_prompt_with_responses.csv"

MODEL_NAME = "gpt-4o-mini"
REQUEST_SLEEP = 0.5  # avoid rate limits

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY") # make sure env var is set
)


# --------------------------------
# PROMPT TEMPLATES (10)
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
"""
}

# --------------------------------
# OPENAI CALL
# --------------------------------
def generate_response(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are an expert automotive analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# --------------------------------
# MAIN PIPELINE
# --------------------------------
def main():
    df = pd.read_csv(INPUT_CSV)

    results = []

    for idx, row in df.iterrows():
        print(f"🚗 Processing {row['brand']} {row['model']} ({idx + 1}/{len(df)})")

        for prompt_type, template in PROMPT_TEMPLATES.items():
            try:
                prompt_text = template.format(**row)

                gpt_response = generate_response(prompt_text)

                results.append({
                    "brand": row["brand"],
                    "model": row["model"],
                    "source_url": row["source_url"],
                    "prompt_type": prompt_type,
                    "prompt_text": prompt_text.strip(),
                    "gpt_response": gpt_response
                })

                time.sleep(REQUEST_SLEEP)

            except Exception as e:
                print(f"❌ Error for {row['brand']} {row['model']} [{prompt_type}]: {e}")

            out_df = pd.DataFrame(results)
            out_df.to_csv(OUTPUT_CSV, index=False)

    print("\n✅ DONE")
    print(f"📄 Saved {len(out_df)} rows to {OUTPUT_CSV}")

# --------------------------------
# RUN
# --------------------------------
if __name__ == "__main__":
    main()
