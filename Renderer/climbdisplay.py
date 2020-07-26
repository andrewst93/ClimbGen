import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt

HIGHLIGHT_RADIUS = 50
HIGHLIGHT_THICKNESS = 3

class Background(QLabel):
    def __init__(self, parent=None):
        super(Background, self).__init__(parent)
        pixmap = QPixmap('layout.jpg')
        self.setPixmap(pixmap)
        self.setScaledContents(True)
        self.highlights = []
        self.pens = [
            QPen(Qt.green, HIGHLIGHT_THICKNESS, Qt.SolidLine),
            QPen(Qt.blue, HIGHLIGHT_THICKNESS, Qt.SolidLine),
            QPen(Qt.red, HIGHLIGHT_THICKNESS, Qt.SolidLine),
            QPen(Qt.magenta, HIGHLIGHT_THICKNESS, Qt.SolidLine),
        ]

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        for highlight in self.highlights:
            painter.setPen(self.pens[highlight[2]])
            painter.drawEllipse(highlight[0], highlight[1], HIGHLIGHT_RADIUS, HIGHLIGHT_RADIUS)
    

class ClimbDisplay(QMainWindow):
    def __init__(self):
        super(ClimbDisplay, self).__init__()
        self.setWindowTitle('Tension Board Display')
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(748, 1248)
        self.layout = QStackedLayout()

        self.background = Background(self)    
        self.layout.addWidget(self.background)
        self.load_climb(r'Routes\test.json')

        centre = QWidget()
        centre.setLayout(self.layout)
        self.setCentralWidget(centre)
        self.show()
        
    def load_climb(self, climb_path: str):
        self.background.highlights.append((40, 40, 0))
        self.background.highlights.append((80, 80, 1))
        self.background.highlights.append((120, 120, 2))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ClimbDisplay()
    app.exec()
