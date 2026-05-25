# filter_turkey.py

import requests
import re
import os

# Kaynak M3U URL'si
SOURCE_URL = "https://raw.githubusercontent.com/kadirsener1/VAVOO/refs/heads/main/vavoo_all.m3u"

# Proxy prefix
PROXY_PREFIX = "https://vavooproxy.magnitude.workers.dev/resolve?url="

# Çıktı dosyası
OUTPUT_FILE = "turkey.m3u"


def download_m3u(url):
    """M3U dosyasını indir"""
    print(f"📥 M3U dosyası indiriliyor: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    print(f"✅ İndirme tamamlandı ({len(response.text)} karakter)")
    return response.text


def parse_and_filter_turkey(m3u_content):
    """M3U içeriğini parse et ve Turkey kategorili kanalları filtrele"""
    lines = m3u_content.strip().splitlines()
    turkey_entries = []
    
    i = 0
    total_channels = 0
    turkey_count = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # EXTINF satırını bul
        if line.startswith("#EXTINF"):
            total_channels += 1
            extinf_line = line
            
            # Bir sonraki satır URL olmalı
            if i + 1 < len(lines):
                url_line = lines[i + 1].strip()
                
                # Turkey kontrolü (group-title, tvg-country, kanal adı vb.)
                is_turkey = False
                
                # group-title="Turkey" veya group-title="Türkiye" kontrolü
                if re.search(r'group-title\s*=\s*"[^"]*(?:Turkey|Türkiye|TR|TURKEY|TÜRKİYE)[^"]*"', extinf_line, re.IGNORECASE):
                    is_turkey = True
                
                # tvg-country="TR" kontrolü
                if re.search(r'tvg-country\s*=\s*"[^"]*(?:TR|TUR)[^"]*"', extinf_line, re.IGNORECASE):
                    is_turkey = True
                
                # Kategori/grup adında Turkey geçiyorsa
                if re.search(r'(?:Turkey|Türkiye|TURKEY|TÜRKİYE)', extinf_line, re.IGNORECASE):
                    is_turkey = True
                
                if is_turkey:
                    turkey_count += 1
                    # URL'nin başına proxy prefix ekle
                    if url_line and not url_line.startswith("#"):
                        proxied_url = f"{PROXY_PREFIX}{url_line}"
                        turkey_entries.append(extinf_line)
                        turkey_entries.append(proxied_url)
                
                i += 2
                continue
        
        i += 1
    
    print(f"📊 Toplam kanal: {total_channels}")
    print(f"🇹🇷 Turkey kanalları: {turkey_count}")
    
    return turkey_entries


def create_m3u_file(entries, output_file):
    """Yeni M3U dosyasını oluştur"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for entry in entries:
            f.write(entry + "\n")
    
    print(f"💾 Dosya oluşturuldu: {output_file}")
    print(f"📄 Toplam satır: {len(entries) + 1}")


def main():
    try:
        # 1. M3U dosyasını indir
        m3u_content = download_m3u(SOURCE_URL)
        
        # 2. Turkey kanallarını filtrele ve proxy ekle
        turkey_entries = parse_and_filter_turkey(m3u_content)
        
        if not turkey_entries:
            print("⚠️ Turkey kategorisinde kanal bulunamadı!")
            # Boş dosya oluştur (Action'ın hata vermemesi için)
            create_m3u_file([], OUTPUT_FILE)
            return
        
        # 3. Yeni M3U dosyasını oluştur
        create_m3u_file(turkey_entries, OUTPUT_FILE)
        
        print("\n✅ İşlem başarıyla tamamlandı!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ İndirme hatası: {e}")
        raise
    except Exception as e:
        print(f"❌ Hata: {e}")
        raise


if __name__ == "__main__":
    main()
