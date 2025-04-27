# note to self: https://eu.qobuz.squid.wtf/api/get-music?q=ISRC&offset=0&limit=0
import csv
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QFileDialog,
    QDialog, QLineEdit, QDialogButtonBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl
import requests

class LoginDialog(QDialog):
    def __init__(self):
        self.session = ""
        
        super().__init__()
        self.setWindowTitle("Login to DAB")
        self.setFixedSize(300, 180)

        layout = QVBoxLayout(self)
        
        heading = QLabel("Login to DAB", self)
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(heading)
        
        form = QFormLayout()
        form.setFormAlignment(Qt.AlignmentFlag.AlignCenter)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Email")
        self.user_edit.setFixedHeight(30)
        self.user_edit.setMinimumWidth(250)
        self.user_edit.setStyleSheet("padding: 5px; border-radius: 5px; outline: none;")
        self.user_edit.setFocus()
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setPlaceholderText("Password")
        self.pass_edit.setFixedHeight(30)
        self.pass_edit.setMinimumWidth(250)
        self.pass_edit.setStyleSheet("padding: 5px; border-radius: 5px; outline: none;")
        form.addRow("Email", self.user_edit)
        form.addRow("Password", self.pass_edit)
        layout.addLayout(form, Qt.AlignmentFlag.AlignHCenter)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        username = self.user_edit.text().strip()
        password = self.pass_edit.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Email and password cannot be empty.")
            return # Stop the accept process
        try:
            # If validation passes, request DAB to see if login is fine
            response = requests.post("https://dab.yeet.su/api/auth/login", json={
                "email": username,
                "password": password
            })
            response.raise_for_status()  # Raise an error for bad responses
            cookies = response.cookies
            if "session" not in cookies:
                raise NotImplementedError("Session cookie not found in response.")
            # print(cookies["session"])
            self.session = cookies["session"]
            super().accept()
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Error", "Invalid email or password.")
            return
        except NotImplementedError as e:
            QMessageBox.warning(self, "Error", "Session cookie not found in response. Try again.")
            return
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An unexpected error occurred: {e}")
            return
        super().accept()

class CsvDropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.isrc_list = []
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout()

        # Add the heading label
        self.heading_label = QLabel("Exportify CSV to DAB Library", self)
        self.heading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.heading_label.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(self.heading_label)

        # Add the drag-and-drop label
        self.label = QLabel("Drag & Drop a CSV file here or click to browse", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                padding: 20px;
                min-height: 100px;
            }
        """)
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)
        self.setWindowTitle('Exportify CSV to DAB Library')
        # Adjusted height slightly for the new heading
        self.setGeometry(300, 300, 400, 200)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Check if the file is a CSV
            url = event.mimeData().urls()[0]
            if url.isLocalFile() and url.toLocalFile().lower().endswith('.csv'):
                event.acceptProposedAction()
                self.label.setStyleSheet("QLabel { border: 2px dashed #00f; padding: 20px; min-height: 100px; }") # Highlight border
            else:
                event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.label.setStyleSheet("QLabel { border: 2px dashed #aaa; padding: 20px; min-height: 100px; }") # Reset border

    def dropEvent(self, event):
        self.label.setStyleSheet("QLabel { border: 2px dashed #aaa; padding: 20px; min-height: 100px; }") # Reset border
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.csv'):
                    self.process_csv(file_path)
                else:
                    self.label.setText("Error: Please drop a CSV file.")
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_file_dialog()

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if file_path:
            self.process_csv(file_path)

    def process_csv(self, file_path):
        self.isrc_list = []
        try:
            with open(file_path, mode='r', encoding='utf-8', newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader) # Read the header row
                try:
                    # Find the index of the 'ISRC' column (case-insensitive)
                    isrc_index = [h.strip().lower() for h in header].index('isrc')
                except ValueError:
                    self.label.setText(f"Error: 'ISRC' column not found in {file_path}")
                    return

                for row in reader:
                    if len(row) > isrc_index:
                        isrc = row[isrc_index].strip()
                        if isrc: # Add only non-empty ISRCs
                            self.isrc_list.append(isrc)

            if self.isrc_list:
                self.label.setText(f"Successfully processed {file_path}\nFound {len(self.isrc_list)} ISRCs.\nSearching Qobuz database...")
                # For validation, run the ISRCs through SquidWTF then DAB using the ID (obviously slower)
                for isrc in self.isrc_list:
                    response = requests.get(f"https://eu.qobuz.squid.wtf/api/get-music?q={isrc}&offset=0&limit=0")
                    if response.status_code == 200:
                        data = response.json()["data"]["tracks"]["items"]
                        correct_ids = []
                        for item in data:
                            if item["isrc"] == isrc:
                                correct_ids.append(item["id"])
                        print(correct_ids)
                    else:
                        print(f"Error fetching ISRC {isrc}: {response.status_code}")
                print("Found ISRCs:", self.isrc_list) # Or store/use the list as needed
                login = LoginDialog()
                if login.exec() == QDialog.DialogCode.Accepted:
                    self.label.setText(f"Found {len(self.isrc_list)} ISRCs.\nSuccessfully logged in.")
                    # Example: send_isrcs_to_service(self.isrc_list, username, password)
            else:
                self.label.setText(f"Processed {file_path}\nNo ISRCs found or 'ISRC' column is empty.")

        except FileNotFoundError:
            self.label.setText(f"Error: File not found - {file_path}")
        except Exception as e:
            self.label.setText(f"Error processing file: {e}")
            print(f"Error processing file: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CsvDropWidget()
    ex.show()
    sys.exit(app.exec())