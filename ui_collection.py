
# ui_collection.py
#
# Sammlung-Viewer-UI für den MTG Desktop Manager
#
# Dieses Modul zeigt die grafische Oberfläche für eine Kartensammlung.
# Hier werden Kartenbilder, Infos, Editier- und Löschfunktionen sowie die Bildanzeige im Dialog umgesetzt.
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGroupBox, QStackedWidget, QComboBox, QCheckBox, QMessageBox, QFrame, QSizePolicy, QDialog
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
            dlg.exec()
class CollectionViewer(QWidget):
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

        # --- Kopfzeile mit Navigation und Titel ---
        top_bar = QHBoxLayout()
        back_button = QPushButton("← Hauptmenü")
        back_button.clicked.connect(self.return_to_menu)
        top_bar.addWidget(back_button)

        # Button: Zurück zu Sammlungen (ruft ggf. show_collections auf)
        back_to_collections_button = QPushButton("Zurück zu Sammlungen")
        back_to_collections_button.setStyleSheet("margin-left: 10px;")
        def go_to_collections():
            parent = find_parent_with_attr(self, attr_name='show_collections')
            if parent:
                parent.show_collections()
        back_to_collections_button.clicked.connect(go_to_collections)
        top_bar.addWidget(back_to_collections_button)

        # Titel der Sammlung
        title = QLabel(f"Sammlung: {self.collection['name']}")
        title.setStyleSheet("font-size: 30px; font-weight: bold; padding: 22px 0 22px 0;")
        top_bar.addWidget(title)
        layout.addLayout(top_bar)

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

        # --- Kartenliste aufbauen ---
        # Filtere alle None/bool/Fehlerhaften Karten raus
        valid_cards = [c for c in self.collection["cards"] if isinstance(c, dict)]
        for idx, card in enumerate(valid_cards):
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


                # Sprache
                # --- Sprache auswählen (DE/ENG) ---
                lang_row = QHBoxLayout()
                lang_label = QLabel("Sprache:")
                lang_selector = QComboBox()
                lang_selector.addItem("DE")
                lang_selector.addItem("ENG")
                lang_selector.setCurrentText(card_obj.get('lang','en').upper())
                lang_row.addWidget(lang_label)
                lang_row.addWidget(lang_selector)
                layout.addLayout(lang_row)

                # Kaufwert (Purchase Price) editierbar
                purchase_row = QHBoxLayout()
                purchase_label = QLabel("Kaufwert (€):")
                from PyQt6.QtWidgets import QLineEdit
                purchase_edit = QLineEdit()
                purchase_edit.setPlaceholderText("z.B. 3.50")
                purchase_edit.setFixedWidth(100)
                # Vorbelegen, falls vorhanden
                kaufwert_vorher = card_obj.get('purchase_price')
                if kaufwert_vorher is not None:
                    try:
                        purchase_edit.setText(str(float(kaufwert_vorher)))
                    except Exception:
                        purchase_edit.setText(str(kaufwert_vorher))
                purchase_row.addWidget(purchase_label)
                purchase_row.addWidget(purchase_edit)
                layout.addLayout(purchase_row)

                # Proxy
                # --- Proxy-Checkbox ---
                proxy_row = QHBoxLayout()
                proxy_checkbox = QCheckBox("Als Proxy")
                proxy_checkbox.setChecked(bool(card_obj.get('is_proxy', False)))
                proxy_checkbox.setStyleSheet("font-size: 20px; min-height: 28px; min-width: 28px; padding: 6px 12px;")
                proxy_row.addWidget(proxy_checkbox)
                layout.addLayout(proxy_row)

                # Event: Wenn Proxy-Status geändert wird, Preis ggf. live nachladen
                def on_proxy_changed(state):
                    if proxy_checkbox.isChecked():
                        edited_card['eur'] = 0
                    else:
                        # Hole Preis aus Scryfall-API für die aktuelle Variante
                        oracle_id = edited_card.get('oracle_id')
                        lang = edited_card.get('lang', 'en')
                        set_code = edited_card.get('set_code') or edited_card.get('set')
                        collector_number = edited_card.get('collector_number')
                        # Suche nach exakter Karte (oracle_id, set, collector_number, lang)
                        price = None
                        try:
                            if oracle_id and set_code and collector_number:
                                url = f"https://api.scryfall.com/cards/{set_code.lower()}/{collector_number}/{lang.lower()}"
                                resp = requests.get(url, timeout=4)
                                if resp.status_code == 200:
                                    data = resp.json()
                                    price = data.get('prices', {}).get('eur')
                            if price is None and 'prices' in edited_card and isinstance(edited_card['prices'], dict):
                                price = edited_card['prices'].get('eur')
                            if price is None:
                                price = edited_card.get('eur')
                            try:
                                price = float(price)
                            except Exception:
                                price = 0
                            edited_card['eur'] = price
                        except Exception as e:
                            edited_card['eur'] = 0
                proxy_checkbox.stateChanged.connect(on_proxy_changed)

                # Variante ändern (über Scryfall Prints-API)
                # --- Variante ändern (öffnet VariantSelector-Dialog) ---
                variant_row = QHBoxLayout()
                variant_label = QLabel("Variante ändern:")
                variant_btn = QPushButton("Alle Varianten anzeigen")
                variant_btn.setStyleSheet("font-size: 16px; padding: 4px 12px;")
                variant_row.addWidget(variant_label)
                variant_row.addWidget(variant_btn)
                layout.addLayout(variant_row)

                # Info-Label für aktuelle Variante
                # Info-Label für aktuelle Variante (Set, Nummer, Sprache)
                info_label = QLabel(f"Set: {card_obj.get('set','')} | Nr: {card_obj.get('collector_number','')} | Sprache: {card_obj.get('lang','').upper()}")
                info_label.setStyleSheet("font-size: 15px; color: #aaa;")
                layout.addWidget(info_label)

                # Speichern-Button
                # --- Speichern-Button ---
                save_btn = QPushButton("Speichern")
                save_btn.setStyleSheet("font-size: 20px; padding: 8px 24px; margin-top: 18px;")
                layout.addWidget(save_btn)

                # Aktuelle Variante (mutable Kopie)
                # Kopie der Karte, damit Änderungen erst beim Speichern übernommen werden
                edited_card = copy.deepcopy(card_obj)

                # Variante ändern Logik
                # --- Variante ändern Logik ---
                def choose_variant():
                    prints_url = edited_card.get('prints_search_uri') or card_obj.get('prints_search_uri')
                    if not prints_url:
                        QMessageBox.warning(edit_dialog, "Fehler", "Keine Varianten-URL vorhanden.")
                        return
                    def on_variant_selected(new_card):
                        # Übernehme alle Felder der neuen Variante, aber behalte Proxy, Sprache, count
                        for k in new_card:
                            if k not in ('is_proxy','lang','count'):
                                edited_card[k] = new_card[k]
                        # Preis der neuen Variante übernehmen, außer Proxy ist aktiv
                        if not edited_card.get('is_proxy'):
                            eur = None
                            # Scryfall-API: Preis kann unter 'prices'->'eur' liegen
                            if 'prices' in new_card and isinstance(new_card['prices'], dict):
                                eur = new_card['prices'].get('eur')
                            if eur is None:
                                eur = new_card.get('eur')
                            try:
                                eur = float(eur)
                            except Exception:
                                eur = 0
                            edited_card['eur'] = eur
                        # Setze Info-Label neu
                        info_label.setText(f"Set: {edited_card.get('set','')} | Nr: {edited_card.get('collector_number','')} | Sprache: {lang_selector.currentText()}")
                        # Bild aktualisieren
                        update_image(edited_card)
                    selector = VariantSelector(prints_url, on_variant_selected)
                    selector.exec()
                variant_btn.clicked.connect(choose_variant)

                # Speichern-Logik
                # --- Speichern-Logik ---
                # Übernimmt die Änderungen aus dem Dialog und speichert sie in collections.json
                def save_changes():
                    # Übernehme Änderungen
                    edited_card['lang'] = lang_selector.currentText().lower()
                    edited_card['is_proxy'] = proxy_checkbox.isChecked()
                    # Preis bei Proxy immer 0, sonst aktuellen Preis aus Variante setzen
                    if edited_card['is_proxy']:
                        edited_card['eur'] = 0
                    else:
                        eur = None
                        # Scryfall-API: Preis kann unter 'prices'->'eur' liegen
                        if 'prices' in edited_card and isinstance(edited_card['prices'], dict):
                            eur = edited_card['prices'].get('eur')
                        if eur is None:
                            eur = edited_card.get('eur')
                        try:
                            eur = float(eur)
                        except Exception:
                            eur = 0
                        edited_card['eur'] = eur
                    # Kaufwert übernehmen
                    kaufwert_str = purchase_edit.text().replace(",", ".").strip()
                    try:
                        kaufwert_float = float(kaufwert_str) if kaufwert_str else None
                    except Exception:
                        kaufwert_float = None
                    if kaufwert_float is not None:
                        edited_card['purchase_price'] = kaufwert_float
                    elif 'purchase_price' in edited_card:
                        del edited_card['purchase_price']
                    # Bild(er) direkt cachen wie beim Hinzufügen
                    if edited_card.get("card_faces") and isinstance(edited_card["card_faces"], list):
                        for face in edited_card["card_faces"]:
                            image_uris_face = face.get("image_uris")
                            if image_uris_face:
                                for key in ["large", "normal", "small"]:
                                    if image_uris_face.get(key):
                                        get_cached_image(image_uris_face[key], face.get('id'), fallback_name=face.get('name'), fallback_set=edited_card.get('set_code') or edited_card.get('set'))
                                        break
                    else:
                        image_uris = edited_card.get("image_uris")
                        if isinstance(image_uris, dict):
                            for key in ["large", "normal", "small"]:
                                if image_uris.get(key):
                                    get_cached_image(image_uris[key], edited_card.get('id'), fallback_name=edited_card.get('name'), fallback_set=edited_card.get('set_code') or edited_card.get('set'))
                                    break
                        elif isinstance(image_uris, str):
                            get_cached_image(image_uris, edited_card.get('id'), fallback_name=edited_card.get('name'), fallback_set=edited_card.get('set_code') or edited_card.get('set'))
                    # Speichere in collections.json
                    try:
                        with open("collections.json", "r", encoding="utf-8") as f:
                            collections = json.load(f)
                        for c in collections:
                            if c['name'] == self.collection['name']:
                                for idx_edit, card_entry in enumerate(c['cards']):
                                    if isinstance(card_entry, dict) and all(card_entry.get(k) == card_obj.get(k) for k in ['id', 'lang', 'is_proxy', 'collector_number', 'set_code']):
                                        c['cards'][idx_edit] = edited_card
                                        break
                                break
                        with open("collections.json", "w", encoding="utf-8") as f:
                            json.dump(collections, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {e}")
                        return
                    edit_dialog.accept()
                    # Ansicht neu laden, Scroll-Position merken und übergeben
                    stack = self.stack_widget or find_parent_with_attr(self, widget_type=QStackedWidget)
                    scroll_value = None
                    if hasattr(self, 'findChild'):
                        scroll_area = self.findChild(QScrollArea)
                        if scroll_area:
                            scroll_value = scroll_area.verticalScrollBar().value()
                    if stack:
                        idx = stack.indexOf(self)
                        stack.removeWidget(self)
                        self.deleteLater()
                        new_viewer = CollectionViewer(self.collection, self.return_to_menu, stack_widget=stack, scroll_value=scroll_value)
                        stack.insertWidget(idx, new_viewer)
                        stack.setCurrentWidget(new_viewer)
                save_btn.clicked.connect(save_changes)

                edit_dialog.setLayout(layout)
                edit_dialog.exec()

            edit_btn.clicked.connect(lambda _, cobj=card: open_edit_dialog(cobj))
            name_price_row.addWidget(edit_btn)
            name_price_row.addWidget(del_btn)
            info_layout.addLayout(name_price_row)
            # --- Kompakte Infozeile: Manakosten | Setname | SETCODE FIN Nummer/Setgröße ---
            mana_cost = card.get('mana_cost', '')
            # Für Flip/DFC-Karten: Manakosten aus beiden Faces zusammenfassen, falls unterschiedlich
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
            # Format: Manakosten: 1WU | FINAL FANTASY | FIN 25/6
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
            # Proxy-Label, falls Karte ein Proxy ist
            if card.get('is_proxy'):
                proxy_label = QLabel("Proxy: Ja")
                proxy_label.setStyleSheet("font-size: 15px; color: #ff8888;")
                proxy_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                info_layout.addWidget(proxy_label)
            info_widget = QWidget()
            info_widget.setLayout(info_layout)
            # --- Oracle-Text (Regeltext) ---
            # Für Flip-/DFC-Karten: Zeige alle Faces mit Typ und Text
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
                # Zeige type_line immer fett, auch wenn oracle_text leer ist
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
        # Nach dem Aufbau: Widget refreshen, damit Bilder aus dem Cache sofort angezeigt werden
        self.repaint()
        self.update()
        # Scroll-Position wiederherstellen, falls übergeben
        if scroll_value is not None:
            scroll.verticalScrollBar().setValue(scroll_value)
        self.update()
        # Scroll-Position wiederherstellen, falls übergeben
        if scroll_value is not None:
            scroll.verticalScrollBar().setValue(scroll_value)