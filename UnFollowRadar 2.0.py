import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import tkinter as tk
from tkinter import messagebox, scrolledtext


class InstagramBotGUI:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.following = []
        self.followers = []
        self.not_following_back = []

        self.root = tk.Tk()
        self.root.title("MEGA-UnFollowRadar 2.0")
        self.root.geometry("650x750")

        self.create_widgets()
        self.root.mainloop()

    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Label(frame, text="Kullanıcı Adı:").grid(row=0, column=0, sticky="e")
        self.entry_username = tk.Entry(frame, width=30)
        self.entry_username.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Şifre:").grid(row=1, column=0, sticky="e")
        self.entry_password = tk.Entry(frame, show="*", width=30)
        self.entry_password.grid(row=1, column=1, padx=5)

        self.var_proxy = tk.IntVar()
        self.check_proxy = tk.Checkbutton(frame, text="Proxy Kullan", variable=self.var_proxy, command=self.toggle_proxy_entry)
        self.check_proxy.grid(row=2, column=0, columnspan=2)

        tk.Label(frame, text="Proxy (ip:port):").grid(row=3, column=0, sticky="e")
        self.entry_proxy = tk.Entry(frame, width=30, state="disabled")
        self.entry_proxy.grid(row=3, column=1, padx=5)

        self.btn_login = tk.Button(self.root, text="Giriş Yap ve Verileri Çek", command=self.threaded_login)
        self.btn_login.pack(pady=10)

        # Takip edilenler collapsible panel
        self.following_panel = self.create_collapsible_panel(self.root, "Takip Edilenler (0)")
        self.list_following = tk.Listbox(self.following_panel['frame'], selectmode=tk.MULTIPLE, width=60, height=8)
        self.list_following.pack()

        btn_frame1 = tk.Frame(self.following_panel['frame'])
        btn_frame1.pack(pady=5)
        tk.Button(btn_frame1, text="Tümünü Seç", command=lambda: self.select_all(self.list_following)).pack(side="left", padx=5)
        tk.Button(btn_frame1, text="Seçili Olanları Kaldır", command=lambda: self.remove_selected(self.list_following)).pack(side="left", padx=5)
        tk.Button(btn_frame1, text="Tümünü Kaldır", command=lambda: self.remove_all(self.list_following)).pack(side="left", padx=5)

        # Takipçiler collapsible panel
        self.followers_panel = self.create_collapsible_panel(self.root, "Takipçiler (0)")
        self.list_followers = tk.Listbox(self.followers_panel['frame'], selectmode=tk.MULTIPLE, width=60, height=8)
        self.list_followers.pack()

        btn_frame2 = tk.Frame(self.followers_panel['frame'])
        btn_frame2.pack(pady=5)
        tk.Button(btn_frame2, text="Tümünü Seç", command=lambda: self.select_all(self.list_followers)).pack(side="left", padx=5)
        tk.Button(btn_frame2, text="Seçili Olanları Kaldır", command=lambda: self.remove_selected(self.list_followers)).pack(side="left", padx=5)
        tk.Button(btn_frame2, text="Tümünü Kaldır", command=lambda: self.remove_all(self.list_followers)).pack(side="left", padx=5)

        # Seni takip etmeyenler collapsible panel
        self.not_following_panel = self.create_collapsible_panel(self.root, "Seni Takip Etmeyenler (0)")
        self.list_not_following_back = tk.Listbox(self.not_following_panel['frame'], selectmode=tk.MULTIPLE, width=60, height=8)
        self.list_not_following_back.pack()

        btn_frame3 = tk.Frame(self.not_following_panel['frame'])
        btn_frame3.pack(pady=5)
        tk.Button(btn_frame3, text="Tümünü Seç", command=lambda: self.select_all(self.list_not_following_back)).pack(side="left", padx=5)
        tk.Button(btn_frame3, text="Seçili Olanları Takipten Çıkar", command=self.threaded_unfollow).pack(side="left", padx=5)
        tk.Button(btn_frame3, text="Tümünü Takipten Çıkar", command=self.unfollow_all_thread).pack(side="left", padx=5)

        # Log alanı
        self.log_text = scrolledtext.ScrolledText(self.root, width=80, height=10, state="disabled")
        self.log_text.pack(pady=10)

    def create_collapsible_panel(self, parent, title):
        panel = {}

        def toggle():
            if panel['frame'].winfo_viewable():
                panel['frame'].pack_forget()
                panel['button'].config(text=f"{title} [+]")
            else:
                panel['frame'].pack(pady=5)
                panel['button'].config(text=f"{title} [-]")

        panel['button'] = tk.Button(parent, text=title + " [+]", relief="raised", command=toggle)
        panel['button'].pack(fill="x", padx=10)
        panel['frame'] = tk.Frame(parent)
        return panel

    def update_panel_title(self, panel, title, count):
        panel['button'].config(text=f"{title} ({count}) [-]")

    def select_all(self, listbox):
        listbox.select_set(0, tk.END)

    def remove_selected(self, listbox):
        selected = listbox.curselection()
        for i in reversed(selected):
            listbox.delete(i)

    def remove_all(self, listbox):
        listbox.delete(0, tk.END)

    def threaded_login(self):
        threading.Thread(target=self.login_and_fetch).start()

    def login_and_fetch(self):
        self.btn_login.config(state="disabled")
        self.clear_lists()
        try:
            username = self.entry_username.get()
            password = self.entry_password.get()
            if not username or not password:
                messagebox.showerror("Hata", "Kullanıcı adı ve şifre giriniz.")
                self.btn_login.config(state="normal")
                return

            proxy = self.entry_proxy.get() if self.var_proxy.get() == 1 else None
            self.log("Tarayıcı başlatılıyor...")
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            if proxy:
                chrome_options.add_argument(f'--proxy-server={proxy}')

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)

            self.log("Giriş yapılıyor...")
            username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
            username_input.send_keys(username)
            password_input.send_keys(password)
            password_input.send_keys(Keys.ENTER)
            time.sleep(5)

            for _ in range(2):
                try:
                    btn = WebDriverWait(self.driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Şimdi Değil')]"))
                    )
                    btn.click()
                    time.sleep(2)
                except TimeoutException:
                    pass

            self.log("Profil sayfasına gidiliyor...")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '/{username}')]"))).click()
            time.sleep(3)

            self.log("Takip edilenler listesi açılıyor...")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following')]"))).click()
            time.sleep(3)

            scroll_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                "div.x6nl9eh.x1a5l9x9.x7vuprf.x1mg3h75.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6")))
            self.scroll_scrollbox(scroll_box)

            following_elements = self.driver.find_elements(By.CSS_SELECTOR, "span._ap3a._aaco._aacw._aacx._aad7._aade")
            self.following = sorted(list({el.text.strip() for el in following_elements if el.text.strip() != ""}))

            self.fill_listbox(self.list_following, self.following)
            self.update_panel_title(self.following_panel, "Takip Edilenler", len(self.following))

            self.log("Takipçiler listesi açılıyor...")
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button._abl-'))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers')]"))).click()
            time.sleep(3)

            scroll_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                "div.x6nl9eh.x1a5l9x9.x7vuprf.x1mg3h75.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6")))
            self.scroll_scrollbox(scroll_box)

            follower_elements = self.driver.find_elements(By.CSS_SELECTOR, "span._ap3a._aaco._aacw._aacx._aad7._aade")
            self.followers = sorted(list({el.text.strip() for el in follower_elements if el.text.strip() != ""}))

            self.fill_listbox(self.list_followers, self.followers)
            self.update_panel_title(self.followers_panel, "Takipçiler", len(self.followers))

            self.not_following_back = sorted([nick for nick in self.following if nick not in self.followers])
            self.fill_listbox(self.list_not_following_back, self.not_following_back)
            self.update_panel_title(self.not_following_panel, "Seni Takip Etmeyenler", len(self.not_following_back))

            self.log(f"Seni takip etmeyen kişi sayısı: {len(self.not_following_back)}")

        except Exception as e:
            messagebox.showerror("Hata", f"Hata oluştu: {str(e)}")
            self.log(f"Hata: {str(e)}")
        finally:
            self.btn_login.config(state="normal")

    def scroll_scrollbox(self, scroll_box):
        self.log("Scroll işlemi başlatılıyor...")
        scroll_pause = 2
        max_empty_scrolls = 7
        empty_scrolls = 0
        last_height = -1

        try:
            while empty_scrolls < max_empty_scrolls:
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)
                self.log(f"Scroll yapıldı, bekleniyor {scroll_pause} saniye...")
                time.sleep(scroll_pause)
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_box)
                self.log(f"Scroll yüksekliği: {new_height}, önceki: {last_height}")
                if new_height == last_height:
                    empty_scrolls += 1
                    self.log(f"Yükseklik değişmedi ({empty_scrolls}/{max_empty_scrolls}), scroll sonlandırılıyor...")
                else:
                    empty_scrolls = 0
                last_height = new_height
            self.log("Scroll işlemi tamamlandı.")
        except Exception as e:
            self.log(f"Scroll işlemi sırasında hata oluştu: {e}")

    def fill_listbox(self, listbox, data):
        listbox.delete(0, tk.END)
        for item in data:
            listbox.insert(tk.END, item)

    def clear_lists(self):
        self.list_following.delete(0, tk.END)
        self.list_followers.delete(0, tk.END)
        self.list_not_following_back.delete(0, tk.END)
        self.following = []
        self.followers = []
        self.not_following_back = []

    def select_all(self, listbox):
        listbox.select_set(0, tk.END)

    def remove_selected(self, listbox):
        selected = listbox.curselection()
        for i in reversed(selected):
            listbox.delete(i)

    def remove_all(self, listbox):
        listbox.delete(0, tk.END)

    def threaded_unfollow(self):
        threading.Thread(target=self.unfollow_selected).start()

    def unfollow_selected(self):
        selected_indices = self.list_not_following_back.curselection()
        if not selected_indices:
            messagebox.showinfo("Bilgi", "Lütfen takipten çıkarmak istediğiniz kullanıcıları seçin.")
            return
        answer = messagebox.askyesno("Onay", f"{len(selected_indices)} kişiyi takipten çıkarmak istediğinize emin misiniz?")
        if not answer:
            return

        self.btn_login.config(state="disabled")

        try:
            for index in selected_indices:
                nick = self.list_not_following_back.get(index)
                self.log(f"{nick} sayfası açılıyor...")
                self.driver.get(f"https://www.instagram.com/{nick}/")
                time.sleep(3)

                try:
                    unfollow_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button._acan._acap._acat._aj1-._ap30"))
                    )
                    unfollow_button.click()
                    time.sleep(2)
                    try:
                        confirm_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[text()='Takibi Bırak']"))
                        )
                        confirm_button.click()
                        self.log(f"{nick} takipten çıkarıldı (onaylı).")
                    except TimeoutException:
                        self.log(f"{nick} takipten çıkarıldı (onaysız).")
                except Exception as e:
                    self.log(f"{nick} için hata oluştu: {e}")
                time.sleep(3)
            messagebox.showinfo("Başarılı", "Seçilen kullanıcılar takipten çıkarıldı.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hata oluştu: {str(e)}")
        finally:
            self.btn_login.config(state="normal")

    def unfollow_all_thread(self):
        if not self.not_following_back:
            messagebox.showinfo("Bilgi", "Takipten çıkarılacak kullanıcı yok.")
            return
        answer = messagebox.askyesno("Onay", f"Tüm ({len(self.not_following_back)}) kullanıcıyı takipten çıkarmak istediğinize emin misiniz?")
        if not answer:
            return
        threading.Thread(target=self.unfollow_all).start()

    def unfollow_all(self):
        self.btn_login.config(state="disabled")
        try:
            for nick in self.not_following_back[:]:
                self.log(f"{nick} sayfası açılıyor...")
                self.driver.get(f"https://www.instagram.com/{nick}/")
                time.sleep(3)
                try:
                    unfollow_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button._acan._acap._acat._aj1-._ap30"))
                    )
                    unfollow_button.click()
                    time.sleep(2)
                    try:
                        confirm_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[text()='Takibi Bırak']"))
                        )
                        confirm_button.click()
                        self.log(f"{nick} takipten çıkarıldı (onaylı).")
                    except TimeoutException:
                        self.log(f"{nick} takipten çıkarıldı (onaysız).")
                except Exception as e:
                    self.log(f"{nick} için hata oluştu: {e}")
                time.sleep(3)
                # Listeden çıkar
                if nick in self.not_following_back:
                    self.not_following_back.remove(nick)
                # Listbox güncelle
                self.fill_listbox(self.list_not_following_back, self.not_following_back)
            messagebox.showinfo("Başarılı", "Tüm kullanıcılar takipten çıkarıldı.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hata oluştu: {str(e)}")
        finally:
            self.btn_login.config(state="normal")

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def toggle_proxy_entry(self):
        if self.var_proxy.get() == 1:
            self.entry_proxy.config(state="normal")
        else:
            self.entry_proxy.delete(0, tk.END)
            self.entry_proxy.config(state="disabled")


if __name__ == "__main__":
    InstagramBotGUI()
