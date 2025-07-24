from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

driver = webdriver.Chrome()
driver.get("https://www.instagram.com/accounts/login/")
driver.maximize_window()
time.sleep(3)

try:
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys("")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys("", Keys.ENTER)
    time.sleep(5)

    for _ in range(2):
        try:
            btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Şimdi Değil')]")))
            btn.click()
            time.sleep(2)
        except TimeoutException:
            pass

    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/efegelinoglu')]"))).click()
    time.sleep(3)

    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following')]"))).click()
    time.sleep(3)

    scroll_box = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.x6nl9eh.x1a5l9x9.x7vuprf.x1mg3h75.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6"))
    )
    print("Takip scroll alanı bulundu.")

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

    print("\nTakip edilen kişiler:")
    for nick in following:
        print(nick)
    print(f"\nToplam takip edilen kişi sayısı: {len(following)}\n")

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button._abl-'))
    ).click()

    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers')]"))).click()
    time.sleep(3)

    scroll_box = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.x6nl9eh.x1a5l9x9.x7vuprf.x1mg3h75.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6"))
    )
    print("Takipçi scroll alanı bulundu.")

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

    print("\nTakipçiler:")
    for nick in followers:
        print(nick)
    print(f"\nToplam takipçi sayısı: {len(followers)}\n")

    # Karşılaştırma
    not_following_back = [nick for nick in following if nick not in followers]

    print("Seni takip etmeyenler:")
    for nick in not_following_back:
        print(nick)
    print(f"\nSeni takip etmeyen toplam kişi sayısı: {len(not_following_back)}\n")
    
    
    secenek = input("Seni takip etmeyenleri kaldırmak ister misin? DİKKAT!!!! ÜNLÜLER DE TAKİPTEN ÇIKARILACAKTIR (E/H): ").strip().upper()

    if secenek == 'E':
        for nick in not_following_back:
            try:
                driver.get(f"https://www.instagram.com/{nick}/")
                time.sleep(3)

                # Takipten çıkarma butonunu bul
                unfollow_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button._acan._acap._acat._aj1-._ap30"))
                )
                unfollow_button.click()
                time.sleep(2)

                try:
                    # Gizli hesaplar için: onay butonu varsa tıkla
                    confirm_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "span.x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft"))
                    )
                    confirm_button.click()
                    print(f"{nick} takipten çıkarıldı (onaylı).")
                except TimeoutException:
                    # Açık profiller: ek onay gerekmez
                    print(f"{nick} takipten çıkarıldı (onaysız).")
                

            except Exception as e:
                print(f"{nick} için hata oluştu: {e}")
            except NoSuchElementException:
                print(f"{nick} kişisi bulunamadı veya zaten takipten çıkarılmış.")
            except TimeoutException:
                print(f"{nick} kişisi için işlem zaman aşımına uğradı.")
            time.sleep(3)
            

except Exception as e:
    print(f"Hata oluştu: {str(e)}")

time.sleep(10)
driver.quit()
