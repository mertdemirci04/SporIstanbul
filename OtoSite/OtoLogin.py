import time
from selenium.webdriver.support import expected_conditions as EC

from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def getSeansData(username, password):
    option = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
    driver.get("https://online.spor.istanbul/uyegiris")

    usernamePlace = driver.find_element(By.ID, "txtTCPasaport")
    passwordPlace = driver.find_element(By.ID, "txtSifre")
    loginPlace = driver.find_element(By.ID, "btnGirisYap")

    usernamePlace.send_keys(username)  # Android'den gelen kullanıcı adı
    passwordPlace.send_keys(password)  # Android'den gelen şifre
    loginPlace.click()

    try:
        checkBox = driver.find_element(By.ID,"checkBox")
        checkBox.click()
        popupPlace = driver.find_element(By.ID, "closeModal")
        popupPlace.click()
    except:
        print("Popup bulunamadı, devam ediliyor...")

    gridPlace = driver.find_element(By.ID, "liUye")
    gridPlace.click()

    seanslarimPlace = driver.find_element(By.ID, "liseanslarim")
    seanslarimPlace.click()

    try:
        popupPlace2 = driver.find_element(By.ID, "closeModal")
        popupPlace2.click()
    except:
        print("İkinci popup bulunamadı, devam ediliyor...")


    seansSec = driver.find_element(By.ID,"pageContent_rptListe_lbtnSeansSecim_0")
    seansSec.click()

    seans_listesi = []
    gun_panelleri = driver.find_elements(By.CLASS_NAME, "panel-info")

    for gun_panel in gun_panelleri:
        try:
            gun_baslik = gun_panel.find_element(By.CLASS_NAME, "panel-title").get_attribute("innerText").strip()
            seanslar = gun_panel.find_elements(By.CLASS_NAME, "well")

            for seans in seanslar:
                try:
                    saat = seans.find_element(By.XPATH, ".//span[contains(@id, 'lblSeansSaat')]").get_attribute("innerText").strip()
                    kontenjan = seans.find_element(By.XPATH, ".//span[@title='Kalan Kontenjan']").get_attribute("innerText").strip()
                    seans_listesi.append({"gun": gun_baslik, "saat": saat, "kontenjan": kontenjan})

                except Exception as e:
                    print("Seans çekme hatası:", e)

        except Exception as e:
            print("Gün bilgisi çekme hatası:", e)

    return seans_listesi

@app.route('/get_seanslar', methods=['POST'])
def get_seans():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Kullanıcı adı ve şifre gerekli"}), 400

    seans_listesi = getSeansData(username, password)
    return jsonify(seans_listesi)


driver = None

@app.route('/seans_al', methods=['POST'])
def seans_al():
    global driver  # Driver'ı global olarak tanımla
    data = request.json
    username = data.get("username")
    password = data.get("password")
    gun = data.get("gun")
    saat = data.get("saat")

    if not username or not password or not gun or not saat:
        return jsonify({"error": "Kullanıcı adı, şifre, gün ve saat gerekli"}), 400

    # Gün bilgisini temizle
    gun = gun.split()[0].strip()

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://online.spor.istanbul/uyegiris")

    usernamePlace = driver.find_element(By.ID, "txtTCPasaport")
    passwordPlace = driver.find_element(By.ID, "txtSifre")
    loginPlace = driver.find_element(By.ID, "btnGirisYap")

    usernamePlace.send_keys(username)
    passwordPlace.send_keys(password)
    loginPlace.click()

    try:
        popupPlace = driver.find_element(By.ID, "closeModal")
        popupPlace.click()
    except:
        print("Popup bulunamadı, devam ediliyor...")

    gridPlace = driver.find_element(By.ID, "liUye")
    gridPlace.click()

    seanslarimPlace = driver.find_element(By.ID, "liseanslarim")
    seanslarimPlace.click()

    try:
        popupPlace2 = driver.find_element(By.ID, "closeModal")
        popupPlace2.click()
    except:
        print("İkinci popup bulunamadı, devam ediliyor...")

    seansSec = driver.find_element(By.ID, "pageContent_rptListe_lbtnSeansSecim_0")
    seansSec.click()

    try:
        popupPlace2 = driver.find_element(By.ID, "closeModal")
        popupPlace2.click()
    except:
        print("İkinci popup bulunamadı, devam ediliyor...")

    gun_to_index = {
        "Pazartesi": 0,
        "Salı": 1,
        "Çarşamba": 2,
        "Perşembe": 3,
        "Cuma": 4,
        "Cumartesi": 5,
        "Pazar": 6
    }

    gun_index = gun_to_index.get(gun, None)
    if gun_index is None:
        return jsonify({"error": "Geçersiz gün bilgisi"}), 400

    try:
        gun_panelleri = driver.find_elements(By.CLASS_NAME, "panel-info")
        checkbox_index = None

        for gun_panel in gun_panelleri:
            gun_baslik_raw = gun_panel.find_element(By.CLASS_NAME, "panel-title").get_attribute("innerText").strip()
            gun_sadece_isim = gun_baslik_raw.split()[0].strip()

            if gun_sadece_isim == gun:
                seanslar = gun_panel.find_elements(By.CLASS_NAME, "well")

                for index, seans in enumerate(seanslar):
                    seans_saat = seans.find_element(By.XPATH, ".//span[contains(@id, 'lblSeansSaat')]").get_attribute("innerText").strip()

                    if saat.strip() == seans_saat:
                        checkbox_index = index
                        break

                break

        if checkbox_index is None:
            return jsonify({"error": "Seans saati bulunamadı"}), 400

        checkbox_id = f"pageContent_rptList_ChildRepeater_{gun_index}_cboxSeans_{checkbox_index}"
        checkbox = driver.find_element(By.ID, checkbox_id)
        checkbox.click()

    except Exception as e:
        return jsonify({"error": "Checkbox bulunamadı"}), 500

    try:
        onay_checkbox = driver.find_element(By.ID, "pageContent_cboxOnay")
        onay_checkbox.click()

        onay_btn = driver.find_element(By.ID, "lbtnKaydet")
        onay_btn.click()

    except Exception as e:
        return jsonify({"error": "Onay butonu bulunamadı"}), 500

    return jsonify({"status": f"{gun} günü {saat} saati için seans alındı. Şimdi SMS doğrulama bekleniyor."})

@app.route('/sms_dogrula', methods=['POST'])
def sms_dogrula():
    data = request.json
    sms_kodu = data.get("sms_kodu")

    if not sms_kodu:
        return jsonify({"error": "SMS kodu gerekli"}), 400

    try:
        # 🔹 Doğrulama kodu giriş alanını bul ve kodu yaz
        kod_yeri = driver.find_element(By.ID, "pageContent_txtDogrulamaKodu")
        kod_yeri.send_keys(sms_kodu)

        # 🔹 SMS Onayla butonuna bas
        onay_butonu = driver.find_element(By.ID, "btnCepTelDogrulamaGonder")
        onay_butonu.click()
        print("✅ SMS doğrulama kodu başarıyla girildi ve onaylandı!")

        return jsonify({"status": "SMS kodu başarıyla onaylandı!"})

    except Exception as e:
        print("❌ SMS doğrulama işlemi başarısız oldu:", e)
        return jsonify({"error": "SMS doğrulama işlemi başarısız oldu"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)