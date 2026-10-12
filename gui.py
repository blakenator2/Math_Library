from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit, QLabel, QHBoxLayout, QTextEdit
import subprocess
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
from pathlib import Path
# Need to make cooler place for db to go

class StreamWriter(QObject):
    textWritten = pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text))
    def flush(self):
        pass
class SQLInsert(QThread):
    finished = pyqtSignal()
    def __init__(self, input):
        super().__init__()
        self.input = input
    def run(self):
        try:
            con = sqlite3.connect(f"{Path.home()}/library.db")
            cur = con.cursor()
            cur.execute(f"""
            INSERT INTO Library VALUES(?,?,?,?,?,?,?,?);
            """, (self.input[0], self.input[1], self.input[2], self.input[3], self.input[4], self.input[5], self.input[6], self.input[7]))
            con.commit()
            con.close()
            print("Added!")
            self.finished.emit()
        except Exception as e:
            print(e)
            self.finished.emit()
class ManualSearch(QThread):
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
    def run(self):
        db_path = f"{Path.home()}/library.db"
        applescript = f'''
        tell application "Terminal"
            activate
            set newTab to do script "sqlite3 \\"{db_path}\\""
            
            repeat while busy of newTab
                delay 0.5
            end repeat
        end tell
        '''
        p = subprocess.Popen(["osascript", "-e", applescript])
        p.wait()
        self.finished.emit()
class Scraping(QThread):
    finished = pyqtSignal(list)
    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            info = []
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')
            chrome_options.page_load_strategy = 'eager'
            driver = webdriver.Chrome(options=chrome_options)

            if " " in self.text:
                self.text = self.text.replace(" ", "+")

            driver.get(f"https://www.amazon.com/s?k={self.text}")

            firstResult = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "s-image"))
                )
            firstResult.click()

            name = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "productTitle"))
                ).text

            bookDesc = driver.find_element(By.ID, "bookDescription_feature_div").text.split("\n")[0]

            detailList = driver.find_element(By.ID, "detailBullets_feature_div").text.split("\n")

            for item in detailList:
                if "Publisher" in item or "Publication date" in item or "Print length" in item or "ISBN-10" in item or "ISBN-13" in item or item[0] == "#":
                    info.append(item)
            self.finished.emit([name, bookDesc, info]) 
        except Exception as e:
            print(e)
            self.finished.emit(["","",[]])
