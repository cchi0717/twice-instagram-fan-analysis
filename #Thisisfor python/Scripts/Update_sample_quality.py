import os
import json
import random
import re
import pandas as pd

# =========================================================
# 1. 四國語言 TWICE 粉絲黑話特徵字典庫
# =========================================================
CORE_FAN_JARGON = [
    # 官方粉絲名 (英/中/韓/日)
    r"#once\b", r"\bonces\b", "萬斯", "万斯", "元斯", "원스", "ワンス",
    # 應援手燈與內部專用語
    "candybong", "candy bong", "糖果棒", "手燈", "手灯", "應援棒", "应援棒",
    "캔디봉", "응원봉", "キャンディー棒", "ペンライト",
    "twicetagram", "withyouth", "strategy", "ten: the story goes on",
    # 粉絲圈術語
    "ot9", "bias", "ult group", "fave", "stan twice", "翻牌", "應援板", "应援板", "空耳",
    "최애", "차애", "덕질", "공봉", "막콘", "첫콘", "올콘", "슬로건",
    "参戦", "現場参戦", "銀テ", "掛け声", "推し", "自引き",
    # 成員外號 / 暱稱 / 韓文日文小名
    "林三歲", "林三岁", "兔牙", "nabongs", "나봉스", "ナヨン",
    "無趣哥", "无趣哥", "yoo", "ジョンヨン",
    "moguri", "모구리", "平井桃", "跳舞機器", "跳舞机器", "モモ",
    "柴犬", "紗夏", "纱夏", "松鼠", "nosananolife", "no sana no life", "サナ", "さーたん", "サナペン",
    "godjihyo", "god志效", "小隊", "小队", "朴隊", "ジヒョ",
    "minari", "미나리", "企鵝", "企鹅", "黑天鵝", "黑天鹅", "南醬", "ミナ",
    "dubu", "두부", "老鷹", "老鹰", "豆腐", "ダヒョン",
    "chaeng", "챙", "小猛獸", "小猛兽", "草莓公主", "彩寶", "チェヨン",
    "尤達", "尤达", "忙內", "忙内", "尤達瑜", "小瑜", "ツウィ", "ツウィペン",
    # 小分隊與 CP 名
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
    """計算貼文品質分數、命中黑話、所屬身分與品質等級"""
    if str(author_handle).lower() in ["twicetagram", "jypetwice_japan"]:
        return "Official Account", 99, ["official_account"], "High Quality (Official)"
        
    if not text or not isinstance(text, str) or not text.strip():
        return "General Public", 0, [], "Low Text Content"
        
    text_lower = text.lower()
    score = 0
    matched = []
    
    # 核心黑話判定 (3分)
    for kw in CORE_FAN_JARGON:
        if kw.startswith(r"#") or kw.startswith(r"\b"):
            if re.search(kw, text_lower):
                score += 3
                matched.append(kw.replace(r"\b", "").replace("#", ""))
        else:
            if kw in text_lower:
                score += 3
                matched.append(kw)
                
    # 一般打卡詞判定 (1分)
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
    
    # 身分判定
    identity = "TWICE Fan" if score >= 3 else "General Public"
    
    # 品質分級評定 (結合長度與詞彙豐富度)
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
# 2. 全庫掃描與母體整合
# =========================================================
def build_master_database():
    current_dir = os.getcwd()
    all_raw_files = []
    
    # 遍歷當前目錄及所有子資料夾 (raw_data, Data base 等)
    for root, dirs, files in os.walk(current_dir):
        if "final_output" in root:
            continue
        for file in files:
            if file.startswith("twice_") or file.startswith("comparison_") or file.startswith("package"):
                continue
            if file.endswith(".csv") or file.endswith(".json") or file.endswith(".xlsx"):
                all_raw_files.append(os.path.join(root, file))

    print(f"[*] 掃描到 {len(all_raw_files)} 個原始數據檔案，正在載入母體資料庫...")

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
    print(f"[✓] 全庫讀取完畢，原始母體總筆數: {len(df_master)} 筆")
    return df_master

def standardize_row(item: dict) -> dict:
    """統一不同資料檔的欄位命名"""
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
# 3. 去重、隨機抽取 300 份樣本與品質評定
# =========================================================
def main():
    df_master = build_master_database()
    if df_master.empty:
        print("[X] 錯誤：資料庫中沒有讀取到任何貼文！")
        return

    # 過濾空貼文
    df_master = df_master[df_master["text"].str.len() > 0].copy()

    # 查重去重
    dedup_key = "url" if df_master["url"].nunique() > 10 else ("uid" if df_master["uid"].nunique() > 10 else "text")
    before_dedup = len(df_master)
    df_unique = df_master.drop_duplicates(subset=[dedup_key]).copy()
    print(f"[✓] 依據 '{dedup_key}' 去重完成：去除 {before_dedup - len(df_unique)} 筆重複貼文，剩餘獨立貼文: {len(df_unique)} 筆。")

    # =====================================================
    # 核心：隨機抽取 300 份樣本 (Random Sampling)
    # =====================================================
    TARGET_SAMPLE_SIZE = 300
    if len(df_unique) >= TARGET_SAMPLE_SIZE:
        random.seed(42)  # 固定隨機種子，確保學術可重複性
        sample_indices = random.sample(list(df_unique.index), TARGET_SAMPLE_SIZE)
        df_sample = df_unique.loc[sample_indices].copy()
        print(f"[*] 成功隨機抽取 {TARGET_SAMPLE_SIZE} 份樣本！")
    else:
        df_sample = df_unique.copy()
        print(f"[!] 獨立貼文總數為 {len(df_unique)} 筆（少於 300），已全數納入樣本。")

    # 執行品質與黑話身分評定
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
    print(f"【{len(df_sample)} 份樣本之身分識別分佈】")
    print(df_sample["classified_identity"].value_counts())
    print("\n【300 份樣本之品質等級分佈】")
    print(df_sample["sample_quality"].value_counts())
    print("="*50)

    # 輸出至 final_output 資料夾
    os.makedirs("final_output", exist_ok=True)
    out_file = os.path.join("final_output", "twice_sample_300_quality.csv")
    df_sample.to_csv(out_file, index=False, encoding="utf-8-sig")
    print(f"\n[✓] 採樣完成！包含品質標註之 300 份樣本已儲存至：{out_file}")

if __name__ == "__main__":
    main()