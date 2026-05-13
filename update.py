import requests

# 1. AYARLAR
SOURCE_URL = "https://raw.githubusercontent.com/kadirsener1/VAVOO/refs/heads/main/turkey.m3u"
OUTPUT_FILE = "ozel_listem.m3u"

# Çekmek istediğin kanalların listesi (M3U içindeki isimleriyle tam veya kısmi eşleşebilir)
MY_CHANNELS = [
    "KANAL D",
    "STAR TV",
    "ATV",
    "TRT 1",
    "TV8",
    "FOX",
    "BEIN SPORTS 1"
]

def update_m3u():
    try:
        print(f"Kaynak listeden veri çekiliyor: {SOURCE_URL}")
        response = requests.get(SOURCE_URL)
        if response.status_code != 200:
            print("Hata: Kaynak dosyaya ulaşılamadı!")
            return

        lines = response.text.splitlines()
        found_content = []
        
        # Seçilen her bir kanal için kaynak dosyayı tara
        for target in MY_CHANNELS:
            is_target = False
            for i in range(len(lines)):
                # Kanal ismini içeren satırı bul (Küçük/Büyük harf duyarsız)
                if lines[i].startswith("#EXTINF") and target.lower() in lines[i].lower():
                    # EXTINF satırını ekle
                    found_content.append(lines[i])
                    # Bir sonraki satır linktir, onu da ekle
                    if i + 1 < len(lines):
                        found_content.append(lines[i+1])
                    print(f"Bulundu: {target}")
                    break # Kanalı bulduk, bu hedef için aramayı bitir

        # 2. DOSYAYA YAZMA
        if found_content:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                for item in found_content:
                    f.write(item + "\n")
            print(f"\nİşlem Tamam: {len(found_content)//2} kanal '{OUTPUT_FILE}' dosyasına kaydedildi.")
        else:
            print("\nUyarı: Listedeki kanalların hiçbiri bulunamadı.")

    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    update_m3u()