class CheckWindow(QWidget):
    finished = pyqtSignal(list)
    def __init__(self, results):
        super().__init__()
        self.name = results[0]
        self.desc = results[1]
        self.other = results[2]
        self.resize(700, 400)
        self.setWindowTitle("Results")
        try:
            if self.other[5:]:
                for i in range(5, len(self.other[5:])+5):
                    text = self.other[i]
                    self.other[i] = text[text.find("in")+3:]
            else:
                while(len(self.other) < 6):
                    self.other.append("")

            self.publisher = self.other[0][11:]
            self.date = self.other[1][18:]
            self.length = self.other[2][14:]
            self.ten = self.other[3][9:]
            self.thirteen = self.other[4][9:]
            self.genre = ", ".join(self.other[5:])

            self.setStyleSheet("""
            QWidget{
                background-color: #245632;
            }
            QLabel{
                color: #CFFFDC;
            }
            QPushButton{
                color: #CFFFDC;
            }
            QLineEdit{
                color: #CFFFDC;
            }
            QPushButton:hover{
                color: #147D6A;
                background-color: #1A3E24;
            }
            """)

            layout = QVBoxLayout()
            self.tlabel = QLabel("Pulled info (This is editable)")
            self.nLabel = QLabel("Book Name:")
            self.nEdit = QLineEdit(f"{self.name}")
            self.dLabel = QLabel("Book Description:")
            self.dEdit = QTextEdit(f"{self.desc}")
            self.dEdit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            self.pLabel = QLabel("Publisher:")
            self.pEdit = QLineEdit(f"{self.publisher}")
            self.dateLabel = QLabel("Date:")
            self.dateEdit = QLineEdit(f"{self.date}")
            self.lLabel = QLabel("Print Length:")
            self.lEdit = QLineEdit(f"{self.length}")
            self.tenLabel = QLabel("ISBN-10:")
            self.tenEdit = QLineEdit(f"{self.ten}")
            self.thLabel = QLabel("ISBN-13:")
            self.thEdit = QLineEdit(f"{self.thirteen}")
            self.gLabel = QLabel("Genre:")
            self.gEdit = QLineEdit(f"{self.genre}")

            hLayout = QHBoxLayout()
            self.aLabel = QLabel("Does this info look correct?")
            self.ybutton = QPushButton("Yes")
            self.ybutton.clicked.connect(self.yes)
            self.nbutton = QPushButton("No")
            self.nbutton.clicked.connect(self.no)

            layout.addWidget(self.tlabel)
            layout.addWidget(self.nLabel)
            layout.addWidget(self.nEdit)
            layout.addWidget(self.dLabel)
            layout.addWidget(self.dEdit)
            layout.addWidget(self.pLabel)
            layout.addWidget(self.pEdit)

            layout.addWidget(self.dateLabel)
            layout.addWidget(self.dateEdit)
            layout.addWidget(self.lLabel)
            layout.addWidget(self.lEdit)
            layout.addWidget(self.tenLabel)
            layout.addWidget(self.tenEdit)

            layout.addWidget(self.thLabel)
            layout.addWidget(self.thEdit)
            layout.addWidget(self.gLabel)
            layout.addWidget(self.gEdit)

            hLayout.addWidget(self.aLabel)
            hLayout.addWidget(self.ybutton)
            hLayout.addWidget(self.nbutton)

            flayout = QVBoxLayout()
            fwidget1 = QWidget()
            fwidget2 = QWidget()

            fwidget1.setLayout(layout)
            fwidget2.setLayout(hLayout)

            flayout.addWidget(fwidget1)
            flayout.addWidget(fwidget2)

            self.setLayout(flayout)
        except Exception as e:
            print(e)
            self.finished.emit()

    def yes(self):
        output = [
            self.nEdit.text(), 
            self.dEdit.toPlainText(),
            self.pEdit.text(),
            self.dateEdit.text(),
            self.lEdit.text(),
            self.tenEdit.text(),
            self.thEdit.text(),
            self.gEdit.text(),
        ]
        self.finished.emit(output)

    def no(self):
        output = [
            "", 
            "",
            "",
            "",
            "",
            "",
            "",
        ]
        self.finished.emit(output)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        con = sqlite3.connect(fr"{Path.home()}/library.db")
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Library(
                Name TEXT NOT NULL,
                Description TEXT,
                Publisher TEXT,
                "Publication Date" TEXT,
                "Print Length" TEXT,
                "ISBN-10" TEXT NOT NULL,
                "ISBN-13" TEXT,
                "Pulled Genres" TEXT,
                PRIMARY KEY (Name, "ISBN-10")
            );
            """)
        con.close()

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0,0,0,0)
        mainWidget = QWidget()
        self.resize(400, 200)
        self.setWindowTitle("Ellie's Library")

        self.setStyleSheet("""
        QMainWindow{
            background-color: #245632;
        }
        QLabel{
            color: #CFFFDC;
        }
        QPushButton{
            color: #CFFFDC;
        }
        QLineEdit{
            color: #CFFFDC;
        }
        QPushButton:hover{
            color: #147D6A;
            background-color: #1A3E24;
        }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        label = QLabel("Enter in ISBN-10:")
        self.enter = QLineEdit()
        self.enter.setPlaceholderText("Enter ISBN-10")
        
        hlayout = QHBoxLayout()
        self.button = QPushButton("Search")
        self.button.clicked.connect(self.search)
        self.manualButton = QPushButton("Manual Search")
        self.manualButton.clicked.connect(self.callManual)

        statuslayout = QVBoxLayout()
        self.status = QLabel("Status: Idle...")
        self.stream = StreamWriter()
        self.stream.textWritten.connect(self.update_label)
        sys.stdout = self.stream

        layout.addWidget(label)
        layout.addWidget(self.enter)
        layout.addWidget(self.button)

        hlayout.addWidget(self.button)
        hlayout.addWidget(self.manualButton)

        statuslayout.addWidget(self.status)

        mwidget = QWidget()
        bwidget = QWidget()
        swidget = QWidget()
        mwidget.setLayout(layout)
        bwidget.setLayout(hlayout)
        swidget.setLayout(statuslayout)

        mainLayout.addWidget(mwidget, alignment=Qt.AlignmentFlag.AlignVCenter)
        mainLayout.addWidget(bwidget, alignment=Qt.AlignmentFlag.AlignVCenter)
        mainLayout.addWidget(swidget, alignment=Qt.AlignmentFlag.AlignCenter)

        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

    def search(self):
        self.button.setEnabled(False)
        self.manualButton.setEnabled(False)
        if not (self.enter.text()):
            print("Enter in an ISBN")
            self.button.setEnabled(True)
            self.manualButton.setEnabled(True)
            return

        print("Scraping...")
        self.worker = Scraping(self.enter.text())
        self.worker.finished.connect(self.restore)
        self.worker.start()

    def callManual(self):
        self.button.setEnabled(False)
        self.manualButton.setEnabled(False)
        self.manual = ManualSearch()
        self.manual.finished.connect(self.finalStep)
        self.manual.start()
        

    def restore(self, results):
        self.w = CheckWindow(results)
        self.w.finished.connect(self.table)
        self.w.show()

    def table(self, input):
        self.w.close()
        self.w = None

        if not any(input):
            print("Canceled")
            self.button.setEnabled(True)
            self.manualButton.setEnabled(True)
            return

        print("Adding to database!")
        self.sql = SQLInsert(input)
        self.sql.finished.connect(self.finalStep)
        self.sql.start()

    def finalStep(self):
        self.button.setEnabled(True)
        self.manualButton.setEnabled(True)

    def update_label(self, text):
        clean = text.strip()
        if clean:
            self.status.setText(clean)
        
app = QApplication([])
window = MainWindow()
window.show() 
app.exec()