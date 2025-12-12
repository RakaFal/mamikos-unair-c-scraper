import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


LIST_URL = "https://mamikos.com/cari/universitas-airlangga-kampus-c-universitas-airlangga-kampus-c-jalan-dokter-ir-haji-soekarno-mulyorejo-kota-surabaya-jawa-timur-indonesia/all/bulanan/0-15000000?keyword=universitas%20airlangga&suggestion_type=search&rent=2&sort=price,-&price=10000-650000&singgahsini=0"


# =========================================================
# DRIVER
# =========================================================
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1024,968")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


# =========================================================
# SCROLL UNTIL ALL CARDS LOADED
# =========================================================
def scroll_until_cards_loaded(driver, timeout=60):
    end = time.time() + timeout
    last_count = 0

    while time.time() < end:
        driver.find_elements(By.CSS_SELECTOR, "div[data-testid='kostRoomCard']")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

        # Click "load more" if available
        try:
            load_more = driver.find_element(By.CSS_SELECTOR, "a.list__content-load-link")
            if load_more.is_displayed():
                driver.execute_script("arguments[0].click();", load_more)
                time.sleep(2.5)
        except:
            pass

        new_count = len(driver.find_elements(By.CSS_SELECTOR, "div[data-testid='kostRoomCard']"))

        # If no new cards and no load button → stop
        if new_count == last_count:
            try:
                driver.find_element(By.CSS_SELECTOR, "a.list__content-load-link")
            except:
                break

        last_count = new_count

    return driver.find_elements(By.CSS_SELECTOR, "div[data-testid='kostRoomCard']")


# =========================================================
# UTILITIES
# =========================================================
def wait_js_exists(driver, script, timeout=15):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script(script))


def get_js(driver, script):
    return driver.execute_script(script)


# =========================================================
# SCRAPE DETAIL PAGE
# =========================================================
def scrape_detail_page(driver):
    data = {}

    # Smooth scroll to load everything
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(0.8)

    # Nama
    try:
        data["Nama"] = driver.find_element(By.CSS_SELECTOR, "p.detail-title__room-name").text.strip()
    except:
        data["Nama"] = ""

    # Tipe indekos
    try:
        wait_js_exists(driver, "return document.querySelector('span.detail-kost-overview__gender-box') !== null;")
        tipe = get_js(driver, """
            let el = document.querySelector('span.detail-kost-overview__gender-box');
            return el ? el.innerText.trim().replace("Kos ", "") : "";
        """)
        data["Tipe Indekos"] = tipe
    except:
        data["Tipe Indekos"] = ""

    # Harga
    try:
        wait_js_exists(driver, "return document.querySelector('[data-testid=\"kostDetailPriceReal\"]') !== null;")
        harga = get_js(driver, """
            let el = document.querySelector('[data-testid="kostDetailPriceReal"]');
            return el ? el.innerText.replace("Rp", "").trim() : "";
        """)
        data["Harga"] = harga
    except:
        data["Harga"] = ""

    # Fasilitas (AC, WiFi, Kamar Mandi, Parkir, Dapur, Kulkas, Listrik)
    def check_facility(label_list, target):
        return "Ada" if target in label_list else "Tidak Ada"

    try:
        labels = get_js(driver, """
            return Array.from(
                document.querySelectorAll('p.detail-kost-facility-item__label')
            ).map(el => el.innerText.trim().toLowerCase());
        """)
    except:
        labels = []

    data["AC"] = "AC" if "ac" in labels else "Tidak AC"
    data["WiFi"] = check_facility(labels, "wifi")

    # Kamar mandi
    km_dalam = any("mandi dalam" in t for t in labels)
    km_luar = any("mandi luar" in t for t in labels)
    data["Kamar Mandi"] = (
        "Dalam & Luar" if km_dalam and km_luar else
        "Dalam" if km_dalam else
        "Luar" if km_luar else ""
    )

    # Parkir
    motor = any(t in labels for t in ["parkir motor", "parkir sepeda"])
    mobil = any("parkir mobil" in t for t in labels)
    data["Parkir"] = "Motor & Mobil" if motor and mobil else "Motor" if motor else "Mobil" if mobil else ""

    data["Dapur"] = "Bersama" if "dapur" in labels else "Tidak Ada"
    data["Kulkas"] = "Ada" if "kulkas" in labels else "Tidak Ada"

    # Listrik
    if any("tidak termasuk listrik" in t for t in labels):
        data["Listrik"] = "Tidak Termasuk"
    elif any("termasuk listrik" in t for t in labels):
        data["Listrik"] = "Termasuk"
    else:
        data["Listrik"] = ""

    # Landmark (jarak)
    try:
        wait_js_exists(driver, "return document.querySelectorAll('[data-testid=\"landmark-item\"]').length > 0;")
        jarak = get_js(driver, """
            let items = document.querySelectorAll('[data-testid="landmark-item"]');
            for (let item of items) {
                let name = item.querySelector('.landmark-item__text-ellipsis')?.innerText.toLowerCase() || "";
                let dist = item.querySelector('.landmark-item__landmark-distance')?.innerText.trim() || "";
                if (name.includes("airlangga")) return dist;
            }
            return "";
        """)
        data["Jarak ke Kampus"] = jarak
    except:
        data["Jarak ke Kampus"] = ""

    # Luas kamar
    try:
        luas = get_js(driver, """
            let items = document.querySelectorAll('p.detail-kost-facility-item__label');
            for (let el of items) {
                if (/\\d+\\s*x\\s*\\d+/i.test(el.innerText)) return el.innerText.trim();
            }
            return "";
        """)
        data["Luas Kamar"] = luas
    except:
        data["Luas Kamar"] = ""

    return data


# =========================================================
# MAIN
# =========================================================
def main():
    driver = init_driver()
    driver.get(LIST_URL)
    time.sleep(5)

    cards = scroll_until_cards_loaded(driver)
    total = len(cards)
    print(f"[INFO] Total card ditemukan: {total}")

    main_window = driver.current_window_handle
    results = []

    for i in range(total):
        print(f"[INFO] Memproses card {i+1}/{total}")

        cards = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='kostRoomCard']")
        if i >= len(cards):
            cards = scroll_until_cards_loaded(driver, timeout=10)

        card = cards[i]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", card)
        time.sleep(2)

        for window in driver.window_handles:
            if window != main_window:
                driver.switch_to.window(window)
                break

        detail = scrape_detail_page(driver)
        results.append(detail)
        print(detail)

        driver.close()
        driver.switch_to.window(main_window)
        time.sleep(1)

    # CSV
    header = [
        "Nama","Tipe Indekos","Jarak ke Kampus","Luas Kamar",
        "AC","WiFi","Kamar Mandi","Parkir","Dapur","Listrik","Kulkas","Harga"
    ]

    with open("data_kos_unair_c.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(results)

    print("[SELESAI] Data tersimpan ke data_kos_unair_c.csv")


if __name__ == "__main__":
    main()
