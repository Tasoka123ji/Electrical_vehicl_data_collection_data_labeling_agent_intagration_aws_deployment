import pandas as pd


def load_and_prepare_data(path: str, sample_size: int = 5000):
    df = pd.read_csv(path)

    # Select useful columns
    df = df[
        [
            "Model Year",
            "Make",
            "Model",
            "Electric Vehicle Type",
            "Electric Range",
            "Base MSRP",
        ]
    ]

    # Clean
    df = df.dropna(subset=["Electric Range"])
    df["Base MSRP"] = df["Base MSRP"].fillna(df["Base MSRP"].median())

    # Label by range
    def range_label(r):
        if r < 150:
            return "short_range"
        elif r <= 300:
            return "mid_range"
        else:
            return "long_range"

    # Label by price
    def price_label(p):
        if p < 30000:
            return "budget"
        elif p <= 60000:
            return "mid"
        else:
            return "premium"

    df["range_label"] = df["Electric Range"].apply(range_label)
    df["price_label"] = df["Base MSRP"].apply(price_label)

    # Sample for performance
    df = df.sample(sample_size, random_state=42)

    return df
