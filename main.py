import sys
# from pathlib import Path
# sys.path.append(str(Path(__file__).parent))
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True) # Enable scaling
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)    # Use high-res icons

# import os
# os.environ["QT_SCALE_FACTOR"] = "1.3"

from gui.main_window import ParameterGUI


def main():
    app = QApplication(sys.argv)
    font = app.font()
    font.setPointSize(10) # Adjust point size as needed
    app.setFont(font)
    gui = ParameterGUI()
    gui.show()    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()