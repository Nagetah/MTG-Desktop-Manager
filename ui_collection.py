
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

            # --- Proxy-Status ---
            proxy_row = QHBoxLayout()
            proxy_label = QLabel("Proxy:")
            proxy_checkbox = QCheckBox()
            proxy_checkbox.setChecked(bool(card_obj.get("is_proxy")))
            proxy_row.addWidget(proxy_label)
            proxy_row.addWidget(proxy_checkbox)
            layout.addLayout(proxy_row)

            # --- Kaufpreis ---
            price_row = QHBoxLayout()
            price_label = QLabel("Kaufpreis (€):")
            from PyQt6.QtWidgets import QLineEdit
            price_edit = QLineEdit()
            price_edit.setPlaceholderText("z.B. 2.50")
            price_edit.setText(str(card_obj.get("purchase_price") or ""))
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
            save_btn.setStyleSheet("font-size: 18px; padding: 8px 24px; margin-top: 18px;")
            layout.addWidget(save_btn)

            edit_dialog.setLayout(layout)

            # --- Dynamik: Felder aktualisieren bei Variantenwahl ---
            # Merke die ursprünglichen Identifikationsdaten der Karte
            original_keys = {k: card_obj.get(k) for k in ['id', 'lang', 'is_proxy', 'collector_number', 'set_code']}

            def update_fields(new_card):
                # Übernehme alle relevanten Felder, auch eur, set_size etc.
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
                price_edit.setText(str(new_card.get("purchase_price") or ""))
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
            price_label = QLabel(f"| {price_str}")
            price_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffd700; margin-bottom: 2px; margin-left: 8px;")
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