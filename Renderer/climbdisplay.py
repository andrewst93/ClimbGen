import sys, json

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt

# Settings to change for visuals etc.
TEST_CLIMB_PATH = r"Routes\Big Pinch Pinchin'.json"
HIGHLIGHT_RADIUS = 50
HIGHLIGHT_THICKNESS = 4
DEBUG_RENDERING = False

# Config settings to map SQLite DB pixel coords to this programs coords
BASE_OFFSET = (69.0, 1176.0)
BASE_OFFSET_SRC = (8.0, 4.0)
GRID_SIZE = (60.5, 60.5)
GRID_SIZE_SRC = (8.0, 8.0)

# Renders the main image and handles rendering highlights over the holds in the correct positions
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
            x = BASE_OFFSET[0] + (highlight[0] - BASE_OFFSET_SRC[0]) * GRID_SIZE[0] / GRID_SIZE_SRC[0] - HIGHLIGHT_RADIUS / 2.0
            y = BASE_OFFSET[1] - (highlight[1] - BASE_OFFSET_SRC[1]) * GRID_SIZE[1] / GRID_SIZE_SRC[1] - HIGHLIGHT_RADIUS / 2.0
            painter.drawEllipse(int(x), int(y), HIGHLIGHT_RADIUS, HIGHLIGHT_RADIUS)
    

class ClimbDisplay(QMainWindow):
    def __init__(self, path: str):
        super(ClimbDisplay, self).__init__()
        self.setWindowTitle('Tension Board Display')
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(748, 1248)
        self.layout = QStackedLayout()

        self.background = Background(self)    
        self.layout.addWidget(self.background)

        centre = QWidget()
        centre.setLayout(self.layout)
        self.setCentralWidget(centre)
        self.show()

        self.holds_data = []
        with open('holds_data.json', 'r') as file:
            self.holds_data = json.load(file)

            if DEBUG_RENDERING:
                for hold_data in self.holds_data:
                    self.background.highlights.append((hold_data['Coord X'], hold_data['Coord Y'], 1))

        if not DEBUG_RENDERING:
            self.load_climb(path)

    def load_climb(self, path: str):
        path = path + '.json' if not path.endswith('.json') else path

        with open(path, 'r') as file:
            json_data = json.load(file)[0]
            for hold, role in zip(json_data['Holds'], json_data['Roles']):
                hold_data = self.holds_data[hold-1]
                self.background.highlights.append((hold_data['Coord X'], hold_data['Coord Y'], role-1))


app = QApplication([])
viewer = ClimbDisplay(TEST_CLIMB_PATH if __name__ == '__main__' else sys.argv[0])
app.exec()
