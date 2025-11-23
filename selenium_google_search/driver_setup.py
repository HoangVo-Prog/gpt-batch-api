import random
import tempfile
import undetected_chromedriver as uc


HEADLESS = True 
CHROME_DRIVER_VERSION = 142

def setup_driver():
    """
    Initializes a Chrome WebDriver instance with undetected-chromedriver.
    """
    chrome_options = uc.ChromeOptions()

    # Use a unique temporary directory for each worker to avoid conflicts
    temp_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    chrome_options.add_argument(f"--data-path={temp_dir}")

    # General browser settings
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-site-isolation-trials")
    chrome_options.add_argument("--disable-popup-blocking")

    # Disable popup blocking to allow new tabs

    # Headless Mode (Avoid Detection)
    chrome_options.headless = HEADLESS

    # Prevent detection by removing automation flags and using a random User-Agent
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation detection

    # Vietnamese user agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL Build/QQ1A.200205.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.120 Mobile Safari/537.36",
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")

    # Set the Accept-Language header to Vietnamese
    chrome_options.add_argument("--lang=en-US")

    try:
        driver = uc.Chrome(
            options=chrome_options,
            use_subprocess=True,
        )
        driver.maximize_window()  # Ensures window is maximized, even in headless mode
        return driver
    except Exception as e:
        raise Exception(f"Failed to initialize WebDriver: {e}")


def setup_driver_linux():
    """
    Initializes a Chrome WebDriver instance for Colab with undetected-chromedriver.
    """
    # Tạo option mới
    chrome_options = uc.ChromeOptions()

    # Tạo thư mục tạm để tránh lỗi profile conflict
    temp_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    chrome_options.add_argument(f"--data-path={temp_dir}")

    # Cấu hình cơ bản
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--lang=vi-VN")

    # Random User-Agent (ẩn bot footprint)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
    chrome_options.add_argument("--lang=vi-VN")


    # Headless Mode (dạng mới để Colab không crash)
    if HEADLESS:
        chrome_options.add_argument("--headless=new")

    try:
        driver = uc.Chrome(options=chrome_options, use_subprocess=True)
        driver.set_window_size(1920, 1080)
        return driver
    except Exception as e:
        raise RuntimeError(f"❌ Failed to initialize WebDriver: {e}")
    
import time
from urllib.parse import quote_plus

from selenium.webdriver.common.by import By

import time
from urllib.parse import quote_plus

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


