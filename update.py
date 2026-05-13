import requests
import re
import shutil
from pathlib import Path
from datetime import datetime

SOURCE_URL = "https://raw.githubusercontent.com/kadirsener1/VAVOO/refs/heads/main/turkey.m3u"

# Kendi sabit listen
LOCAL_M3U = "ozel_listem.m3u"

# Yedek alınsın mı?
CREATE_BACKUP = True

# Sol taraf: kendi m3u dosyandaki kanal adı
# Sağ taraf: kaynak m3u içindeki aranacak kanal adı
CHANNEL_MAP = {
    "24 TV ": "24",
    "TRT 1": "TRT 1",
    "KANAL D": "KANAL D",
    "SHOW TV": "SHOW TV",
    "STAR TV": "STAR TV",
    "ATV": "ATV",
    "TV8": "TV8",
    "NOW TV": "NOW TV",
    "BEIN SPORTS 1": "BEIN SPORTS 1",
}
def normalize(text):
    return re.sub(r"\s+", " ", text.casefold().strip())


def get_attr(extinf_line, attr):
    match = re.search(rf'{attr}="([^"]*)"', extinf_line)
    return match.group(1) if match else ""


def get_display_name(extinf_line):
    if "," in extinf_line:
        return extinf_line.rsplit(",", 1)[1].strip()
    return ""


def is_media_url_line(line):
    line = line.strip()
    if not line:
        return False
    if line.startswith("#"):
        return False
    return True


def parse_m3u_entries(lines):
    entries = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF"):
            extinf_index = i
            extinf_line = lines[i].strip()
            url_index = None

            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()

                if next_line.startswith("#EXTINF"):
                    break

                if is_media_url_line(next_line):
                    url_index = j
                    break

                j += 1

            entries.append({
                "extinf_index": extinf_index,
                "url_index": url_index,
                "extinf": extinf_line,
                "display_name": get_display_name(extinf_line),
                "tvg_name": get_attr(extinf_line, "tvg-name"),
            })

        i += 1

    return entries


def matches_channel(entry, channel_name, exact=False):
    wanted = normalize(channel_name)

    candidates = [
        entry.get("display_name", ""),
        entry.get("tvg_name", ""),
    ]

    if exact:
        return any(normalize(c) == wanted for c in candidates if c)

    # Önce isim alanlarında ara
    if any(wanted in normalize(c) for c in candidates if c):
        return True

    # Son çare olarak EXTINF satırının tamamında ara
    return wanted in normalize(entry.get("extinf", ""))


def find_source_url(source_entries, source_lines, source_channel_name):
    # Önce birebir isim eşleşmesi dene
    for entry in source_entries:
        if entry["url_index"] is None:
            continue

        if matches_channel(entry, source_channel_name, exact=True):
            return source_lines[entry["url_index"]].strip()

    # Birebir bulunamazsa kısmi eşleşme dene
    for entry in source_entries:
        if entry["url_index"] is None:
            continue

        if matches_channel(entry, source_channel_name, exact=False):
            return source_lines[entry["url_index"]].strip()

    return None


def update_only_links():
    local_path = Path(LOCAL_M3U)

    if not local_path.exists():
        print(f"Hata: {LOCAL_M3U} bulunamadı.")
        return

    # Kaynak listeyi indir
    print("Kaynak liste indiriliyor...")
    response = requests.get(SOURCE_URL, timeout=20)

    if response.status_code != 200:
        print("Hata: Kaynak m3u indirilemedi.")
        return

    source_lines = response.text.splitlines()

    # Kendi listeyi oku
    local_lines = local_path.read_text(encoding="utf-8").splitlines()

    source_entries = parse_m3u_entries(source_lines)
    local_entries = parse_m3u_entries(local_lines)

    updated_count = 0
    not_found_in_source = []
    not_found_in_local = []

    for local_channel_name, source_channel_name in CHANNEL_MAP.items():
        new_url = find_source_url(
            source_entries,
            source_lines,
            source_channel_name
        )

        if not new_url:
            not_found_in_source.append(source_channel_name)
            continue

        local_entry = None

        for entry in local_entries:
            if entry["url_index"] is None:
                continue

            if matches_channel(entry, local_channel_name, exact=False):
                local_entry = entry
                break

        if not local_entry:
            not_found_in_local.append(local_channel_name)
            continue

        old_url = local_lines[local_entry["url_index"]].strip()

        if old_url != new_url:
            local_lines[local_entry["url_index"]] = new_url
            updated_count += 1
            print(f"Güncellendi: {local_channel_name}")
        else:
            print(f"Zaten güncel: {local_channel_name}")

    # Yedek al
    if CREATE_BACKUP:
        backup_name = f"{LOCAL_M3U}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(LOCAL_M3U, backup_name)
        print(f"Yedek alındı: {backup_name}")

    # Aynı dosyaya geri yaz
    local_path.write_text("\n".join(local_lines) + "\n", encoding="utf-8")

    print("")
    print(f"İşlem tamamlandı. Güncellenen kanal sayısı: {updated_count}")

    if not_found_in_source:
        print("")
        print("Kaynak listede bulunamayanlar:")
        for ch in not_found_in_source:
            print(f"- {ch}")

    if not_found_in_local:
        print("")
        print("Kendi listende bulunamayanlar:")
        for ch in not_found_in_local:
            print(f"- {ch}")


if __name__ == "__main__":
    update_only_links()
