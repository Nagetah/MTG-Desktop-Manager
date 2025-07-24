# price_updater.py
# Hintergrund-Worker für Preisupdates von Sammlungen
from PyQt6.QtCore import QObject, QThread, pyqtSignal
import requests
import time

class PriceUpdaterWorker(QObject):
    update_status = pyqtSignal(str, str)  # (sammlungsname, status: 'pending'|'done'|'error')
    update_progress = pyqtSignal(str, int, int)  # (sammlungsname, aktuelle_karte, gesamt)
    update_finished = pyqtSignal(str, list)  # (sammlungsname, cards)

    def __init__(self, sammlung, sammlungsname):
        super().__init__()
        self.sammlungsname = sammlungsname
        self.sammlung = sammlung  # dict mit 'cards': [...]
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        import traceback
        self.update_status.emit(self.sammlungsname, 'pending')
        cards = self.sammlung.get('cards', [])
        for idx, card in enumerate(cards):
            if self._abort:
                print(f"[DEBUG] Preisupdate-Worker für '{self.sammlungsname}' abgebrochen bei Karte {idx+1}/{len(cards)}: {card.get('name')}")
                self.update_status.emit(self.sammlungsname, 'error')
                return
            try:
                scryfall_id = card.get('id')
                print(f"[DEBUG] Preisupdate-Worker: {self.sammlungsname} | {idx+1}/{len(cards)} | {card.get('name')} | id={scryfall_id}")
                if not scryfall_id:
                    print(f"[DEBUG] Preisupdate-Worker: Karte ohne Scryfall-ID übersprungen: {card.get('name')}")
                    continue
                url = f"https://api.scryfall.com/cards/{scryfall_id}"
                try:
                    resp = requests.get(url, timeout=5)
                except Exception as e:
                    print(f"[ERROR] Preisupdate-Worker: Request-Fehler bei {card.get('name')} ({scryfall_id}): {e}")
                    card['eur'] = ''
                    continue
                if resp.status_code == 200:
                    data = resp.json()
                    variant = card.get('variant', 'nonfoil')
                    price = None
                    if variant == 'foil':
                        price = data.get('prices', {}).get('eur_foil')
                    elif variant == 'etched':
                        price = data.get('prices', {}).get('eur_etched')
                    elif variant == 'gilded':
                        price = data.get('prices', {}).get('eur_gilded')
                    else:
                        price = data.get('prices', {}).get('eur')
                    card['eur'] = price if price not in (None, '', '0', 0) else ''
                    print(f"[DEBUG] Preisupdate-Worker: {card.get('name')} | Variante: {variant} | Preis: {card['eur']}")
                else:
                    print(f"[ERROR] Preisupdate-Worker: HTTP {resp.status_code} für {card.get('name')} ({scryfall_id})")
                    card['eur'] = ''
            except Exception as e:
                print(f"[ERROR] Preisupdate-Worker: Exception bei {card.get('name')} ({card.get('id')}): {e}\n{traceback.format_exc()}")
                card['eur'] = ''
            self.update_progress.emit(self.sammlungsname, idx+1, len(cards))
            time.sleep(0.05)  # UI-Entlastung
        self.update_status.emit(self.sammlungsname, 'done')
        self.update_finished.emit(self.sammlungsname, cards)