def _google_search_once(query, num_results=5, allowed_domains=None,
                        debug=False, sleep_time=3):
    """
    Chạy 1 lần Google Search, trả về list url (có thể rỗng).
    Không retry ở đây, để hàm bên ngoài lo.
    """
    driver = setup_driver()  # dùng driver local đã chỉnh

    try:
        encoded_q = quote_plus(query)
        search_url = (
            f"https://www.google.com/search?q={encoded_q}"
            f"&num={num_results}&hl=en&gl=us&pws=0"
        )
        driver.get(search_url)

        # Đợi cho trang load, ưu tiên khi trong #search đã có ít nhất 1 link http
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(
                    By.CSS_SELECTOR,
                    "div#search a[href^='http']"
                )
                or "did not match any documents." in d.page_source.lower()
            )
        except TimeoutException:
            # Không tìm được link nào trong thời gian chờ
            if debug:
                print("[_google_search_once] Timeout đợi link trong #search.")
                print("Current URL:", driver.current_url)
            time.sleep(sleep_time)

        if debug:
            print("[_google_search_once] Current URL:", driver.current_url)

        html = driver.page_source
        lower_html = html.lower()

        # 1. Kiểm tra bị block / CAPTCHA
        block_phrases = [
            "unusual traffic from your computer network",
            "/sorry/index",
            "our systems have detected unusual traffic",
        ]
        if any(p in lower_html for p in block_phrases):
            if debug:
                print("[_google_search_once] Bị Google chặn (CAPTCHA / unusual traffic).")
                print(lower_html[:1500])
            return []

        # 2. Trang consent / cookie
        if "consent.google.com" in driver.current_url or "consent" in lower_html:
            if debug:
                print("[_google_search_once] Trang consent / đồng ý cookie.")
            btn_selectors = [
                "button[aria-label*='Agree to all']",
                "button[aria-label*='Accept all']",
                "button[aria-label*='I agree']",
                "button[aria-label*='Tôi đồng ý']",
                "form[action*='consent'] button[type='submit']",
            ]
            clicked = False
            for sel in btn_selectors:
                try:
                    btns = driver.find_elements(By.CSS_SELECTOR, sel)
                    if btns:
                        btns[0].click()
                        clicked = True
                        if debug:
                            print("[_google_search_once] Đã click consent:", sel)
                        break
                except Exception:
                    pass

            if not clicked:
                if debug:
                    print("[_google_search_once] Không click được consent, trả []")
                    print(lower_html[:1500])
                return []

            time.sleep(sleep_time)
            html = driver.page_source
            lower_html = html.lower()

        urls = []
        seen = set()

        def collect_results():
            # ==== ĐOẠN MỚI QUAN TRỌNG NHẤT ====
            # Cố gắng giới hạn trong khối kết quả chính
            try:
                root = driver.find_element(By.CSS_SELECTOR, "div#search")
            except Exception:
                root = driver

            anchors = root.find_elements(By.CSS_SELECTOR, "a[href^='http']")
            if debug:
                print(f"[_google_search_once] Thấy {len(anchors)} anchors (raw).")

            found_any = False

            for a in anchors:
                href = a.get_attribute("href")
                if not href:
                    continue

                # Bỏ qua các link nội bộ của Google
                if any(skip in href for skip in [
                    "google.com/search",
                    "google.com/url?",
                    "google.com/preferences",
                    "webcache.googleusercontent.com",
                    "translate.google.com",
                ]):
                    continue

                # Bỏ trùng
                if href in seen:
                    continue

                # Lọc theo domain nếu có yêu cầu
                if allowed_domains and not any(dom in href for dom in allowed_domains):
                    continue

                seen.add(href)
                urls.append(href)
                found_any = True

                if len(urls) >= num_results:
                    return True

            if debug:
                print(f"[_google_search_once] Sau khi lọc còn {len(urls)} urls.")
            return found_any

        # 3. Thu kết quả + scroll thêm nếu cần
        enough = collect_results()
        scroll_tries = 0
        while not enough and len(urls) < num_results and scroll_tries < 5:
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(1.5)
            enough = collect_results()
            scroll_tries += 1

        if debug and not urls:
            print("[_google_search_once] Kết quả rỗng, HTML preview:")
            print(lower_html[:1500])

        return urls[:num_results]

    finally:
        try:
            driver.quit()
        except Exception:
            pass

def google_search_urls(query, num_results=5, allowed_domains=None,
                       debug=False, sleep_time=3,
                       max_attempts=3, base_delay=2.0):
    """
    Wrapper có retry.

    max_attempts: số lần thử tối đa.
    base_delay: delay cơ bản giữa các lần thử (sẽ nhân với số attempt).
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        if debug:
            print(f"[google_search_urls] Attempt {attempt}/{max_attempts}")

        try:
            urls = _google_search_once(
                query,
                num_results=num_results,
                allowed_domains=allowed_domains,
                debug=debug,
                sleep_time=sleep_time,
            )
        except Exception as e:
            last_error = e
            urls = []
            if debug:
                print(f"[google_search_urls] Exception ở attempt {attempt}: {e}")

        if urls:
            if debug:
                print(f"[google_search_urls] Thành công ở attempt {attempt}")
            return urls

        # Nếu chưa có kết quả thì chờ rồi thử lại (backoff nhẹ)
        if attempt < max_attempts:
            delay = base_delay * attempt
            if debug:
                print(f"[google_search_urls] Chưa có kết quả, sleep {delay} giây rồi retry...")
            time.sleep(delay)

    if debug:
        print("[google_search_urls] Hết attempts mà vẫn rỗng.")
        if last_error:
            print("Last error:", last_error)

    return []
