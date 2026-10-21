import os
import json
import random
import re
import pandas as pd

# =========================================================
# 1. Four-language TWICE fan slang dictionary
# # =========================================================
CORE_FAN_JARGON = [
    # Official Fan Name (English/Chinese/Korean/Japanese)
    r"#once\b", r"\bonces\b", "萬斯", "万斯", "元斯", "원스", "ワンス",
    # Support light sticks and internal phrases
    "candybong", "candy bong", "糖果棒", "手燈", "手灯", "應援棒", "应援棒",
    "캔디봉", "응원봉", "キャンディー棒", "ペンライト",
    "twicetagram", "withyouth", "strategy", "ten: the story goes on",
    # Fan circle terminology
    "ot9", "bias", "ult group", "fave", "stan twice", "翻牌", "應援板", "应援板", "空耳",
    "최애", "차애", "덕질", "공봉", "막콘", "첫콘", "올콘", "슬로건",
    "参戦", "現場参戦", "銀テ", "掛け声", "推し", "自引き",
    # Member nicknames / nicknames / Korean and Japanese pet names
    "林三歲", "林三岁", "兔牙", "nabongs", "나봉스", "ナヨン",
    "無趣哥", "无趣哥", "yoo", "ジョンヨン",
    "moguri", "모구리", "平井桃", "跳舞機器", "跳舞机器", "モモ",
    "柴犬", "紗夏", "纱夏", "松鼠", "nosananolife", "no sana no life", "サナ", "さーたん", "サナペン",
    "godjihyo", "god志效", "小隊", "小队", "朴隊", "ジヒョ",
    "minari", "미나리", "企鵝", "企鹅", "黑天鵝", "黑天鹅", "南醬", "ミナ",
    "dubu", "두부", "老鷹", "老鹰", "豆腐", "ダヒョン",
    "chaeng", "챙", "小猛獸", "小猛兽", "草莓公主", "彩寶", "チェヨン",
    "尤達", "尤达", "忙內", "忙内", "尤達瑜", "小瑜", "ツウィ", "ツウィペン",
    # Squad and CP Name
    "misamo", "미사모", "ミサモ", "2yeon", "mihyo", "saida", "michaeng", "satzu", "namo"
]

CASUAL_KEYWORDS = [
    r"#twice\b", r"#thisisfor\b", r"#twiceconcert\b", r"#twicetour\b", r"#kpop\b",
    "twice", "트와이스", "トワイス", "jyp", "jype",
    "nayeon", "jeongyeon", "momo", "sana", "jihyo", "mina", "dahyun", "chaeyoung", "tzuyu",
    "娜璉", "娜琏", "定延", "志效", "多賢", "多贤", "彩瑛", "子瑜", "周子瑜",
    "나연", "정연", "모모", "사나", "지효", "미나", "다현", "채영", "쯔위"
]

def score_and_classify(text: str, author_handle: str = ""):
    if str(author_handle).lower() in ["twicetagram", "jypetwice_japan"]:
        return "Official Account", 99, ["official_account"]
        
    if not text or not isinstance(text, str) or not text.strip():
        return "General Public", 0, []
        
    text_lower = text.lower()
    total_score = 0
    matched = []
    
    for kw in CORE_FAN_JARGON:
        if kw.startswith(r"#") or kw.startswith(r"\b"):
            if re.search(kw, text_lower):
                total_score += 3
                matched.append(kw.replace(r"\b", "").replace("#", ""))
        else:
            if kw in text_lower:
                total_score += 3
                matched.append(kw)
                
    for kw in CASUAL_KEYWORDS:
        if kw.startswith(r"#"):
            if re.search(kw, text_lower):
                total_score += 1
                matched.append(kw.replace("#", ""))
        else:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower) or kw in text_lower:
                total_score += 1
                matched.append(kw)

    matched = list(set(matched))
    if total_score >= 3:
        return "TWICE Fan", total_score, matched
    else:
        return "General Public", total_score, matched

# =========================================================
# 2. Recursively read all original files and integrate them into the parent database.
# =========================================================
def build_master_database():
    current_dir = os.getcwd()
    all_raw_files = []
    
    #Traverse the current directory and all subfolders (raw_data, Data base and so on)
    for root, dirs, files in os.walk(current_dir):
        # Exclude folders containing analysis results
        if "final_output" in root:
            continue
        for file in files:
            # Exclude the generated analysis output files and system files
            if file.startswith("twice_") or file.startswith("comparison_") or file.startswith("package"):
                continue
            if file.endswith(".csv") or file.endswith(".json") or file.endswith(".xlsx"):
                all_raw_files.append(os.path.join(root, file))

    print(f"[*] Found the following raw data source files (total {len(all_raw_files)}):")
    for f in all_raw_files:
        print(f"    - {os.path.relpath(f, current_dir)}")

    records = []
    for file_path in all_raw_files:
        try:
            if file_path.endswith(".csv"):
                df_temp = pd.read_csv(file_path, low_memory=False)
                for _, row in df_temp.iterrows():
                    records.append(extract_standard_row(row.to_dict()))
            elif file_path.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                posts = content.get("posts", []) if isinstance(content, dict) else content
                if isinstance(posts, list):
                    for item in posts:
                        if isinstance(item, dict):
                            records.append(extract_standard_row(item))
            elif file_path.endswith(".xlsx"):
                df_temp = pd.read_excel(file_path)
                for _, row in df_temp.iterrows():
                    records.append(extract_standard_row(row.to_dict()))
        except Exception as e:
            print(f"[!] Failed to read file ({os.path.basename(file_path)}): {e}")

    df_master = pd.DataFrame(records)
    print(f"\n[✓] The entire database has been read; the total number of entries in the original merged parent database is now complete.: {len(df_master)} posts.")
    return df_master

