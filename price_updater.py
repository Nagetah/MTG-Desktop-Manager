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
        self.update_status.emit(self.sammlungsname, 'pending')
        cards = self.sammlung.get('cards', [])
        for idx, card in enumerate(cards):
            if self._abort:
                self.update_status.emit(self.sammlungsname, 'error')
                return
            try:
                # Scryfall-API: Preis für exakte Variante holen
                scryfall_id = card.get('id')
                if not scryfall_id:
                    continue
                url = f"https://api.scryfall.com/cards/{scryfall_id}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    # Preis je nach Variante
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
                else:
                    card['eur'] = ''
            except Exception:
                card['eur'] = ''
            self.update_progress.emit(self.sammlungsname, idx+1, len(cards))
            time.sleep(0.1)  # UI-Entlastung
        self.update_status.emit(self.sammlungsname, 'done')
        self.update_finished.emit(self.sammlungsname, cards)
