import os
import json
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
from ui_startscreen import StartScreen
from ui_search import MTGDesktopManager
from ui_collection import CollectionViewer
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTextEdit, QScrollArea, QDialog, QSizePolicy, QStackedWidget, QListWidget, QInputDialog, QComboBox, QCheckBox, QGroupBox, QFrame
    )

# HIER BEGINNT DIE KORREKTE MAINWINDOW-KLASSE
class MainWindow(QWidget):
    def closeEvent(self, event):
        # Beim Schließen des Hauptfensters: Beende alle CollectionOverview-Threads sauber
        if hasattr(self, 'collection_view') and self.collection_view is not None:
            self.collection_view.closeEvent(event)
        super().closeEvent(event)
    

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MTG Desktop Manager")
        self.stack = QStackedWidget()
        # Platzhalter für spätere Initialisierung
        self.start_screen = None
        self.search_view = None
        self.collection_view = None
        self.init_views()

    def init_views(self):
        # Diese Methoden müssen existieren, bevor sie an die Views übergeben werden
        self.start_screen = StartScreen(self.show_search, self.show_collections)
        self.search_view = MTGDesktopManager(self.show_start)
        self.collection_view = self.CollectionOverview(self.show_start)
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

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import io
    from PyQt6.QtGui import QImage

    class CollectionOverview(QWidget):
        @staticmethod
        def safe_float(val):
            if val is None:
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                val = val.replace(',', '.')
                try:
                    return float(val)
                except Exception:
                    return 0.0
            return 0.0
        def closeEvent(self, event):
            # Beende alle laufenden Preisupdate-Threads und Timer sauber (mit Timeout)
            print(f"[DEBUG] closeEvent: Beende {len(self.threads)} Threads...")
            # Beende und entferne ALLE Threads, auch wenn kein update_finished mehr kommt
            for name, thread in list(self.threads.items()):
                print(f"[DEBUG] closeEvent: Thread für '{name}' wird FINAL beendet...")
                try:
                    thread.quit()
                    thread.wait(5000)
                    print(f"[DEBUG] closeEvent: Thread für '{name}' gestoppt: {not thread.isRunning()}")
                except Exception as e:
                    print(f"[DEBUG] closeEvent: Fehler beim Beenden von Thread '{name}': {e}")
                del self.threads[name]
            if self.threads:
                print(f"[DEBUG] closeEvent: Nach dem FINALEN Beenden sind noch {len(self.threads)} Threads im Dict: {list(self.threads.keys())}")
                self.threads.clear()
            for timer in self.status_timers.values():
                timer.stop()
            self.status_timers.clear()
            self.status_start_times.clear()
            print(f"[DEBUG] closeEvent: Alle Threads/Ticker gestoppt.")
            super().closeEvent(event)
        def __init__(self, return_to_menu):
            super().__init__()
            self.return_to_menu = return_to_menu
            self.setStyleSheet("background-color: #1e1e1e; color: white;")

            # --- Wichtige Attribute initialisieren, bevor load_collections() aufgerufen werden kann ---
            self.threads = {}        # sammlungsname -> QThread
            self.status_timers = {}  # sammlungsname -> QTimer
            self.status_start_times = {}  # sammlungsname -> float (startzeit)
            self.update_status = {}  # sammlungsname -> 'pending'|'done'|'error'
            self.status_labels = {}  # sammlungsname -> QLabel

            # --- Kreisdiagramm für alle Sammlungen ---
            diagram_label = QLabel()
            diagram_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            diagram_label.setStyleSheet("margin-bottom: 18px;")
            self.diagram_label = diagram_label

            top_bar = QHBoxLayout()
            # --- Back-Button: ← Hauptmenü ---
            back_button = QPushButton("← Hauptmenü")
            font_metrics = back_button.fontMetrics()
            padding_px = 28  # wie im Stylesheet
            min_width = font_metrics.horizontalAdvance(back_button.text()) + 2 * padding_px
            back_button.setMinimumWidth(max(min_width, 2 * padding_px + 80))  # 80 als sinnvolles Minimum
            back_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            back_button.clicked.connect(self.return_to_menu)
            top_bar.addWidget(back_button)

            self.label = QLabel("Sammlungen")
            self.label.setStyleSheet("font-size: 18px; padding: 10px;")
            top_bar.addWidget(self.label)

            top_bar.addStretch(1)

            # --- Preise updaten Button (blau, rechts) ---
            self.update_all_button = QPushButton("Preise updaten")
            font_metrics2 = self.update_all_button.fontMetrics()
            min_width2 = font_metrics2.horizontalAdvance(self.update_all_button.text()) + 2 * padding_px
            self.update_all_button.setMinimumWidth(max(min_width2, 2 * padding_px + 80))
            self.update_all_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            self.update_all_button.setStyleSheet("background-color: #1976d2; color: white; border-radius: 8px; padding: 10px 24px;")
            self.update_all_button.clicked.connect(self.manual_update_all_prices)
            top_bar.addWidget(self.update_all_button)

            self.list_widget = QListWidget()
            self.list_widget.itemDoubleClicked.connect(self.open_collection)

            self.new_button = QPushButton("Neue Sammlung erstellen")
            font_metrics3 = self.new_button.fontMetrics()
            min_width3 = font_metrics3.horizontalAdvance(self.new_button.text()) + 2 * padding_px
            self.new_button.setMinimumWidth(max(min_width3, 2 * padding_px + 80))
            self.new_button.clicked.connect(self.create_collection)

            self.delete_button = QPushButton("Ausgewählte Sammlung löschen")
            font_metrics4 = self.delete_button.fontMetrics()
            min_width4 = font_metrics4.horizontalAdvance(self.delete_button.text()) + 2 * padding_px
            self.delete_button.setMinimumWidth(max(min_width4, 2 * padding_px + 80))
            self.delete_button.clicked.connect(self.delete_collection)

            # Layout erst jetzt anlegen und befüllen
            layout = QVBoxLayout()
            layout.addWidget(self.diagram_label)
            layout.addLayout(top_bar)
            layout.addWidget(self.list_widget)
            layout.addWidget(self.new_button)
            layout.addWidget(self.delete_button)
            self.setLayout(layout)
        def manual_update_all_prices(self):
            """Manuelles Update aller Preise: setzt alle last_price_update auf 0 und startet load_collections neu."""
            if hasattr(self, 'updating_collections') and self.updating_collections:
                return
            # Setze alle last_price_update auf 0 (force update)
            if os.path.exists("collections.json"):
                with open("collections.json", "r", encoding="utf-8") as f:
                    collections = json.load(f)
                for col in collections:
                    col['last_price_update'] = 0
                with open("collections.json", "w", encoding="utf-8") as f:
                    json.dump(collections, f, indent=2, ensure_ascii=False)
            # --- ALLE laufenden Threads und Timer beenden, bevor Status zurückgesetzt wird ---
            for name, thread in list(self.threads.items()):
                try:
                    thread.quit()
                    thread.wait(5000)
                except Exception:
                    pass
                del self.threads[name]
            for timer in self.status_timers.values():
                timer.stop()
            self.status_timers.clear()
            self.status_start_times.clear()
            self.update_status.clear()
            self.status_labels.clear()
            # Button deaktivieren während Update läuft
            self.update_all_button.setEnabled(False)
            self.load_collections()




            # Status-Tracking für Preisupdates
            self.update_status = {}  # sammlungsname -> 'pending'|'done'|'error'
            self.status_labels = {}  # sammlungsname -> QLabel
            self.threads = {}        # sammlungsname -> QThread
            self.status_timers = {}  # sammlungsname -> QTimer
            self.status_start_times = {}  # sammlungsname -> float (startzeit)
            self.load_collections()

        def update_overview_diagram(self, collections):
            # Summiere alle Karten aller Sammlungen
            all_cards = []
            for col in collections:
                all_cards.extend([c for c in col.get('cards', []) if isinstance(c, dict)])
            marktwert = sum(self.safe_float(c.get('eur')) for c in all_cards)
            einkauf = sum(self.safe_float(c.get('purchase_price')) for c in all_cards)
            diff = marktwert - einkauf
            num_cards = len(all_cards)
            percent = (diff / einkauf * 100) if einkauf > 0 else 0

            # Farben
            color_bg = '#1e1e1e'  # Exakter Hintergrund wie das Programm
            color_gain = '#4caf50'  # Grün für Gewinn
            color_loss = '#e53935'  # Rot für Verlust

            # Anteile und Farben pro Sammlung (nach Marktwert inkl. Wertsteigerung)
            values = []
            colors = []
            for col in collections:
                col_cards = [c for c in col.get('cards', []) if isinstance(c, dict)]
                col_value = sum(self.safe_float(c.get('eur')) for c in col_cards)
                if col_value > 0:
                    values.append(col_value)
                    colors.append(col.get('color', '#888888'))

            # Falls alles 0 ist, Dummy-Wert für leeres Diagramm
            if not values or sum(values) == 0:
                values = [1]
                colors = ['#444444']

            fig, ax = plt.subplots(figsize=(3.5, 3.5), dpi=100)
            wedges, texts = ax.pie(values, colors=colors, startangle=90, wedgeprops=dict(width=0.22, edgecolor=color_bg))
            plt.setp(wedges, linewidth=2, edgecolor=color_bg)
            ax.set(aspect="equal")
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            ax.set_facecolor(color_bg)
            fig.patch.set_facecolor(color_bg)

            # Text im Kreis: Entwicklung, Marktwert, Kartenzahl
            if einkauf > 0:
                diff_str = f"+{diff:.0f}" if diff >= 0 else f"{diff:.0f}"
                percent_str = f"(+{percent:.1f}%)" if diff >= 0 else f"({percent:.1f}%)"
            else:
                diff_str = "0"
                percent_str = "(0%)"
            mw_str = f"{marktwert:.0f} €"
            card_str = f"{num_cards} Karten"
            text_color = color_gain if diff >= 0 else color_loss
            ax.text(0, 0.32, f"{diff_str} {percent_str}", ha='center', va='center', fontsize=14, color=text_color, fontweight='bold')
            ax.text(0, 0.08, mw_str, ha='center', va='center', fontsize=22, color='white', fontweight='bold')
            ax.text(0, -0.18, card_str, ha='center', va='center', fontsize=13, color='#cccccc')

            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', transparent=False)
            plt.close(fig)
            buf.seek(0)
            qimg = QImage.fromData(buf.getvalue())
            pixmap = QPixmap.fromImage(qimg)
            buf.close()
            self.diagram_label.setPixmap(pixmap)

        def open_collection(self, item):
            # Hole den Namen der Sammlung aus dem Item (wird als Data gespeichert)
            collection_name = None
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i) is item:
                    widget = self.list_widget.itemWidget(item)
                    if widget:
                        name_label = widget.layout().itemAt(1).widget()
                        if name_label:
                            collection_name = name_label.text()
                    break
            if not collection_name:
                collection_name = item.text().split('|')[0].strip()
            # --- Blockiere Öffnen, wenn Preisupdate für diese Sammlung läuft ---
            if self.update_status.get(collection_name) == 'pending':
                QMessageBox.information(self, "Preisupdate läuft", f"Das Preisupdate für '{collection_name}' läuft noch. Bitte warte, bis es abgeschlossen ist.")
                return
            if not os.path.exists("collections.json"):
                QMessageBox.warning(self, "Fehler", "Sammlung nicht gefunden.")
                return
            # --- Stoppe alle laufenden Preisupdate-Threads und Timer, bevor die Einzelansicht geladen wird ---
            for thread in self.threads.values():
                thread.quit()
                thread.wait(3000)
            self.threads.clear()
            for timer in self.status_timers.values():
                timer.stop()
            self.status_timers.clear()
            self.status_start_times.clear()
            with open("collections.json", "r", encoding="utf-8") as f:
                collections = json.load(f)
                for col in collections:
                    if col["name"] == collection_name:
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
            # Button während Update deaktivieren
            if hasattr(self, 'update_all_button'):
                self.update_all_button.setEnabled(False)
            from PyQt6.QtWidgets import QListWidgetItem, QWidget, QHBoxLayout, QLabel, QSizePolicy
            from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
            from PyQt6.QtCore import QThread, QTimer
            from price_updater import PriceUpdaterWorker
            import time
            UPDATE_INTERVAL = 3600  # 1 Stunde (in Sekunden)
            # --- ALLE laufenden Threads und Timer beenden, bevor Status zurückgesetzt wird ---
            for name, thread in list(self.threads.items()):
                try:
                    thread.quit()
                    thread.wait(5000)
                except Exception:
                    pass
                del self.threads[name]
            for timer in self.status_timers.values():
                timer.stop()
            self.status_timers.clear()
            self.status_start_times.clear()
            self.update_status.clear()
            self.status_labels.clear()
            # --- SCHUTZ: Parallele Preisupdates verhindern ---
            if hasattr(self, 'updating_collections') and self.updating_collections:
                print('[DEBUG] Preisupdate: Parallelversuch blockiert (Flag)')
                return
            if self.threads:
                print(f"[DEBUG] Preisupdate: Es laufen noch alte Threads: {list(self.threads.keys())} – Starte KEINE neuen Worker!")
                return
            self.updating_collections = True
            self.list_widget.clear()
            collections = []
            if os.path.exists("collections.json"):
                with open("collections.json", "r", encoding="utf-8") as f:
                    collections = json.load(f)
            self.update_overview_diagram(collections)
            now = time.time()
            def start_workers():
                for col in collections:
                    # Prüfe, ob das letzte Update zu lange her ist
                    last_update = col.get('last_price_update', 0)
                    needs_update = (now - last_update) > UPDATE_INTERVAL
                    color = col.get('color', '#888888')
                    pix = QPixmap(28, 28)
                    pix.fill(QColor(0,0,0,0))
                    painter = QPainter(pix)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setBrush(QColor(color))
                    painter.setPen(QColor(color))
                    painter.drawEllipse(4, 4, 20, 20)
                    painter.end()
                    marktwert = sum(self.safe_float(c.get('eur')) * int(c.get('count', 1) or 1) for c in col['cards'])
                    einkauf = sum(self.safe_float(c.get('purchase_price')) * int(c.get('count', 1) or 1) for c in col['cards'])
                    diff = marktwert - einkauf
                    row_widget = QWidget()
                    row_layout = QHBoxLayout()
                    row_layout.setContentsMargins(2,2,2,2)
                    icon_label = QLabel()
                    icon_label.setPixmap(pix)
                    icon_label.setFixedWidth(32)
                    row_layout.addWidget(icon_label)
                    name_label = QLabel(col['name'])
                    name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
                    row_layout.addWidget(name_label)
                    # Zeige die Gesamtanzahl aller Karten (inkl. Stückzahl)
                    total_count = 0
                    for card in col['cards']:
                        cnt = card.get('count', 1)
                        try:
                            cnt = int(cnt)
                        except Exception:
                            cnt = 1
                        total_count += cnt
                    count_label = QLabel(f"| {total_count} Karten |")
                    count_label.setStyleSheet("font-size: 16px; margin-left: 8px;")
                    row_layout.addWidget(count_label)
                    marktwert_label = QLabel(f"Marktwert: {marktwert:.2f} €")
                    marktwert_label.setStyleSheet("font-size: 16px; color: #ffd700; margin-left: 8px;")
                    row_layout.addWidget(marktwert_label)
                    if einkauf > 0:
                        if diff > 0:
                            diff_color = '#4caf50'
                            diff_symbol = '▲'
                        elif diff < 0:
                            diff_color = '#e53935'
                            diff_symbol = '▼'
                        else:
                            diff_color = '#cccccc'
                            diff_symbol = '•'
                        kaufwert_label = QLabel(f"Kaufwert: {einkauf:.2f} €")
                        kaufwert_label.setStyleSheet(f"font-size: 16px; margin-left: 8px; color: {diff_color};")
                        row_layout.addWidget(kaufwert_label)
                        diff_label = QLabel(f"{diff_symbol} {abs(diff):.2f} €")
                        diff_label.setStyleSheet(f"font-size: 16px; margin-left: 4px; color: {diff_color}; font-weight: bold;")
                        row_layout.addWidget(diff_label)
                    status_label = QLabel()
                    status_label.setStyleSheet("font-size: 20px; margin-left: 12px;")
                    status_label.setText('⟳ 0s')
                    row_layout.addWidget(status_label)
                    self.status_labels[col['name']] = status_label
                    if len(col['cards']) == 0:
                        status_label.setText('✅')
                        status_label.setStyleSheet("font-size: 20px; margin-left: 12px; color: #4caf50;")
                        self.update_status[col['name']] = 'done'
                    else:
                        if needs_update:
                            self.update_status[col['name']] = 'pending'
                            # Status-Label sofort auf gelb setzen
                            status_label.setText('⟳ 0s')
                            status_label.setStyleSheet("font-size: 20px; margin-left: 12px; color: #ffd700;")
                        else:
                            self.update_status[col['name']] = 'done'
                            status_label.setText('✅')
                            status_label.setStyleSheet("font-size: 20px; margin-left: 12px; color: #4caf50;")
                        timer = QTimer(self)
                        timer.setInterval(1000)
                        def update_label(name=col['name'], label=status_label):
                            import time
                            start = self.status_start_times.get(name)
                            if start:
                                sek = int(time.time() - start)
                                label.setText(f'⟳ {sek}s')
                        timer.timeout.connect(update_label)
                        self.status_timers[col['name']] = timer
                        # --- Preisupdate-Worker nur starten, wenn nötig ---
                        if needs_update and col['name'] not in self.threads:
                            print(f"[DEBUG] Starte Preisupdate-Worker für Sammlung '{col['name']}' um {time.strftime('%H:%M:%S')}")
                            self.status_start_times[col['name']] = time.time()
                            self.status_timers[col['name']].start()
                            thread = QThread()
                            worker = PriceUpdaterWorker(col, col['name'])
                            worker.moveToThread(thread)
                            worker.update_status.connect(self.on_update_status)
                            worker.update_finished.connect(self.on_update_finished)
                            def handle_worker_error(sammlungsname, status):
                                print(f"[DEBUG] Fehler im Preisupdate-Worker für '{sammlungsname}' um {time.strftime('%H:%M:%S')}: Status={status}")
                                self.on_update_status(sammlungsname, 'error')
                            worker.update_status.connect(lambda name, status: handle_worker_error(name, status) if status == 'error' else None)
                            thread.started.connect(worker.run)
                            thread.start()
                            self.threads[col['name']] = thread
                    row_layout.addStretch(1)
                    row_widget.setLayout(row_layout)
                    item = QListWidgetItem()
                    item.setSizeHint(row_widget.sizeHint())
                    self.list_widget.addItem(item)
                    self.list_widget.setItemWidget(item, row_widget)
                self.updating_collections = False
                # Button wieder aktivieren, wenn keine Updates mehr laufen
                if hasattr(self, 'update_all_button'):
                    self.update_all_button.setEnabled(True)
            # Starte Worker erst nach kurzem Delay, damit alle alten Threads wirklich beendet sind
            QTimer.singleShot(150, start_workers)

        def on_update_status(self, sammlungsname, status):
            import time
            print(f"[DEBUG] on_update_status: {sammlungsname} -> {status}")
            label = self.status_labels.get(sammlungsname)
            if not label:
                return
            if status == 'pending':
                # Timer läuft weiter, Label zeigt Sekunden
                sek = int(time.time() - self.status_start_times.get(sammlungsname, time.time()))
                label.setText(f'⟳ {sek}s')
                label.setStyleSheet("font-size: 20px; margin-left: 12px; color: #ffd700;")
            elif status == 'done':
                print(f"[DEBUG] Preisupdate für '{sammlungsname}' abgeschlossen um {time.strftime('%H:%M:%S')}")
                label.setText('✅')
                label.setStyleSheet("font-size: 20px; margin-left: 12px; color: #4caf50;")
                timer = self.status_timers.get(sammlungsname)
                if timer:
                    timer.stop()
            elif status == 'error':
                print(f"[DEBUG] Preisupdate für '{sammlungsname}' FEHLER um {time.strftime('%H:%M:%S')}")
                label.setText('❌')
                label.setStyleSheet("font-size: 20px; margin-left: 12px; color: #e53935;")
                timer = self.status_timers.get(sammlungsname)
                if timer:
                    timer.stop()
            self.update_status[sammlungsname] = status

        def on_update_finished(self, sammlungsname, cards):
            import time
            print(f"[DEBUG] on_update_finished für '{sammlungsname}' um {time.strftime('%H:%M:%S')} (Threads: {list(self.threads.keys())})")
            # --- Update last_price_update Zeitstempel ---
            now = time.time()
            if os.path.exists("collections.json"):
                with open("collections.json", "r", encoding="utf-8") as f:
                    collections = json.load(f)
                for col in collections:
                    if col['name'] == sammlungsname:
                        col['cards'] = cards
                        col['last_price_update'] = now
                        break
                with open("collections.json", "w", encoding="utf-8") as f:
                    json.dump(collections, f, indent=2, ensure_ascii=False)
            thread = self.threads.get(sammlungsname)
            if thread:
                print(f"[DEBUG] on_update_finished: Thread für '{sammlungsname}' wird beendet...")
                thread.quit()
                thread.wait(5000)
                print(f"[DEBUG] on_update_finished: Thread für '{sammlungsname}' gestoppt: {not thread.isRunning()}")
                del self.threads[sammlungsname]
            else:
                print(f"[DEBUG] on_update_finished: Kein Thread für '{sammlungsname}' gefunden!")
            print(f"[DEBUG] on_update_finished: Noch laufende Threads: {list(self.threads.keys())}")
            with open("collections.json", "r", encoding="utf-8") as f:
                collections = json.load(f)
            self.update_overview_diagram(collections)
            # Status-Label auf 'done' setzen (wird ohnehin von on_update_status gemacht)
            # (Optional: Hier könnte man gezielt die Zeile für die Sammlung aktualisieren)

        def create_collection(self):
            from PyQt6.QtWidgets import QColorDialog
            from PyQt6.QtGui import QColor
            collections = []
            if os.path.exists("collections.json"):
                with open("collections.json", "r", encoding="utf-8") as f:
                    collections = json.load(f)
            name, ok = QInputDialog.getText(self, "Sammlung benennen", "Name der neuen Sammlung:")
            if not (ok and name):
                return
            # Farbauswahl-Dialog anzeigen
            color = QColorDialog.getColor()
            if not color.isValid():
                color = QColor("#888888")
            color_hex = color.name()
            collections.append({"name": name, "cards": [], "color": color_hex})
            with open("collections.json", "w", encoding="utf-8") as f:
                json.dump(collections, f, indent=2, ensure_ascii=False)
            self.load_collections()
import sys
from PyQt6.QtWidgets import QApplication
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
    min-height: 38px;
    min-width: 140px;
    font-size: 21px;
    font-weight: 600;
    letter-spacing: 0.5px;
    white-space: nowrap;
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
