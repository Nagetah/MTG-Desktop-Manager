# ui_search.py
# Such- und Kartenanzeige-UI
import os
import json
import requests
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QLabel, QComboBox, QCheckBox, QMessageBox, QFrame, QSizePolicy
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from dialogs import CardSelectorDialog, VariantSelector
from utils import get_cached_image



###############################################################
# --- MOVE TO ui_search.py ---
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
        back_button.setStyleSheet("font-size: 18px; font-weight: 600; padding: 8px 24px;")
        back_button.clicked.connect(self.return_to_menu)
        top_bar.addWidget(back_button)
        layout = QVBoxLayout()
        layout.addLayout(top_bar)  # <-- Top-Bar mit Zurück-Button einfügen

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Kartennamen eingeben (auch Teil möglich)...")
        self.search_input.setStyleSheet("background-color: #2e2e2e; color: white; padding: 7px; font-size: 18px; font-weight: 600;")
        self.search_input.returnPressed.connect(self.search_card)
        search_layout.addWidget(self.search_input)

        search_button = QPushButton("Suchen")
        search_button.setStyleSheet("font-size: 18px; font-weight: 600; padding: 8px 24px;")
        search_button.clicked.connect(self.search_card)
        search_layout.addWidget(search_button)

        reset_button = QPushButton("Zurücksetzen")
        reset_button.setStyleSheet("font-size: 18px; font-weight: 600; padding: 8px 24px;")
        reset_button.clicked.connect(self.clear_all)
        search_layout.addWidget(reset_button)

        layout.addLayout(search_layout)


        # Button-Zeile für Sprache/Variante
        button_row = QHBoxLayout()
        self.language_toggle_button = QPushButton("Karte auf Deutsch anzeigen")
        self.language_toggle_button.setStyleSheet("font-size: 18px; font-weight: 600; padding: 8px 24px;")
        self.language_toggle_button.setVisible(False)
        self.language_toggle_button.clicked.connect(self.toggle_card_language)
        button_row.addWidget(self.language_toggle_button)

        self.variant_button = QPushButton("Alle Varianten anzeigen")
        self.variant_button.setStyleSheet("font-size: 18px; font-weight: 600; padding: 8px 24px;")
        self.variant_button.setVisible(False)
        self.variant_button.clicked.connect(self.show_variants)
        button_row.addWidget(self.variant_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
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
            variant_key, variant_price = variant_selector.currentData()
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
            # Sprache aus Dropdown
            lang_selected = language_selector.currentText().lower()
            # Kaufpreis aus Feld übernehmen
            purchase_price = purchase_price_edit.text().strip()
            # Stückzahl aus Feld übernehmen
            try:
                count_val = int(count_edit.text())
                if count_val < 1:
                    count_val = 1
            except Exception:
                count_val = 1

            # Immer das größte verfügbare Bild cachen (large > normal > small), egal ob Flipkarte oder nicht
            image_uris = None
            if current.get("card_faces") and isinstance(current["card_faces"], list):
                # Flipkarte: cache für jedes Face das beste Bild
                for face in current["card_faces"]:
                    image_uris_face = face.get("image_uris")
                    if image_uris_face:
                        for key in ["large", "normal", "small"]:
                            if image_uris_face.get(key):
                                img_path = get_cached_image(image_uris_face[key], face.get('id'), fallback_name=face.get('name'), fallback_set=current.get('set_code') or current.get('set'))
                                if img_path and os.path.exists(img_path):
                                    print(f"DEBUG: Flipkarte: Image cached at: {img_path}")
                                else:
                                    print("DEBUG: Flipkarte: Failed to cache image.")
                                break
            else:
                # Nicht-Flipkarte: bestes Bild suchen
                image_uris = current.get("image_uris")
                img_path = None
                if isinstance(image_uris, dict):
                    for key in ["large", "normal", "small"]:
                        if image_uris.get(key):
                            img_path = get_cached_image(image_uris[key], current.get('id'), fallback_name=current.get('name'), fallback_set=current.get('set_code') or current.get('set'))
                            if img_path and os.path.exists(img_path):
                                print(f"DEBUG: Image cached at: {img_path}")
                            else:
                                print("DEBUG: Failed to cache image.")
                            break
                elif isinstance(image_uris, str):
                    img_path = get_cached_image(image_uris, current.get('id'), fallback_name=current.get('name'), fallback_set=current.get('set_code') or current.get('set'))
                    if img_path and os.path.exists(img_path):
                        print(f"DEBUG: Image cached at: {img_path}")
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

            # Bestimme die tatsächlich verwendete Bild-URL für den Eintrag
            best_image_url = None
            if current.get("card_faces") and isinstance(current["card_faces"], list):
                # Flipkarte: nimm das größte Bild des ersten Faces
                face = current["card_faces"][0]
                image_uris_face = face.get("image_uris")
                if image_uris_face:
                    for key in ["large", "normal", "small"]:
                        if image_uris_face.get(key):
                            best_image_url = image_uris_face[key]
                            break
            else:
                image_uris = current.get("image_uris")
                if isinstance(image_uris, dict):
                    for key in ["large", "normal", "small"]:
                        if image_uris.get(key):
                            best_image_url = image_uris[key]
                            break
                elif isinstance(image_uris, str):
                    best_image_url = image_uris


            # Preis bei Proxy immer 0
            # Preis je nach Variante, bei Proxy immer 0
            if proxy:
                eur_value = 0
            else:
                eur_value = variant_price if variant_price is not None else 0
            # Übernehme ALLE Felder aus Scryfall-Response
            new_entry = dict(current)
            # Ergänze/überschreibe lokale Felder
            new_entry["lang"] = lang_selected
            new_entry["is_proxy"] = proxy
            new_entry["count"] = count_val
            new_entry["image_url"] = best_image_url
            new_entry["eur"] = eur_value
            new_entry["set_size"] = set_size
            new_entry["variant"] = variant_key
            new_entry["purchase_price"] = purchase_price

            print(f"DEBUG: New entry being added: {new_entry}")  # Debugging
            selected_collection["cards"].append(new_entry)
            with open(collections_file, "w", encoding="utf-8") as f:
                json.dump(collections, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Erfolg", f"Karte wurde zur Sammlung '{selected_collection['name']}' hinzugefügt.")

        self.clear_result_area()

        # (Kartenname und Infozeile außerhalb des Frames entfernt)
        # Set-Name ausgeschrieben immer anzeigen

        # --- NEU: Karte und Infos nebeneinander ---
        card_info_row = QHBoxLayout()
        # Kartenbild(er) links (Flipkarten-Bilder nebeneinander mit Mindestabstand)
        image_hbox = QHBoxLayout()
        image_hbox.setSpacing(0)
        image_hbox.setContentsMargins(0, 0, 0, 0)
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
                image_hbox.addWidget(label)
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
            image_hbox.addWidget(label)
        image_widget = QWidget()
        image_widget.setLayout(image_hbox)
        image_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        card_info_row.addWidget(image_widget, 0)

        # Infos rechts
        info_col = QVBoxLayout()
        info_col.setSpacing(-1)  # Negativer Spacing für maximalen Abstandabbau
        name = QLabel(f"<b>{card['name']}</b>")
        name.setStyleSheet("font-size: 26px; font-weight: bold; margin: 0 !important; line-height: 1 !important; padding: 0 !important;")
        name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        name.setWordWrap(True)
        name.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        info_col.addWidget(name)

        info_widget = QWidget()
        info_widget.setLayout(info_col)
        info_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        card_info_row.addWidget(info_widget, 1)
        # Kompakte Infozeile: Manakosten | Set | Nummer (nur einmal, auch bei Flipkarten)
        mana_cost = card.get('mana_cost', '')
        set_code = card.get('set_code') or card.get('set') or ''
        collector_number = card.get('collector_number', '')
        set_size = card.get('set_size')
        # Falls set_size fehlt, hole sie aus Scryfall
        if not set_size:
            set_code = card.get('set_code') or card.get('set') or ''
            if set_code:
                try:
                    set_api_url = f"https://api.scryfall.com/sets/{set_code}"
                    import requests
                    resp = requests.get(set_api_url, timeout=3)
                    if resp.status_code == 200:
                        set_data = resp.json()
                        set_size = set_data.get("card_count", "?")
                    else:
                        set_size = "?"
                except Exception as e:
                    set_size = "?"
            else:
                set_size = "?"
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
            info_label.setStyleSheet("font-size: 15px; margin: 0 !important; line-height: 1 !important; padding: 0 !important;")
            info_label.setTextFormat(Qt.TextFormat.RichText)
            info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_label.setWordWrap(True)
            info_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            info_col.addWidget(info_label)
        # Set-Name ausgeschrieben immer anzeigen
        set_name = card.get('set_name', '')
        if set_name:
            set_label = QLabel(f"Set-Name: {set_name}")
            set_label.setStyleSheet("font-size: 15px; margin: 0 !important; line-height: 1 !important; padding: 0 !important;")
            set_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            set_label.setWordWrap(True)
            set_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            info_col.addWidget(set_label)
        type_line = QLabel(f"Typ: {card.get('type_line', '-')}")
        type_line.setStyleSheet("font-size: 15px; margin: 0 !important; line-height: 1 !important; padding: 0 !important;")
        type_line.setWordWrap(True)
        type_line.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        type_line.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        info_col.addWidget(type_line)

        # Preis-Anzeige mit FOIL-Label, wenn nötig
        # Prüfe, ob das aktuelle Card-Objekt aus der Sammlung kommt (hat 'variant')
        variant = card.get('variant', None)
        eur_price = card.get('eur') if 'eur' in card else card.get('prices', {}).get('eur')
        price_text = f"Preis (EUR): {eur_price if eur_price is not None else 'Nicht verfügbar'}"
        if variant == 'foil':
            price_text += " <span style='color:#ffd700; font-weight:bold;'>FOIL</span>"
        price = QLabel(price_text)
        price.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffd700; margin: 0 !important; line-height: 1 !important; padding: 0 !important;")
        price.setTextFormat(Qt.TextFormat.RichText)
        price.setWordWrap(True)
        price.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        price.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        info_col.addWidget(price)

        # --- Erweiterung: Zeige Foil-Typ, Preise, Legalities ---
        info_block = QVBoxLayout()
        info_block.setSpacing(2)
        finishes = card.get('finishes', [])
        finishes_str = ', '.join(finishes) if finishes else 'Unbekannt'
        finishes_label = QLabel(f"Foil-Typ: {finishes_str}")
        finishes_label.setStyleSheet("font-size: 13px; color: #cccccc; margin: 0 !important; line-height: 1 !important; padding: 0 !important;")
        finishes_label.setWordWrap(True)
        finishes_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        finishes_label.setWordWrap(True)
        info_block.addWidget(finishes_label)

        prices = card.get('prices', {})
        price_strs = []
        # EUR normal
        if prices.get('eur'):
            price_strs.append(f"{prices['eur']} €")
        # EUR Foil
        if prices.get('eur_foil'):
            price_strs.append(f"Foil: {prices['eur_foil']} €")
        # USD normal
        if prices.get('usd'):
            price_strs.append(f"{prices['usd']} $")
        # USD Foil
        if prices.get('usd_foil'):
            price_strs.append(f"Foil: {prices['usd_foil']} $")
        # TIX (optional, falls vorhanden)
        if prices.get('tix'):
            price_strs.append(f"TIX: {prices['tix']}")
        prices_label = QLabel("Preise: " + (" | ".join(price_strs) if price_strs else "Keine Preise"))
        prices_label.setStyleSheet("font-size: 13px; color: #cccccc; margin: 0 !important; line-height: 1 !important; padding: 0 !important;")
        prices_label.setWordWrap(True)
        prices_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_block.addWidget(prices_label)

        legalities = card.get('legalities', {})
        legal_formats = [fmt.capitalize() for fmt, status in legalities.items() if status == 'legal']
        not_legal_formats = [fmt.capitalize() for fmt, status in legalities.items() if status != 'legal']
        legalities_text = "Legal: " + (', '.join(legal_formats) if legal_formats else "Keine")
        not_legalities_text = "Nicht Legal: " + (', '.join(not_legal_formats) if not_legal_formats else "Keine")
        legalities_label = QLabel(legalities_text)
        legalities_label.setStyleSheet("font-size: 12px; color: #4caf50; margin: 0 !important; line-height: 1 !important; padding: 0 !important;")
        legalities_label.setWordWrap(True)
        legalities_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        legalities_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        info_block.addWidget(legalities_label)
        not_legalities_label = QLabel(not_legalities_text)
        not_legalities_label.setStyleSheet("font-size: 12px; color: #e53935; margin: 0 !important; line-height: 1 !important; padding: 0 !important;")
        not_legalities_label.setWordWrap(True)
        not_legalities_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        not_legalities_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        info_block.addWidget(not_legalities_label)

        info_widget_block = QWidget()
        info_widget_block.setLayout(info_block)
        info_widget_block.setMaximumWidth(420)
        info_col.addWidget(info_widget_block)

        # Oracle-Text
        if "card_faces" in card and isinstance(card["card_faces"], list) and len(card["card_faces"]) > 1:
            for idx, face in enumerate(card["card_faces"]):
                face_name = face.get('name', '')
                face_text = face.get('oracle_text', '')
                face_label = QLabel(f"<b>{face_name}</b><br>{face_text}")
                face_label.setStyleSheet("background-color: #2e2e2e; color: white; padding: 2px !important; border-radius: 4px; font-size:13px; margin:0 !important; line-height: 1 !important;")
                face_label.setWordWrap(True)
                face_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                info_col.addWidget(face_label)
                if idx < len(card["card_faces"]) - 1:
                    line = QFrame()
                    line.setFrameShape(QFrame.Shape.HLine)
                    line.setFrameShadow(QFrame.Shadow.Sunken)
                    line.setStyleSheet("color: #888; margin: 0;")
                    info_col.addWidget(line)
        else:
            oracle_text = card.get("oracle_text", "Kein Text verfügbar")
            oracle_label = QLabel(oracle_text.strip())
            oracle_label.setStyleSheet("background-color: #2e2e2e; color: white; padding: 2px !important; border-radius: 4px; font-size:13px; margin:0 !important; line-height: 1 !important;")
            oracle_label.setWordWrap(True)
            oracle_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_col.addWidget(oracle_label)

        card_info_row.addLayout(info_col)

        # In QFrame für optische Trennung
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("background-color: #232323; border-radius: 10px; padding: 16px;")
        frame.setLayout(card_info_row)
        self.result_area.addWidget(frame)
        # (Alte, jetzt überflüssige Bild- und Oracle-Textanzeige entfernt)

        # (Kein weiteres Widget mit image_row anhängen, da Bild bereits im Frame ist)

        # Sammlung hinzufügen UI

        # --- Optionsleiste mittig zentrieren ---
        outer_center_row = QHBoxLayout()
        outer_center_row.addStretch(1)
        control_row = QHBoxLayout()
        # Sammlung Dropdown (breiter)
        collection_selector = QComboBox()
        collection_selector.setFixedWidth(170)
        collection_selector.setStyleSheet("QComboBox { font-size: 18px; font-weight: 600; min-width: 120px; max-width: 170px; padding: 8px 18px 8px 14px; border-radius: 8px; } QComboBox QAbstractItemView { font-size: 18px; }")

        # Sprachauswahl (Dropdown, schmaler)
        language_selector = QComboBox()
        language_selector.addItem("DE")
        language_selector.addItem("ENG")
        language_selector.setFixedWidth(80)
        language_selector.setStyleSheet("QComboBox { font-size: 18px; font-weight: 600; min-width: 60px; max-width: 80px; padding: 8px 12px 8px 10px; border-radius: 8px; } QComboBox QAbstractItemView { font-size: 18px; }")

        # Variantendropdown (Foil/Nonfoil + Preis, breiter)
        variant_selector = QComboBox()
        variant_options = []
        prices = card.get('prices', {})
        if prices.get('eur'):
            variant_options.append((f"Nonfoil ({prices['eur']} €)", 'nonfoil', prices['eur']))
        if prices.get('eur_foil'):
            variant_options.append((f"Foil ({prices['eur_foil']} €)", 'foil', prices['eur_foil']))
        if not variant_options:
            variant_options.append(("Nonfoil (Preis unbekannt)", 'nonfoil', None))
        for label, key, price in variant_options:
            variant_selector.addItem(label, (key, price))
        variant_selector.setFixedWidth(170)
        variant_selector.setStyleSheet("QComboBox { font-size: 18px; font-weight: 600; min-width: 120px; max-width: 170px; padding: 8px 18px 8px 14px; border-radius: 8px; } QComboBox QAbstractItemView { font-size: 18px; }")

        # Proxy-Checkbox
        proxy_checkbox = QCheckBox("Proxy")
        proxy_checkbox.setFixedWidth(100)
        proxy_checkbox.setStyleSheet('''
            QCheckBox {
                font-size: 18px;
                min-height: 38px;
                min-width: 100px;
                max-width: 100px;
                padding: 8px 10px;
                color: white;
                background-color: #222;
                border: 1.5px solid #444;
                border-radius: 8px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            QCheckBox:hover {
                background-color: #333;
                border: 1.5px solid #888;
            }
            QCheckBox:checked {
                background-color: #262a36;
                border: 1.5px solid #0078d7;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 4px;
                border: 1.5px solid #444;
                background: #232323;
            }
            QCheckBox::indicator:checked {
                background: #0078d7;
                border: 1.5px solid #0078d7;
            }
        ''')

        # Stückzahl-Eingabe (wie Kaufpreis, aber kleiner)
        count_row = QHBoxLayout()
        count_row.setContentsMargins(0, 0, 0, 0)
        count_row.setSpacing(8)
        count_label = QLabel("Stück:")
        count_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #cccccc; margin-right: 2px;")
        count_inner_frame = QFrame()
        count_inner_frame.setFrameShape(QFrame.Shape.StyledPanel)
        count_inner_frame.setStyleSheet("QFrame { border: 1.5px solid #888; border-radius: 6px; background: #232323; }")
        count_inner_hbox = QHBoxLayout()
        count_inner_hbox.setContentsMargins(6, 2, 6, 2)
        count_inner_hbox.setSpacing(0)
        count_edit = QLineEdit()
        count_edit.setPlaceholderText("z.B. 1")
        count_edit.setFixedWidth(60)
        count_edit.setText("1")
        count_edit.setStyleSheet("QLineEdit { font-size: 18px; font-weight: 600; border: none; background: transparent; color: #cccccc; min-width: 0; max-width: 60px; padding: 0 0; }")
        count_inner_hbox.addWidget(count_edit)
        count_inner_frame.setLayout(count_inner_hbox)
        count_inner_frame.setFixedHeight(32)
        count_row.addWidget(count_label)
        count_row.addWidget(count_inner_frame)
        count_row.addSpacing(2)
        count_widget = QWidget()
        count_widget.setLayout(count_row)
        count_widget.setContentsMargins(0, 8, 0, 8)
        count_widget.setStyleSheet("")

        # --- Kaufpreis Label + Eingabefeld: Label normal, Eingabebox mit grauem Rahmen, kleiner und mehr Abstand ---
        purchase_price_row = QHBoxLayout()
        purchase_price_row.setContentsMargins(0, 0, 0, 0)
        purchase_price_row.setSpacing(8)
        purchase_price_label = QLabel("Kaufpreis:")
        purchase_price_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #cccccc; margin-right: 2px;")
        # Eingabebox in eigenem kleinen Rahmen
        purchase_price_inner_frame = QFrame()
        purchase_price_inner_frame.setFrameShape(QFrame.Shape.StyledPanel)
        purchase_price_inner_frame.setStyleSheet("QFrame { border: 1.5px solid #888; border-radius: 6px; background: #232323; }")
        purchase_price_inner_hbox = QHBoxLayout()
        purchase_price_inner_hbox.setContentsMargins(6, 2, 6, 2)
        purchase_price_inner_hbox.setSpacing(0)
        purchase_price_edit = QLineEdit()
        purchase_price_edit.setPlaceholderText("z.B. 2.50")
        purchase_price_edit.setFixedWidth(90)
        purchase_price_edit.setStyleSheet("QLineEdit { font-size: 18px; font-weight: 600; border: none; background: transparent; color: #cccccc; min-width: 0; max-width: 90px; padding: 0 0; }")
        purchase_price_inner_hbox.addWidget(purchase_price_edit)
        purchase_price_inner_frame.setLayout(purchase_price_inner_hbox)
        purchase_price_inner_frame.setFixedHeight(32)
        purchase_price_row.addWidget(purchase_price_label)
        purchase_price_row.addWidget(purchase_price_inner_frame)
        purchase_price_row.addSpacing(2)
        purchase_price_widget = QWidget()
        purchase_price_widget.setLayout(purchase_price_row)
        purchase_price_widget.setContentsMargins(0, 8, 0, 8)
        purchase_price_widget.setStyleSheet("")

        # Hinzufügen Button
        add_button = QPushButton("Hinzufügen")
        add_button.setStyleSheet('''
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: 1.5px solid #4caf50;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 18px;
                font-weight: 600;
                min-width: 100px;
                min-height: 38px;
            }
            QPushButton:hover {
                background-color: #43a047;
            }
            QPushButton:pressed {
                background-color: #388e3c;
            }
        ''')
        add_button.clicked.connect(add_to_collection)

        # Sammlungen laden
        if os.path.exists("collections.json"):
            with open("collections.json", "r", encoding="utf-8") as f:
                collections = json.load(f)
                for c in collections:
                    collection_selector.addItem(c["name"])

        control_row.addWidget(collection_selector)
        control_row.addWidget(language_selector)
        control_row.addWidget(variant_selector)
        control_row.addWidget(proxy_checkbox)
        control_row.addWidget(count_widget)
        control_row.addWidget(purchase_price_widget)
        control_row.addWidget(add_button)
        # Kein Stretch im inneren Layout, damit Controls kompakt bleiben

        control_widget = QWidget()
        control_widget.setLayout(control_row)
        outer_center_row.addWidget(control_widget)
        outer_center_row.addStretch(1)
        outer_center_widget = QWidget()
        outer_center_widget.setLayout(outer_center_row)
        self.result_area.addWidget(outer_center_widget)