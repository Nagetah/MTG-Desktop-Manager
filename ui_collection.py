
# ui_collection.py
#
# Sammlung-Viewer-UI für den MTG Desktop Manager
#
# Dieses Modul zeigt die grafische Oberfläche für eine Kartensammlung.
# Hier werden Kartenbilder, Infos, Editier- und Löschfunktionen sowie die Bildanzeige im Dialog umgesetzt.
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGroupBox, QStackedWidget, QComboBox, QCheckBox, QMessageBox, QFrame, QSizePolicy, QDialog, QLineEdit
)
from dialogs import VariantSelector  # Dialog zum Auswählen von Kartenvarianten
from utils import get_cached_image   # Hilfsfunktion zum Laden/Cachen von Kartenbildern
from PyQt6.QtGui import QPixmap      # Für Bilder
from PyQt6.QtCore import Qt         # Für Ausrichtungen und Flags
import os
import json
from urllib.parse import quote       # Für evtl. URL-Encoding



##
# Hilfsfunktion: Sucht im Widget-Baum nach einem Eltern-Widget mit bestimmtem Attribut oder Typ.
# Praktisch, um z.B. den QStackedWidget oder ein Widget mit bestimmter Methode zu finden.
# Gibt das gefundene Eltern-Widget zurück oder None, falls nicht gefunden.
def find_parent_with_attr(widget, attr_name=None, widget_type=None):
    parent = widget.parent()
    while parent:
        if attr_name and hasattr(parent, attr_name):
            return parent
        if widget_type and isinstance(parent, widget_type):
            return parent
        parent = parent.parent()
    return None

