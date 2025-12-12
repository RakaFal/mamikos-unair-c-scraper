# 🏠 mamikos-unair-c-scraper

A Selenium-based web scraper for collecting detailed boarding house (indekos) information near **Universitas Airlangga Campus C** from the Mamikos platform. The scraper extracts room details, facilities, pricing, and distance to campus, then saves the results into a structured **CSV file** for analysis and research.

---

## ✨ Features
- Scrapes indekos listings around **UNAIR Campus C (Mulyorejo, Surabaya)**.
- Handles dynamic content using **Selenium WebDriver**.
- Extracts detailed attributes including:
  - Room size  
  - AC, WiFi, refrigerator availability  
  - Bathroom type  
  - Parking availability  
  - Electricity inclusion  
  - Monthly price  
- Calculates distance to UNAIR C (if coordinates available).
- Outputs clean, structured data into **CSV**.

---

## 🧰 Tech Stack
- **Python 3**
- **Selenium WebDriver**
- **ChromeDriver / GeckoDriver**
- **Pandas**

---

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/mamikos-unair-c-scraper.git
cd mamikos-unair-c-scraper
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download WebDriver

Choose based on your browser:

* Chrome → `chromedriver`
* Firefox → `geckodriver`

Ensure the driver version matches your browser.

---

## ▶️ Usage

Run the scraper:

```bash
python scraper.py
```

The output will be saved as:

```
data_kos_unair_c.csv
```

---

## 🗂️ CSV Output Structure

| Var | Name                 | Description                  | Coding                            |
| --- | -------------------- | ---------------------------- | --------------------------------- |
| X1  | Tipe Indekos         | Boarding house type          | 0 = Male, 1 = Female, 2 = Mixed   |
| X2  | Jarak ke Kampus (km) | Distance to UNAIR C          | Numeric                           |
| X3  | Luas Kamar (m²)      | Room area                    | Numeric                           |
| X4  | AC                   | Air conditioner availability | 0 = No, 1 = Yes                   |
| X5  | WiFi                 | WiFi availability            | 0 = No, 1 = Yes                   |
| X6  | Kamar Mandi          | Bathroom type                | 0 = Inside, 1 = Outside, 2 = Both |
| X7  | Parkir               | Parking facility             | 0 = Motorbike, 1 = Car, 2 = Both  |
| X8  | Dapur Bersama        | Shared kitchen availability  | 0 = No, 1 = Yes                   |
| X9  | Listrik              | Electricity inclusion        | 0 = Not included, 1 = Included    |
| X10 | Kulkas               | Refrigerator availability    | 0 = No, 1 = Yes                   |

---

## 📁 Project Structure

```bash
mamikos-unair-c-scraper/
│
├── scraper.py            # Main Selenium scraper
├── data_kos_unair_c.csv  # Scraping output (generated)
├── requirements.txt       # Dependencies
└── README.md              # Documentation
```

---

## ⚠️ Disclaimer

This project is intended for **educational and research purposes only**.
Please respect the terms of service of the Mamikos platform when scraping.

---

## 📜 License

This project is released under the **MIT License**.

---

## 🤝 Contribution

Pull requests and improvements are welcome!
Feel free to open issues for bugs or feature suggestions.
