# dialogs.py
# Dialogklassen für das Projekt
import os
import requests
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from utils import get_cached_image

class CardSelectorDialog(QDialog):
    def __init__(self, search_results, on_select):
        super().__init__()
        self.setWindowTitle("Suchergebnisse")
        self.setMinimumSize(600, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.layout = QVBoxLayout()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet('''
            QScrollBar:vertical, QScrollBar:horizontal {
                background: transparent;
                width: 16px;
                height: 16px;
                margin: 0px;
                border: none;
            }
            QScrollBar::groove:vertical, QScrollBar::groove:horizontal {
                background: #444;
                border-radius: 8px;
                margin: 2px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #888;
                min-height: 36px;
                min-width: 36px;
                border-radius: 50%;
                margin: 4px;
                border: none;
                width: 8px;
                height: 8px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #aaa;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                height: 0px;
                width: 0px;
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        ''')
        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout()
        self.result_widget.setLayout(self.result_layout)
        self.scroll.setWidget(self.result_widget)
        self.layout.addWidget(self.scroll)
        self.setLayout(self.layout)
        self.on_select = on_select
        self.load_results(search_results)

    def load_results(self, results):
        from urllib.parse import quote
        buttons = []
        for card in results:
            hbox = QHBoxLayout()
            hbox.setSpacing(18)
            name = card.get("name", "Unbekannt")
            set_name = card.get("set_name", "Unbekanntes Set")
            image_url = card.get("image_uris", {}).get("small", "")
            if not image_url and "card_faces" in card:
                image_url = card["card_faces"][0].get("image_uris", {}).get("small", "")
            if not image_url:
                api_name = name.split('//')[0].strip()
                api_name = quote(api_name)
                api_set = quote(set_name)
                scryfall_url = f"https://api.scryfall.com/cards/named?exact={api_name}&set={api_set}"
                try:
                    resp = requests.get(scryfall_url, timeout=3)
                    if resp.status_code == 200:
                        data = resp.json()
                        image_url = data.get("image_uris", {}).get("small")
                        if not image_url and "card_faces" in data:
                            image_url = data["card_faces"][0].get("image_uris", {}).get("small")
                except:
                    image_url = None
            image_label = QLabel()
            image_label.setMinimumSize(80, 110)
            image_label.setMaximumSize(80, 110)
            img_path = get_cached_image(image_url, card.get('id')) if image_url else None
            if img_path and os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                pixmap = pixmap.scaled(80, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(pixmap)
            else:
                image_label.setText("Kein Bild")
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            name_label = QLabel(name)
            name_label.setStyleSheet("font-weight: bold; font-size: 19px;")
            name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            set_label = QLabel(set_name)
            set_label.setStyleSheet("font-size: 16px; color: #cccccc;")
            set_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addWidget(name_label)
            info_layout.addWidget(set_label)
            set_size = card.get("set_size")
            if not set_size:
                set_code = card.get("set") or card.get("set_code")
                if set_code:
                    try:
                        set_api_url = f"https://api.scryfall.com/sets/{set_code}"
                        resp = requests.get(set_api_url, timeout=3)
                        if resp.status_code == 200:
                            set_data = resp.json()
                            set_size = set_data.get("card_count", "?")
                    except Exception as e:
                        print(f"Fehler beim Laden von set_size: {e}")
                        set_size = "?"
            collector_number = card.get("collector_number", "?")
            fin_info = f"FIN {collector_number}/{set_size}"
            fin_label = QLabel(fin_info)
            fin_label.setStyleSheet("font-size: 14px; color: #cccccc;")
            info_layout.addWidget(fin_label)
            info_widget = QWidget()
            info_widget.setLayout(info_layout)
            button = QPushButton("Auswählen")
            button.setFixedWidth(170)
            button.clicked.connect(lambda _, c=card: self.select_card(c))
            buttons.append(button)
            hbox.addWidget(image_label)
            hbox.addWidget(info_widget, 1)
            hbox.addWidget(button)
            wrapper = QWidget()
            wrapper.setLayout(hbox)
            wrapper.setMinimumHeight(120)
            self.result_layout.addWidget(wrapper)
        if buttons:
            min_width = min(b.sizeHint().width() for b in buttons)
            for b in buttons:
                b.setMinimumWidth(min_width)
        self.result_layout.setSpacing(10)
        self.result_widget.setMinimumWidth(500)

    def select_card(self, card_data):
        self.on_select(card_data)
        self.accept()


        from urllib.parse import quote
        buttons = []
        for card in results:
            hbox = QHBoxLayout()
            hbox.setSpacing(18)
            name = card.get("name", "Unbekannt")
            set_name = card.get("set_name", "Unbekanntes Set")
            image_url = card.get("image_uris", {}).get("small", "")
            if not image_url and "card_faces" in card:
                image_url = card["card_faces"][0].get("image_uris", {}).get("small", "")
            if not image_url:
                api_name = name.split('//')[0].strip()
                api_name = quote(api_name)
                api_set = quote(set_name)
                scryfall_url = f"https://api.scryfall.com/cards/named?exact={api_name}&set={api_set}"
                try:
                    resp = requests.get(scryfall_url, timeout=3)
                    if resp.status_code == 200:
                        data = resp.json()
                        image_url = data.get("image_uris", {}).get("small")
                        if not image_url and "card_faces" in data:
                            image_url = data["card_faces"][0].get("image_uris", {}).get("small")
                except:
                    image_url = None
            image_label = QLabel()
            image_label.setMinimumSize(80, 110)
            image_label.setMaximumSize(80, 110)
            img_path = get_cached_image(image_url, card.get('id')) if image_url else None
            if img_path and os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                pixmap = pixmap.scaled(80, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(pixmap)
            else:
                image_label.setText("Kein Bild")
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Info-Block: Name fett, darunter Set
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            name_label = QLabel(name)
            name_label.setStyleSheet("font-weight: bold; font-size: 19px;")
            name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            set_label = QLabel(set_name)
            set_label.setStyleSheet("font-size: 16px; color: #cccccc;")
            set_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addWidget(name_label)
            info_layout.addWidget(set_label)

            set_size = card.get("set_size")
            if not set_size:
                set_code = card.get("set") or card.get("set_code")
                if set_code:
                    try:
                        set_api_url = f"https://api.scryfall.com/sets/{set_code}"
                        resp = requests.get(set_api_url, timeout=3)
                        if resp.status_code == 200:
                            set_data = resp.json()
                            set_size = set_data.get("card_count", "?")
                    except Exception as e:
                        print(f"Fehler beim Laden von set_size: {e}")
                        set_size = "?"

            collector_number = card.get("collector_number", "?")
            fin_info = f"FIN {collector_number}/{set_size}"
            fin_label = QLabel(fin_info)
            fin_label.setStyleSheet("font-size: 14px; color: #cccccc;")
            info_layout.addWidget(fin_label)

            info_widget = QWidget()
            info_widget.setLayout(info_layout)

            button = QPushButton("Auswählen")
            button.setFixedWidth(170)
            button.clicked.connect(lambda _, c=card: self.select_card(c))
            buttons.append(button)

            hbox.addWidget(image_label)
            hbox.addWidget(info_widget, 1)
            hbox.addWidget(button)
            wrapper = QWidget()
            wrapper.setLayout(hbox)
            wrapper.setMinimumHeight(120)
            self.result_layout.addWidget(wrapper)
        # Einheitliche Button-Breite auf die Breite des kleinsten Buttons setzen
        if buttons:
            min_width = min(b.sizeHint().width() for b in buttons)
            for b in buttons:
                b.setMinimumWidth(min_width)
        self.result_layout.setSpacing(10)
        self.result_widget.setMinimumWidth(500)

    def select_card(self, card_data):
        self.on_select(card_data)
        self.accept()


###############################################################
# --- MOVE TO dialogs.py ---
class VariantSelector(QDialog):
    def __init__(self, prints_url, callback):
        super().__init__()
        self.setWindowTitle("Alle Varianten")
        self.setMinimumSize(600, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.callback = callback
        self.layout = QVBoxLayout()
        # ScrollArea für Varianten, damit nichts abgeschnitten wird
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet('''
            QScrollBar:vertical, QScrollBar:horizontal {
                background: transparent;
                width: 16px;
                height: 16px;
                margin: 0px;
                border: none;
            }
            QScrollBar::groove:vertical, QScrollBar::groove:horizontal {
                background: #444;
                border-radius: 8px;
                margin: 2px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #888;
                min-height: 36px;
                min-width: 36px;
                border-radius: 50%;
                margin: 4px;
                border: none;
                width: 8px;
                height: 8px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #aaa;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                height: 0px;
                width: 0px;
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        ''')
        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout()
        self.result_widget.setLayout(self.result_layout)
        self.scroll.setWidget(self.result_widget)
        self.layout.addWidget(self.scroll)
        self.setLayout(self.layout)
        self.load_variants(prints_url)

    def load_variants(self, url):
        from urllib.parse import quote
        response = requests.get(url)
        if response.status_code != 200:
            return
        data = response.json()
        buttons = []
        for card in data.get('data', []):
            hbox = QHBoxLayout()
            hbox.setSpacing(18)
            image_url = card.get('image_uris', {}).get('small', '')
            if not image_url and 'card_faces' in card:
                image_url = card['card_faces'][0].get('image_uris', {}).get('small', '')
            if not image_url:
                api_name = quote(card.get('name', ''))
                api_set = quote(card.get('set_name', ''))
                scryfall_url = f"https://api.scryfall.com/cards/named?exact={api_name}&set={api_set}"
                try:
                    resp = requests.get(scryfall_url, timeout=3)
                    if resp.status_code == 200:
                        data2 = resp.json()
                        image_url = data2.get("image_uris", {}).get("small")
                        if not image_url and "card_faces" in data2:
                            image_url = data2["card_faces"][0].get("image_uris", {}).get("small")
                except:
                    image_url = None
            image_label = QLabel()
            image_label.setMinimumSize(80, 110)
            image_label.setMaximumSize(80, 110)
            img_path = get_cached_image(image_url, card.get('id')) if image_url else None
            if img_path and os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                pixmap = pixmap.scaled(80, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(pixmap)
            else:
                image_label.setText("Kein Bild")
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Info-Block: Set fett, Sprache normal
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            set_label = QLabel(card['set_name'])
            set_label.setStyleSheet("font-weight: bold; font-size: 18px;")
            set_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lang_label = QLabel(f"Sprache: {card['lang'].upper()}")
            lang_label.setStyleSheet("font-size: 15px; color: #cccccc;")
            lang_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addWidget(set_label)
            info_layout.addWidget(lang_label)

            set_code = card.get("set") or card.get("set_code")
            if not set_code:
                set_code = "?"

            set_size = card.get("set_size")
            if not set_size and set_code != "?":
                try:
                    set_api_url = f"https://api.scryfall.com/sets/{set_code}"
                    resp = requests.get(set_api_url, timeout=3)
                    if resp.status_code == 200:
                        set_data = resp.json()
                        set_size = set_data.get("card_count", "?")
                except Exception as e:
                    print(f"Fehler beim Laden von set_size: {e}")
                    set_size = "?"

            collector_number = card.get("collector_number", "?")
           # --- Erweiterung: Zeige Foil-Typ, Preise, Legalities ---
            # Kompakter Info-Block für Scryfall-Felder
            info_block = QVBoxLayout()
            info_block.setSpacing(2)
            info_widget_block = QWidget()
            info_widget_block.setLayout(info_block)
            info_widget_block.setMaximumWidth(320)

            finishes = card.get('finishes', [])
            finishes_str = ', '.join(finishes) if finishes else 'Unbekannt'
            finishes_label = QLabel(f"Foil-Typ: {finishes_str}")
            finishes_label.setStyleSheet("font-size: 14px; color: #cccccc;")
            finishes_label.setWordWrap(True)
            info_block.addWidget(finishes_label)

            prices = card.get('prices', {})
            price_strs = []
            for k, v in prices.items():
                if v:
                    if k == 'eur':
                        price_strs.append(f"EUR: {v} €")
                    elif k == 'usd':
                        price_strs.append(f"USD: {v} $")
                    elif k == 'tix':
                        price_strs.append(f"TIX: {v}")
                    else:
                        price_strs.append(f"{k}: {v}")
            prices_label = QLabel("Preise: " + (" | ".join(price_strs) if price_strs else "Keine Preise"))
            prices_label.setStyleSheet("font-size: 14px; color: #cccccc;")
            prices_label.setWordWrap(True)
            info_block.addWidget(prices_label)

            legalities = card.get('legalities', {})
            legal_formats = [fmt.capitalize() for fmt, status in legalities.items() if status == 'legal']
            not_legal_formats = [fmt.capitalize() for fmt, status in legalities.items() if status != 'legal']
            legalities_text = "Legal: " + (', '.join(legal_formats) if legal_formats else "Keine")
            not_legalities_text = "Nicht Legal: " + (', '.join(not_legal_formats) if not_legal_formats else "Keine")
            legalities_label = QLabel(legalities_text)
            legalities_label.setStyleSheet("font-size: 13px; color: #4caf50; margin-bottom: 2px;")
            legalities_label.setWordWrap(True)
            info_block.addWidget(legalities_label)
            not_legalities_label = QLabel(not_legalities_text)
            not_legalities_label.setStyleSheet("font-size: 13px; color: #e53935; margin-bottom: 8px;")
            not_legalities_label.setWordWrap(True)
            info_block.addWidget(not_legalities_label)

            info_layout.addWidget(info_widget_block)
            fin_prefix = set_code.upper()[:3] if set_code and set_code != "?" else "?"
            fin_info = f"{fin_prefix} {collector_number}/{set_size}"
            fin_label = QLabel(fin_info)
            fin_label.setStyleSheet("font-size: 14px; color: #cccccc;")
            info_layout.addWidget(fin_label)

            info_widget = QWidget()
            info_widget.setLayout(info_layout)

            select_button = QPushButton("Diese auswählen")
            select_button.setFixedWidth(170)
            select_button.clicked.connect(lambda _, c=card: self.select_variant(c))
            buttons.append(select_button)

            hbox.addWidget(image_label)
            hbox.addWidget(info_widget, 1)
            hbox.addWidget(select_button)
            wrapper = QWidget()
            wrapper.setLayout(hbox)
            wrapper.setMinimumHeight(120)
            self.result_layout.addWidget(wrapper)
        # Einheitliche Button-Breite auf die Breite des kleinsten Buttons setzen
        if buttons:
            min_width = min(b.sizeHint().width() for b in buttons)
            for b in buttons:
                b.setMinimumWidth(min_width)
        self.result_layout.setSpacing(10)
        self.result_widget.setMinimumWidth(500)

    def select_variant(self, card_data):
        self.callback(card_data)
        print(f"DEBUG: Variant selected: {card_data}")  # Debugging
        self.accept()