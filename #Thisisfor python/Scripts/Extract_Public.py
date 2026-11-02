import pandas as pd

# 1. Load the classified dataset containing 300 posts
input_file = r"final_output\twice_sample_300_classified.csv"
df = pd.read_csv(input_file)

# 2. Filter posts classified as 'General Public' (11 posts)
public_df = df[df["classified_identity"] == "General Public"]

# ----------------------------------------------------
# Task A: Analyze media format distribution (Image / Carousel / Video)
# ----------------------------------------------------
print("=" * 60)
print("[Media Format Distribution for General Public (N=11)]")
print("=" * 60)

media_col_found = False
for col in ["type", "productType", "media_type", "mediaType"]:
    if col in public_df.columns:
        media_col_found = True
        print(f"Detected media format column: '{col}'")
        type_counts = public_df[col].value_counts()
        print(type_counts)
        print("-" * 60)
        break

if not media_col_found:
    print(
        "Warning: Could not detect media type column automatically. Check public_df.columns."
    )

# ----------------------------------------------------
# Task B: Identify URL column and extract Instagram permalinks
# ----------------------------------------------------
possible_url_cols = [
    "url",
    "postUrl",
    "permalink",
    "link",
    "shortCode",
    "shortcode",
]
url_col = None

for col in possible_url_cols:
    if col in public_df.columns:
        url_col = col
        break

if not url_col:
    print("Warning: URL column not found. Available columns in CSV:")
    print(list(public_df.columns))
else:
    print(f"[✓] Detected URL column: '{url_col}'")

    urls = []
    for val in public_df[url_col].dropna():
        val = str(val).strip()
        # Assemble full URL if shortCode is used
        if val.startswith("http"):
            urls.append(val)
        else:
            urls.append(f"https://www.instagram.com/p/{val}/")

    print("\n" + "=" * 60)
    print(f"Extracted Permalinks for General Public Posts (Total: {len(urls)}):")
    print("=" * 60)
    for idx, u in enumerate(urls, 1):
        print(f"[{idx}] {u}")

    # Export URLs to a plain text file for easy access
    output_txt = r"final_output\public_posts_urls.txt"
    with open(output_txt, "w", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")

    print("=" * 60)
    print(f"[✓] Successfully exported all URLs to: {output_txt}")