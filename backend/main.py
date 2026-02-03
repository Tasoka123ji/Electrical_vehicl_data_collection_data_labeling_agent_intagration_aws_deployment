from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data_loader import load_and_prepare_data

DATA_PATH = "../data/Electric_Vehicle_Population_Data.csv"

app = FastAPI(title="Electric Vehicle Dataset API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

df = load_and_prepare_data(DATA_PATH)


@app.get("/")
def root():
    return {"status": "EV API is running"}


@app.get("/vehicles")
def get_vehicles(limit: int = 50):
    return df.head(limit).to_dict(orient="records")


@app.get("/stats")
def get_stats():
    return {
        "total_samples": len(df),
        "range_labels": df["range_label"].value_counts().to_dict(),
        "price_labels": df["price_label"].value_counts().to_dict(),
    }
