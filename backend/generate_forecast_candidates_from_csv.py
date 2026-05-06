import pandas as pd


INPUT_FILE = "categorized_output_with_ml_fallback.csv"
OUTPUT_FILE = "data/forecast_candidates_for_labeling.csv"


def build_forecast_candidates():
    df = pd.read_csv(INPUT_FILE)

    # Keep only rows that can be used for time-based forecast
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    df = df.dropna(subset=["merchant_token", "date", "amount"])

    rows = []

    grouped = df.groupby(["merchant_token", "mcc", "predicted_main_category"])

    for (merchant_token, mcc, main_category), group in grouped:
        group = group.sort_values("date")

        if len(group) < 2:
            continue

        amounts = group["amount"].tolist()
        dates = group["date"].tolist()

        intervals = []
        for i in range(1, len(dates)):
            intervals.append((dates[i] - dates[i - 1]).days)

        rows.append(
            {
                "merchant_token": merchant_token,
                "mcc": mcc,
                "main_category": main_category,
                "amount_avg": round(pd.Series(amounts).mean(), 2),
                "amount_std": round(pd.Series(amounts).std(), 2),
                "interval_avg_days": round(pd.Series(intervals).mean(), 2),
                "interval_std_days": round(pd.Series(intervals).std(), 2) if len(intervals) > 1 else 0,
                "occurrence_count": len(group),

                # Manual label to fill later:
                # 1 = recurring / subscription-like
                # 0 = not recurring
                "is_recurring": "",
            }
        )

    output_df = pd.DataFrame(rows)
    output_df.to_csv(OUTPUT_FILE, index=False)

    print("Forecast candidates generated successfully")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Rows generated: {len(output_df)}")


if __name__ == "__main__":
    build_forecast_candidates()