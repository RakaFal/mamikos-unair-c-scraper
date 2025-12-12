import time
import csv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


LIST_URL = "https://mamikos.com/cari/universitas-airlangga-kampus-c-universitas-airlangga-kampus-c-jalan-dokter-ir-haji-soekarno-mulyorejo-kota-surabaya-jawa-timur-indonesia/all/bulanan/0-15000000?keyword=universitas%20airlangga&suggestion_type=search&rent=2&sort=price,-&price=10000-20000000&singgahsini=0"


# ============================================================
# DRIVER SETUP
# ============================================================

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


# ============================================================
# LOAD ALL KOST CARDS BY SCROLLING
# ============================================================

def scroll_until_cards_loaded(driver, timeout=20):
    end_time = time.time() + timeout
    last_count = 0

    while time.time() < end_time:
        cards = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='kostRoomCard']")
        count = len(cards)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.8)

        if count == last_count:
            break

        last_count = count

    return driver.find_elements(By.CSS_SELECTOR, "div[data-testid='kostRoomCard']")


# ============================================================
# SCRAPE DETAIL OF ONE KOST PAGE
# ============================================================

def scrape_detail_page(driver):
    data = {}

    # Allow React components to render
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(0.8)

    # Nama kos
    try:
        data["Nama"] = driver.find_element(By.CSS_SELECTOR, "p.detail-title__room-name").text.strip()
    except:
        data["Nama"] = ""

    # Tipe indekos
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script(
                "return document.querySelector('span.detail-kost-overview__gender-box')?.innerText.trim().length > 0;"
            )
        )
        tipe = driver.execute_script("""
            const el = document.querySelector('span.detail-kost-overview__gender-box');
            return el ? el.innerText.trim() : "";
        """)
        data["Tipe Indekos"] = tipe.replace("Kos ", "")
    except:
        data["Tipe Indekos"] = ""

    # Harga
    try:
        harga_elem = driver.find_elements(By.XPATH, "//div[contains(text(),'Rp')]")
        data["Harga"] = harga_elem[0].text.strip() if harga_elem else ""
    except:
        data["Harga"] = ""

    # Fasilitas via HTML text
    fasilitas_text = driver.page_source.lower()

    data["AC"] = "Ada" if "ac" in fasilitas_text else "Tidak Ada"
    data["WiFi"] = "Ada" if "wifi" in fasilitas_text else "Tidak Ada"

    # Kamar mandi
    dalam = "kamar mandi dalam" in fasilitas_text
    luar = "kamar mandi luar" in fasilitas_text

    if dalam and luar:
        data["Kamar Mandi"] = "Dalam dan Luar"
    elif dalam:
        data["Kamar Mandi"] = "Dalam"
    elif luar:
        data["Kamar Mandi"] = "Luar"
    else:
        data["Kamar Mandi"] = ""

    data["Parkir"] = "Ada" if "parkir" in fasilitas_text else "Tidak Ada"
    data["Dapur"] = "Ada" if "dapur" in fasilitas_text else "Tidak Ada"
    data["Kulkas"] = "Ada" if "kulkas" in fasilitas_text else "Tidak Ada"
    data["Listrik"] = "Termasuk" if "listrik" in fasilitas_text else "Tidak Termasuk"

    # Label fields: Jarak & Luas
    def find_label(label):
        try:
            elems = driver.find_elements(By.XPATH, f"//*[contains(text(),'{label}')]")
            if not elems:
                return ""
            return elems[0].find_element(By.XPATH, "following-sibling::*[1]").text.strip()
        except:
            return ""

    data["Jarak ke Kampus"] = find_label("Jarak ke Kampus")
    data["Luas Kamar"] = find_label("Luas Kamar")

    return data


# ============================================================
# MAIN LOGIC
# ============================================================

def main():
    driver = init_driver()
    driver.get(LIST_URL)
    time.sleep(5)

    print("[INFO] Memuat semua kartu kos…")
    cards = scroll_until_cards_loaded(driver)
    total_cards = len(cards)

    print(f"[INFO] Total kartu kos ditemukan: {total_cards}")

    main_window = driver.current_window_handle
    results = []

    for i in range(total_cards):
        print(f"\n[INFO] Mengambil data kos {i+1}/{total_cards}")

        cards = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='kostRoomCard']")
        card = cards[i]

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
        time.sleep(1)

        driver.execute_script("arguments[0].click();", card)
        time.sleep(2)

        # Switch tab
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

    # Save CSV
    header = [
        "Nama","Tipe Indekos","Jarak ke Kampus","Luas Kamar",
        "AC","WiFi","Kamar Mandi","Parkir","Dapur","Listrik","Kulkas","Harga"
    ]

    with open("data_kos_unair_c.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(results)

    print("\n[SELESAI] Data berhasil disimpan ke data_kos_unair_c.csv")


if __name__ == "__main__":
    main()