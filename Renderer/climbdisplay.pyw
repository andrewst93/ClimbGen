import sys, json, math

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QEvent, QPoint

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
        self.parent = parent
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

        super().installEventFilter(self)
        self.num_starts = 0

    def get_corrected_position(self, x, y ):
        x = BASE_OFFSET[0] + (x - BASE_OFFSET_SRC[0]) * GRID_SIZE[0] / GRID_SIZE_SRC[0]
        y = BASE_OFFSET[1] - (y - BASE_OFFSET_SRC[1]) * GRID_SIZE[1] / GRID_SIZE_SRC[1]
        return QPoint(int(x), int(y))

    def add_highlight(self, x, y, role):
        self.highlights.append((x, y, role))
        if role == 0:
            self.num_starts += 1

    # Draw highlights over the background image
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        for highlight in self.highlights:
            painter.setPen(self.pens[highlight[2]])
            pos = self.get_corrected_position(highlight[0], highlight[1])
            painter.drawEllipse(pos.x() - HIGHLIGHT_RADIUS / 2.0, pos.y() - HIGHLIGHT_RADIUS / 2.0, HIGHLIGHT_RADIUS, HIGHLIGHT_RADIUS)

    # On-click handler for modifying the climb
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonRelease:
            for hold_data in self.parent.holds_data:
                pos = self.get_corrected_position(hold_data['Coord X'], hold_data['Coord Y'])
                direction = (pos - event.pos())

                # Collision check
                if math.sqrt(math.pow(direction.x(), 2) + math.pow(direction.y(), 2)) <= HIGHLIGHT_RADIUS / 2.0:

                    # Search for matching existing highlight at this position
                    found = next((i for i, x in enumerate(self.highlights) if x[0] == hold_data['Coord X'] and x[1] == hold_data['Coord Y']), -1)

                    # Either add new one, or update found one
                    if found == -1:
                        self.add_highlight(hold_data['Coord X'], hold_data['Coord Y'], 0 if self.num_starts < 2 else 1)
                    elif self.highlights[found][2] == 3 or event.button() == Qt.RightButton:
                        del self.highlights[found]
                    else:
                        copy = self.highlights[found]
                        self.highlights[found] = (copy[0], copy[1], (copy[2] + 1) % 4)
                        self.num_starts -= 1 if copy[2] == 0 else 0
                        self.num_starts += 1 if copy[2] == 3 else 0

                    # Re-paint
                    self.update()
                    return True
             
        return False
    

class ClimbDisplay(QMainWindow):
    def __init__(self, path: str):
        super(ClimbDisplay, self).__init__()
        self.setWindowTitle('Tension Board Display')
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(748, 1248)
        self.layout = QStackedLayout()

        self.holds_data = []
        with open('holds_data.json', 'r') as file:
            self.holds_data = json.load(file)

        self.background = Background(self)    
        self.layout.addWidget(self.background)

        centre = QWidget()
        centre.setLayout(self.layout)
        self.setCentralWidget(centre)
        self.show()

        if DEBUG_RENDERING:
            for hold_data in self.holds_data:
                self.background.add_highlight(hold_data['Coord X'], hold_data['Coord Y'], 1)
        else:
            self.load_climb(path)

    # Loads a climb from a given .json file to be renderered
    def load_climb(self, path: str):
        path = path + '.json' if not path.endswith('.json') else path

        with open(path, 'r') as file:
            json_data = json.load(file)[0]
            for hold, role in zip(json_data['Holds'], json_data['Roles']):
                hold_data = self.holds_data[hold-1]
                self.background.add_highlight(hold_data['Coord X'], hold_data['Coord Y'], role - 1)

    def save_climb(self, path: str):
        # TO DO
        pass


app = QApplication([])
viewer = ClimbDisplay(TEST_CLIMB_PATH if __name__ == '__main__' else sys.argv[0])
app.exec()
