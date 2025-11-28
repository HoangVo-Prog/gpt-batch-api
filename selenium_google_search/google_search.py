from driver_setup import google_search_urls
from tqdm import tqdm 
import pandas as pd



def urls_to_string(url_list):
    if not isinstance(url_list, list):
        return ""
    return ", ".join(url_list)

df = pd.read_csv("test.csv")

if "statement" not in df.columns:
    raise ValueError("File CSV không có cột 'statement'")

if "searchResults" not in df.columns:
    df["searchResults"] = ""

output_path = "liar_test.csv"

# Duyệt theo index để dễ cập nhật trực tiếp vào df
for idx, statement in tqdm(df["statement"].iloc[::-1].astype(str).items(), desc="Processing"):
    # Nếu dòng này đã có kết quả rồi thì bỏ qua
    existing = df.at[idx, "searchResults"]
    if isinstance(existing, str) and existing.strip() != "":
        continue

    query = statement + " -site:politifact.com"

    try:
        urls = google_search_urls(
            query,
            num_results=3,
            debug=True,
            max_attempts=10,
            base_delay=2.0
        )
    except Exception as e:
        print(f"Error at row {idx}:", e)
        urls = []

    # Lưu kết quả vào df ngay cho dòng hiện tại
    df.at[idx, "searchResults"] = urls_to_string(urls)

    # Ghi file ngay sau khi xử lý xong một dòng
    df.to_csv(output_path, index=False)

print("Xong. Đã lưu vào:", output_path)