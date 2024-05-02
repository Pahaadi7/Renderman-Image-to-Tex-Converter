import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QListWidget, QMessageBox, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class ConverterThread(QThread):
    progress_changed = pyqtSignal(int)
    conversion_finished = pyqtSignal(list, list)

    def __init__(self, texmake_path, input_files):
        super().__init__()
        self.texmake_path = texmake_path
        self.input_files = input_files

    def run(self):
        success_list = []
        fail_list = []
        total_files = len(self.input_files)
        for index, input_file in enumerate(self.input_files):
            try:
                output_file = input_file.rsplit('.', 1)[0] + "_tex.tex"
                command = f'"{self.texmake_path}" "{input_file}" "{output_file}"'
                subprocess.run(command, shell=True, check=True)
                success_list.append(os.path.basename(input_file))
            except Exception as e:
                fail_list.append(os.path.basename(input_file))
            progress = int((index + 1) / total_files * 100)
            self.progress_changed.emit(progress)

        self.conversion_finished.emit(success_list, fail_list)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.texmake_path = ""
        self.input_files = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Add a QLabel to display the icon image
        icon_label = QLabel()
        icon_path = resource_path("renderman.png")  # Use resource_path function to get the absolute path
        pixmap = QPixmap(icon_path)  
        scaled_width = int(pixmap.width() * 0.50)  # Scale width by 75%
        scaled_height = int(pixmap.height() * 0.55)  # Scale height by 75%
        pixmap = pixmap.scaled(scaled_width, scaled_height) 
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        header_label = QLabel("Batch Image to TEX Converter")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header_label)

        texmake_layout = QHBoxLayout()
        texmake_label = QLabel("TxMake Path:")
        texmake_layout.addWidget(texmake_label)
        self.texmake_label = QLabel("Please select txmake.exe")
        self.texmake_label.setStyleSheet("border: 1px solid black; padding: 5px;")
        texmake_layout.addWidget(self.texmake_label)
        select_texmake_button = QPushButton("Select")
        select_texmake_button.clicked.connect(self.select_texmake)
        select_texmake_button.setStyleSheet("padding: 5px;")
        texmake_layout.addWidget(select_texmake_button)
        layout.addLayout(texmake_layout)

        image_files_layout = QHBoxLayout()
        image_files_label = QLabel("Image Files:")
        image_files_layout.addWidget(image_files_label)
        self.image_files_list = QListWidget()
        image_files_layout.addWidget(self.image_files_list)
        layout.addLayout(image_files_layout)

        select_images_button = QPushButton("Select Images")
        select_images_button.clicked.connect(self.select_images)
        select_images_button.setStyleSheet("padding: 5px;")
        layout.addWidget(select_images_button)

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_image)
        remove_button.setStyleSheet("padding: 5px;")
        layout.addWidget(remove_button)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        convert_button = QPushButton("Convert")
        convert_button.clicked.connect(self.convert_images)
        convert_button.setObjectName("convertButton")  # Set object name for styling
        layout.addWidget(convert_button)

        footer_label = QLabel("Developed by Anshul Vashist")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(footer_label)

        self.setLayout(layout)
        self.setWindowTitle("Batch Image to TEX Converter")
        self.show()

    def select_texmake(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select texmake.exe File", "", "Executable Files (*.exe)")
        if file_path:
            self.texmake_path = file_path
            self.texmake_label.setText(os.path.basename(file_path))

    def select_images(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Image Files (*.tiff *.exr *.jpg *.jpeg *.sgi *.tga *.iff *.dpx *.bmp *.hdr *.png *.gif *.ppm *.xpm *.tex *.z)")
        file_paths, _ = file_dialog.getOpenFileNames(self, "Select Image Files", "", "Image Files (*.tiff *.exr *.jpg *.jpeg *.sgi *.tga *.iff *.dpx *.bmp *.hdr *.png *.gif *.ppm *.xpm *.tex *.z)")
        if file_paths:
            for file_path in file_paths:
                self.input_files.append(file_path)
                self.image_files_list.addItem(os.path.basename(file_path))


    def remove_image(self):
        selected_item = self.image_files_list.currentItem()
        if selected_item:
            index = self.image_files_list.row(selected_item)
            self.input_files.pop(index)
            self.image_files_list.takeItem(index)

    def convert_images(self):
        if not self.texmake_path:
            QMessageBox.warning(self, "Warning", "Please select texmake.exe file.")
            return
        if not self.input_files:
            QMessageBox.warning(self, "Warning", "No image files selected.")
            return

        self.progress_bar.setValue(0)
        self.converter_thread = ConverterThread(self.texmake_path, self.input_files)
        self.converter_thread.progress_changed.connect(self.update_progress)
        self.converter_thread.conversion_finished.connect(self.show_conversion_status)
        self.converter_thread.start()

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def show_conversion_status(self, success_list, fail_list):
        if success_list and fail_list:
            QMessageBox.information(None, "Conversion Status", f"Conversion Status:\n\nFailed to convert:\n{', '.join(fail_list)}")
        elif success_list:
            QMessageBox.information(None, "Conversion Status", "All images converted successfully.")
        elif fail_list:
            QMessageBox.information(None, "Conversion Status", f"Failed to convert:\n{', '.join(fail_list)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(open(resource_path("style.css")).read())

    # Create QIcon object with the path to your icon
    icon_path = resource_path("renderman.png")  # Use resource_path function to get the absolute path
    icon = QIcon(icon_path)

    # Create main window and set its icon
    window = MainWindow()
    window.setWindowIcon(icon)

    sys.exit(app.exec_())
