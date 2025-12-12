import time
import csv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


LIST_URL = "https://mamikos.com/cari/universitas-airlangga-kampus-c-universitas-airlangga-kampus-c-jalan-dokter-ir-haji-soekarno-mulyorejo-kota-surabaya-jawa-timur-indonesia/all/bulanan/0-15000000?keyword=universitas%20airlangga&suggestion_type=search&rent=2&sort=price,-&price=10000-20000000&singgahsini=0"


# ===============================
# DRIVER
# ===============================

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


# ===============================
# SCROLL UNTIL ALL CARDS LOADED
# ===============================

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


# ===============================
# SCRAPE DETAIL PAGE
# ===============================

def scrape_detail_page(driver):
    WebDriverWait(driver, 15)
    data = {}

    # Scroll pelan agar semua komponen React muncul
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(0.8)

    # Tunggu h1 (nama kos)
    try:
        name = driver.find_element(
            By.CSS_SELECTOR, "p.detail-title__room-name"
        ).text.strip()
    except:
        name = ""
    data["Nama"] = name


    # Tipe indekos lebih robust
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.querySelector('span.detail-kost-overview__gender-box')?.innerText.trim().length > 0;")
        )

        tipe = driver.execute_script("""
            let el = document.querySelector('span.detail-kost-overview__gender-box');
            return el ? el.innerText.trim() : "";
        """)

        data['Tipe Indekos'] = tipe.replace("Kos ", "")
    except:
        data['Tipe Indekos'] = ""


    # ======================
    # HARGA (AMBIL DARI kostDetailPriceReal)
    # ======================
    try:
        # Tunggu elemen harga benar-benar ada
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script(
                "return document.querySelector('[data-testid=\"kostDetailPriceReal\"]') !== null;"
            )
        )

        harga_raw = driver.execute_script("""
            let el = document.querySelector('[data-testid="kostDetailPriceReal"]');
            return el ? el.innerText.trim() : "";
        """)

        # Bersihkan: Rp
        data["Harga"] = harga_raw.replace("Rp", "").strip()

    except:
        data["Harga"] = ""


    # Ambil seluruh page source untuk fasilitas
    fasilitas_text = driver.page_source.lower()

    data["AC"] = "Ada" if "ac" in fasilitas_text else "Tidak Ada"
    data["WiFi"] = "Ada" if "wifi" in fasilitas_text else "Tidak Ada"

    # ======================
    # KAMAR MANDI (FIX FINAL)
    # ======================
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("""
                return Array.from(
                    document.querySelectorAll('p.detail-kost-facility-item__label')
                ).some(el => el.innerText.includes('Mandi'));
            """)
        )

        kamar_mandi = driver.execute_script("""
            let labels = Array.from(
                document.querySelectorAll('p.detail-kost-facility-item__label')
            ).map(el => el.innerText.trim().toLowerCase());

            let has_dalam = labels.some(t => t.includes('mandi dalam'));
            let has_luar  = labels.some(t => t.includes('mandi luar'));

            if (has_dalam && has_luar) return 'Dalam & Luar';
            if (has_dalam) return 'Dalam';
            if (has_luar) return 'Luar';
            return '';
        """)

        data["Kamar Mandi"] = kamar_mandi

    except:
        data["Kamar Mandi"] = ""


    # ======================
    # PARKIR (Motor / Mobil / Motor & Mobil)
    # Sepeda dianggap MOTOR
    # ======================
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("""
                return Array.from(
                    document.querySelectorAll('p.detail-kost-facility-item__label')
                ).some(el => el.innerText.toLowerCase().includes('parkir'));
            """)
        )

        parkir = driver.execute_script("""
            let labels = Array.from(
                document.querySelectorAll('p.detail-kost-facility-item__label')
            ).map(el => el.innerText.trim().toLowerCase());

            // Sepeda dianggap motor
            let has_motor = labels.some(t =>
                t.includes('parkir motor') || t.includes('parkir sepeda')
            );

            let has_mobil = labels.some(t => t.includes('parkir mobil'));

            if (has_motor && has_mobil) return 'Motor & Mobil';
            if (has_motor) return 'Motor';
            if (has_mobil) return 'Mobil';
            return '';
        """)

        data["Parkir"] = parkir

    except:
        data["Parkir"] = ""


    data["Dapur"] = "Ada" if "dapur" in fasilitas_text else "Tidak Ada"
    data["Kulkas"] = "Ada" if "kulkas" in fasilitas_text else "Tidak Ada"
    data["Listrik"] = "Termasuk" if "listrik" in fasilitas_text else "Tidak Termasuk"

    # Cari label yang memerlukan scroll lebih jauh
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

    def find_label(label):
        try:
            elems = driver.find_elements(By.XPATH, f"//*[contains(text(),'{label}')]")
            if not elems:
                return ""
            sibling = elems[0].find_element(By.XPATH, "following-sibling::*[1]")
            return sibling.text.strip()
        except:
            return ""

    data["Jarak ke Kampus"] = find_label("Jarak ke Kampus")

    # ======================
    # LUAS KAMAR
    # ======================
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("""
                return Array.from(document.querySelectorAll(
                    'p.detail-kost-facility-item__label'
                )).some(el => el.innerText.includes('x'));
            """)
        )

        luas_kamar = driver.execute_script("""
            let items = document.querySelectorAll('p.detail-kost-facility-item__label');
            for (let el of items) {
                let text = el.innerText.trim();
                if (text.match(/\\d+\\s*x\\s*\\d+/i)) {
                    return text;
                }
            }
            return "";
        """)

        data["Luas Kamar"] = luas_kamar

    except:
        data["Luas Kamar"] = ""

    return data


# ===============================
# MAIN LOGIC
# ===============================

def main():
    driver = init_driver()
    driver.get(LIST_URL)
    time.sleep(5)

    print("[INFO] Loading all cards...")
    cards = scroll_until_cards_loaded(driver)
    total_cards = len(cards)

    print(f"[INFO] Total card ditemukan: {total_cards}")

    # Save window utama
    main_window = driver.current_window_handle

    results = []

    for i in range(total_cards):
        print(f"\n[INFO] Klik card {i+1}/{total_cards}")

        cards = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='kostRoomCard']")

        if i >= len(cards):
            print("[WARN] Card belum muncul, scrolling ulang...")
            cards = scroll_until_cards_loaded(driver, timeout=10)

        card = cards[i]

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
        time.sleep(1)

        # Klik card
        driver.execute_script("arguments[0].click();", card)
        time.sleep(2)

        # Pindah ke tab baru
        for window in driver.window_handles:
            if window != main_window:
                driver.switch_to.window(window)
                break

        # Scrape detail
        detail = scrape_detail_page(driver)
        results.append(detail)
        print(detail)

        # Tutup tab detail
        driver.close()

        # Kembali ke tab utama
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

    print("\n[SELESAI] Data tersimpan ke data_kos_unair_c.csv")


if __name__ == "__main__":
    main()