##
# ClickableLabel: Ein QLabel, das auf Klick ein großes Kartenbild im Dialog anzeigt.
# Unterstützt auch doppelseitige Karten (DFC/Flip) und zeigt alle Bilder nebeneinander an.
class ClickableLabel(QLabel):
    def __init__(self, img_path=None, card=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.img_path = img_path
        self.card = card

    def mousePressEvent(self, event):
        # Diese Methode wird aufgerufen, wenn auf das Bild geklickt wird.
        # Sie öffnet einen Dialog und zeigt das Kartenbild (oder mehrere Bilder) groß an.
        dlg = QDialog(self)
        dlg.setWindowTitle("Kartenbild(er)")
        layout = QVBoxLayout()
        hbox = QHBoxLayout()
        images = []  # Hier werden die Bildpfade gesammelt, die angezeigt werden sollen

        # Hilfsfunktion: Sucht das beste verfügbare Bild (groß, normal, klein)
        def get_best_img_path(image_uris, face, card):
            if isinstance(image_uris, dict):
                for key in ["large", "normal", "small"]:
                    if image_uris.get(key):
                        return get_cached_image(image_uris[key], face.get('id') if face else card.get('id'), fallback_name=face.get('name') if face else card.get('name'), fallback_set=card.get('set_code') or card.get('set'))
            elif isinstance(image_uris, str):
                return get_cached_image(image_uris, face.get('id') if face else card.get('id'), fallback_name=face.get('name') if face else card.get('name'), fallback_set=card.get('set_code') or card.get('set'))
            return None

        # Prüfe, ob die Karte mehrere Seiten (Faces) hat (z.B. doppelseitige Karten)
        # Wenn ja, sammle für jede Seite das Bild, sonst nur das Einzelbild
        if self.card and self.card.get("card_faces") and isinstance(self.card["card_faces"], list) and len(self.card["card_faces"]) > 1:
            for face in self.card["card_faces"]:
                image_uris = face.get("image_uris")
                img_path = get_best_img_path(image_uris, face, self.card)
                if img_path and os.path.exists(img_path):
                    images.append(img_path)
        elif self.img_path and os.path.exists(self.img_path):
            images.append(self.img_path)

        # Wenn mindestens ein Bild gefunden wurde, zeige alle Bilder nebeneinander im Dialog an
        if images:
            for path in images:
                label = QLabel()
                pix = QPixmap(path)
                # Skaliere das Bild auf eine große Ansicht (z.B. 460x640)
                pix = pix.scaled(460, 640, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                label.setPixmap(pix)
                hbox.addWidget(label)
            hbox.setSpacing(24)  # Abstand zwischen den Bildern
            hbox.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            layout.addLayout(hbox)
            dlg.setLayout(layout)
            # Passe die Mindestgröße des Dialogs an die Anzahl der Bilder an
            min_width = 500 * len(images) + 40
            dlg.setMinimumWidth(min_width)
            dlg.setMinimumHeight(700)
            dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            dlg.show()  # Nicht-modal öffnen

import matplotlib
matplotlib.use('Agg')  # Kein GUI-Backend nötig
import matplotlib.pyplot as plt
import io
from PyQt6.QtGui import QImage

class CollectionViewer(QWidget):
    def _build_card_widgets(self, grid, cards):
        print(f"[DEBUG] _build_card_widgets: {len(cards)} Karten werden gebaut.")
        for idx, card in enumerate(cards):
            print(f"[DEBUG]   Karte {idx+1}: {card.get('name','?')}")

        # --- Funktionsdefinitionen müssen VOR der Verwendung im Lambda stehen! ---
        def delete_card(card_obj, card_name):
            print(f"[DEBUG] delete_card aufgerufen für: {card_name} (Objekt: {card_obj})")
            reply = QMessageBox.question(self, "Karte löschen", f"Möchtest du '{card_name}' wirklich aus der Sammlung entfernen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    with open("collections.json", "r", encoding="utf-8") as f:
                        collections = json.load(f)
                    for c in collections:
                        if c['name'] == self.collection['name']:
                            print(f"[DEBUG] Karten vor dem Löschen: {len(c['cards'])}")
                            for idx_del, card_entry in enumerate(c['cards']):
                                if isinstance(card_entry, dict) and all(card_entry.get(k) == card_obj.get(k) for k in ['id', 'lang', 'is_proxy', 'collector_number', 'set_code']):
                                    del c['cards'][idx_del]
                                    print(f"[DEBUG] Karte entfernt an Index {idx_del}")
                                    break
                            print(f"[DEBUG] Karten nach dem Löschen: {len(c['cards'])}")
                            break
                    with open("collections.json", "w", encoding="utf-8") as f:
                        json.dump(collections, f, indent=2, ensure_ascii=False)
                    print("[DEBUG] collections.json wurde aktualisiert.")
                    # Nach dem Löschen: Ansicht neu laden
                    updated_collection = None
                    for c in collections:
                        if c['name'] == self.collection['name']:
                            updated_collection = c
                            break
                    stack = self.stack_widget or find_parent_with_attr(self, widget_type=QStackedWidget)
                    if stack and updated_collection:
                        idx = stack.indexOf(self)
                        stack.removeWidget(self)
                        self.deleteLater()
                        new_viewer = CollectionViewer(updated_collection, self.return_to_menu, stack_widget=stack)
                        stack.insertWidget(idx, new_viewer)
                        stack.setCurrentWidget(new_viewer)
                        print("[DEBUG] CollectionViewer wurde neu geladen.")
                except Exception as e:
                    QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen der Karte: {e}")

        def open_edit_dialog(card_obj):
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QMessageBox
            from PyQt6.QtCore import QTimer
            from PyQt6.QtGui import QPixmap
            # Bild vorab cachen
            def pre_cache_image(card_data):
                if card_data.get("card_faces") and isinstance(card_data["card_faces"], list):
                    face = card_data["card_faces"][0]
                    img_url = face.get("image_uris", {}).get("large")
                    if img_url:
                        get_cached_image(img_url, face.get('id'), fallback_name=face.get('name'), fallback_set=card_data.get('set_code') or card_data.get('set'))
                else:
                    img_url = card_data.get("image_uris", {}).get("large")
                    if img_url:
                        get_cached_image(img_url, card_data.get('id'), fallback_name=card_data.get('name'), fallback_set=card_data.get('set_code') or card_data.get('set'))
            pre_cache_image(card_obj)

            edit_dialog = QDialog(self)
            edit_dialog.setWindowTitle(f"Karte bearbeiten: {card_obj.get('name','')}")
            edit_dialog.setMinimumWidth(480)
            layout = QVBoxLayout()
            name_label = QLabel(f"<b>{card_obj.get('name','')}</b>")
            name_label.setStyleSheet("font-size: 24px; font-weight: bold;")
            layout.addWidget(name_label)
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            def update_image(card_data, retry=True):
                image_uris = None
                img_path = None
                fallback_set = card_data.get('set_code') or card_data.get('set')
                if card_data.get("card_faces") and isinstance(card_data["card_faces"], list):
                    face = card_data["card_faces"][0]
                    image_uris = face.get("image_uris")
                    img_path = get_cached_image(
                        image_uris,
                        face.get('id'),
                        fallback_name=face.get('name'),
                        fallback_set=fallback_set
                    )
                elif card_data.get("image_uris"):
                    image_uris = card_data.get("image_uris")
                    img_path = get_cached_image(
                        image_uris,
                        card_data.get('id'),
                        fallback_name=card_data.get('name'),
                        fallback_set=fallback_set
                    )
                else:
                    image_uris = card_data.get("image_url")
                    img_path = get_cached_image(
                        image_uris,
                        card_data.get('id'),
                        fallback_name=card_data.get('name'),
                        fallback_set=fallback_set
                    )
                if img_path and os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    pixmap = pixmap.scaled(180, 255, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    image_label.setPixmap(pixmap)
                    image_label.setText("")
                else:
                    image_label.setPixmap(QPixmap())
                    image_label.setText("Kein Bild")
                    if retry:
                        QTimer.singleShot(400, lambda: update_image(card_data, retry=False))
            update_image(card_obj)
            layout.addWidget(image_label)

            # --- Info-Schema (oben, wie in der Übersicht) ---
            def build_info_line(card):
                mana_cost = card.get('mana_cost', '')
                if not mana_cost and card.get('card_faces') and isinstance(card['card_faces'], list) and len(card['card_faces']) > 0:
                    faces = card['card_faces']
                    mana_costs = [f.get('mana_cost', '') for f in faces if f.get('mana_cost')]
                    mana_costs_clean = [mc.replace('{', '').replace('}', '') for mc in mana_costs if mc]
                    mana_cost_clean = ' // '.join(mana_costs_clean) if mana_costs_clean else ''
                else:
                    mana_cost_clean = mana_cost.replace('{', '').replace('}', '') if mana_cost else ''
                set_name = card.get('set') or card.get('set_name', '')
                set_code = card.get('set_code') or card.get('set') or ''
                set_code_disp = set_code.upper()[:3] if set_code else ''
                set_size = card.get('set_size')
                collector_number = card.get('collector_number', '')
                # Versuche set_size nachzuladen, falls nicht vorhanden
                if (not set_size or set_size == '?') and set_code:
                    try:
                        import requests
                        set_api_url = f"https://api.scryfall.com/sets/{set_code}"
                        resp = requests.get(set_api_url, timeout=3)
                        if resp.status_code == 200:
                            set_data = resp.json()
                            set_size = set_data.get("card_count", '')
                            card['set_size'] = set_size
                    except Exception:
                        set_size = ''
                info_line = []
                if mana_cost_clean:
                    info_line.append(f"Manakosten: {mana_cost_clean}")
                if set_name:
                    info_line.append(str(set_name))
                if set_code_disp or collector_number:
                    fin_str = f"{set_code_disp} {collector_number}/{set_size}" if set_code_disp and collector_number and set_size else ''
                    if fin_str:
                        info_line.append(fin_str)
                return " | ".join(info_line)

            info_label = QLabel(build_info_line(card_obj))
            info_label.setStyleSheet("font-size: 16px; margin-bottom: 8px;")
            layout.addWidget(info_label)

            # --- Sprache ---
            lang_row = QHBoxLayout()
            lang_label = QLabel("Sprache:")
            lang_combo = QComboBox()
            languages = ["de", "en", "fr", "it", "es", "pt", "ja", "ko", "ru", "zhs", "zht"]
            lang_combo.addItems(languages)
            if card_obj.get("lang") in languages:
                lang_combo.setCurrentText(card_obj.get("lang"))
            lang_row.addWidget(lang_label)
            lang_row.addWidget(lang_combo)
            layout.addLayout(lang_row)


            # --- Foil/Nonfoil Dropdown ---
            foil_row = QHBoxLayout()
            foil_label = QLabel("Variante:")
            foil_combo = QComboBox()
            finishes = card_obj.get('finishes', [])
            prices = card_obj.get('prices', {})
            foil_options = []
            # Always add nonfoil if available
            if 'nonfoil' in finishes or prices.get('eur'):
                foil_combo.addItem("Nonfoil", ('nonfoil', prices.get('eur')))
                foil_options.append('nonfoil')
            # Add foil if available
            if 'foil' in finishes or prices.get('eur_foil'):
                foil_combo.addItem("Foil", ('foil', prices.get('eur_foil')))
                foil_options.append('foil')
            # Add etched if available
            if 'etched' in finishes or prices.get('eur_etched'):
                foil_combo.addItem("Etched", ('etched', prices.get('eur_etched')))
                foil_options.append('etched')
            # Add gilded if available
            if 'gilded' in finishes or prices.get('eur_gilded'):
                foil_combo.addItem("Gilded", ('gilded', prices.get('eur_gilded')))
                foil_options.append('gilded')
            # Set current index based on card_obj["variant"] if present
            if card_obj.get('variant') in foil_options:
                foil_combo.setCurrentIndex(foil_options.index(card_obj.get('variant')))
            foil_row.addWidget(foil_label)
            foil_row.addWidget(foil_combo)
            layout.addLayout(foil_row)

            # --- Proxy-Status (exakt wie Optionsleiste in ui_search.py) ---
            proxy_checkbox = QCheckBox("Proxy")
            proxy_checkbox.setChecked(bool(card_obj.get("is_proxy")))
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
            proxy_row = QHBoxLayout()
            proxy_row.setContentsMargins(0,0,0,0)
            proxy_row.setSpacing(0)
            proxy_row.addWidget(proxy_checkbox)
            proxy_row.addStretch(1)
            layout.addLayout(proxy_row)


            # --- Kaufpreis (dynamisch, je nach Foil/Nonfoil) ---
            price_row = QHBoxLayout()
            price_label = QLabel("Kaufpreis (€):")
            from PyQt6.QtWidgets import QLineEdit
            price_edit = QLineEdit()
            price_edit.setPlaceholderText("z.B. 2.50")
            # Set initial price based on variant selection
            def set_price_from_variant():
                variant_key, variant_price = foil_combo.currentData()
                if variant_price not in (None, '', '0', 0):
                    price_edit.setText(str(variant_price))
                else:
                    price_edit.setText("")
            set_price_from_variant()
            foil_combo.currentIndexChanged.connect(set_price_from_variant)
            # If card_obj has explicit purchase_price, prefer that
            if card_obj.get("purchase_price") not in (None, '', '0', 0):
                price_edit.setText(str(card_obj.get("purchase_price")))
            price_row.addWidget(price_label)
            price_row.addWidget(price_edit)
            layout.addLayout(price_row)


            # --- Varianten-Button ---
            variant_row = QHBoxLayout()
            variant_btn = QPushButton("Variante wählen ...")
            variant_row.addWidget(variant_btn)
            layout.addLayout(variant_row)

            # --- Speichern-Button ---
            save_btn = QPushButton("Speichern")
            save_btn.setStyleSheet('''
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: 1.5px solid #388e3c;
                    border-radius: 8px;
                    padding: 8px 24px;
                    min-width: 100px;
                    min-height: 38px;
                    font-size: 18px;
                    font-weight: 600;
                    margin-top: 18px;
                    letter-spacing: 0.5px;
                }
                QPushButton:hover {
                    background-color: #43a047;
                    border: 1.5px solid #66bb6a;
                }
                QPushButton:pressed {
                    background-color: #388e3c;
                    border: 1.5px solid #2e7031;
                }
            ''')
            layout.addWidget(save_btn)

            edit_dialog.setLayout(layout)

            # --- Dynamik: Felder aktualisieren bei Variantenwahl ---
            # Merke die ursprünglichen Identifikationsdaten der Karte
            original_keys = {k: card_obj.get(k) for k in ['id', 'lang', 'is_proxy', 'collector_number', 'set_code']}


            def update_fields(new_card):
                # Übernehme alle relevanten Felder, auch eur, set_size etc.
                # Set-Code aus Scryfall übernehmen, falls vorhanden
                if 'set' in new_card:
                    new_card['set_code'] = new_card['set']
                # set_size ggf. nachladen
                if not new_card.get('set_size') and new_card.get('set_code'):
                    try:
                        import requests
                        set_api_url = f"https://api.scryfall.com/sets/{new_card.get('set_code')}"
                        resp = requests.get(set_api_url, timeout=3)
                        if resp.status_code == 200:
                            set_data = resp.json()
                            new_card['set_size'] = set_data.get("card_count", '')
                    except Exception:
                        pass
                # Marktwert (eur) aus prices['eur'] übernehmen, falls vorhanden
                if 'prices' in new_card and isinstance(new_card['prices'], dict):
                    eur_val = new_card['prices'].get('eur')
                    if eur_val not in (None, '', '0', 0):
                        new_card['eur'] = eur_val
                # Fallback: eur von alter Karte übernehmen, falls in neuer nicht vorhanden
                if not new_card.get('eur') and card_obj.get('eur'):
                    new_card['eur'] = card_obj.get('eur')
                name_label.setText(f"<b>{new_card.get('name','')}")
                info_label.setText(build_info_line(new_card))
                lang_combo.setCurrentText(new_card.get("lang", "en"))
                proxy_checkbox.setChecked(bool(new_card.get("is_proxy")))
                # Update foil_combo and price_edit
                # Update foil_combo options
                finishes = new_card.get('finishes', [])
                prices = new_card.get('prices', {})
                foil_combo.blockSignals(True)
                foil_combo.clear()
                foil_options = []
                if 'nonfoil' in finishes or prices.get('eur'):
                    foil_combo.addItem("Nonfoil", ('nonfoil', prices.get('eur')))
                    foil_options.append('nonfoil')
                if 'foil' in finishes or prices.get('eur_foil'):
                    foil_combo.addItem("Foil", ('foil', prices.get('eur_foil')))
                    foil_options.append('foil')
                if 'etched' in finishes or prices.get('eur_etched'):
                    foil_combo.addItem("Etched", ('etched', prices.get('eur_etched')))
                    foil_options.append('etched')
                if 'gilded' in finishes or prices.get('eur_gilded'):
                    foil_combo.addItem("Gilded", ('gilded', prices.get('eur_gilded')))
                    foil_options.append('gilded')
                # Set current index based on new_card["variant"] if present
                if new_card.get('variant') in foil_options:
                    foil_combo.setCurrentIndex(foil_options.index(new_card.get('variant')))
                else:
                    foil_combo.setCurrentIndex(0)
                foil_combo.blockSignals(False)
                # Update price_edit
                def set_price_from_variant():
                    variant_key, variant_price = foil_combo.currentData()
                    if variant_price not in (None, '', '0', 0):
                        price_edit.setText(str(variant_price))
                    else:
                        price_edit.setText("")
                set_price_from_variant()
                foil_combo.currentIndexChanged.connect(set_price_from_variant)
                # If new_card has explicit purchase_price, prefer that
                if new_card.get("purchase_price") not in (None, '', '0', 0):
                    price_edit.setText(str(new_card.get("purchase_price")))
                update_image(new_card)
                card_obj.clear()
                card_obj.update(new_card)


            def choose_variant():
                prints_url = card_obj.get('prints_search_uri')
                if not prints_url:
                    QMessageBox.warning(self, "Fehler", "Für diese Karte ist keine Varianten-URL hinterlegt.")
                    return
                def on_variant_selected(new_card):
                    if new_card:
                        update_fields(new_card)
                dlg = VariantSelector(prints_url, on_variant_selected)
                dlg.exec()
            variant_btn.clicked.connect(choose_variant)


            def save_changes():
                try:
                    with open("collections.json", "r", encoding="utf-8") as f:
                        collections = json.load(f)
                    for c in collections:
                        if c['name'] == self.collection['name']:
                            for idx_card, card in enumerate(c['cards']):
                                if isinstance(card, dict) and all(card.get(k) == original_keys.get(k) for k in ['id', 'lang', 'is_proxy', 'collector_number', 'set_code']):
                                    # Übernehme alle Felder aus card_obj (nach Variantenwahl und Edit)
                                    new_card = dict(card_obj)
                                    new_card['lang'] = lang_combo.currentText()
                                    new_card['is_proxy'] = proxy_checkbox.isChecked()
                                    # Speichere die gewählte Variante
                                    variant_key, variant_price = foil_combo.currentData()
                                    new_card['variant'] = variant_key
                                    # Setze den Marktwert (eur) auf den Preis der gewählten Variante
                                    if variant_price not in (None, '', '0', 0):
                                        new_card['eur'] = variant_price
                                    else:
                                        new_card['eur'] = ''
                                    try:
                                        new_card['purchase_price'] = float(price_edit.text().replace(",", "."))
                                    except Exception:
                                        new_card['purchase_price'] = price_edit.text()
                                    c['cards'][idx_card] = new_card
                                    break
                            break
                    with open("collections.json", "w", encoding="utf-8") as f:
                        json.dump(collections, f, indent=2, ensure_ascii=False)
                    edit_dialog.accept()
                    # Nach dem Editieren: Ansicht neu laden
                    updated_collection = None
                    for c in collections:
                        if c['name'] == self.collection['name']:
                            updated_collection = c
                            break
                    stack = self.stack_widget or find_parent_with_attr(self, widget_type=QStackedWidget)
                    if stack and updated_collection:
                        idx = stack.indexOf(self)
                        stack.removeWidget(self)
                        self.deleteLater()
                        new_viewer = CollectionViewer(updated_collection, self.return_to_menu, stack_widget=stack)
                        stack.insertWidget(idx, new_viewer)
                        stack.setCurrentWidget(new_viewer)
                except Exception as e:
                    QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {e}")

            save_btn.clicked.connect(save_changes)
            edit_dialog.exec()

        # Komplette Kartenlisten-Logik wie im Original (inkl. Buttons, Oracle-Text, Trennlinien)
        for idx, card in enumerate(cards):
            group = QGroupBox()
            group.setStyleSheet("QGroupBox { border: 1px solid #444; border-radius: 6px; margin-top: 8px; margin-bottom: 8px; padding: 8px; }")
            hbox = QHBoxLayout()
            hbox.setSpacing(18)
            image_uris = None
            if card.get("card_faces") and isinstance(card["card_faces"], list):
                image_uris = card["card_faces"][0].get("image_uris")
            elif card.get("image_uris"):
                image_uris = card["image_uris"]
            else:
                image_uris = card.get("image_url")
            fallback_set = card.get('set_code') or card.get('set')
            img_path = get_cached_image(
                image_uris,
                card.get('id'),
                fallback_name=card.get('name'),
                fallback_set=fallback_set
            )
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
            # --- Info-Block (Name, Preis, Editieren, Löschen, Proxy, Oracle-Text) ---
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            name_price_row = QHBoxLayout()
            lang_disp = card.get('lang', 'en').upper()
            name_lang = f"{card['name']} - {lang_disp}"
            name_label = QLabel(name_lang)
            name_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 2px;")
            name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            name_price_row.addWidget(name_label)
            eur = card.get('eur')
            purchase_price = card.get('purchase_price')
            if card.get('is_proxy'):
                price_str = "0 €"
            else:
                price_str = f"{eur} €" if eur not in (None, '', 'Nicht verfügbar', 0, '0') else "- €"
            # FOIL-Label, wenn Variante foil
            foil_str = ""
            if card.get('variant') == 'foil':
                foil_str = " <span style='color:#ffd700; font-weight:bold;'>FOIL</span>"
            price_label = QLabel(f"| {price_str}{foil_str}")
            price_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffd700; margin-bottom: 2px; margin-left: 8px;")
            price_label.setTextFormat(Qt.TextFormat.RichText)
            price_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            name_price_row.addWidget(price_label)
            if purchase_price is not None:
                try:
                    eur_f = float(eur) if eur not in (None, '', 'Nicht verfügbar', 0, '0') else 0
                    kauf_f = float(purchase_price)
                    diff = eur_f - kauf_f
                    if diff > 0:
                        color = '#4caf50'
                    elif diff < 0:
                        color = '#e53935'
                    else:
                        color = '#cccccc'
                    kaufwert_label = QLabel(f"Kaufwert: {kauf_f:.2f} €")
                    kaufwert_label.setStyleSheet(f"font-size: 16px; font-weight: 500; margin-left: 12px; color: {color};")
                    kaufwert_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    name_price_row.addWidget(kaufwert_label)
                except Exception:
                    pass
            name_price_row.addStretch(1)
            # --- Mülleimer-Button (Karte löschen) ---
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
            del_btn.clicked.connect(lambda _, cobj=card, cname=card.get('name', '?'): delete_card(cobj, cname))
            # --- Editier-Button (Karte bearbeiten) ---
            edit_btn = QPushButton()
            edit_btn.setFixedSize(24, 24)
            edit_btn.setStyleSheet('''
                QPushButton {
                    border: none;
                    background: transparent;
                    min-width: 24px; min-height: 24px; max-width: 24px; max-height: 24px;
                    padding: 0;
                    color: #4caf50;
                    font-size: 22px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #ddffdd;
                    border-radius: 6px;
                }
            ''')
            edit_btn.setText('✎')
            edit_btn.clicked.connect(lambda _, cobj=card: open_edit_dialog(cobj))
            name_price_row.addWidget(edit_btn)
            name_price_row.addWidget(del_btn)
            info_layout.addLayout(name_price_row)
            # --- Kompakte Infozeile: Manakosten | Setname | SETCODE FIN Nummer/Setgröße ---
            mana_cost = card.get('mana_cost', '')
            if not mana_cost and card.get('card_faces') and isinstance(card['card_faces'], list) and len(card['card_faces']) > 0:
                faces = card['card_faces']
                mana_costs = [f.get('mana_cost', '') for f in faces if f.get('mana_cost')]
                mana_costs_clean = [mc.replace('{', '').replace('}', '') for mc in mana_costs if mc]
                mana_cost_clean = ' // '.join(mana_costs_clean) if mana_costs_clean else ''
            else:
                mana_cost_clean = mana_cost.replace('{', '').replace('}', '') if mana_cost else ''
            set_name = card.get('set') or card.get('set_name', '')
            set_code = card.get('set_code') or card.get('set') or ''
            set_code_disp = set_code.upper()[:3] if set_code else '?'
            set_size = card.get('set_size', '?')
            collector_number = card.get('collector_number', '?')
            info_line = []
            if mana_cost_clean:
                info_line.append(f"Manakosten: {mana_cost_clean}")
            if set_name:
                info_line.append(str(set_name))
            if set_code_disp or collector_number:
                info_line.append(f"{set_code_disp} {collector_number}/{set_size}")
            if info_line:
                info_label = QLabel(" | ".join(info_line))
                info_label.setStyleSheet("font-size: 15px; margin-bottom: 4px;")
                info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                info_layout.addWidget(info_label)
            if card.get('is_proxy'):
                proxy_label = QLabel("Proxy: Ja")
                proxy_label.setStyleSheet("font-size: 15px; color: #ff8888;")
                proxy_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                info_layout.addWidget(proxy_label)
            info_widget = QWidget()
            info_widget.setLayout(info_layout)
            # --- Oracle-Text (Regeltext) ---
            if card.get('card_faces') and isinstance(card['card_faces'], list) and len(card['card_faces']) > 1:
                oracle_texts = []
                for face in card['card_faces']:
                    face_type = face.get('type_line', '')
                    face_text = face.get('oracle_text', '')
                    block = ''
                    if face_type:
                        block += f"<b>{face_type}</b><br>"
                    if face_text:
                        block += face_text
                    if block:
                        oracle_texts.append(block)
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
                oracle_type = card.get('type_line', '')
                oracle_text = card.get('oracle_text', '')
                oracle_frame = QFrame()
                oracle_frame.setStyleSheet("background-color: #292f3a; border-radius: 6px; padding: 8px; margin-top: 6px; margin-bottom: 2px;")
                oracle_layout = QVBoxLayout()
                oracle_html = ''
                if oracle_type:
                    oracle_html += f"<b>{oracle_type}</b>"
                if oracle_text:
                    oracle_html += f"<br>{oracle_text}"
                oracle_label = QLabel(oracle_html)
                oracle_label.setStyleSheet("color: #fff; font-size: 15px;")
                oracle_label.setWordWrap(True)
                oracle_label.setTextFormat(Qt.TextFormat.RichText)
                oracle_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                oracle_layout.addWidget(oracle_label)
                oracle_frame.setLayout(oracle_layout)
                info_layout.addWidget(oracle_frame)
            hbox.addWidget(image_label)
            hbox.addWidget(info_widget, 1)
            group.setLayout(hbox)
            grid.addWidget(group)
            if idx < len(cards) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                line.setStyleSheet("color: #444;")
                grid.addWidget(line)
    def _refresh_card_list(self):
        print("[DEBUG] _refresh_card_list aufgerufen")
        # Diese Methode baut die Kartenliste nach Filter/Sortierung neu auf
        # Sie wird von Suchfeld und Sort-Dropdown getriggert
        # Die Logik ist identisch zum Kartenlisten-Aufbau im Konstruktor
        # --- Kartenliste aufbauen (mit Filter & Sortierung) ---
        # Finde das Layout für die Kartenliste
        scroll_area = None
        for child in self.findChildren(QScrollArea):
            scroll_area = child
            break
        if not scroll_area:
            return
        content = scroll_area.widget()
        if not content:
            return
        grid = content.layout()
        if not grid:
            return
        search_text = self.search_field.text().strip().lower() if hasattr(self, 'search_field') else ""
        sort_mode = self.sort_dropdown.currentText() if hasattr(self, 'sort_dropdown') else "Name (A-Z)"
        filtered_cards = [c for c in self.collection["cards"] if isinstance(c, dict) and search_text in c.get('name','').lower()]
        if sort_mode == "Name (A-Z)":
            filtered_cards.sort(key=lambda c: c.get('name','').lower())
        elif sort_mode == "Name (Z-A)":
            filtered_cards.sort(key=lambda c: c.get('name','').lower(), reverse=True)

        print(f"[DEBUG] _refresh_card_list: {len(filtered_cards)} Karten nach Filter/Suche")
        for idx, card in enumerate(filtered_cards):
            print(f"[DEBUG]   Karte {idx+1}: {card.get('name','?')}")

        # Vorherigen Inhalt leeren (Widgets entfernen)
        for i in reversed(range(grid.count())):
            item = grid.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        self._build_card_widgets(grid, filtered_cards)
    # Entfernt: doppelte __init__ mit self.card_grid = grid (war fehlerhaft und hat das Layout zerstört)

    def import_deck_text(self):
        """
        Öffnet einen Dialog, in den der Nutzer eine Deckliste (Text) einfügen kann. Importiert Karten per Scryfall.
        """
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QMessageBox, QLabel
        import requests
        import re
        dlg = QDialog(self)
        dlg.setWindowTitle("Deck importieren")
        dlg.setMinimumWidth(480)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Füge hier deine Deckliste ein (z.B. aus Moxfield, Archidekt, etc.):"))
        textedit = QTextEdit()
        textedit.setPlaceholderText("z.B.\n4 Lightning Bolt\n2 Mountain\n...")
        layout.addWidget(textedit)
        import_btn = QPushButton("Import starten")
        layout.addWidget(import_btn)
        dlg.setLayout(layout)


        def do_import():
            lines = textedit.toPlainText().splitlines()
            cards = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                m = re.match(r"(\d+)[xX]?\s+(.+)", line)
                if not m:
                    continue
                qty = int(m.group(1))
                rest = m.group(2).strip()
                # Extrahiere Set-Code und Nummer, falls vorhanden
                set_match = re.match(r"(.+?)\s*\(([^)]+)\)\s*([\w-]+)?", rest)
                if set_match:
                    name = set_match.group(1).strip()
                    set_code = set_match.group(2).strip()
                    collector_number = set_match.group(3).strip() if set_match.group(3) else None
                else:
                    name = rest
                    set_code = None
                    collector_number = None
                try:
                    if set_code and collector_number:
                        scry_url = f"https://api.scryfall.com/cards/{set_code.lower()}/{collector_number}"
                        scry_resp = requests.get(scry_url, timeout=6)
                        if scry_resp.status_code != 200:
                            scry_url = f"https://api.scryfall.com/cards/named?exact={requests.utils.quote(name)}"
                            scry_resp = requests.get(scry_url, timeout=6)
                    elif set_code:
                        scry_url = f"https://api.scryfall.com/cards/named?exact={requests.utils.quote(name)}&set={set_code.lower()}"
                        scry_resp = requests.get(scry_url, timeout=6)
                        if scry_resp.status_code != 200:
                            scry_url = f"https://api.scryfall.com/cards/named?exact={requests.utils.quote(name)}"
                            scry_resp = requests.get(scry_url, timeout=6)
                    else:
                        scry_url = f"https://api.scryfall.com/cards/named?exact={requests.utils.quote(name)}"
                        scry_resp = requests.get(scry_url, timeout=6)
                    if scry_resp.status_code != 200:
                        continue
                    scry_card = scry_resp.json()
                except Exception:
                    continue
                # --- Normalize card entry as in add_to_collection ---
                # Variant detection (foil/nonfoil) - fallback to 'nonfoil' if not found
                variant = 'nonfoil'
                if scry_card.get('foil') and not scry_card.get('nonfoil'):
                    variant = 'foil'
                # Best image URL (large > normal > small)
                best_image_url = None
                if scry_card.get("card_faces") and isinstance(scry_card["card_faces"], list):
                    face = scry_card["card_faces"][0]
                    image_uris_face = face.get("image_uris")
                    if image_uris_face:
                        for key in ["large", "normal", "small"]:
                            if image_uris_face.get(key):
                                best_image_url = image_uris_face[key]
                                break
                else:
                    image_uris = scry_card.get("image_uris")
                    if isinstance(image_uris, dict):
                        for key in ["large", "normal", "small"]:
                            if image_uris.get(key):
                                best_image_url = image_uris[key]
                                break
                    elif isinstance(image_uris, str):
                        best_image_url = image_uris
                # Set size
                set_code_val = scry_card.get("set") or scry_card.get("set_code") or scry_card.get("set_id")
                set_size = scry_card.get("set_size")
                if not set_size and set_code_val:
                    try:
                        set_api_url = f"https://api.scryfall.com/sets/{set_code_val}"
                        resp = requests.get(set_api_url, timeout=3)
                        if resp.status_code == 200:
                            set_data = resp.json()
                            set_size = set_data.get("card_count")
                    except Exception:
                        set_size = None
                # Price (EUR)
                eur_value = scry_card.get("prices", {}).get("eur")
                # Build normalized card entry
                for _ in range(qty):
                    card_entry = dict(scry_card)
                    card_entry["lang"] = scry_card.get("lang", "en")
                    card_entry["is_proxy"] = False
                    card_entry["count"] = 1
                    card_entry["image_url"] = best_image_url
                    card_entry["eur"] = eur_value
                    card_entry["set_size"] = set_size
                    card_entry["variant"] = variant
                    card_entry["purchase_price"] = None
                    # For compatibility with collection logic
                    card_entry["set_code"] = scry_card.get("set")
                    cards.append(card_entry)
            if not cards:
                QMessageBox.warning(dlg, "Fehler", "Keine Karten im Text gefunden oder alle Karten konnten nicht erkannt werden.")
                return
            try:
                with open("collections.json", "r", encoding="utf-8") as f:
                    collections = json.load(f)
                for c in collections:
                    if c["name"] == self.collection["name"]:
                        c["cards"].extend(cards)
                        break
                with open("collections.json", "w", encoding="utf-8") as f:
                    json.dump(collections, f, indent=2, ensure_ascii=False)
                QMessageBox.information(dlg, "Import erfolgreich", f"{len(cards)} Karten wurden importiert.")
                dlg.accept()
                # Ansicht neu laden
                stack = self.stack_widget or find_parent_with_attr(self, widget_type=QStackedWidget)
                if stack:
                    idx = stack.indexOf(self)
                    stack.removeWidget(self)
                    self.deleteLater()
                    new_viewer = CollectionViewer(self.collection, self.return_to_menu, stack_widget=stack)
                    stack.insertWidget(idx, new_viewer)
                    stack.setCurrentWidget(new_viewer)
            except Exception as e:
                QMessageBox.critical(dlg, "Fehler", f"Fehler beim Hinzufügen der Karten: {e}")

        import_btn.clicked.connect(do_import)
        dlg.exec()

    def __init__(self, collection_data, return_to_menu, stack_widget=None, scroll_value=None):
        super().__init__()
        # --- Sammlung laden ---
        # Die Sammlung wird immer frisch aus der Datei geladen, damit Änderungen (z.B. Bild, Name) sofort sichtbar sind.
        self.collection = None
        if isinstance(collection_data, dict) and 'name' in collection_data:
            collection_name = collection_data['name']
            try:
                if os.path.exists("collections.json"):
                    with open("collections.json", "r", encoding="utf-8") as f:
                        collections = json.load(f)
                    # Suche die Sammlung mit passendem Namen
                    for c in collections:
                        if c['name'] == collection_name:
                            self.collection = c
                            break
                    else:
                        self.collection = collection_data
                else:
                    self.collection = collection_data
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Sammlung: {e}")
                self.collection = collection_data
        else:
            self.collection = collection_data
        self.return_to_menu = return_to_menu
        self.stack_widget = stack_widget  # QStackedWidget explizit merken (für Navigation)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        layout = QVBoxLayout()
        # (Erste Kopfzeile entfernt, damit sie nicht doppelt erscheint)

        # --- Neue Kopfzeile: Sammlungsname zentriert oben ---
        title = QLabel(f"Sammlung: {self.collection['name']}")
        title.setStyleSheet("font-size: 30px; font-weight: bold; padding: 18px 0 10px 0;")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title)

        # --- Zweite Zeile: Buttons links, Suche/Sortierung rechts ---
        bar_row = QHBoxLayout()
        # Linke Seite: Buttons
        btns_layout = QHBoxLayout()
        back_button = QPushButton("← Hauptmenü")
        back_button.clicked.connect(self.return_to_menu)
        btns_layout.addWidget(back_button)
        back_to_collections_button = QPushButton("Zurück zu Sammlungen")
        back_to_collections_button.setStyleSheet("margin-left: 10px;")
        def go_to_collections():
            parent = find_parent_with_attr(self, attr_name='show_collections')
            if parent:
                parent.show_collections()
        back_to_collections_button.clicked.connect(go_to_collections)
        btns_layout.addWidget(back_to_collections_button)
        # --- Moxfield-Import-Button ---
        import_btn = QPushButton("Deck importieren")
        import_btn.setStyleSheet("margin-left: 10px; background-color: #0078d7; color: white; font-weight: bold;")
        import_btn.clicked.connect(self.import_deck_text)
        btns_layout.addWidget(import_btn)
        # --- Deck Exportieren Button ---
        export_btn = QPushButton("Deck exportieren")
        export_btn.setStyleSheet("margin-left: 10px; background-color: #4caf50; color: white; font-weight: bold;")
        export_btn.clicked.connect(self.export_deck_text)
        btns_layout.addWidget(export_btn)
        btns_layout.addStretch(1)
        bar_row.addLayout(btns_layout, 2)
        # Rechte Seite: Suche und Sortierung
        search_sort_layout = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Nach Name suchen...")
        self.search_field.setFixedWidth(220)
        search_sort_layout.addWidget(self.search_field)
        self.sort_dropdown = QComboBox()
        self.sort_dropdown.addItems(["Name (A-Z)", "Name (Z-A)"])
        self.sort_dropdown.setFixedWidth(160)
        search_sort_layout.addWidget(self.sort_dropdown)
        search_sort_layout.addStretch(1)
        bar_row.addLayout(search_sort_layout, 1)
        layout.addLayout(bar_row)

        # Signalverbindungen für Live-Filter und Sortierung
        self.search_field.textChanged.connect(self._refresh_card_list)
        self.sort_dropdown.currentIndexChanged.connect(self._refresh_card_list)

        # --- Scrollbarer Bereich für Kartenliste ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        grid = QVBoxLayout()
        content.setLayout(grid)
        content.setMinimumWidth(400)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.setLayout(layout)

        # --- Kartenliste aufbauen ---
        search_text = self.search_field.text().strip().lower() if hasattr(self, 'search_field') else ""
        sort_mode = self.sort_dropdown.currentText() if hasattr(self, 'sort_dropdown') else "Name (A-Z)"
        filtered_cards = [c for c in self.collection["cards"] if isinstance(c, dict) and search_text in c.get('name','').lower()]
        if sort_mode == "Name (A-Z)":
            filtered_cards.sort(key=lambda c: c.get('name','').lower())
        elif sort_mode == "Name (Z-A)":
            filtered_cards.sort(key=lambda c: c.get('name','').lower(), reverse=True)
        self._build_card_widgets(grid, filtered_cards)
    def export_deck_text(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
        dlg = QDialog(self)
        dlg.setWindowTitle("Deck exportieren")
        dlg.setMinimumWidth(480)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Kopiere den Text und füge ihn z.B. in Moxfield ein:"))
        textedit = QTextEdit()
        textedit.setReadOnly(True)
        deck_text = self._generate_moxfield_deck_text()
        textedit.setText(deck_text)
        layout.addWidget(textedit)
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.setLayout(layout)
        dlg.exec()

    def _generate_moxfield_deck_text(self):
        # Zähle Karten nach Name, Set, Nummer, Foil, ggf. Doppelseiten
        from collections import Counter, defaultdict
        card_lines = []
        # Gruppiere Karten nach Name, Set, Nummer, Foil, Faces
        def card_key(card):
            # Doppelseiten: Name als 'Face1 // Face2' wenn vorhanden
            if card.get('card_faces') and isinstance(card['card_faces'], list) and len(card['card_faces']) > 1:
                name = ' // '.join([f.get('name', '') for f in card['card_faces']])
            else:
                name = card.get('name', '')
            set_code = card.get('set_code') or card.get('set') or ''
            collector_number = card.get('collector_number', '')
            foil = card.get('is_foil', False) or (str(card.get('collector_number', '')).endswith('*F*'))
            # Moxfield: Foil wird als *F* am Ende dargestellt
            return (name, set_code, collector_number, foil)
        # Zähle alle Karten
        counter = defaultdict(int)
        for card in self.collection.get('cards', []):
            key = card_key(card)
            counter[key] += 1
        for (name, set_code, collector_number, foil), qty in counter.items():
            line = f"{qty} {name}"
            if set_code:
                line += f" ({set_code.upper()})"
            if collector_number:
                line += f" {collector_number}"
            if foil:
                line += " *F*"
            card_lines.append(line)
        return '\n'.join(card_lines)
        bar_row.addLayout(btns_layout, 2)
        # Rechte Seite: Suche und Sortierung
        search_sort_layout = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Nach Name suchen...")
        self.search_field.setFixedWidth(220)
        search_sort_layout.addWidget(self.search_field)
        self.sort_dropdown = QComboBox()
        self.sort_dropdown.addItems(["Name (A-Z)", "Name (Z-A)"])
        self.sort_dropdown.setFixedWidth(160)
        search_sort_layout.addWidget(self.sort_dropdown)
        search_sort_layout.addStretch(1)
        bar_row.addLayout(search_sort_layout, 1)
        layout.addLayout(bar_row)

        # Signalverbindungen für Live-Filter und Sortierung
        self.search_field.textChanged.connect(self._refresh_card_list)
        self.sort_dropdown.currentIndexChanged.connect(self._refresh_card_list)

        # --- Kreisdiagramm entfernt ---

        # --- Scrollbarer Bereich für Kartenliste ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Style für Scrollbar (dunkel, modern)
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

        # --- Am Ende: ScrollArea und Layout verbinden ---
        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.setLayout(layout)

        # --- Kartenliste aufbauen ---
        # --- Kartenliste aufbauen (mit Filter & Sortierung) ---
        search_text = self.search_field.text().strip().lower() if hasattr(self, 'search_field') else ""
        sort_mode = self.sort_dropdown.currentText() if hasattr(self, 'sort_dropdown') else "Name (A-Z)"
        filtered_cards = [c for c in self.collection["cards"] if isinstance(c, dict) and search_text in c.get('name','').lower()]
        if sort_mode == "Name (A-Z)":
            filtered_cards.sort(key=lambda c: c.get('name','').lower())
        elif sort_mode == "Name (Z-A)":
            filtered_cards.sort(key=lambda c: c.get('name','').lower(), reverse=True)

        # Vorherigen Inhalt leeren (Widgets entfernen)
        for i in reversed(range(grid.count())):
            item = grid.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        for idx, card in enumerate(filtered_cards):
            group = QGroupBox()
            group.setStyleSheet("QGroupBox { border: 1px solid #444; border-radius: 6px; margin-top: 8px; margin-bottom: 8px; padding: 8px; }")
            # Hauptlayout für die Karte (links Bild, rechts Infos)
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
            # Bild-Label, das auf Klick das große Bild öffnet
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

            # --- Info-Block (Name, Preis, Editieren, Löschen, Proxy, Oracle-Text) ---
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            # Name + Sprache | Preis (Proxy = immer 0 €) | Kaufwert
            name_price_row = QHBoxLayout()
            lang_disp = card.get('lang', 'en').upper()
            name_lang = f"{card['name']} - {lang_disp}"
            name_label = QLabel(name_lang)
            name_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 2px;")
            name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            name_price_row.addWidget(name_label)
            eur = card.get('eur')
            purchase_price = card.get('purchase_price')
            if card.get('is_proxy'):
                price_str = "0 €"
            else:
                price_str = f"{eur} €" if eur not in (None, '', 'Nicht verfügbar', 0, '0') else "- €"
            price_label = QLabel(f"| {price_str}")
            price_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffd700; margin-bottom: 2px; margin-left: 8px;")
            price_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            name_price_row.addWidget(price_label)
            # Kaufwert anzeigen, wenn vorhanden
            if purchase_price is not None:
                try:
                    eur_f = float(eur) if eur not in (None, '', 'Nicht verfügbar', 0, '0') else 0
                    kauf_f = float(purchase_price)
                    diff = eur_f - kauf_f
                    if diff > 0:
                        color = '#4caf50'  # grün
                    elif diff < 0:
                        color = '#e53935'  # rot
                    else:
                        color = '#cccccc'  # neutral
                    kaufwert_label = QLabel(f"Kaufwert: {kauf_f:.2f} €")
                    kaufwert_label.setStyleSheet(f"font-size: 16px; font-weight: 500; margin-left: 12px; color: {color};")
                    kaufwert_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    name_price_row.addWidget(kaufwert_label)
                except Exception:
                    pass
            name_price_row.addStretch(1)
            # --- Mülleimer-Button (Karte löschen) ---
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
            # Funktion zum Löschen einer Karte aus der Sammlung
            def delete_card(card_obj, card_name):
                print(f"[DEBUG] delete_card aufgerufen für: {card_name} (Objekt: {card_obj})")
                reply = QMessageBox.question(self, "Karte löschen", f"Möchtest du '{card_name}' wirklich aus der Sammlung entfernen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        with open("collections.json", "r", encoding="utf-8") as f:
                            collections = json.load(f)
                        for c in collections:
                            if c['name'] == self.collection['name']:
                                print(f"[DEBUG] Karten vor dem Löschen: {len(c['cards'])}")
                                for idx_del, card_entry in enumerate(c['cards']):
                                    if isinstance(card_entry, dict) and all(card_entry.get(k) == card_obj.get(k) for k in ['id', 'lang', 'is_proxy', 'collector_number', 'set_code']):
                                        del c['cards'][idx_del]
                                        print(f"[DEBUG] Karte entfernt an Index {idx_del}")
                                        break
                                print(f"[DEBUG] Karten nach dem Löschen: {len(c['cards'])}")
                                break
                        with open("collections.json", "w", encoding="utf-8") as f:
                            json.dump(collections, f, indent=2, ensure_ascii=False)
                        print("[DEBUG] collections.json wurde aktualisiert.")
                        # Nach dem Löschen: Ansicht neu laden
                        updated_collection = None
                        for c in collections:
                            if c['name'] == self.collection['name']:
                                updated_collection = c
                                break
                        stack = self.stack_widget or find_parent_with_attr(self, widget_type=QStackedWidget)
                        if stack and updated_collection:
                            idx = stack.indexOf(self)
                            stack.removeWidget(self)
                            self.deleteLater()
                            new_viewer = CollectionViewer(updated_collection, self.return_to_menu, stack_widget=stack)
                            stack.insertWidget(idx, new_viewer)
                            stack.setCurrentWidget(new_viewer)
                            print("[DEBUG] CollectionViewer wurde neu geladen.")
                    except Exception as e:
                        QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen der Karte: {e}")
            del_btn.clicked.connect(lambda _, cobj=card, cname=card.get('name', '?'): delete_card(cobj, cname))
            # --- Editier-Button (Karte bearbeiten) ---
            edit_btn = QPushButton()
            edit_btn.setFixedSize(24, 24)
            edit_btn.setStyleSheet('''
                QPushButton {
                    border: none;
                    background: transparent;
                    min-width: 24px; min-height: 24px; max-width: 24px; max-height: 24px;
                    padding: 0;
                    color: #4caf50;
                    font-size: 22px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #ddffdd;
                    border-radius: 6px;
                }
            ''')
            edit_btn.setText('✎')

            # Funktion zum Öffnen des Editier-Dialogs für eine Karte
            # Hier kann man Sprache, Proxy-Status und Variante ändern
            def open_edit_dialog(card_obj):
                import requests
                from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QMessageBox
                import copy
                from PyQt6.QtGui import QPixmap
                # Bild vorab cachen, damit es beim ersten Öffnen angezeigt wird
                # Bild vorab cachen, damit es beim ersten Öffnen angezeigt wird
                def pre_cache_image(card_data):
                    if card_data.get("card_faces") and isinstance(card_data["card_faces"], list):
                        face = card_data["card_faces"][0]
                        img_url = face.get("image_uris", {}).get("large")
                        if img_url:
                            get_cached_image(img_url, face.get('id'), fallback_name=face.get('name'), fallback_set=card_data.get('set_code') or card_data.get('set'))
                    else:
                        img_url = card_data.get("image_uris", {}).get("large")
                        if img_url:
                            get_cached_image(img_url, card_data.get('id'), fallback_name=card_data.get('name'), fallback_set=card_data.get('set_code') or card_data.get('set'))
                pre_cache_image(card_obj)

                edit_dialog = QDialog(self)
                edit_dialog.setWindowTitle(f"Karte bearbeiten: {card_obj.get('name','')}")
                edit_dialog.setMinimumWidth(480)
                layout = QVBoxLayout()

                # Name
                name_label = QLabel(f"<b>{card_obj.get('name','')}</b>")
                name_label.setStyleSheet("font-size: 24px; font-weight: bold;")
                layout.addWidget(name_label)

                # Bild (aktuelle Variante)
                image_label = QLabel()
                image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                from PyQt6.QtCore import QTimer
                # Bild im Dialog aktualisieren (z.B. nach Variantenwechsel)
                def update_image(card_data, retry=True):
                    # Exakt dieselbe Logik wie im CollectionViewer für das Bild
                    image_uris = None
                    img_path = None
                    fallback_set = card_data.get('set_code') or card_data.get('set')
                    # Flipkarte: nimm das erste Face, wie in der Sammlung
                    if card_data.get("card_faces") and isinstance(card_data["card_faces"], list):
                        face = card_data["card_faces"][0]
                        image_uris = face.get("image_uris")
                        img_path = get_cached_image(
                            image_uris,
                            face.get('id'),
                            fallback_name=face.get('name'),
                            fallback_set=fallback_set
                        )
                    elif card_data.get("image_uris"):
                        image_uris = card_data.get("image_uris")
                        img_path = get_cached_image(
                            image_uris,
                            card_data.get('id'),
                            fallback_name=card_data.get('name'),
                            fallback_set=fallback_set
                        )
                    else:
                        image_uris = card_data.get("image_url")
                        img_path = get_cached_image(
                            image_uris,
                            card_data.get('id'),
                            fallback_name=card_data.get('name'),
                            fallback_set=fallback_set
                        )
                    if img_path and os.path.exists(img_path):
                        pixmap = QPixmap(img_path)
                        pixmap = pixmap.scaled(180, 255, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        image_label.setPixmap(pixmap)
                        image_label.setText("")
                    else:
                        image_label.setPixmap(QPixmap())
                        image_label.setText("Kein Bild")
                        if retry:
                            QTimer.singleShot(400, lambda: update_image(card_data, retry=False))
                update_image(card_obj)
                layout.addWidget(image_label)


        self._build_card_widgets(grid, filtered_cards)