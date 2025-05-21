import json 
import pandas as pd
import os
from tqdm import tqdm

# Directory with your JSON files
input_dir = "Spotify Extended Streaming History"
excel_output = "spotify_playtime_analysis.xlsx"

print("\U0001F50D Scanning directory for JSON files...")
# List all JSON files
json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
print(f"\U0001F4C2 Found {len(json_files)} JSON files.")

# Load all records
all_data = []
for file in tqdm(json_files, desc="\U0001F4E5 Loading JSON files"):
    file_path = os.path.join(input_dir, file)
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            all_data.extend(data)
        except json.JSONDecodeError:
            print(f"\u26A0\uFE0F  Warning: Skipping invalid JSON file: {file}")

# Convert to DataFrame and filter
df = pd.DataFrame(all_data)
initial_count = len(df)
df = df[df["ms_played"] >= 30000]  # Exclude plays under 30 seconds
filtered_count = len(df)
df["year"] = pd.to_datetime(df["ts"], errors='coerce').dt.year

print(f"\n\U0001F4CA Loaded {initial_count} total records.")
print(f"\u2705 Retained {filtered_count} records (played ≥ 30 seconds).")
print("\n\U0001F9EA Beginning analysis...")

def analyze(group_cols, label, id_col=None, separate_columns=False):
    print(f"\U0001F539 Processing {label} data...")

    # Filter necessary columns
    required_cols = group_cols + ["ms_played", "year"]
    subset = df.dropna(subset=group_cols + ["ms_played", "ts"])[required_cols].copy()

    if separate_columns:
        key_cols = group_cols  # Use multiple columns for grouping
    elif id_col:
        subset[id_col] = subset[group_cols[0]] + " – " + subset[group_cols[1]]
        key_cols = [id_col]
    else:
        key_cols = [group_cols[0]]

    # --- Total ---
    total_df = (
        subset.groupby(key_cols)["ms_played"]
        .sum()
        .reset_index()
        .rename(columns={"ms_played": "total_ms_played"})
    )
    total_df["total_minutes_played"] = (total_df["total_ms_played"] / 60000).round(2)
    total_df["total_hours_played"] = (total_df["total_ms_played"] / 3600000).round(2)
    total_time = total_df["total_minutes_played"].sum()
    total_df["percent_of_total"] = (total_df["total_minutes_played"] / total_time * 100).round(2)
    total_df.drop(columns="total_ms_played", inplace=True)
    total_df.sort_values(by="total_minutes_played", ascending=False, inplace=True)
    total_df.to_excel(writer, index=False, sheet_name=f"{label} - Total")
    print(f"   \U0001F4C4 Sheet written: {label} - Total")

    # --- Yearly ---
    yearly_df = (
        subset.groupby(key_cols + ["year"])["ms_played"]
        .sum()
        .reset_index()
        .rename(columns={"ms_played": "total_ms_played"})
    )
    yearly_df["total_minutes_played"] = (yearly_df["total_ms_played"] / 60000).round(2)
    yearly_df.drop(columns="total_ms_played", inplace=True)
    yearly_df.sort_values(by=key_cols + ["year"], inplace=True)
    yearly_df.to_excel(writer, index=False, sheet_name=f"{label} - By Year")
    print(f"   \U0001F4C4 Sheet written: {label} - By Year")

    # --- Pivot ---
    if len(key_cols) == 1:
        pivot_index = key_cols[0]
    else:
        pivot_index = key_cols

    pivot_df = yearly_df.pivot_table(
        index=pivot_index,
        columns="year",
        values="total_minutes_played",
        fill_value=0
    ).round(2)

    pivot_df["Total (mins)"] = pivot_df.sum(axis=1)
    pivot_df["Total (hrs)"] = (pivot_df["Total (mins)"] / 60).round(2)
    pivot_df.sort_values(by="Total (mins)", ascending=False, inplace=True)
    pivot_df = pivot_df.reset_index()

    pivot_df.columns.name = None

    pivot_df.rename(columns={
        "master_metadata_track_name": "Track",
        "master_metadata_album_artist_name": "Artist",
        "master_metadata_album_album_name": "Album",
        "spotify_track_uri": "Spotify URI"
    }, inplace=True)

    pivot_df.to_excel(writer, index=False, sheet_name=f"{label} - Pivot")
    print(f"   \U0001F4C4 Sheet written: {label} - Pivot")

    total_df.to_csv(f"{label.lower()}_total.csv", index=False)
    print(f"   \U0001F4BE CSV exported: {label.lower()}_total.csv")

# Prepare Excel writer
with pd.ExcelWriter(excel_output, engine="openpyxl") as writer:

    # Run for each category
    analyze(["master_metadata_album_artist_name"], "Artist")
    analyze(["master_metadata_track_name", "master_metadata_album_artist_name", "spotify_track_uri"], "Song", separate_columns=True)
    analyze(["master_metadata_album_album_name", "master_metadata_album_artist_name"], "Album", separate_columns=True)

print(f"\n✅ All playtime summaries saved to: {excel_output}")
