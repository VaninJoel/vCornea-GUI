from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PyQt5.QtCore import QPropertyAnimation

class CollapsibleGroupBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.toggle_button = QPushButton(text=title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet("QPushButton { text-align: left; }")
        self.toggle_button.clicked.connect(self.on_toggle)

        self.content_area = QWidget()
        # Initially collapsed
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)

        self.toggle_animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.toggle_animation.setDuration(200)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.toggle_button)
        self.main_layout.addWidget(self.content_area)

    def on_toggle(self):
        checked = self.toggle_button.isChecked()
        content_height = self.content_area.layout().sizeHint().height()
        self.toggle_animation.setDuration(200)
        if checked:
            self.toggle_animation.setStartValue(0)
            self.toggle_animation.setEndValue(content_height)
        else:
            self.toggle_animation.setStartValue(content_height)
            self.toggle_animation.setEndValue(0)
        self.toggle_animation.start()
