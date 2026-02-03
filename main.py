from fastapi import FastAPI
import pandas as pd

app = FastAPI()
df = pd.read_csv("labeled_ev_data.csv")

@app.get("/vehicles")
def get_vehicles():
    # Convert dataframe to JSON for the frontend
    return df.to_dict(orient="records")

@app.get("/vehicles/{brand}")
def get_by_brand(brand: str):
    filtered = df[df['brand'].str.lower() == brand.lower()]
    return filtered.to_dict(orient="records")
