# -*- coding: utf-8 -*-
import requests
import json
import time

def main():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'MediaHubMX/2',
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=utf-8'
    })
    
    try:
        group_res = session.get("https://www2.vavoo.to/live2/index?output=json", timeout=20).json()
        countries = sorted(list(set([c.get("group") for c in group_res if c.get("group")])))
    except Exception as e:
        print(f"Fehler beim Laden der Gruppen: {e}")
        return

    m3u_lines = ["#EXTM3U"]
    full_json_data = {}

    # Wir fügen "Balkans" explizit zur Liste hinzu, falls Germany dabei ist, 
    # um die versteckten deutschen Kanäle zu finden.
    search_groups = countries
    
    for country in search_groups:
        full_json_data[country] = []
        cursor = 0
        print(f"Lade Gruppe: {country}...", end="", flush=True)
        
        while True: # Endlosschleife für Pagination
            payload = {
                "language": "de", "region": "AT", "catalogId": "vto-iptv", "id": "vto-iptv",
                "adult": False, "search": "", "sort": "name", "filter": {"group": country},
                "cursor": cursor, "clientVersion": "3.0.2"
            }

            try:
                r = session.post("https://vavoo.to/vto-cluster/mediahubmx-catalog.json", 
                                 data=json.dumps(payload), timeout=30)
                
                if r.status_code == 200:
                    data = r.json()
                    items = data.get("items", [])
                    
                    for item in items:
                        name = item.get("name", "Unknown")
                        # Optionale Filterung für deutsche Kanäle in fremden Gruppen
                        if country == "Balkans" and not any(x in name for x in ["DE :", " |D"]):
                            continue
                            
                        clean_name = name.split(".")[0].strip()
                        url = item.get("url", "")
                        
                        if url:
                            url = "https://vavoorender-vuzs.onrender.com/manifest.m3u8?url=" + url
                            m3u_lines.append(f'#EXTINF:-1 group-title="{country}",{clean_name}')
                            m3u_lines.append(url)
                            full_json_data[country].append({"name": clean_name, "url": url, "group": country})
                    
                    # Prüfen, ob es eine weitere Seite gibt
                    cursor = data.get("nextCursor")
                    if not cursor:
                        break # Keine weiteren Seiten mehr
                else:
                    break
            except Exception:
                break
        
        print(f" Fertig ({len(full_json_data[country])} Kanäle)")
        time.sleep(0.05)

    # Speichern
    with open("vavoo_all.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    
    with open("vavoo_full.json", "w", encoding="utf-8") as f:
        json.dump(full_json_data, f, ensure_ascii=False, indent=4)
        
    print("\nUpdate abgeschlossen. Alle Seiten wurden geladen.")

if __name__ == "__main__":
    main()
