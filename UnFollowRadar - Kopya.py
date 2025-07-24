from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import tkinter as tk
from tkinter import messagebox
import threading
import os

# GUI Arayüzünü Başlat
def start_gui():
    def start_bot():
        username = entry_username.get()
        password = entry_password.get()
        use_proxy = var_proxy.get()
        proxy_address = entry_proxy.get() if use_proxy else None
        if not username or not password:
            messagebox.showerror("Hata", "Kullanıcı adı ve şifre giriniz.")
            return
        threading.Thread(target=run_bot, args=(username, password, proxy_address)).start()

    root = tk.Tk()
    root.title("Instagram Takipçi Analiz Botu")
    root.geometry("400x300")

    tk.Label(root, text="Kullanıcı Adı:").pack()
    entry_username = tk.Entry(root)
    entry_username.pack()

    tk.Label(root, text="Şifre:").pack()
    entry_password = tk.Entry(root, show="*")
    entry_password.pack()

    var_proxy = tk.IntVar()
    tk.Checkbutton(root, text="Proxy kullan", variable=var_proxy).pack()

    tk.Label(root, text="Proxy (ip:port):").pack()
    entry_proxy = tk.Entry(root)
    entry_proxy.pack()

    tk.Button(root, text="Başlat", command=start_bot).pack(pady=10)
    root.mainloop()

# Bot Fonksiyonu
def run_bot(username, password, proxy=None):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)

        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
        wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password, Keys.ENTER)
        time.sleep(5)

        for _ in range(2):
            try:
                btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Şimdi Değil')]")))
                btn.click()
                time.sleep(2)
            except TimeoutException:
                pass

        wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '/{username}')]"))).click()
        time.sleep(3)

        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following')]"))).click()
        time.sleep(3)

        scroll_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.x6nl9eh.x1a5l9x9.x7vuprf.x1mg3h75.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6")))
        scroll_pause = 2
        max_empty_scrolls = 5
        empty_scrolls = 0
        last_height = 0

        while empty_scrolls < max_empty_scrolls:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)
            time.sleep(scroll_pause)
            new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_box)
            if new_height == last_height:
                empty_scrolls += 1
            else:
                empty_scrolls = 0
            last_height = new_height

        time.sleep(3)

        following_elements = driver.find_elements(By.CSS_SELECTOR, "span._ap3a._aaco._aacw._aacx._aad7._aade")
        following = list({el.text.strip() for el in following_elements if el.text.strip() != ""})

        with open("takip_edilenler.txt", "w", encoding="utf-8") as f:
            for nick in following:
                f.write(nick + "\n")

        print(f"Takip edilen kişi sayısı: {len(following)}")

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button._abl-'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers')]"))).click()
        time.sleep(3)

        scroll_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.x6nl9eh.x1a5l9x9.x7vuprf.x1mg3h75.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6")))
        empty_scrolls = 0
        last_height = 0

        while empty_scrolls < max_empty_scrolls:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)
            time.sleep(scroll_pause)
            new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_box)
            if new_height == last_height:
                empty_scrolls += 1
            else:
                empty_scrolls = 0
            last_height = new_height

        time.sleep(3)

        follower_elements = driver.find_elements(By.CSS_SELECTOR, "span._ap3a._aaco._aacw._aacx._aad7._aade")
        followers = list({el.text.strip() for el in follower_elements if el.text.strip() != ""})

        with open("takipciler.txt", "w", encoding="utf-8") as f:
            for nick in followers:
                f.write(nick + "\n")

        print(f"Takipçi sayısı: {len(followers)}")

        not_following_back = [nick for nick in following if nick not in followers]

        with open("takip_etmeyenler.txt", "w", encoding="utf-8") as f:
            for nick in not_following_back:
                f.write(nick + "\n")

        print(f"Seni takip etmeyen kişi sayısı: {len(not_following_back)}")

        secenek = input("Seni takip etmeyenleri kaldırmak ister misin? (E/H): ").strip().upper()
        if secenek == 'E':
            for nick in not_following_back:
                try:
                    driver.get(f"https://www.instagram.com/{nick}/")
                    time.sleep(3)

                    unfollow_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button._acan._acap._acat._aj1-._ap30"))
                    )
                    unfollow_button.click()
                    time.sleep(2)

                    try:
                        confirm_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Takibi Bırak')]"))
                        )
                        confirm_button.click()
                        print(f"{nick} takipten çıkarıldı (onaylı).")
                    except TimeoutException:
                        print(f"{nick} takipten çıkarıldı (onaysız).")
                except Exception as e:
                    print(f"{nick} için hata oluştu: {e}")
                time.sleep(3)
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
    finally:
        time.sleep(5)
        driver.quit()

start_gui()
