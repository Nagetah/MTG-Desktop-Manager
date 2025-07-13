# ui_startscreen.py
# Startscreen-UI
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


###############################################################
# --- MOVE TO ui_startscreen.py ---
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