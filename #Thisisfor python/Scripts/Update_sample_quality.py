import os
import json
import random
import re
import pandas as pd

# =========================================================
# 1. Four-language TWICE fan slang dictionary
# =========================================================
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
    "나연", "정연", "모모", "사나", "지효", "미南", "다현", "채영", "쯔위"
]

def evaluate_quality_and_identity(text: str, author_handle: str = ""):
    """Calculate post quality score, hit slang, associated identity, and quality level."""
    if str(author_handle).lower() in ["twicetagram", "jypetwice_japan"]:
        return "Official Account", 99, ["official_account"], "High Quality (Official)"
        
    if not text or not isinstance(text, str) or not text.strip():
        return "General Public", 0, [], "Low Text Content"
        
    text_lower = text.lower()
    score = 0
    matched = []
    
    # Determining core slang (3 points)
    for kw in CORE_FAN_JARGON:
        if kw.startswith(r"#") or kw.startswith(r"\b"):
            if re.search(kw, text_lower):
                score += 3
                matched.append(kw.replace(r"\b", "").replace("#", ""))
        else:
            if kw in text_lower:
                score += 3
                matched.append(kw)
                
    # General check-in word judgment (1 point)
    for kw in CASUAL_KEYWORDS:
        if kw.startswith(r"#"):
            if re.search(kw, text_lower):
                score += 1
                matched.append(kw.replace("#", ""))
        else:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower) or kw in text_lower:
                score += 1
                matched.append(kw)

    matched = list(set(matched))
    
    # Identity verification
    identity = "TWICE Fan" if score >= 3 else "General Public"
    
    # Quality grading (combining length and vocabulary richness)
    text_clean = text.strip()
    if len(text_clean) > 60 and score >= 3:
        quality = "Tier 1: High Quality (Detailed Fan post)"
    elif len(text_clean) > 40:
        quality = "Tier 2: Medium Quality (Rich Context)"
    elif len(text_clean) > 15:
        quality = "Tier 3: Standard Post"
    else:
        quality = "Tier 4: Short / Tag-only Post"
        
    return identity, score, matched, quality

# =========================================================
# 2. Full database scanning and integration
# =========================================================
def build_master_database():
    current_dir = os.getcwd()
    all_raw_files = []
    
    # Traverse the current directory and all subfolders (raw_data, Data base and so on)
    for root, dirs, files in os.walk(current_dir):
        if "final_output" in root:
            continue
        for file in files:
            if file.startswith("twice_") or file.startswith("comparison_") or file.startswith("package"):
                continue
            if file.endswith(".csv") or file.endswith(".json") or file.endswith(".xlsx"):
                all_raw_files.append(os.path.join(root, file))

    print(f"[*] Scanned {len(all_raw_files)} raw data files, loading master database...")
    records = []
    for file_path in all_raw_files:
        try:
            if file_path.endswith(".csv"):
                df_temp = pd.read_csv(file_path, low_memory=False)
                for _, row in df_temp.iterrows():
                    records.append(standardize_row(row.to_dict()))
            elif file_path.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                posts = content.get("posts", []) if isinstance(content, dict) else content
                if isinstance(posts, list):
                    for item in posts:
                        if isinstance(item, dict):
                            records.append(standardize_row(item))
            elif file_path.endswith(".xlsx"):
                df_temp = pd.read_excel(file_path)
                for _, row in df_temp.iterrows():
                    records.append(standardize_row(row.to_dict()))
        except Exception as e:
            continue

    df_master = pd.DataFrame(records)
    print(f"[✓] The entire database has been read; the total number of entries in the original parent database is now complete.: {len(df_master)} 筆")
    return df_master

def standardize_row(item: dict) -> dict:
    """Standardize the field naming across different data files"""
    uid = item.get("entity_id") or item.get("id") or item.get("shortCode") or item.get("code") or ""
    url = item.get("url") or item.get("postUrl") or item.get("inputUrl") or ""
    text = item.get("text") or item.get("caption") or item.get("clean_caption") or item.get("description") or ""
    if isinstance(text, dict):
        text = text.get("text", "")
    author = item.get("author_handle") or item.get("owner_username") or item.get("author_name") or ""
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
# 3. Deduplication, random selection of 300 samples, and quality assessment.
# =========================================================
def main():
    df_master = build_master_database()
    if df_master.empty:
        print("[X] Error: No posts were found in the database!")
        return

    # Filtering empty posts
    df_master = df_master[df_master["text"].str.len() > 0].copy()

    # Duplicate detection and deduplication
    dedup_key = "url" if df_master["url"].nunique() > 10 else ("uid" if df_master["uid"].nunique() > 10 else "text")
    before_dedup = len(df_master)
    df_unique = df_master.drop_duplicates(subset=[dedup_key]).copy()
    print(f"[✓] According '{dedup_key}' Deduplication complete: Remove {before_dedup - len(df_unique)} Duplicate posts, remaining independent posts: {len(df_unique)} posts。")

    # =====================================================
    # Core: Randomly select 300 samples.
    # =====================================================
    TARGET_SAMPLE_SIZE = 300
    if len(df_unique) >= TARGET_SAMPLE_SIZE:
        random.seed(42)  # Fixed random seed to ensure academic reproducibility
        sample_indices = random.sample(list(df_unique.index), TARGET_SAMPLE_SIZE)
        df_sample = df_unique.loc[sample_indices].copy()
        print(f"[*] Successful random sampling {TARGET_SAMPLE_SIZE} samples！")
    else:
        df_sample = df_unique.copy()
        print(f"[!] The total number of independent posts is {len(df_unique)} posts（<300）All of them have been included in the sample.")

    # Execution quality and slang identity assessment
    identities, scores, matched_lists, qualities = [], [], [], []
    for _, row in df_sample.iterrows():
        ident, sc, m_list, qual = evaluate_quality_and_identity(row["text"], row["author_handle"])
        identities.append(ident)
        scores.append(sc)
        matched_lists.append(", ".join(m_list) if m_list else "None")
        qualities.append(qual)

    df_sample["classified_identity"] = identities
    df_sample["fan_score"] = scores
    df_sample["matched_jargon"] = matched_lists
    df_sample["sample_quality"] = qualities
    df_sample["text_length"] = df_sample["text"].apply(len)

    print("\n" + "="*50)
    print(f"【{len(df_sample)} samples of Idtentity verifying")
    print(df_sample["classified_identity"].value_counts())
    print("\n【Quality grade distribution of 300 samples】")
    print(df_sample["sample_quality"].value_counts())
    print("="*50)

    # Output to the final_output folder
    os.makedirs("final_output", exist_ok=True)
    out_file = os.path.join("final_output", "twice_sample_300_quality.csv")
    df_sample.to_csv(out_file, index=False, encoding="utf-8-sig")
    print(f"\n[✓] Sampling complete! 300 samples, including quality labels, have been stored in:{out_file}")

if __name__ == "__main__":
    main()