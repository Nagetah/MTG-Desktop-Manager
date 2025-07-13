from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTextEdit, QScrollArea, QDialog, QSizePolicy, QStackedWidget, QListWidget, QInputDialog, QComboBox, QCheckBox, QGroupBox, QFrame
)
import hashlib
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
import requests
from io import BytesIO
import sys
import os
import json

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


class CardSelectorDialog(QDialog):
    def __init__(self, search_results, on_select):
        super().__init__()
        self.setWindowTitle("Suchergebnisse")
        self.setMinimumSize(600, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.layout = QVBoxLayout()
        # ScrollArea für Ergebnisse, damit nichts abgeschnitten wird
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
            fin_info = f"FIN {collector_number}/{set_size}"
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


class MTGDesktopManager(QWidget):
    def __init__(self, return_to_menu):
        self.return_to_menu = return_to_menu
        super().__init__()
        self.setWindowTitle("MTG Desktop Manager")
        self.setStyleSheet("background-color: #1e1e1e; color: white; font-size: 14px;")
        self.init_ui()
        self.current_card_data = None
        self.current_language = 'en'

    def init_ui(self):
        top_bar = QHBoxLayout()
        back_button = QPushButton("← Hauptmenü")
        back_button.clicked.connect(self.return_to_menu)
        top_bar.addWidget(back_button)
        layout = QVBoxLayout()
        layout.addLayout(top_bar)  # <-- Top-Bar mit Zurück-Button einfügen

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Kartennamen eingeben (auch Teil möglich)...")
        self.search_input.setStyleSheet("background-color: #2e2e2e; color: white; padding: 5px;")
        self.search_input.returnPressed.connect(self.search_card)
        search_layout.addWidget(self.search_input)

        search_button = QPushButton("Suchen")
        search_button.clicked.connect(self.search_card)
        search_layout.addWidget(search_button)

        reset_button = QPushButton("Zurücksetzen")
        reset_button.clicked.connect(self.clear_all)
        search_layout.addWidget(reset_button)

        layout.addLayout(search_layout)

        self.language_toggle_button = QPushButton("Karte auf Deutsch anzeigen")
        self.language_toggle_button.setVisible(False)
        self.language_toggle_button.clicked.connect(self.toggle_card_language)
        layout.addWidget(self.language_toggle_button)

        self.variant_button = QPushButton("Alle Varianten anzeigen")
        self.variant_button.setVisible(False)
        self.variant_button.clicked.connect(self.show_variants)
        layout.addWidget(self.variant_button)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('''
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
        self.result_container = QWidget()
        self.result_area = QVBoxLayout()
        self.result_container.setLayout(self.result_area)
        scroll.setWidget(self.result_container)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def clear_result_area(self):
        while self.result_area.count():
            item = self.result_area.takeAt(0)
            widget = item.widget()
            layout = item.layout()
            if widget:
                widget.deleteLater()
            elif layout:
                while layout.count():
                    sub_item = layout.takeAt(0)
                    sub_widget = sub_item.widget()
                    if sub_widget:
                        sub_widget.deleteLater()
                layout.deleteLater()

    def clear_all(self):
        self.search_input.clear()
        self.clear_result_area()
        self.current_card_data = None
        self.language_toggle_button.setVisible(False)
        self.variant_button.setVisible(False)

    def search_card(self):
        card_name = self.search_input.text().strip()
        if not card_name:
            return

        self.clear_result_area()

        direct_url = f"https://api.scryfall.com/cards/named?fuzzy={card_name}"
        response = requests.get(direct_url)

        if response.status_code == 200:
            self.current_card_data = response.json()
            print(f"DEBUG: Direct search result: {self.current_card_data}")  # Debugging
            self.current_language = self.current_card_data.get('lang', 'en')
            self.search_input.setText(self.current_card_data.get("name", card_name))
            self.load_selected_card(self.current_card_data)
            return

        search_url = f"https://api.scryfall.com/cards/search?q={card_name}&unique=cards"
        search_response = requests.get(search_url)
        if search_response.status_code == 200:
            data = search_response.json()
            print(f"DEBUG: Search results: {data}")  # Debugging
            if data.get("total_cards", 0) > 1:
                dialog = CardSelectorDialog(data["data"], self.load_selected_card)
                dialog.exec()
                return

    def load_selected_card(self, card_data):
        self.clear_result_area()
        self.current_card_data = card_data
        print(f"DEBUG: Selected card data: {self.current_card_data}")  # Debugging
        self.current_language = card_data.get('lang', 'en')
        self.search_input.setText(card_data.get("name", ""))
        self.display_card(card_data)
        self.check_for_de_language(card_data)
        self.variant_button.setVisible(True)

    def toggle_card_language(self):
        if not self.current_card_data:
            return
        oracle_id = self.current_card_data.get("oracle_id")
        if not oracle_id:
            return

        new_lang = "de" if self.current_language == "en" else "en"
        url = f"https://api.scryfall.com/cards/search?q=oracleid:{oracle_id}+lang:{new_lang}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["total_cards"] > 0:
                self.load_selected_card(data["data"][0])
                self.language_toggle_button.setText(
                    "Karte auf Englisch anzeigen" if new_lang == "de" else "Karte auf Deutsch anzeigen"
                )

    def check_for_de_language(self, card_data):
        oracle_id = card_data.get("oracle_id")
        url = f"https://api.scryfall.com/cards/search?q=oracleid:{oracle_id}+lang:de"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["total_cards"] > 0:
                self.language_toggle_button.setVisible(True)
                self.language_toggle_button.setText("Karte auf Deutsch anzeigen")
            else:
                self.language_toggle_button.setVisible(False)

    def show_variants(self):
        if not self.current_card_data:
            return
        prints_url = self.current_card_data.get("prints_search_uri")
        if not prints_url:
            return
        print(f"DEBUG: Prints URL: {prints_url}")  # Debugging
        selector = VariantSelector(prints_url, self.load_selected_card)
        selector.exec()

    def display_card(self, card):
        collections_file = "collections.json"

        def add_to_collection():
            current = self.current_card_data if hasattr(self, 'current_card_data') and self.current_card_data else card
            print(f"DEBUG: Card being added to collection: {current}")  # Debugging
            if not os.path.exists(collections_file):
                with open(collections_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
            with open(collections_file, "r", encoding="utf-8") as f:
                collections = json.load(f)

            selected_index = collection_selector.currentIndex()
            if selected_index < 0 or selected_index >= len(collections):
                QMessageBox.warning(self, "Fehler", "Keine gültige Sammlung ausgewählt.")
                return

            selected_collection = collections[selected_index]
            proxy = proxy_checkbox.isChecked()

            image_url = current.get("image_uris", {}).get("small")
            if not image_url and "card_faces" in current:
                image_url = current["card_faces"][0].get("image_uris", {}).get("small")

            # Ensure the image URL is correctly fetched and cached
            if image_url:
                img_path = get_cached_image(image_url, current.get('id'))
                if img_path and os.path.exists(img_path):
                    print(f"DEBUG: Image cached at: {img_path}")  # Debugging
                else:
                    print("DEBUG: Failed to cache image.")
            else:
                print("DEBUG: No image URL found.")

            set_code = current.get("set") or current.get("set_code") or current.get("set_id")
            set_size = current.get("set_size")
            if not set_size and set_code:
                try:
                    set_api_url = f"https://api.scryfall.com/sets/{set_code}"
                    resp = requests.get(set_api_url, timeout=3)
                    if resp.status_code == 200:
                        set_data = resp.json()
                        set_size = set_data.get("card_count")
                except Exception as e:
                    print(f"Fehler beim Laden von set_size: {e}")
                    set_size = None

            new_entry = {
                "id": current.get("id"),
                "name": current.get("name"),
                "set": current.get("set_name"),
                "set_code": set_code,
                "lang": current.get("lang", "en"),
                "is_proxy": proxy,
                "eur": current.get("prices", {}).get("eur", 0),
                "image_url": image_url,
                "count": 1,
                "oracle_text": current.get("oracle_text"),
                "mana_cost": current.get("mana_cost"),
                "card_faces": current.get("card_faces"),
                "collector_number": current.get("collector_number"),
                "set_size": set_size
            }

            print(f"DEBUG: New entry being added: {new_entry}")  # Debugging
            selected_collection["cards"].append(new_entry)
            with open(collections_file, "w", encoding="utf-8") as f:
                json.dump(collections, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Erfolg", f"Karte wurde zur Sammlung '{selected_collection['name']}' hinzugefügt.")

        self.clear_result_area()

        name = QLabel(f"<b>{card['name']}</b>")
        name.setStyleSheet("font-size: 30px; font-weight: bold; margin-bottom: 4px;")
        name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.result_area.addWidget(name)
        # Kompakte Infozeile: Manakosten | Set | Nummer (nur einmal, auch bei Flipkarten)
        mana_cost = card.get('mana_cost', '')
        set_code = card.get('set_code') or card.get('set') or ''
        collector_number = card.get('collector_number', '')
        set_size = card.get('set_size', '?')
        set_code_disp = set_code.upper() if set_code else ''
        info_parts = []
        if mana_cost:
            info_parts.append(f"<span style='color:#b0b0b0;'>Manakosten: {mana_cost}</span>")
        if set_code_disp:
            info_parts.append(f"<span style='color:#b0b0b0;'>Set: {set_code_disp}</span>")
        if collector_number:
            info_parts.append(f"<span style='color:#b0b0b0;'>Nr: {collector_number}/{set_size}</span>")
        if info_parts:
            info_label = QLabel(" | ".join(info_parts))
            info_label.setStyleSheet("font-size: 16px; margin-bottom: 4px;")
            info_label.setTextFormat(Qt.TextFormat.RichText)
            info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.result_area.addWidget(info_label)
        # Set-Name ausgeschrieben immer anzeigen
        set_name = card.get('set_name', '')
        if set_name:
            set_label = QLabel(f"Set-Name: {set_name}")
            set_label.setStyleSheet("font-size: 16px; margin-bottom: 8px;")
            set_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.result_area.addWidget(set_label)
        type_line = QLabel(f"Typ: {card.get('type_line', '-')}")
        type_line.setStyleSheet("font-size: 18px; margin-bottom: 4px;")
        type_line.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.result_area.addWidget(type_line)
        price = QLabel(f"Preis (EUR): {card['prices'].get('eur', 'Nicht verfügbar')}")
        price.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffd700; margin-bottom: 12px;")
        price.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.result_area.addWidget(price)

        # Oracle-Text mit besserer Trennung für Flip-/DFC-Karten
        if "card_faces" in card and isinstance(card["card_faces"], list) and len(card["card_faces"]) > 1:
            for idx, face in enumerate(card["card_faces"]):
                face_name = face.get('name', '')
                face_text = face.get('oracle_text', '')
                face_label = QLabel(f"<b>{face_name}</b><br>{face_text}")
                face_label.setStyleSheet("background-color: #2e2e2e; color: white; padding: 8px; border-radius: 4px;")
                face_label.setWordWrap(True)
                face_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                self.result_area.addWidget(face_label)
                if idx < len(card["card_faces"]) - 1:
                    line = QFrame()
                    line.setFrameShape(QFrame.Shape.HLine)
                    line.setFrameShadow(QFrame.Shadow.Sunken)
                    line.setStyleSheet("color: #888; margin: 8px 0;")
                    self.result_area.addWidget(line)
        else:
            oracle_text = card.get("oracle_text", "Kein Text verfügbar")
            oracle_label = QLabel(oracle_text.strip())
            oracle_label.setStyleSheet("background-color: #2e2e2e; color: white; padding: 8px; border-radius: 4px;")
            oracle_label.setWordWrap(True)
            oracle_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.result_area.addWidget(oracle_label)

        # Kartenbilder zentriert anzeigen
        image_row = QHBoxLayout()
        image_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        if "card_faces" in card:
            for face in card["card_faces"]:
                img_url = face.get("image_uris", {}).get("large")
                img_path = get_cached_image(img_url, face.get('id')) if img_url else None
                label = QLabel()
                if img_path and os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    pixmap = pixmap.scaled(360, 510, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                if not (img_path and os.path.exists(img_path)):
                    label.setText("Kein Bild")
                image_row.addWidget(label)
        else:
            img_url = card.get("image_uris", {}).get("large")
            img_path = get_cached_image(img_url, card.get('id')) if img_url else None
            label = QLabel()
            if img_path and os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                pixmap = pixmap.scaled(360, 510, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            if not (img_path and os.path.exists(img_path)):
                label.setText("Kein Bild")
            image_row.addWidget(label)

        wrapper = QWidget()
        wrapper.setLayout(image_row)
        self.result_area.addWidget(wrapper)

        # Sammlung hinzufügen UI
        control_row = QHBoxLayout()
        collection_selector = QComboBox()
        proxy_checkbox = QCheckBox("Als Proxy")
        add_button = QPushButton("Zur Sammlung hinzufügen")
        add_button.clicked.connect(add_to_collection)

        # Sammlungen laden
        if os.path.exists("collections.json"):
            with open("collections.json", "r", encoding="utf-8") as f:
                collections = json.load(f)
                for c in collections:
                    collection_selector.addItem(c["name"])

        control_row.addWidget(collection_selector)
        control_row.addWidget(proxy_checkbox)
        control_row.addWidget(add_button)

        control_widget = QWidget()
        control_widget.setLayout(control_row)
        self.result_area.addWidget(control_widget)


class StartScreen(QWidget):
    def __init__(self, switch_to_search, switch_to_collection):
        super().__init__()
        layout = QVBoxLayout()
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        title = QLabel("MTG Desktop Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 38px; font-weight: bold; padding: 36px 0 36px 0;")
        layout.addWidget(title)

        # Buttons näher an den Titel rücken und mittig anordnen
        button_container = QVBoxLayout()
        button_container.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        search_button = QPushButton("Karten suchen")
        search_button.setFixedWidth(440)
        search_button.setFixedHeight(120)
        search_button.setStyleSheet("font-size: 26px; padding: 32px 32px; margin-bottom: 38px; font-weight: bold; border-radius: 12px;")
        search_button.clicked.connect(switch_to_search)
        button_container.addWidget(search_button)

        collection_button = QPushButton("Sammlung öffnen")
        collection_button.setFixedWidth(440)
        collection_button.setFixedHeight(120)
        collection_button.setStyleSheet("font-size: 26px; padding: 32px 32px; font-weight: bold; border-radius: 12px;")
        collection_button.clicked.connect(switch_to_collection)
        button_container.addWidget(collection_button)

        layout.addLayout(button_container)
        self.setLayout(layout)


class CollectionViewer(QWidget):
    def __init__(self, collection_data, return_to_menu, stack_widget=None):
        super().__init__()
        self.collection = collection_data
        self.return_to_menu = return_to_menu
        self.stack_widget = stack_widget  # QStackedWidget explizit merken
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        layout = QVBoxLayout()

        top_bar = QHBoxLayout()
        back_button = QPushButton("← Hauptmenü")
        back_button.clicked.connect(self.return_to_menu)
        top_bar.addWidget(back_button)

        # Zurück zu Sammlungen Button
        back_to_collections_button = QPushButton("Zurück zu Sammlungen")
        back_to_collections_button.setStyleSheet("margin-left: 10px;")
        def go_to_collections():
            # Finde das MainWindow und zeige die Sammlungsübersicht
            parent = self.parent()
            while parent and not hasattr(parent, 'show_collections'):
                parent = parent.parent()
            if parent and hasattr(parent, 'show_collections'):
                parent.show_collections()
        back_to_collections_button.clicked.connect(go_to_collections)
        top_bar.addWidget(back_to_collections_button)

        title = QLabel(f"Sammlung: {self.collection['name']}")
        title.setStyleSheet("font-size: 30px; font-weight: bold; padding: 22px 0 22px 0;")
        top_bar.addWidget(title)
        layout.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('''
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
        content = QWidget()
        grid = QVBoxLayout()
        content.setLayout(grid)
        content.setMinimumWidth(400)  # Mindestbreite für Scrollbereich

        from urllib.parse import quote
        # Filtere alle None/bool/Fehlerhaften Karten raus
        valid_cards = [c for c in self.collection["cards"] if isinstance(c, dict)]
        for idx, card in enumerate(valid_cards):
            group = QGroupBox()
            group.setStyleSheet("QGroupBox { border: 1px solid #444; border-radius: 6px; margin-top: 8px; margin-bottom: 8px; padding: 8px; }")
            # Hauptlayout für die Karte
            hbox = QHBoxLayout()
            hbox.setSpacing(18)
            # Immer bestes Bild laden: versuche zuerst "large", dann "normal", dann "small"
            image_uris = None
            if card.get("card_faces") and isinstance(card["card_faces"], list):
                # Für DFCs: nimm das erste Face
                image_uris = card["card_faces"][0].get("image_uris")
            elif card.get("image_uris"):
                image_uris = card["image_uris"]
            else:
                image_uris = card.get("image_url")  # Fallback: evtl. String
            fallback_set = card.get('set_code') or card.get('set')
            img_path = get_cached_image(
                image_uris,
                card.get('id'),
                fallback_name=card.get('name'),
                fallback_set=fallback_set
            )
            class ClickableLabel(QLabel):
                def __init__(self, img_path=None, card=None, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.img_path = img_path
                    self.card = card

                def mousePressEvent(self, event):
                    from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel as QL, QVBoxLayout
                    from PyQt6.QtGui import QPixmap
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Kartenbild(er)")
                    layout = QVBoxLayout()
                    hbox = QHBoxLayout()
                    images = []

                    # Immer das größte verfügbare Bild nehmen (large > normal > small)
                    def get_best_img_path(image_uris, face, card):
                        if isinstance(image_uris, dict):
                            for key in ["large", "normal", "small"]:
                                if image_uris.get(key):
                                    return get_cached_image(image_uris[key], face.get('id') if face else card.get('id'), fallback_name=face.get('name') if face else card.get('name'), fallback_set=card.get('set_code') or card.get('set'))
                        elif isinstance(image_uris, str):
                            return get_cached_image(image_uris, face.get('id') if face else card.get('id'), fallback_name=face.get('name') if face else card.get('name'), fallback_set=card.get('set_code') or card.get('set'))
                        return None

                    if self.card and self.card.get("card_faces") and isinstance(self.card["card_faces"], list) and len(self.card["card_faces"]) > 1:
                        for face in self.card["card_faces"]:
                            image_uris = face.get("image_uris")
                            img_path = get_best_img_path(image_uris, face, self.card)
                            if img_path and os.path.exists(img_path):
                                images.append(img_path)
                    elif self.img_path and os.path.exists(self.img_path):
                        images.append(self.img_path)

                    if images:
                        for path in images:
                            lbl = QL()
                            pix = QPixmap(path)
                            pix = pix.scaled(460, 640, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            lbl.setPixmap(pix)
                            hbox.addWidget(lbl)
                        hbox.setSpacing(24)
                        hbox.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                        layout.addLayout(hbox)
                        dlg.setLayout(layout)
                        # Dialoggröße anpassen
                        min_width = 500 * len(images) + 40
                        dlg.setMinimumWidth(min_width)
                        dlg.setMinimumHeight(700)
                        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                        dlg.show()
            image_label = ClickableLabel(img_path=img_path, card=card)
            image_label.setMinimumSize(132, 182)
            image_label.setMaximumSize(132, 182)
            if img_path and os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                pixmap = pixmap.scaled(132, 182, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(pixmap)
                image_label.setCursor(Qt.CursorShape.PointingHandCursor)
                image_label.setToolTip("Bild im Explorer öffnen")
            else:
                image_label.setText("Kein Bild")
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Info-Block (Name, kompakte Infozeile, Preis, Proxy, Mülleimer)
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            # Name | Preis (eine Zeile, Preis: falls nicht vorhanden, "- €")
            name_price_row = QHBoxLayout()
            name_label = QLabel(card['name'])
            name_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 2px;")
            name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            name_price_row.addWidget(name_label)
            # Preis
            eur = card.get('eur')
            price_str = f"{eur} €" if eur not in (None, '', 'Nicht verfügbar', 0, '0') else "- €"
            price_label = QLabel(f"| {price_str}")
            price_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffd700; margin-bottom: 2px; margin-left: 8px;")
            price_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            name_price_row.addWidget(price_label)
            name_price_row.addStretch(1)
            # Mülleimer-Button
            del_btn = QPushButton()
            del_btn.setFixedSize(24, 24)
            del_btn.setStyleSheet('''
                QPushButton {
                    border: none;
                    background: transparent;
                    min-width: 24px; min-height: 24px; max-width: 24px; max-height: 24px;
                    padding: 0;
                    color: #e53935;
                    font-size: 22px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #ffdddd;
                    border-radius: 6px;
                }
            ''')
            del_btn.setText('✗')
            def delete_card(card_id, card_name):
                print(f"[DEBUG] delete_card aufgerufen für: {card_name} (ID: {card_id})")
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(self, "Karte löschen", f"Möchtest du '{card_name}' wirklich aus der Sammlung entfernen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    with open("collections.json", "r", encoding="utf-8") as f:
                        collections = json.load(f)
                    for c in collections:
                        if c['name'] == self.collection['name']:
                            print(f"[DEBUG] Karten vor dem Löschen: {len(c['cards'])}")
                            c['cards'] = [card for card in c['cards'] if isinstance(card, dict) and card.get('id') != card_id]
                            print(f"[DEBUG] Karten nach dem Löschen: {len(c['cards'])}")
                            break
                    with open("collections.json", "w", encoding="utf-8") as f:
                        json.dump(collections, f, indent=2, ensure_ascii=False)
                    print("[DEBUG] collections.json wurde aktualisiert.")
                    updated_collection = None
                    for c in collections:
                        if c['name'] == self.collection['name']:
                            updated_collection = c
                            break
                    stack = self.stack_widget
                    if not stack:
                        parent = self.parent()
                        while parent and not isinstance(parent, QStackedWidget):
                            parent = parent.parent()
                        stack = parent
                    if stack and updated_collection:
                        idx = stack.indexOf(self)
                        stack.removeWidget(self)
                        self.deleteLater()
                        new_viewer = CollectionViewer(updated_collection, self.return_to_menu, stack_widget=stack)
                        stack.insertWidget(idx, new_viewer)
                        stack.setCurrentWidget(new_viewer)
                        print("[DEBUG] CollectionViewer wurde neu geladen.")
            del_btn.clicked.connect(lambda _, cid=card.get('id'), cname=card.get('name', '?'): delete_card(cid, cname))
            name_price_row.addWidget(del_btn)
            info_layout.addLayout(name_price_row)
            # Kompakte Infozeile: Manakosten (ohne Klammern), Setname, Setcode und Nummer
            mana_cost = card.get('mana_cost', '')
            # Für Flip/DFC-Karten: Manakosten aus beiden Faces zusammenfassen, falls unterschiedlich
            if not mana_cost and card.get('card_faces') and isinstance(card['card_faces'], list) and len(card['card_faces']) > 0:
                faces = card['card_faces']
                mana_costs = [f.get('mana_cost', '') for f in faces if f.get('mana_cost')]
                mana_costs_clean = [mc.replace('{', '').replace('}', '') for mc in mana_costs if mc]
                mana_cost_clean = ' // '.join(mana_costs_clean) if mana_costs_clean else ''
            else:
                mana_cost_clean = mana_cost.replace('{', '').replace('}', '') if mana_cost else ''
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
                        print(f"DEBUG: Fetched set_size: {set_size} for set_code: {set_code}")  # Debugging
                    else:
                        print(f"DEBUG: Failed to fetch set_size for set_code: {set_code}, status code: {resp.status_code}")
                except Exception as e:
                    print(f"Fehler beim Laden von set_size: {e}")
                    set_size = "?"

            collector_number = card.get("collector_number", "?")
            set_code_disp = set_code.upper() if set_code != "?" else "?"
            # Format: Manakosten: 1WU | Setname | SPE 25/6
            info_line = []
            if mana_cost_clean:
                info_line.append(f"Manakosten: {mana_cost_clean}")
            if set_code_disp or collector_number:
                info_line.append(f"{set_code_disp} {collector_number}/{set_size}")
            if info_line:
                info_label = QLabel(" | ".join(info_line))
                info_label.setStyleSheet("font-size: 15px; margin-bottom: 4px;")
                info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                info_layout.addWidget(info_label)
            # Proxy
            if card.get('is_proxy'):
                proxy_label = QLabel("Proxy: Ja")
                proxy_label.setStyleSheet("font-size: 15px; color: #ff8888;")
                proxy_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                info_layout.addWidget(proxy_label)
            info_widget = QWidget()
            info_widget.setLayout(info_layout)
            # Oracle-Text für Flip-/DFC-Karten platzsparend in einer Box, Absätze zwischen den Texten
            if card.get('card_faces') and isinstance(card['card_faces'], list) and len(card['card_faces']) > 1:
                oracle_texts = []
                for face in card['card_faces']:
                    face_name = face.get('name', '')
                    face_text = face.get('oracle_text', '')
                    if face_name and face_text:
                        oracle_texts.append(f"<b>{face_name}</b><br>{face_text}")
                    elif face_text:
                        oracle_texts.append(face_text)
                oracle_html = "<br><br>".join(oracle_texts)
                oracle_frame = QFrame()
                oracle_frame.setStyleSheet("background-color: #292f3a; border-radius: 6px; padding: 8px; margin-top: 6px; margin-bottom: 2px;")
                oracle_layout = QVBoxLayout()
                oracle_label = QLabel()
                oracle_label.setText(oracle_html)
                oracle_label.setStyleSheet("color: #fff; font-size: 15px;")
                oracle_label.setWordWrap(True)
                oracle_label.setTextFormat(Qt.TextFormat.RichText)
                oracle_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                oracle_layout.addWidget(oracle_label)
                oracle_frame.setLayout(oracle_layout)
                info_layout.addWidget(oracle_frame)
            else:
                oracle_text = card.get('oracle_text', '')
                if oracle_text:
                    oracle_frame = QFrame()
                    oracle_frame.setStyleSheet("background-color: #292f3a; border-radius: 6px; padding: 8px; margin-top: 6px; margin-bottom: 2px;")
                    oracle_layout = QVBoxLayout()
                    oracle_label = QLabel(oracle_text)
                    oracle_label.setStyleSheet("color: #fff; font-size: 15px;")
                    oracle_label.setWordWrap(True)
                    oracle_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    oracle_layout.addWidget(oracle_label)
                    oracle_frame.setLayout(oracle_layout)
                    info_layout.addWidget(oracle_frame)

            hbox.addWidget(image_label)
            hbox.addWidget(info_widget, 1)
            group.setLayout(hbox)
            grid.addWidget(group)
            if idx < len(self.collection["cards"]) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                line.setStyleSheet("color: #444;")
                grid.addWidget(line)
        content.setMinimumWidth(500)
        content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.setLayout(layout)


# HIER BEGINNT DIE KORREKTE MAINWINDOW-KLASSE
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MTG Desktop Manager")
        self.stack = QStackedWidget()
        self.search_view = MTGDesktopManager(self.show_start)

        class CollectionOverview(QWidget):
            def __init__(self, return_to_menu):
                super().__init__()
                self.return_to_menu = return_to_menu
                self.setStyleSheet("background-color: #1e1e1e; color: white;")
                layout = QVBoxLayout()

                top_bar = QHBoxLayout()
                back_button = QPushButton("← Hauptmenü")
                back_button.clicked.connect(self.return_to_menu)
                top_bar.addWidget(back_button)

                self.label = QLabel("Sammlungen")
                self.label.setStyleSheet("font-size: 18px; padding: 10px;")
                top_bar.addWidget(self.label)
                layout.addLayout(top_bar)

                self.list_widget = QListWidget()
                self.list_widget.itemDoubleClicked.connect(self.open_collection)
                layout.addWidget(self.list_widget)

                self.new_button = QPushButton("Neue Sammlung erstellen")
                self.new_button.clicked.connect(self.create_collection)
                layout.addWidget(self.new_button)

                self.delete_button = QPushButton("Ausgewählte Sammlung löschen")
                self.delete_button.clicked.connect(self.delete_collection)
                layout.addWidget(self.delete_button)

                self.setLayout(layout)
                self.load_collections()

            def open_collection(self, item):
                collection_name = item.text().split('|')[0].strip()
                if not os.path.exists("collections.json"):
                    QMessageBox.warning(self, "Fehler", "Sammlung nicht gefunden.")
                    return
                with open("collections.json", "r", encoding="utf-8") as f:
                    collections = json.load(f)
                    for col in collections:
                        if col["name"] == collection_name:
                            # QStackedWidget explizit übergeben
                            stack = self.parent()
                            viewer = CollectionViewer(col, self.return_to_menu, stack_widget=stack)
                            stack.addWidget(viewer)
                            stack.setCurrentWidget(viewer)
                            return

            def delete_collection(self):
                selected = self.list_widget.currentRow()
                if selected < 0:
                    QMessageBox.warning(self, "Fehler", "Keine Sammlung ausgewählt.")
                    return
                if not os.path.exists("collections.json"):
                    return
                with open("collections.json", "r", encoding="utf-8") as f:
                    collections = json.load(f)
                name = collections[selected]["name"]
                reply = QMessageBox.question(
                    self,
                    "Bestätigung",
                    f"Möchtest du die Sammlung '{name}' wirklich löschen?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    del collections[selected]
                    with open("collections.json", "w", encoding="utf-8") as f:
                        json.dump(collections, f, indent=2, ensure_ascii=False)
                    self.load_collections()
                    QMessageBox.information(self, "Gelöscht", f"Die Sammlung '{name}' wurde gelöscht.")

            def load_collections(self):
                self.list_widget.clear()
                if os.path.exists("collections.json"):
                    with open("collections.json", "r", encoding="utf-8") as f:
                        collections = json.load(f)
                        for col in collections:
                            self.list_widget.addItem(f"{col['name']} | {len(col['cards'])} Karten | Wert: {sum(float(c.get('eur') or 0) for c in col['cards']):.2f} €")

            def create_collection(self):
                collections = []
                if os.path.exists("collections.json"):
                    with open("collections.json", "r", encoding="utf-8") as f:
                        collections = json.load(f)
                name, ok = QInputDialog.getText(self, "Sammlung benennen", "Name der neuen Sammlung:")
                if ok and name:
                    collections.append({"name": name, "cards": []})
                    with open("collections.json", "w", encoding="utf-8") as f:
                        json.dump(collections, f, indent=2, ensure_ascii=False)
                    self.load_collections()

        self.collection_view = CollectionOverview(self.show_start)
        self.start_screen = StartScreen(self.show_search, self.show_collections)

        self.stack.addWidget(self.start_screen)
        self.stack.addWidget(self.search_view)
        self.stack.addWidget(self.collection_view)

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

        self.stack.setCurrentWidget(self.start_screen)

    def show_start(self):
        self.stack.setCurrentWidget(self.start_screen)

    def show_search(self):
        self.stack.setCurrentWidget(self.search_view)

    def show_collections(self):
        self.collection_view.load_collections()
        self.stack.setCurrentWidget(self.collection_view)



app = QApplication(sys.argv)
# Setze Fusion Style, damit Stylesheet für Scrollbars auf Windows greift
try:
    from PyQt6.QtWidgets import QStyleFactory
    app.setStyle(QStyleFactory.create('Fusion'))
except Exception:
    pass
# Globales dunkles Stylesheet anwenden
app.setStyleSheet("""
    QWidget { background-color: #1e1e1e; color: white; font-size: 17px; }
    QPushButton {
        background-color: #222;
        color: white;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 12px 28px;
        min-width: 100px;
        min-height: 38px;
        font-size: 21px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    QPushButton:hover {
        background-color: #333;
        border: 1px solid #888;
    }
    QPushButton:pressed {
        background-color: #111;
        border: 1px solid #666;
    }
    QLineEdit, QTextEdit {
        background-color: #232323;
        color: white;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 7px;
        font-size: 18px;
    }
    QLineEdit:focus, QTextEdit:focus {
        border: 1.5px solid #0078d7;
        background-color: #262a36;
    }

    /* Apple/macOS style QComboBox */
    QComboBox {
        background-color: #232323;
        color: white;
        border: 1.5px solid #444;
        border-radius: 8px;
        padding: 8px 40px 8px 16px;
        font-size: 19px;
        min-height: 38px;
        min-width: 140px;
        qproperty-iconSize: 22px 22px;
    }
    QComboBox:focus {
        border: 1.5px solid #0078d7;
        background-color: #262a36;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 32px;
        border-left: 1px solid #444;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
        background: transparent;
    }
    QComboBox::down-arrow {
        image: url(data:image/svg+xml;utf8,<svg width='16' height='16' viewBox='0 0 16 16' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M4 6L8 10L12 6' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>);
        width: 16px;
        height: 16px;
        margin-right: 8px;
    }
    QComboBox QAbstractItemView {
        background: #232323;
        color: white;
        border: 1px solid #444;
        selection-background-color: #444;
        selection-color: #fff;
        border-radius: 8px;
        font-size: 18px;
    }

    QScrollArea { background-color: #1e1e1e; }
    QGroupBox {
        background-color: #232323;
        color: white;
        border: 1px solid #444;
        border-radius: 6px;
        margin-top: 8px;
        margin-bottom: 8px;
        padding: 10px;
        font-size: 18px;
        font-weight: 500;
    }
    QListWidget {
        background-color: #232323;
        color: white;
        border: 1px solid #444;
        border-radius: 4px;
        font-size: 18px;
    }
    QListWidget::item:selected {
        background: #444;
        color: #fff;
    }
    QLabel { color: white; font-size: 17px; }
""")
main_window = MainWindow()
from PyQt6.QtGui import QScreen
screen = app.primaryScreen()
screen_size = screen.availableGeometry()
width = min(1000, screen_size.width() - 100)
height = min(850, screen_size.height() - 100)
main_window.resize(width, height)
main_window.show()
app.exec()
