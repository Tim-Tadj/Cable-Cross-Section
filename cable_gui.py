import sys
import threading
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                               QColorDialog, QLabel, QSpinBox, QHBoxLayout)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
import main  # Import your main.py file

class CableGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cable Simulation GUI")

        self.core_color = QColor(*main.CORE_COLORS["single"])
        self.sheath_color = QColor(*main.CABLE_SHEATH_COLOR)
        self.background_color = QColor(*main.BACKGROUND_COLOR)

        self.initUI()
        self.start_pygame_thread()

    def initUI(self):
        layout = QVBoxLayout()

        # Color selection buttons
        self.core_color_button = self.create_color_button("Core Color", self.core_color, self.set_core_color)
        self.sheath_color_button = self.create_color_button("Sheath Color", self.sheath_color, self.set_sheath_color)
        self.background_color_button = self.create_color_button("Background Color", self.background_color, self.set_background_color)

        layout.addWidget(self.core_color_button)
        layout.addWidget(self.sheath_color_button)
        layout.addWidget(self.background_color_button)

        # Spawn Cable Button
        self.spawn_button = QPushButton("Spawn Cable")
        self.spawn_button.clicked.connect(self.spawn_cable)
        layout.addWidget(self.spawn_button)

        # Reset View Button
        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(self.reset_view)
        layout.addWidget(self.reset_button)

        self.setLayout(layout)

    def create_color_button(self, text, initial_color, callback):
        button = QPushButton(text)
        button.clicked.connect(lambda: self.open_color_dialog(initial_color, callback))
        return button

    def open_color_dialog(self, initial_color, callback):
        color = QColorDialog.getColor(initial_color, self)
        if color.isValid():
            callback(color)

    def set_core_color(self, color):
        self.core_color = color
        main.CORE_COLORS["single"] = (color.red(), color.green(), color.blue())

    def set_sheath_color(self, color):
        self.sheath_color = color
        main.CABLE_SHEATH_COLOR = (color.red(), color.green(), color.blue())

    def set_background_color(self, color):
        self.background_color = color
        main.BACKGROUND_COLOR = (color.red(), color.green(), color.blue())

    def spawn_cable(self):
        main.spawn_cable()

    def reset_view(self):
        main.reset_view()

    def start_pygame_thread(self):
        pygame_thread = threading.Thread(target=main.main)
        pygame_thread.daemon = True
        pygame_thread.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = CableGUI()
    gui.show()
    sys.exit(app.exec())