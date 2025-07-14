import os
import json
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
            from PyQt6.QtWidgets import QListWidgetItem
            from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
            self.list_widget.clear()
            if os.path.exists("collections.json"):
                with open("collections.json", "r", encoding="utf-8") as f:
                    collections = json.load(f)
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
                        item = QListWidgetItem(f"{col['name']} | {len(col['cards'])} Karten | Wert: {sum(float(c.get('eur') or 0) for c in col['cards']):.2f} €")
                        item.setIcon(QIcon(pix))
                        self.list_widget.addItem(item)

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