def extract_standard_row(item: dict) -> dict:
    """Consolidate fields from different platforms or formats into a standard field format."""
    # Unique identifier priority
    uid = item.get("entity_id") or item.get("id") or item.get("shortCode") or item.get("code") or ""
    url = item.get("url") or item.get("postUrl") or item.get("inputUrl") or ""
    # Text content priority
    text = item.get("text") or item.get("caption") or item.get("clean_caption") or item.get("description") or ""
    if isinstance(text, dict):
        text = text.get("text", "")
    # Author field
    author = item.get("author_handle") or item.get("owner_username") or item.get("author_name") or ""
    # Interaction metrics
    likes = item.get("likes") or item.get("likesCount") or 0
    comments = item.get("comments") or item.get("commentsCount") or 0
    posted_at = item.get("posted_at") or item.get("timestamp") or item.get("date") or ""

    return {
        "uid": str(uid).strip(),
        "url": str(url).strip(),
        "author_handle": str(author).strip(),
        "text": str(text).replace("\n", " ").strip(),
        "likes": pd.to_numeric(likes, errors="coerce") or 0,
        "comments": pd.to_numeric(comments, errors="coerce") or 0,
        "posted_at": str(posted_at).strip()
    }

# =========================================================
# 3. Deduplication, selection of 300 samples, and comparative analysis.
# =========================================================
def main():
    df_master = build_master_database()
    if df_master.empty:
        print("[X] 錯誤：資料庫中沒有讀取到任何貼文！")
        return

    # Remove empty posts
    df_master = df_master[df_master["text"].str.len() > 0].copy()

    # Detect and remove duplicates (prioritize URL; if the URL is invalid, use UID or random text).
    if df_master["url"].nunique() > 10:
        dedup_key = "url"
    elif df_master["uid"].nunique() > 10:
        dedup_key = "uid"
    else:
        dedup_key = "text"

    before_dedup = len(df_master)
    df_unique = df_master.drop_duplicates(subset=[dedup_key]).copy()
    print(f"[✓] According to '{dedup_key}' Deduplication: removing duplicates {before_dedup - len(df_unique)} Duplicate posts, remaining independent posts in total inventory: {len(df_unique)} 筆。")

    # 300 samples were randomly selected.
    TARGET_SAMPLE_SIZE = 300
    if len(df_unique) >= TARGET_SAMPLE_SIZE:
        random.seed(42)  # Fixed random seed to ensure academic reproducibility
        sample_indices = random.sample(list(df_unique.index), TARGET_SAMPLE_SIZE)
        df_sample = df_unique.loc[sample_indices].copy()
        print(f"[*] Successfully selected {TARGET_SAMPLE_SIZE} samples randomly from the entire database.！")
    else:
        df_sample = df_unique.copy()
        print(f"[!] Independent post count is {len(df_unique)} (less than 300), all posts included in the sample.")

    # Implementing slang classification and labeling
    results = [score_and_classify(row["text"], row["author_handle"]) for _, row in df_sample.iterrows()]
    df_sample["classified_identity"] = [r[0] for r in results]
    df_sample["fan_score"] = [r[1] for r in results]
    df_sample["matched_jargon"] = [", ".join(r[2]) if r[2] else "None" for r in results]

    # Feature engineering (text length and number of tags)
    df_sample["text_length"] = df_sample["text"].apply(len)
    df_sample["hashtag_count"] = df_sample["text"].apply(lambda x: x.count("#"))

    # Printed Sample Cluster Statistics
    print("\n" + "="*50)
    print(f"【{len(df_sample)} Identity Recognition Distribution of Samples】")
    print(df_sample["classified_identity"].value_counts())
    print("="*50)

    # Summary of Calculated Statistics (Comparison of Fans vs. the General Public, excluding official accounts)
    df_compare = df_sample[df_sample["classified_identity"].isin(["TWICE Fan", "General Public"])]
    summary_table = df_compare.groupby("classified_identity").agg(
        Sample_Count=("classified_identity", "count"),
        Average_Likes=("likes", "mean"),
        Median_Likes=("likes", "median"),
        Average_Comments=("comments", "mean"),
        Average_Text_Length=("text_length", "mean"),
        Average_Hashtag_Count=("hashtag_count", "mean")
    ).round(2)

    print("\n【Comparison of Behavioral Characteristics of TWICE Fans vs. the General Public】")
    print(summary_table)
    print("="*50)

    # Ensure the output directory exists and export the archive.
    os.makedirs("final_output", exist_ok=True)
    
    # 1. Output 300 sampling detail tables
    output_sample_csv = os.path.join("final_output", "twice_sample_300_classified.csv")
    df_sample.to_csv(output_sample_csv, index=False, encoding="utf-8-sig")
    print(f"\n[✓] Sampling details have been stored to：{output_sample_csv}")

    # 2. Output behavioral indicator statistics table
    output_summary_csv = os.path.join("final_output", "comparison_summary.csv")
    summary_table.to_csv(output_summary_csv, encoding="utf-8-sig")
    print(f"[✓] Statistical comparison summary has been stored to：{output_summary_csv}")

if __name__ == "__main__":
    main()