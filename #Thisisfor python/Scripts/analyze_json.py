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
# 2. 全域遞迴讀取所有原始檔案並整合母體資料庫
# =========================================================
def build_master_database():
    current_dir = os.getcwd()
    all_raw_files = []
    
    # 遍歷當前目錄及所有子資料夾 (raw_data, Data base 等)
    for root, dirs, files in os.walk(current_dir):
        # 排除存放分析結果的資料夾
        if "final_output" in root:
            continue
        for file in files:
            # 排除已生成的分析輸出檔案與系統檔
            if file.startswith("twice_") or file.startswith("comparison_") or file.startswith("package"):
                continue
            if file.endswith(".csv") or file.endswith(".json") or file.endswith(".xlsx"):
                all_raw_files.append(os.path.join(root, file))

    print(f"[*] 找到以下原始資料來源檔 (共 {len(all_raw_files)} 個):")
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
            print(f"[!] 讀取檔案失敗 ({os.path.basename(file_path)}): {e}")

    df_master = pd.DataFrame(records)
    print(f"\n[✓] 全庫讀取完畢，原始合併母體總筆數: {len(df_master)} 筆")
    return df_master

def extract_standard_row(item: dict) -> dict:
    """將來自不同平台或格式的欄位統整為標準欄位格式"""
    # 唯一標識優先級
    uid = item.get("entity_id") or item.get("id") or item.get("shortCode") or item.get("code") or ""
    url = item.get("url") or item.get("postUrl") or item.get("inputUrl") or ""
    # 文字內容優先級
    text = item.get("text") or item.get("caption") or item.get("clean_caption") or item.get("description") or ""
    if isinstance(text, dict):
        text = text.get("text", "")
    # 作者欄位
    author = item.get("author_handle") or item.get("owner_username") or item.get("author_name") or ""
    # 互動指標
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
# 3. 去重、抽取 300 份樣本與比較分析
# =========================================================
def main():
    df_master = build_master_database()
    if df_master.empty:
        print("[X] 錯誤：資料庫中沒有讀取到任何貼文！")
        return

    # 去除空貼文
    df_master = df_master[df_master["text"].str.len() > 0].copy()

    # 查重去重（優先根據 url，若 url 無效則根據 uid 或文字雜湊）
    if df_master["url"].nunique() > 10:
        dedup_key = "url"
    elif df_master["uid"].nunique() > 10:
        dedup_key = "uid"
    else:
        dedup_key = "text"

    before_dedup = len(df_master)
    df_unique = df_master.drop_duplicates(subset=[dedup_key]).copy()
    print(f"[✓] 已根據 '{dedup_key}' 去重：去除 {before_dedup - len(df_unique)} 筆重複貼文，剩餘獨立貼文總庫存: {len(df_unique)} 筆。")

    # 隨機抽取 300 份樣本
    TARGET_SAMPLE_SIZE = 300
    if len(df_unique) >= TARGET_SAMPLE_SIZE:
        random.seed(42)  # 固定隨機種子，確保學術可重複性
        sample_indices = random.sample(list(df_unique.index), TARGET_SAMPLE_SIZE)
        df_sample = df_unique.loc[sample_indices].copy()
        print(f"[*] 成功從全體資料庫隨機抽取 {TARGET_SAMPLE_SIZE} 份樣本！")
    else:
        df_sample = df_unique.copy()
        print(f"[!] 獨立貼文總數為 {len(df_unique)} 筆（少於 300 筆），已全數納入樣本。")

    # 執行黑話分類標註
    results = [score_and_classify(row["text"], row["author_handle"]) for _, row in df_sample.iterrows()]
    df_sample["classified_identity"] = [r[0] for r in results]
    df_sample["fan_score"] = [r[1] for r in results]
    df_sample["matched_jargon"] = [", ".join(r[2]) if r[2] else "None" for r in results]

    # 特徵工程（文字長度與標籤數）
    df_sample["text_length"] = df_sample["text"].apply(len)
    df_sample["hashtag_count"] = df_sample["text"].apply(lambda x: x.count("#"))

    # 列印樣本分群統計
    print("\n" + "="*50)
    print(f"【{len(df_sample)} 份樣本之身分識別分佈】")
    print(df_sample["classified_identity"].value_counts())
    print("="*50)

    # 計算統計摘要（排除官方帳號後的粉絲 vs 大眾對比）
    df_compare = df_sample[df_sample["classified_identity"].isin(["TWICE Fan", "General Public"])]
    summary_table = df_compare.groupby("classified_identity").agg(
        樣本數=("classified_identity", "count"),
        平均讚數=("likes", "mean"),
        中位數讚數=("likes", "median"),
        平均留言數=("comments", "mean"),
        平均內文字數=("text_length", "mean"),
        平均標籤數=("hashtag_count", "mean")
    ).round(2)

    print("\n【TWICE 粉絲 vs 大眾 行為特徵比較表】")
    print(summary_table)
    print("="*50)

    # 確保輸出目錄存在並導出檔案
    os.makedirs("final_output", exist_ok=True)
    
    # 1. 輸出 300 份抽樣明細表
    output_sample_csv = os.path.join("final_output", "twice_sample_300_classified.csv")
    df_sample.to_csv(output_sample_csv, index=False, encoding="utf-8-sig")
    print(f"\n[✓] 抽樣明細已儲存至：{output_sample_csv}")

    # 2. 輸出行為指標統計表
    output_summary_csv = os.path.join("final_output", "comparison_summary.csv")
    summary_table.to_csv(output_summary_csv, encoding="utf-8-sig")
    print(f"[✓] 統計對比摘要已儲存至：{output_summary_csv}")

if __name__ == "__main__":
    main()