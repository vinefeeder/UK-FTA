import sys
import os
import webbrowser
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QCheckBox
from PyQt6.QtCore import QThread, pyqtSignal

import shutil

# Check for available terminal emulators
def get_terminal():
    terminals = ["gnome-terminal", "xterm", "konsole", "lxterminal", "xfce4-terminal"]
    for term in terminals:
        if shutil.which(term):
            return term
    raise EnvironmentError("No suitable terminal emulator found.")

TERMINAL = None

if os.name == 'posix':
    TERMINAL = get_terminal()
elif os.name == 'nt':  # Windows
    if shutil.which("WindowsTerminal.exe"):
        TERMINAL = "WindowsTerminal.exe"
    elif shutil.which("OpenConsole.exe"):
        TERMINAL = "OpenConsole.exe"
    elif shutil.which("powershell.exe"):
        TERMINAL = "powershell.exe"
    else:
        TERMINAL = "cmd.exe"

class ScriptRunner(QThread):
    finished = pyqtSignal()
    script = ""
    title = ""

    def __init__(self, script):
        super().__init__()
        self.script = script
        if script == None:
            pass
        else:
            self.title = script.split('/')[-1]

    def run(self):
        if self.script == 'ukfta/configs/config.py':
            if os.name == 'posix':
                os.system(f'{TERMINAL} -- bash -c "nano ukfta/configs/config.py" &')
            else:
                if TERMINAL == "WindowsTerminal.exe":
                    os.system(f'start wt "notepad.exe ./ukfta/configs/config.py"')
                elif TERMINAL == "OpenConsole.exe" or TERMINAL == "cmd.exe":
                    os.system(f'start cmd /k notepad.exe ./ukfta/configs/config.py')
                elif TERMINAL == "powershell.exe":
                    os.system(f'start powershell.exe -Command "notepad.exe ./ukfta/configs/config.py"')
                else:
                    os.system('start notepad.exe ./ukfta/configs/config.py')
        else:
            if os.name == 'posix':
                os.system(f'{TERMINAL} --tab --title "{self.title}" -- bash -c "python {self.script}; exec bash" &')
            else:
                if TERMINAL == "WindowsTerminal.exe":
                    os.system(f'start wt "python {self.script}"')
                elif TERMINAL == "OpenConsole.exe" or TERMINAL == "cmd.exe":
                    os.system(f'start cmd /k python {self.script}')
                elif TERMINAL == "powershell.exe":
                    os.system(f'start powershell.exe -Command "python {self.script}"')
                else:
                    os.system(f'start cmd /k python {self.script}')
        self.finished.emit()

class UKFTAGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 200, 400)
        self.setWindowTitle('UK-FTA')

        self.light_theme = """
        QWidget {
            background-color: #ffffff;
            color: #000000;
        }
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #c0c0c0;
            padding: 5px;
        }
        """
        
        self.dark_theme = """
        QWidget {
            background-color: #2e2e2e;
            color: #ffffff;
        }
        QPushButton {
            background-color: #4e4e4e;
            border: 1px solid #6e6e6e;
            padding: 5px;
        }
        """

        layout = QVBoxLayout()

        title_label = QLabel('UK-FTA')
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: green;")
        layout.addWidget(title_label)

        subtitle_label = QLabel('Search, Select and Download.\n\nWhich Channel?')
        subtitle_label.setStyleSheet("font-size: 14px; color: red;")
        layout.addWidget(subtitle_label)

        buttons = [
            ('BBC', 'ukfta/bbc_dl/getBBCLinks.py'),
            ('ITVX', 'ukfta/itv_dl/itv_loader.py'),
            ('All4', 'ukfta/c4_dl/chan4_loader.py'),
            ('My5', 'ukfta/my5_dl/my5_loader.py'),
            ('U', 'ukfta/uktvp/uktvp_loader.py'),
            ('STV', 'ukfta/stv_dl/stv_loader.py'),
            ('TPTV', 'ukfta/tptvencore/TalkingPics.py'),
            ('AllHell3 GUI', 'ukfta/allhell3gui.py'),
            ('______', None),
            ('Config', 'ukfta/configs/config.py'),
            ('Update My5', 'ukfta/my5_dl/hmac-aes-update.py'),
            ('Batch Download', 'ukfta/getbatch.py')
        ]
        for label, script in buttons:
            if label == '______':
                button = QPushButton('--><--')
                button.clicked.connect(lambda: webbrowser.open('https://forum.videohelp.com/threads/411884-UK-Free-to-Air-Downloader'))
                layout.addWidget(button)
            else:
                button = QPushButton(label)
                button.clicked.connect(lambda _, s=script: self.run_script(s))
                layout.addWidget(button)

        # Add light/dark theme toggle
        theme_layout = QHBoxLayout()
        self.theme_checkbox = QCheckBox('Light Theme')
        self.theme_checkbox.stateChanged.connect(self.toggle_theme)
        theme_layout.addWidget(self.theme_checkbox)
        layout.addLayout(theme_layout)

        self.setLayout(layout)
        self.apply_dark_theme()

    def run_script(self, script):
        self.script_runner = ScriptRunner(script)
        self.script_runner.finished.connect(self.on_script_finished)
        self.script_runner.start()

    def on_script_finished(self):
        print("Script execution finished.")

    def toggle_theme(self):
        if self.theme_checkbox.isChecked():
            self.apply_light_theme()
        else:
            self.apply_dark_theme()

    def apply_light_theme(self):
        self.setStyleSheet(self.light_theme)

    def apply_dark_theme(self):
        self.setStyleSheet(self.dark_theme)

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        gui = UKFTAGUI()
        gui.show()
        sys.exit(app.exec())
    except EnvironmentError as e:
        print(e)
        sys.exit(1)
