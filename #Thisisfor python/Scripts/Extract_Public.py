import pandas as pd

# 1. 讀取分類後的 CSV 檔案
input_file = r"final_output\twice_sample_300_classified.csv"
df = pd.read_csv(input_file)

# 2. 篩選出 11 條 General Public 的貼文
public_df = df[df["classified_identity"] == "General Public"]

# 3. 自動偵測網址欄位名稱 (常見的有 url, permalink, postUrl 等)
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
    # 如果找不到預設欄位，列印出所有欄位名稱供檢查
    print("未能自動識別網址欄位，目前的 CSV 欄位清單如下：")
    print(list(public_df.columns))
else:
    print(f"[✓] 成功識別網址欄位: '{url_col}'")

    # 4. 提取網址列表
    urls = []
    for val in public_df[url_col].dropna():
        val = str(val).strip()
        # 如果欄位存的是短代碼 (shortCode)，自動拼裝成完整 Instagram 網址
        if val.startswith("http"):
            urls.append(val)
        else:
            urls.append(f"https://www.instagram.com/p/{val}/")

    # 5. 在終端機印出 11 條連結
    print("\n" + "=" * 60)
    print(f"提取出的 11 條 General Public 貼文網頁連結 (共 {len(urls)} 筆)：")
    print("=" * 60)
    for idx, u in enumerate(urls, 1):
        print(f"[{idx}] {u}")

    # 6. 保存為純文字檔案，方便直接點擊打開查看
    output_txt = r"final_output\public_posts_urls.txt"
    with open(output_txt, "w", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")

    print("=" * 60)
    print(f"[✓] 所有連結已輸出保存至: {output_txt}")