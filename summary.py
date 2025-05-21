import json
import pandas as pd
import os
from tqdm import tqdm

# Directory with your JSON files
input_dir = "Spotify Extended Streaming History"
excel_output = "spotify_playtime_summary.xlsx"

print("🔍 Scanning directory for JSON files...")
# List all JSON files
json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
print(f"📂 Found {len(json_files)} JSON files.")

# Load all records
all_data = []
for file in tqdm(json_files, desc="📅 Loading JSON files"):
    file_path = os.path.join(input_dir, file)
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            all_data.extend(data)
        except json.JSONDecodeError:
            print(f"⚠️  Warning: Skipping invalid JSON file: {file}")

# Convert to DataFrame and filter
df = pd.DataFrame(all_data)
initial_count = len(df)
df = df[df["ms_played"] >= 30000]  # Exclude plays under 30 seconds
filtered_count = len(df)
df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
df["year"] = df["ts"].dt.year

print(f"\n📊 Loaded {initial_count} total records.")
print(f"✅ Retained {filtered_count} records (played ≥ 30 seconds).")
print("\n🧪 Beginning summary analysis...")

def filter_reasons(series, allowed):
    return series[series.isin(allowed)].value_counts().to_dict()

def generate_summary():
    with pd.ExcelWriter(excel_output, engine="openpyxl") as writer:
        df["date"] = df["ts"].dt.date
        df["month"] = df["ts"].dt.to_period("M")
        df["weekday"] = df["ts"].dt.day_name()

        allowed_reasons = {"trackdone", "fwdbutton", "endplay", "clickrow"}

        # --- Overall Summary ---
        minutes_total = df["ms_played"].sum() / 60000
        hours_total = df["ms_played"].sum() / 3600000
        avg_play_length = round(df["ms_played"].mean() / 1000, 2)
        median_play_length = round(df["ms_played"].median() / 1000, 2)
        unique_days = sorted(df["date"].dropna().unique())
        listening_days = len(unique_days)
        avg_minutes_per_day = round(minutes_total / listening_days, 2)
        avg_plays_per_day = round(len(df) / listening_days, 2)
        first_date, last_date = unique_days[0], unique_days[-1]
        most_active_day = df.groupby("date")["ms_played"].sum().idxmax()
        most_active_day_minutes = round(df.groupby("date")["ms_played"].sum().max() / 60000, 2)
        gaps = pd.Series(unique_days[1:]) - pd.Series(unique_days[:-1])
        max_gap = gaps.max().days if not gaps.empty else 0

        top_artist_time = df.groupby("master_metadata_album_artist_name")["ms_played"].sum().idxmax()
        top_album_time = df.groupby("master_metadata_album_album_name")["ms_played"].sum().idxmax()
        top_song_time = df.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"])["ms_played"].sum().idxmax()

        reason_start_counts = filter_reasons(df["reason_start"], allowed_reasons)
        reason_end_counts = filter_reasons(df["reason_end"], allowed_reasons)
        shuffle_count = df["shuffle"].sum()
        skipped_count = df["skipped"].sum()
        offline_count = df["offline"].sum()

        summary_df = pd.DataFrame({
            "Total Plays": [len(df)],
            "Total Minutes": [round(minutes_total, 2)],
            "Total Hours": [round(hours_total, 2)],
            "Average Play Length (sec)": [avg_play_length],
            "Median Play Length (sec)": [median_play_length],
            "Listening Days": [listening_days],
            "Avg Minutes per Day": [avg_minutes_per_day],
            "Avg Plays per Listening Day": [avg_plays_per_day],
            "Most Active Day": [most_active_day],
            "Most Active Day Minutes": [most_active_day_minutes],
            "First Listening Date": [first_date],
            "Last Listening Date": [last_date],
            "Longest Listening Gap (days)": [max_gap],
            "Unique Songs": [df["master_metadata_track_name"].nunique()],
            "Unique Albums": [df["master_metadata_album_album_name"].nunique()],
            "Unique Artists": [df["master_metadata_album_artist_name"].nunique()],
            "Top Artist (by time)": [top_artist_time],
            "Top Album (by time)": [top_album_time],
            "Top Song (by time)": [" – ".join(top_song_time)],
            "Shuffle Plays": [shuffle_count],
            "Skipped Tracks": [skipped_count],
            "Offline Plays": [offline_count]
        })

        for reason, count in reason_start_counts.items():
            summary_df[f"Reason Start: {reason}"] = [count]
        for reason, count in reason_end_counts.items():
            summary_df[f"Reason End: {reason}"] = [count]

        summary_df.to_excel(writer, index=False, sheet_name="Summary")
        print("📋 Summary sheet written.")

        # --- Yearly Summary ---
        yearly_stats = []
        for year, group in df.groupby("year"):
            group["date"] = group["ts"].dt.date
            row = {
                "Year": year,
                "Total Plays": len(group),
                "Total Minutes": round(group["ms_played"].sum() / 60000, 2),
                "Total Hours": round(group["ms_played"].sum() / 3600000, 2),
                "Avg Play Length (sec)": round(group["ms_played"].mean() / 1000, 2),
                "Median Play Length (sec)": round(group["ms_played"].median() / 1000, 2),
                "Longest Single Play (min)": round(group["ms_played"].max() / 60000, 2),
                "Listening Days": group["date"].nunique(),
            }
            row["Avg Minutes per Day"] = round(row["Total Minutes"] / row["Listening Days"], 2)
            row["Avg Plays per Listening Day"] = round(len(group) / row["Listening Days"], 2)
            daily = group.groupby("date")["ms_played"].sum()
            row["Most Active Day"] = daily.idxmax()
            row["Most Active Day Minutes"] = round(daily.max() / 60000, 2)
            row["Top Artist"] = group["master_metadata_album_artist_name"].mode().iloc[0] if not group["master_metadata_album_artist_name"].isnull().all() else "N/A"
            row["Top Song"] = group["master_metadata_track_name"].mode().iloc[0] if not group["master_metadata_track_name"].isnull().all() else "N/A"
            row["Top Album"] = group["master_metadata_album_album_name"].mode().iloc[0] if not group["master_metadata_album_album_name"].isnull().all() else "N/A"

            for reason, count in filter_reasons(group["reason_start"], allowed_reasons).items():
                row[f"Reason Start: {reason}"] = count
            for reason, count in filter_reasons(group["reason_end"], allowed_reasons).items():
                row[f"Reason End: {reason}"] = count

            row["Shuffle Plays"] = group["shuffle"].sum()
            row["Skipped Tracks"] = group["skipped"].sum()
            row["Offline Plays"] = group["offline"].sum()

            yearly_stats.append(row)

        pd.DataFrame(yearly_stats).sort_values("Year").to_excel(writer, index=False, sheet_name="Summary by Year")
        print("📋 Year-by-year summary sheet written.")

        # --- Monthly Summary ---
        monthly_stats = []
        for month, group in df.groupby("month"):
            group["date"] = group["ts"].dt.date
            row = {
                "Month": str(month),
                "Total Plays": len(group),
                "Total Minutes": round(group["ms_played"].sum() / 60000, 2),
                "Total Hours": round(group["ms_played"].sum() / 3600000, 2),
                "Average Play Length (sec)": round(group["ms_played"].mean() / 1000, 2),
                "Median Play Length (sec)": round(group["ms_played"].median() / 1000, 2),
                "Listening Days": group["date"].nunique(),
                "Top Artist": group["master_metadata_album_artist_name"].mode().iloc[0] if not group["master_metadata_album_artist_name"].isnull().all() else "N/A",
                "Top Song": group["master_metadata_track_name"].mode().iloc[0] if not group["master_metadata_track_name"].isnull().all() else "N/A",
                "Top Album": group["master_metadata_album_album_name"].mode().iloc[0] if not group["master_metadata_album_album_name"].isnull().all() else "N/A"
            }
            for reason, count in filter_reasons(group["reason_start"], allowed_reasons).items():
                row[f"Reason Start: {reason}"] = count
            for reason, count in filter_reasons(group["reason_end"], allowed_reasons).items():
                row[f"Reason End: {reason}"] = count

            row["Shuffle Plays"] = group["shuffle"].sum()
            row["Skipped Tracks"] = group["skipped"].sum()
            row["Offline Plays"] = group["offline"].sum()

            monthly_stats.append(row)

        pd.DataFrame(monthly_stats).sort_values("Month").to_excel(writer, index=False, sheet_name="Monthly Summary")
        print("📆 Monthly summary written.")

if __name__ == "__main__":
    generate_summary()
    print(f"\n✅ All playtime summaries saved to: {excel_output}")
