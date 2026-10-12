from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sqlite3
import subprocess


def scrape(text):
    info = []
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.page_load_strategy = 'eager'
    driver = webdriver.Chrome(options=chrome_options)

    if " " in text:
        text = text.replace(" ", "+")

    driver.get(f"https://www.amazon.com/s?k={text}")

    firstResult = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "s-image"))
        )
    firstResult.click()

    name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        ).text

    bookDesc = driver.find_element(By.ID, "bookDescription_feature_div").text.split("\n")[0]

    detailList = driver.find_element(By.ID, "detailBullets_feature_div").text.split("\n")

    for item in detailList:
        if "Publisher" in item or "Publication date" in item or "Print length" in item or "ISBN-10" in item or "ISBN-13" in item or item[0] == "#":
            info.append(item)
    return name, bookDesc, info   
def sqlTable(name, bookDesc, info):
    con = sqlite3.connect(r"C:\Users\blake\Desktop\Python Code\Ellie Code!\test.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Library(
            Name TEXT NOT NULL,
            Description TEXT,
            Publisher TEXT,
            "Publication Date" TEXT,
            "Print Length" TEXT,
            "ISBN-10" TEXT NOT NULL,
            "ISBN-13" TEXT,
            "Pulled Genres" TEXT,
            PRIMARY KEY (Name, "ISBN-10")
        );
        """)

    cur.execute(f"""
    INSERT INTO Library VALUES(?,?,?,?,?,?,?,?);
    """, (name, bookDesc, info[0][11:], info[1][18:], info[2][14:], info[3][9:], info[4][9:], ", ".join(info[5:])))

    cur.execute("SELECT * FROM Library;")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    cur.close()
    return name, bookDesc, info
def manual():
        subprocess.Popen(r'start cmd /k sqlite3 "C:\Users\blake\Desktop\Python Code\Ellie Code!\test.db"', shell=True)
    
# start = time.time()
# item = "0578036428"
# name, bookDesc, info = scrape(item)
# sqlTable(name, bookDesc, info)
# print(f"This took {time.time()-start:.2f} seconds.")