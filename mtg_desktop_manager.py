
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
        def __init__(self, return_to_menu):
            super().__init__()
            self.return_to_menu = return_to_menu
            self.setStyleSheet("background-color: #1e1e1e; color: white;")
            layout = QVBoxLayout()

            # --- Kreisdiagramm für alle Sammlungen ---
            diagram_label = QLabel()
            diagram_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            diagram_label.setStyleSheet("margin-bottom: 18px;")
            self.diagram_label = diagram_label
            layout.addWidget(diagram_label)

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

        def update_overview_diagram(self, collections):
            # Summiere alle Karten aller Sammlungen
            all_cards = []
            for col in collections:
                all_cards.extend([c for c in col.get('cards', []) if isinstance(c, dict)])
            marktwert = sum(float(c.get('eur') or 0) for c in all_cards)
            einkauf = sum(float(c.get('purchase_price') or 0) for c in all_cards)
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
                col_value = sum(float(c.get('eur') or 0) for c in col_cards)
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
            # Suche nach dem Widget-Index, um das passende Item zu finden
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i) is item:
                    # Wir haben das Item gefunden, jetzt das Widget auslesen
                    widget = self.list_widget.itemWidget(item)
                    if widget:
                        # Der Name steht im zweiten Widget (Label)
                        name_label = widget.layout().itemAt(1).widget()
                        if name_label:
                            collection_name = name_label.text()
                    break
            if not collection_name:
                # Fallback: versuche alten Weg
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
            from PyQt6.QtWidgets import QListWidgetItem, QWidget, QHBoxLayout, QLabel, QSizePolicy
            from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
            self.list_widget.clear()
            collections = []
            if os.path.exists("collections.json"):
                with open("collections.json", "r", encoding="utf-8") as f:
                    collections = json.load(f)
            # Update das Kreisdiagramm mit allen Sammlungen
            self.update_overview_diagram(collections)
            for col in collections:
                # Farbigen Punkt als Icon erzeugen
                color = col.get('color', '#888888')
                pix = QPixmap(28, 28)
                pix.fill(QColor(0,0,0,0))
                painter = QPainter(pix)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setBrush(QColor(color))
                painter.setPen(QColor(color))
                painter.drawEllipse(4, 4, 20, 20)
                painter.end()
                # Summen berechnen
                marktwert = sum(float(c.get('eur') or 0) for c in col['cards'])
                einkauf = sum(float(c.get('purchase_price') or 0) for c in col['cards'])
                diff = marktwert - einkauf
                # Widget für Zeile bauen
                row_widget = QWidget()
                row_layout = QHBoxLayout()
                row_layout.setContentsMargins(2,2,2,2)
                # Farbkreis
                icon_label = QLabel()
                icon_label.setPixmap(pix)
                icon_label.setFixedWidth(32)
                row_layout.addWidget(icon_label)
                # Name
                name_label = QLabel(col['name'])
                name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
                row_layout.addWidget(name_label)
                # Kartenanzahl
                count_label = QLabel(f"| {len(col['cards'])} Karten |")
                count_label.setStyleSheet("font-size: 16px; margin-left: 8px;")
                row_layout.addWidget(count_label)
                # Marktwert
                marktwert_label = QLabel(f"Marktwert: {marktwert:.2f} €")
                marktwert_label.setStyleSheet("font-size: 16px; color: #ffd700; margin-left: 8px;")
                row_layout.addWidget(marktwert_label)
                # Kaufwert + Differenz
                if einkauf > 0:
                    if diff > 0:
                        diff_color = '#4caf50'  # grün
                        diff_symbol = '▲'
                    elif diff < 0:
                        diff_color = '#e53935'  # rot
                        diff_symbol = '▼'
                    else:
                        diff_color = '#cccccc'  # neutral
                        diff_symbol = '•'
                    kaufwert_label = QLabel(f"Kaufwert: {einkauf:.2f} €")
                    kaufwert_label.setStyleSheet(f"font-size: 16px; margin-left: 8px; color: {diff_color};")
                    row_layout.addWidget(kaufwert_label)
                    diff_label = QLabel(f"{diff_symbol} {abs(diff):.2f} €")
                    diff_label.setStyleSheet(f"font-size: 16px; margin-left: 4px; color: {diff_color}; font-weight: bold;")
                    row_layout.addWidget(diff_label)
                row_layout.addStretch(1)
                row_widget.setLayout(row_layout)
                item = QListWidgetItem()
                item.setSizeHint(row_widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, row_widget)

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
