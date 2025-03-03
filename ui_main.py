import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QListWidget, 
                             QTextEdit, QFileDialog, QLabel, QProgressBar, QVBoxLayout, QWidget, QLineEdit)
from PyQt5.QtCore import QThread, pyqtSignal
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Controller, Key
import time
import json
from qreader import QReader
import cv2
from datetime import datetime

# Worker thread để đọc QR và gõ tự động
class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    update_log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, image_files=None, mode="read", cong_van="TLT-000", parent=None):
        super().__init__(parent)
        self.image_files = image_files
        self.mode = mode
        self.cong_van = cong_van  # Số công văn từ text box
        self.running = True
        self.keyboard = Controller()
        self.qreader = QReader()

    def vietnamese_to_telex(self, text):
        telex_map = {
            'à': 'af', 'á': 'as', 'ả': 'ar', 'ã': 'ax', 'ạ': 'aj',
            'è': 'ef', 'é': 'es', 'ẻ': 'er', 'ẽ': 'ex', 'ẹ': 'ej',
            'ì': 'if', 'í': 'is', 'ỉ': 'ir', 'ĩ': 'ix', 'ị': 'ij',
            'ò': 'of', 'ó': 'os', 'ỏ': 'or', 'õ': 'ox', 'ọ': 'oj',
            'ù': 'uf', 'ú': 'us', 'ủ': 'ur', 'ũ': 'ux', 'ụ': 'uj',
            'ỳ': 'yf', 'ý': 'ys', 'ỷ': 'yr', 'ỹ': 'yx', 'ỵ': 'yj',
            'ă': 'aw', 'ằ': 'awf', 'ắ': 'aws', 'ẳ': 'awr', 'ẵ': 'awx', 'ặ': 'awj',
            'â': 'aa', 'ầ': 'aaf', 'ấ': 'aas', 'ẩ': 'aar', 'ẫ': 'aax', 'ậ': 'aaj',
            'ê': 'ee', 'ề': 'eef', 'ế': 'ees', 'ể': 'eer', 'ễ': 'eex', 'ệ': 'eej',
            'ô': 'oo', 'ồ': 'oof', 'ố': 'oos', 'ổ': 'oor', 'ỗ': 'oox', 'ộ': 'ooj',
            'ơ': 'ow', 'ờ': 'owf', 'ớ': 'ows', 'ở': 'owr', 'ỡ': 'owx', 'ợ': 'owj',
            'ư': 'uw', 'ừ': 'uwf', 'ứ': 'uws', 'ử': 'uwr', 'ữ': 'uwx', 'ự': 'uwj',
            'đ': 'dd'
        }
        unaccented_map = {
            'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'đ': 'd'
        }
        result = ""
        for char in text.lower():
            if char in telex_map:
                result += telex_map[char]
            elif char in unaccented_map:
                result += unaccented_map[char]
            else:
                result += char
        return result

    def type_text(self, text):
        for char in text:
            if not self.running:
                break
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(0.15)

    def press_tab(self):
        self.keyboard.press(Key.tab)
        self.keyboard.release(Key.tab)
        time.sleep(0.1)

    def press_enter(self):
        self.keyboard.press(Key.enter)
        self.keyboard.release(Key.enter)
        time.sleep(0.1)

    def find_code_by_name(self, name, refer_code, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                result_data = json.load(file)
            name_lower = name.lower()
            result = [item for item in result_data if any(name_lower in key.lower() for key in item.keys())]
            if not result:
                return ""
            if len(result) == 1:
                key = next((k for k in result[0] if name_lower in k.lower()), None)
                if key:
                    values = result[0][key].split(", ")
                    return values[0] if len(values) > 1 else result[0][key]
            if len(result) > 1:
                result_with_refer_code = next((
                    item for item in result
                    if any(refer_code in item[k] for k in item if name_lower in k.lower())
                ), None)
                if not result_with_refer_code:
                    return ""
                key = next((k for k in result_with_refer_code if name_lower in k.lower()), None)
                if key:
                    return result_with_refer_code[key].replace(f", {refer_code}", "")
            return ""
        except Exception as e:
            self.update_log.emit(f"Lỗi đọc {file_path}: {str(e)}")
            return ""

    def find_ky_tu_tinh(self, tinh_name):
        try:
            with open('data/ky_tu_tinh.json', 'r', encoding='utf-8') as file:
                ky_tu_data = json.load(file)
            tinh_lower = tinh_name.lower()
            for item in ky_tu_data:
                key = next(iter(item))
                if tinh_lower == key.lower():
                    return item[key]
            return ""
        except Exception as e:
            self.update_log.emit(f"Lỗi data ky_tu_tinh.json: {str(e)}")
            return ""

    def qr_code_reader(self, path):
        try:
            image = cv2.imread(path)
            if image is None:
                return "Không thể đọc file ảnh"
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            decoded_text = self.qreader.detect_and_decode(image=image)
            if decoded_text and isinstance(decoded_text, tuple):
                qr_data = decoded_text[0]
            else:
                return "Không thể giải mã QR code"
            fields = qr_data.split('|')
            if len(fields) < 6:
                return "Dữ liệu QR không đủ để phân tích"
            ngaycccd = fields[-1]
            address = fields[5]
            address_parts = [part.strip() for part in address.split(',')]
            if len(address_parts) >= 4:
                tinh = address_parts[-1]
                huyen = address_parts[-2]
                xa_phuong_name = address_parts[-3]
                dia_chi = address_parts[-4]
            else:
                return "Địa chỉ không đầy đủ để phân tích"
            ma_tinh = self.find_code_by_name(tinh, None, 'data/tinh_tp.json')
            ma_huyen = self.find_code_by_name(huyen, ma_tinh, 'data/quan_huyen.json')
            ma_xa = self.find_code_by_name(xa_phuong_name, ma_huyen, 'data/xa_phuong.json')
            ky_tu_tinh = self.find_ky_tu_tinh(tinh)
            gioi_tinh = "M" if fields[4].lower() == "nam" else "F"
            result = {
                "cccd": fields[0], "ngay_cccd": ngaycccd, "ho_ten": fields[2],
                "ngay_sinh": fields[3], "gioi_tinh": gioi_tinh, "tinh": tinh,
                "ky_tu_tinh": ky_tu_tinh, "ma_tinh": ma_tinh, "huyen": huyen,
                "ma_huyen": ma_huyen, "xa": xa_phuong_name, "ma_xa": ma_xa,
                "dia_chi": dia_chi, "data": qr_data
            }
            return result
        except Exception as e:
            return f"Error: {str(e)}"

    def run(self):
        if self.mode == "read":
            results = {}
            error_images = {}
            total_files = len(self.image_files)
            for idx, file_path in enumerate(self.image_files):
                if not self.running:
                    break
                qr_result = self.qr_code_reader(file_path)
                if isinstance(qr_result, str):
                    error_images[file_path] = qr_result
                    self.update_log.emit(f"Hình ảnh lỗi {os.path.basename(file_path)}: {qr_result}")
                else:
                    results[file_path] = qr_result
                    self.update_log.emit(f"Đang xử lý {os.path.basename(file_path)}: {qr_result['cccd']}")
                self.update_progress.emit(int((idx + 1) / total_files * 100))
            if self.running:
                with open('result_infomations.json', 'w', encoding='utf-8') as json_file:
                    json.dump(results, json_file, ensure_ascii=False, indent=4)
                if error_images:
                    with open('error_images.json', 'w', encoding='utf-8') as error_file:
                        json.dump(error_images, error_file, ensure_ascii=False, indent=4)
                self.update_log.emit(f"Đã xử lý xong kết quả")
            else:
                self.update_log.emit("Đã hủy đọc QR!")

        elif self.mode == "type":
            try:
                with open('result_infomations.json', 'r', encoding='utf-8') as json_file:
                    results_data = json.load(json_file)
            except Exception as e:
                self.update_log.emit(f"Lỗi đọc data result_infomations.json: {str(e)}")
                self.finished.emit()
                return

            current_date = datetime.now().strftime("%d%m%Y")
            all_forms = []
            for filename, data in results_data.items():
                form = [
                    {"text": self.cong_van, "tab": True, "enter": None},  # Dùng số công văn từ text box
                    {"text": self.vietnamese_to_telex(data["ho_ten"]), "tab": True, "enter": None},
                    {"text": data["gioi_tinh"], "tab": True, "enter": None},
                    {"text": data["ngay_sinh"], "tab": None, "enter": None},
                    {"text": "D", "tab": True, "enter": None},
                    {"text": data["ky_tu_tinh"], "tab": True, "enter": None},
                    {"text": "1", "tab": True, "enter": None},
                    {"text": "8", "tab": True, "enter": None},
                    {"text": data["cccd"], "tab": None, "enter": None},
                    {"text": data["ngay_cccd"], "tab": None, "enter": None},
                    {"text": data["ky_tu_tinh"], "tab": True, "enter": None},
                    {"text": data["ky_tu_tinh"], "tab": True, "enter": None},
                    {"text": data["ma_huyen"], "tab": True, "enter": None},
                    {"text": data["ma_xa"], "tab": True, "enter": None},
                    {"text": self.vietnamese_to_telex(data["dia_chi"]), "tab": True, "enter": None},
                    {"text": "", "tab": True, "enter": None},
                    {"text": "1", "tab": True, "enter": None},
                    {"text": "2", "tab": True, "enter": None},
                    {"text": self.vietnamese_to_telex("tự do"), "tab": True, "enter": None},
                    {"text": "", "tab": True, "enter": None},
                    {"text": "", "tab": True, "enter": None},
                    {"text": "", "tab": True, "enter": None},
                    {"text": "", "tab": True, "enter": None},
                    {"text": current_date, "tab": None, "enter": True}
                ]
                all_forms.append(form)

            self.update_log.emit("Click chuột trái vào ứng dụng thứ 3 để bắt đầu nhập...")
            with MouseListener(on_click=self.on_click) as listener:
                listener.join()

            total_forms = len(all_forms)
            for idx, form_data in enumerate(all_forms):
                if not self.running:
                    break
                total_fields = len(form_data)
                for i, field in enumerate(form_data):
                    if not self.running:
                        break
                    self.type_text(field["text"])
                    if idx == total_forms - 1 and i == total_fields - 1:
                        break
                    if field.get("tab"):
                        self.press_tab()
                    elif field.get("enter"):
                        self.press_enter()
                self.update_progress.emit(int((idx + 1) / total_forms * 100))
                if idx < total_forms - 1:
                    self.update_log.emit(f"Đã xong Form {idx + 1}")
                    time.sleep(1)
            if self.running:
                self.update_log.emit("Đã gõ xong tất cả các form!")
            else:
                self.update_log.emit("Đã hủy nhập form!")

        self.finished.emit()

    def on_click(self, x, y, button, pressed):
        if pressed and str(button) == "Button.left":
            return False

    def stop(self):
        self.running = False

# Giao diện chính
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Auto Typer")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Thêm text box cho số công văn
        self.cong_van_label = QLabel("Số công văn:")
        self.cong_van_input = QLineEdit()
        self.cong_van_input.setText("TLT-000")  # Giá trị mặc định
        self.input_btn = QPushButton("Input QR Images")
        self.image_list = QListWidget()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.start_btn = QPushButton("Start Typing")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Chọn ảnh QR để bắt đầu.")

        # Thêm các widget vào layout
        layout.addWidget(self.cong_van_label)
        layout.addWidget(self.cong_van_input)
        layout.addWidget(self.input_btn)
        layout.addWidget(self.image_list)
        layout.addWidget(self.log_text)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.cancel_btn)

        self.input_btn.clicked.connect(self.select_images)
        self.start_btn.clicked.connect(self.start_typing)
        self.cancel_btn.clicked.connect(self.cancel_process)

        self.image_files = []
        self.worker = None

    def select_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn ảnh QR", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if files:
            self.image_files = files
            self.image_list.clear()
            for file in files:
                self.image_list.addItem(os.path.basename(file))
            self.log_text.append(f"Đã chọn {len(files)} ảnh.")
            self.worker = WorkerThread(self.image_files, mode="read")
            self.worker.update_progress.connect(self.progress_bar.setValue)
            self.worker.update_log.connect(self.log_text.append)
            self.worker.finished.connect(self.read_finished)
            self.worker.start()
            self.input_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)

    def start_typing(self):
        time.sleep(1)
        cong_van = self.cong_van_input.text().strip()  # Lấy số công văn từ text box
        if not cong_van:
            self.log_text.append("Vui lòng nhập số công văn!")
            return
        self.worker = WorkerThread(mode="type", cong_van=cong_van)  # Truyền số công văn vào worker
        self.worker.update_progress.connect(self.progress_bar.setValue)
        self.worker.update_log.connect(self.log_text.append)
        self.worker.finished.connect(self.process_finished)
        self.worker.start()
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

    def cancel_process(self):
        if self.worker:
            self.worker.stop()
            self.cancel_btn.setEnabled(False)

    def read_finished(self):
        self.input_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Đã đọc xong QR, nhấn Start Typing để nhập.")

    def process_finished(self):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Quá trình hoàn tất hoặc đã hủy.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())