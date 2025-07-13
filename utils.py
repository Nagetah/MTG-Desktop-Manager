# utils.py
# Hilfsfunktionen für das Projekt
import os
import hashlib
import requests

def get_cached_image(image_uris_or_url, card_id=None, fallback_name=None, fallback_set=None):
    image_url = None
    if isinstance(image_uris_or_url, dict):
        for key in ["large", "normal", "small"]:
            if image_uris_or_url.get(key):
                image_url = image_uris_or_url[key]
                break
    elif isinstance(image_uris_or_url, str):
        image_url = image_uris_or_url
    if (not image_url or image_url == "null") and fallback_name and fallback_set:
        from urllib.parse import quote
        api_name = quote(fallback_name.split('//')[0].strip())
        api_set = quote(fallback_set)
        scryfall_url = f"https://api.scryfall.com/cards/named?exact={api_name}&set={api_set}"
        try:
            resp = requests.get(scryfall_url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                image_uris = data.get("image_uris")
                if image_uris:
                    for key in ["large", "normal", "small"]:
                        if image_uris.get(key):
                            image_url = image_uris[key]
                            break
                elif "card_faces" in data:
                    faces = data["card_faces"]
                    for face in faces:
                        image_uris = face.get("image_uris")
                        if image_uris:
                            for key in ["large", "normal", "small"]:
                                if image_uris.get(key):
                                    image_url = image_uris[key]
                                    break
                            if image_url:
                                break
        except Exception as e:
            print(f"Scryfall-API-Fehler: {e}")
            image_url = None
    if not image_url or image_url == "null":
        return None
    if not os.path.exists('images'):
        os.makedirs('images')
    filename = hashlib.md5(image_url.encode('utf-8')).hexdigest() + ".jpg"
    path = os.path.join('images', filename)
    if os.path.exists(path):
        return path
    try:
        img_data = requests.get(image_url, timeout=5).content
        with open(path, 'wb') as f:
            f.write(img_data)
        return path
    except Exception as e:
        print(f"Bild-Download-Fehler: {e}")
        return None

###############################################################
# --- MOVE TO utils.py ---
# Hilfsfunktion für Bild-Caching
def get_cached_image(image_uris_or_url, card_id=None, fallback_name=None, fallback_set=None):
    # image_uris_or_url kann ein dict (image_uris) oder ein String (direkte URL) sein
    image_url = None
    # 1. Wenn dict, bestes Format wählen
    if isinstance(image_uris_or_url, dict):
        for key in ["large", "normal", "small"]:
            if image_uris_or_url.get(key):
                image_url = image_uris_or_url[key]
                break
    elif isinstance(image_uris_or_url, str):
        image_url = image_uris_or_url

    # 2. Fallback: Scryfall-API
    if (not image_url or image_url == "null") and fallback_name and fallback_set:
        from urllib.parse import quote
        api_name = quote(fallback_name.split('//')[0].strip())
        api_set = quote(fallback_set)
        scryfall_url = f"https://api.scryfall.com/cards/named?exact={api_name}&set={api_set}"
        try:
            resp = requests.get(scryfall_url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                image_uris = data.get("image_uris")
                if image_uris:
                    for key in ["large", "normal", "small"]:
                        if image_uris.get(key):
                            image_url = image_uris[key]
                            break
                elif "card_faces" in data:
                    faces = data["card_faces"]
                    for face in faces:
                        image_uris = face.get("image_uris")
                        if image_uris:
                            for key in ["large", "normal", "small"]:
                                if image_uris.get(key):
                                    image_url = image_uris[key]
                                    break
                            if image_url:
                                break
        except Exception as e:
            print(f"Scryfall-API-Fehler: {e}")
            image_url = None
    if not image_url or image_url == "null":
        return None
    if not os.path.exists('images'):
        os.makedirs('images')
    # Cache nach Bild-URL, nicht nur card_id, damit verschiedene Qualitäten nicht überschrieben werden
    filename = hashlib.md5(image_url.encode('utf-8')).hexdigest() + ".jpg"
    path = os.path.join('images', filename)
    if os.path.exists(path):
        return path
    try:
        img_data = requests.get(image_url, timeout=5).content
        with open(path, 'wb') as f:
            f.write(img_data)
        return path
    except Exception as e:
        print(f"Bild-Download-Fehler: {e}")
        return None