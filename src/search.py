import requests
from itertools import cycle
from pathlib import Path
import pandas as pd
from tqdm import tqdm


# =========================
# Load config: API keys, CX
# =========================

def load_api_keys(path: str = "env/search.txt"):
    """Đọc nhiều API key từ file txt, mỗi dòng 1 key."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Không tìm thấy file API keys: {p.resolve()}")

    keys = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        keys.append(line)

    if not keys:
        raise ValueError("File api_keys.txt không có API key hợp lệ nào.")

    return keys


def load_cx_id(path: str = "env/cx_id.txt"):
    """Đọc cx id từ file txt, dùng dòng đầu tiên không rỗng."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Không tìm thấy file cx_id: {p.resolve()}")

    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            return line

    raise ValueError("File cx_id.txt không chứa cx id hợp lệ.")


_API_KEYS = load_api_keys()
_API_KEY_CYCLE = cycle(_API_KEYS)
CX_ID = load_cx_id()


def get_api_key():
    """Lấy API key tiếp theo theo kiểu round robin."""
    return next(_API_KEY_CYCLE)


# =========================
# Google search logic
# =========================

def google_search(query: str, num_results: int = 5, max_attempts: int = 5):
    """
    Gọi Custom Search JSON API, exclude politifact, giới hạn num_results.
    Retry tối đa max_attempts, mỗi lần thử đổi API key.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    safe_query = f'{query} -site:politifact.com -site:www.politifact.com'

    last_error = None

    for attempt in range(1, max_attempts + 1):
        api_key = get_api_key()

        params = {
            "key": api_key,
            "cx": CX_ID,
            "q": safe_query,
            "num": num_results,
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])

            results = []
            for item in items:
                results.append(
                    {
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet"),
                    }
                )

            return results

        except Exception as e:
            last_error = e
            print(
                f"[google_search] Attempt {attempt}/{max_attempts} failed "
                f"with key starting '{api_key[:6]}...': {e}"
            )

    # Nếu đến đây nghĩa là tất cả attempt đều fail
    raise RuntimeError(
        f"Google search failed after {max_attempts} attempts"
    ) from last_error


# =========================
# Helper xử lý URL để lưu CSV
# =========================

def urls_to_string(results):
    """
    Convert list kết quả search thành 1 string để lưu CSV.
    Ở đây lấy link là chính, ngăn cách bằng ' | '.
    """
    if not isinstance(results, list):
        return ""

    links = []
    for item in results:
        if isinstance(item, dict) and "link" in item:
            links.append(str(item["link"]))
        else:
            links.append(str(item))

    return " | ".join(links)


# =========================
# Main pipeline
# =========================

def main():
    # Đọc CSV
    df = pd.read_csv("data/test.csv")

    if "statement" not in df.columns:
        raise ValueError("File CSV không có cột 'statement'")

    if "urls" not in df.columns:
        df["urls"] = ""

    output_path = "google_search/test.csv"

    # Duyệt theo index để dễ cập nhật trực tiếp vào df
    # đảo ngược thứ tự để đi từ cuối file lên đầu giống code ban đầu
    series_statements = df["statement"].iloc[::-1].astype(str)

    for idx, statement in tqdm(series_statements.items(), desc="Processing"):
        # idx ở đây là index thật của df (do iloc[::-1] giữ nguyên index gốc)

        existing = df.at[idx, "urls"]
        if isinstance(existing, str) and existing.strip() != "":
            continue

        try:
            search_results = google_search(
                statement,
                num_results=5,
            )
            urls_str = urls_to_string(search_results)
        except Exception as e:
            print(f"Error at row {idx}: {e}")
            urls_str = ""

        df.at[idx, "urls"] = urls_str

        # Ghi file ngay sau khi xử lý xong một dòng
        df.to_csv(output_path, index=False)

    print("Xong. Đã lưu vào:", output_path)


if __name__ == "__main__":
    main()
