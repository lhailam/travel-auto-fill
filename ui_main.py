import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QListWidget, 
                             QTextEdit, QFileDialog, QLabel, QProgressBar, QVBoxLayout, QWidget, QLineEdit)
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Controller, Key
import time
import json
from qreader import QReader
import cv2
from datetime import datetime
import chardet
import ftfy
import unicodedata
import os
from google.cloud import vision
import requests
import random
from flask import Flask, request, jsonify
import threading
import mysql.connector
from mysql.connector import Error
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "google_auth.json"

# Worker thread để đọc QR và gõ tự động
class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    update_log = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, image_files=None, mode="read", cong_van="TLT-000", parent=None):
        super().__init__(parent)
        self.image_files = image_files
        self.mode = mode
        self.cong_van = cong_van
        self.running = True
        self.keyboard = Controller()
        self.qreader = QReader()
        self._is_running = True
        self._pause = False
        self._lock = QMutex()
        self._wait_condition = QWaitCondition()

    def pause(self):
        """Tạm dừng thread"""
        self._lock.lock()
        self._pause = True
        self._lock.unlock()

    def resume(self):
        """Tiếp tục thread"""
        self._lock.lock()
        self._pause = False
        self._lock.unlock()

    def stop(self):
        """Dừng thread"""
        self._lock.lock()
        self._is_running = False
        self._pause = False
        self._lock.unlock()
        self.wait()

    def is_running(self):
        """Kiểm tra thread có đang chạy không"""
        self._lock.lock()
        is_running = self._is_running
        self._lock.unlock()
        return is_running

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
            
            # Thêm độ trễ ngẫu nhiên để mô phỏng gõ tự nhiên hơn
            delay = 0.25 + (random.random() * 0.1)  # Độ trễ từ 0.25-0.35s
            
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(delay)

    def press_tab(self):
        self.keyboard.press(Key.tab)
        self.keyboard.release(Key.tab)
        time.sleep(0.15)

    def press_enter(self):
        self.keyboard.press(Key.enter)
        self.keyboard.release(Key.enter)
        time.sleep(0.1)

    def find_code_by_name(self, name, refer_code, file_path):
        try:
            if not os.path.exists(file_path):
                self.update_log.emit(f"File không tồn tại: {file_path}")
                return ""
                
            with open(file_path, "r", encoding="utf-8") as file:
                result_data = json.load(file)
                
            if not isinstance(result_data, list):
                self.update_log.emit(f"Dữ liệu không đúng định dạng trong {file_path}")
                return ""
                
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
        except json.JSONDecodeError as e:
            self.update_log.emit(f"Lỗi đọc JSON từ {file_path}: {str(e)}")
            return ""
        except Exception as e:
            self.update_log.emit(f"Lỗi đọc {file_path}: {str(e)}")
            return ""

    def find_xa_phuong_by_name(self, xa_phuong_name, ma_huyen, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        xa_phuong_name_lower = xa_phuong_name.lower()

        for item in data:
            for key, value in item.items():
                codes = value.split(", ")
                if ma_huyen in codes and xa_phuong_name_lower in key.lower():
                    return key

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


    def detect_encoding(self, text):
        if not text:
            return text

        text_fixed = ftfy.fix_text(text)

        if "?" not in text_fixed and "�" not in text_fixed:
            return text_fixed

        possible_encodings = ["utf-8", "latin-1", "shift-jis", "big5"]
        for enc in possible_encodings:
            try:
                fixed_text = text.encode(enc).decode("utf-8")
                return fixed_text
            except (UnicodeDecodeError, UnicodeEncodeError):
                continue

        detected = chardet.detect(text.encode("utf-8", errors="ignore"))
        encoding = detected.get("encoding", "utf-8")

        try:
            return text.encode(encoding).decode("utf-8")
        except:
            return text_fixed

    def is_valid_vietnamese(self, text):
        # Danh sách các ký tự hợp lệ trong tiếng Việt
        vietnamese_chars = "aáàảãạăắằẳẵặâấầẩẫậbcdđeéèẻẽẹêếềểễệfghiíìỉĩịjklmnoóòỏõọôốồổỗộơớờởỡợpqrs"
        vietnamese_chars += "tuúùủũụưứừửữựvwx"
        vietnamese_chars += "yýỳỷỹỵzAÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬBCDĐEÉÈẺẼẸÊẾỀỂỄỆFGHIÍÌỈĨỊJKLMNOÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢPQRS"
        vietnamese_chars += "TUÚÙỦŨỤƯỨỪỬỮỰVWX"
        vietnamese_chars += "YÝỲỶỸỴZ0123456789.,- "

        # Kiểm tra từng ký tự có thuộc danh sách tiếng Việt hay không
        return all(c in vietnamese_chars for c in text)
    
    def normalize_text(self, text):
        """Chuẩn hóa Unicode (NFC, NFD) để tránh lỗi hiển thị"""
        return unicodedata.normalize("NFC", text)


    def detect_text_google(self, image_path):
        """Sử dụng Google Vision API để nhận diện văn bản từ ảnh"""
        client = vision.ImageAnnotatorClient()

        with open(image_path, "rb") as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Google Vision API Error: {response.error.message}")
        
        text = response.full_text_annotation.text
        return text

    def extract_name(self, text):
        """Lọc họ và tên từ dữ liệu quét được, lấy dòng ngay dưới 'Họ và tên I Full name:'"""
        lines = text.split("\n")
        
        for i, line in enumerate(lines):
            if "Họ và tên I Full name" in line:
                # Kiểm tra dòng tiếp theo có phải là tên không
                if i + 1 < len(lines):
                    name_line = lines[i + 1].strip()
                    if name_line.isupper():  # Chỉ lấy nếu là chữ in hoa (tên thường in hoa trên CCCD)
                        return name_line

        return "Không tìm thấy tên"


    def qr_code_reader(self, path):
        try:
            if not os.path.exists(path):
                return "File ảnh không tồn tại"
                
            image = cv2.imread(path)
            if image is None:
                return "Không thể đọc file ảnh"
                
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            decoded_result = self.qreader.detect_and_decode(image=image)

            if not decoded_result:
                return "Không tìm thấy QR code trong ảnh"

            decoded_text = decoded_result[0] if isinstance(decoded_result, tuple) else decoded_result

            if not decoded_text:
                return "Không thể giải mã QR code"

            decoded_text = self.detect_encoding(decoded_text)
            decoded_text = self.normalize_text(decoded_text)

            fields = decoded_text.split('|')
            print("fields: ",fields)
            if len(fields) < 7:
                return "Dữ liệu QR không đủ để phân tích"

            fullname = fields[2]
            if not self.is_valid_vietnamese(fullname):
                try:
                    text_result = self.detect_text_google(path)
                    fullname = self.extract_name(text_result)
                except Exception as e:
                    self.update_log.emit(f"Lỗi khi sử dụng Google Vision API: {str(e)}")

            ngaycccd = fields[6]
            address = fields[5]
            address_parts = [part.strip() for part in address.split(',')]
            
            if len(address_parts) < 4:
                return "Địa chỉ không đầy đủ để phân tích"

            tinh = address_parts[-1]
            huyen = address_parts[-2]
            xa_phuong_name = address_parts[-3]
            dia_chi = address_parts[-4]

            ma_tinh = self.find_code_by_name(tinh, None, 'data/tinh_tp.json')
            if not ma_tinh:
                return "Không tìm thấy mã tỉnh"

            ma_huyen = self.find_code_by_name(huyen, ma_tinh, 'data/quan_huyen.json')
            if not ma_huyen:
                return "Không tìm thấy mã huyện"

            ten_xa = self.find_xa_phuong_by_name(xa_phuong_name, ma_huyen, 'data/xa_phuong.json')
            if not ten_xa:
                return "Không tìm thấy tên xã"

            ky_tu_tinh = self.find_ky_tu_tinh(tinh)
            if not ky_tu_tinh:
                return "Không tìm thấy ký tự tỉnh"

            gioi_tinh = "M" if fields[4].lower() == "nam" else "F"

            result = {
                "cccd": fields[0], "ngay_cccd": ngaycccd, "ho_ten": fullname,
                "ngay_sinh": fields[3], "gioi_tinh": gioi_tinh, "tinh": tinh,
                "ky_tu_tinh": ky_tu_tinh, "ma_tinh": ma_tinh, "huyen": huyen,
                "ma_huyen": ma_huyen, "xa": xa_phuong_name, "ten_xa": ten_xa,
                "dia_chi": dia_chi, "data": decoded_text, "cong_van": self.cong_van
            }
            return result
            
        except Exception as e:
            return f"Lỗi xử lý QR code: {str(e)}"

    def run(self):
        try:
            if self.mode == "read":
                self._run_read_mode()
            elif self.mode == "type":
                self._run_type_mode()
        except Exception as e:
            self.error.emit(f"Lỗi trong quá trình xử lý: {str(e)}")
        finally:
            self.finished.emit()

    def _run_read_mode(self):
        """Xử lý chế độ đọc QR"""
        try:
            results = {}
            error_images = {}
            total_files = len(self.image_files)

            for idx, file_path in enumerate(self.image_files):
                if not self.is_running():
                    break

                self._check_pause()

                qr_result = self.qr_code_reader(file_path)
                if isinstance(qr_result, str):
                    error_images[file_path] = qr_result
                    self.update_log.emit(f"Hình ảnh lỗi {os.path.basename(file_path)}: {qr_result}")
                else:
                    results[file_path] = qr_result
                    self.update_log.emit(f"Đang xử lý {os.path.basename(file_path)}: {qr_result['cccd']}")

                self.update_progress.emit(int((idx + 1) / total_files * 100))

            if self.is_running():
                self._save_results(results, error_images)
                self.update_log.emit("Đã xử lý xong kết quả")
            else:
                self.update_log.emit("Đã hủy đọc QR!")

        except Exception as e:
            self.error.emit(f"Lỗi trong chế độ đọc: {str(e)}")

    def _run_type_mode(self):
        """Xử lý chế độ nhập liệu"""
        try:
            if not os.path.exists('result_infomations.json'):
                self.error.emit("Không tìm thấy file kết quả đọc QR!")
                return

            with open('result_infomations.json', 'r', encoding='utf-8') as json_file:
                results_data = json.load(json_file)

            current_date = datetime.now().strftime("%d%m%Y")
            all_forms = self._prepare_forms(results_data, current_date)

            self.update_log.emit("Click chuột trái vào ứng dụng thứ 3 để bắt đầu nhập...")
            with MouseListener(on_click=self.on_click) as listener:
                listener.join()

            self._process_forms(all_forms)

        except Exception as e:
            self.error.emit(f"Lỗi trong chế độ nhập: {str(e)}")

    def _check_pause(self):
        """Kiểm tra và xử lý tạm dừng"""
        self._lock.lock()
        while self._pause and self._is_running:
            self._wait_condition.wait(self._lock)
        self._lock.unlock()

    def _save_results(self, results, error_images):
        """Lưu kết quả xử lý và gửi lên server"""
        try:
            # Lưu vào file local như cũ
            with open('result_infomations.json', 'w', encoding='utf-8') as json_file:
                json.dump(results, json_file, ensure_ascii=False, indent=4)
            if error_images:
                with open('error_images.json', 'w', encoding='utf-8') as error_file:
                    json.dump(error_images, error_file, ensure_ascii=False, indent=4)
            
            # Gửi dữ liệu lên server
            for data in results.values():
                try:
                    response = requests.post(
                        'http://localhost:5000/save_user',
                        json=data,
                        headers={'Content-Type': 'application/json'}
                    )
                    if response.status_code == 200:
                        self.update_log.emit(f"Đã lưu thông tin {data['ho_ten']} lên server")
                    else:
                        self.update_log.emit(f"Lỗi khi lưu lên server: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    self.update_log.emit(f"Lỗi kết nối server: {str(e)}")
                    
        except Exception as e:
            self.error.emit(f"Lỗi khi lưu kết quả: {str(e)}")

    def _prepare_forms(self, results_data, current_date):
        """Chuẩn bị dữ liệu form"""
        all_forms = []
        for data in results_data.values():
            form = [
                {"text": self.cong_van, "tab": True, "enter": None},
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
                {"text": "", "tab": True, "enter": None},
                {"text": self.vietnamese_to_telex(f"{data['dia_chi']}, {data['ten_xa']}"), "tab": True, "enter": None},
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
        return all_forms

    def _process_forms(self, all_forms):
        """Xử lý nhập liệu form"""
        total_forms = len(all_forms)
        for idx, form_data in enumerate(all_forms):
            if not self.is_running():
                break

            self._check_pause()

            total_fields = len(form_data)
            for i, field in enumerate(form_data):
                if not self.is_running():
                    break

                self._check_pause()

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

        if self.is_running():
            self.update_log.emit("Đã gõ xong tất cả các form!")
        else:
            self.update_log.emit("Đã hủy nhập form!")

    def on_click(self, x, y, button, pressed):
        """Xử lý sự kiện click chuột"""
        if pressed and str(button) == "Button.left":
            return False

# Thêm class WebServerThread
class WebServerThread(QThread):
    def __init__(self, port=5000):
        super().__init__()
        self.port = port
        self.app = Flask(__name__)
        self._running = True  # Thêm flag để kiểm soát server
        
        # Cấu hình database
        self.DB_USER = "user"
        self.DB_PASSWORD = "password" 
        self.DB_HOST = "14.225.206.102"
        self.DB_NAME = "travel_web"
        
        # Tạo URL kết nối
        self.DATABASE_URL = f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"
        
        # Move route definitions inside __init__
        self.setup_routes()

    def setup_routes(self):
        # Define routes using add_url_rule instead of decorators
        self.app.add_url_rule('/', 'hello', self.hello)
        self.app.add_url_rule('/save_user', 'save_user', self.save_user, methods=['POST'])

    def hello(self):
        try:
            print("\n=== Testing Database Connection ===")
            engine = self.create_db_engine()
            if engine:
                with engine.connect() as connection:
                    result = connection.execute(text("SELECT VERSION()"))
                    version = result.scalar()
                    print(f"Connected to MySQL version: {version}")
                    return f"Successfully connected to MySQL!\nServer version: {version}"
            return "Failed to create database engine"
            
        except SQLAlchemyError as e:
            error = str(e.__dict__['orig'])
            print(f"Database error: {error}")
            return f"Database error: {error}"
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return f"Error: {str(e)}"

    def create_db_engine(self):
        """Tạo engine kết nối database"""
        try:
            print("Creating database engine...")
            engine = create_engine(
                self.DATABASE_URL,
                pool_recycle=3600,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_pre_ping=True
            )
            print("Engine created successfully")
            return engine
        except Exception as e:
            print(f"Error creating engine: {str(e)}")
            return None

    def test_connection(self):
        """Test kết nối database"""
        try:
            engine = self.create_db_engine()
            if engine:
                with engine.connect() as connection:
                    # Test basic connectivity - use text() for raw SQL
                    result = connection.execute(text("SELECT 1"))
                    result.fetchone()
                    
                    # Get server version - use text() for raw SQL
                    version_result = connection.execute(text("SELECT VERSION()"))
                    version = version_result.scalar()
                    print(f"Connected to MySQL version: {version}")
                    
                    # Test if customers table exists - use text() for raw SQL
                    try:
                        table_result = connection.execute(text("SHOW TABLES LIKE 'customers'"))
                        if table_result.fetchone():
                            print("Customers table exists")
                        else:
                            print("Customers table not found")
                    except Exception as table_error:
                        print(f"Error checking customers table: {str(table_error)}")
                    
                    print("Connection test successful!")
                    return True
            return False
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False

    @staticmethod
    def convert_date_format(date_str):
        """Convert date from DDMMYYYY to YYYY-MM-DD format"""
        try:
            if not date_str:
                return None
            return datetime.strptime(date_str, '%d%m%Y').strftime('%Y-%m-%d')
        except ValueError:
            print(f"Invalid date format: {date_str}")
            return None


    def save_user(self):
        try:
            data = request.json
            print("Call API save_user")
            # Validate required fields
            required_fields = ['ho_ten', 'cccd', 'dia_chi']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            engine = self.create_db_engine()
            if not engine:
                return jsonify({'error': 'Database connection failed'}), 500
            
            # Convert dates
            ngay_cccd = self.convert_date_format(data['ngay_cccd'])
            ngay_sinh = self.convert_date_format(data['ngay_sinh'])
            
            if ngay_cccd is None or ngay_sinh is None:
                return jsonify({'error': 'Invalid date format. Use DDMMYYYY'}), 400

            # Construct full address
            full_address = f"{data['dia_chi']}, {data.get('xa', '')}, {data.get('huyen', '')}, {data.get('tinh', '')}"
            gioitinh = 'Nam' if data['gioi_tinh'] == 'M' else 'Nữ'
            national = ''
            ma_xa = ''
            documentNumber = data['cong_van']        
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert user data using SQLAlchemy
            insert_query = text("""
            INSERT INTO customers (
                documentNumber, cardID, createdAtCard, dayOfBirth, fullName, 
                gender, national, province, district, commune, provinceCode, 
                districtCode, communeCode, address, createdAt, updatedAt, deletedAt
            ) VALUES (
                :doc_num, :card_id, :created_at_card, :dob, :full_name,
                :gender, :national, :province, :district, :commune, :province_code,
                :district_code, :commune_code, :address, :created_at, :updated_at, :deleted_at
            )
            """)
            
            with engine.connect() as connection:
                connection.execute(insert_query, {
                    'doc_num': documentNumber,
                    'card_id': data['cccd'],
                    'created_at_card': ngay_cccd,
                    'dob': ngay_sinh,
                    'full_name': data['ho_ten'],
                    'gender': gioitinh,
                    'national': national,
                    'province': data['tinh'],
                    'district': data['huyen'],
                    'commune': data['xa'],
                    'province_code': data['ma_tinh'],
                    'district_code': data['ma_huyen'],
                    'commune_code': ma_xa,
                    'address': full_address,
                    'created_at': current_time,
                    'updated_at': current_time,
                    'deleted_at': None
                })
                connection.commit()
            
            print("User information saved successfully")
            return jsonify({'message': 'User information saved successfully'}), 200
            
        except SQLAlchemyError as e:
            error_msg = str(e.__dict__['orig'])
            if 'Duplicate entry' in error_msg:
                return jsonify({'error': 'CCCD already exists'}), 409
            return jsonify({'error': f'Database error: {error_msg}'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def run(self):
        if self.test_connection():
            print("Database connection verified, starting server...")
            # Chạy server trong thread riêng để có thể dừng
            server_thread = threading.Thread(target=self.run_server)
            server_thread.daemon = True  # Đảm bảo thread sẽ dừng khi chương trình chính dừng
            server_thread.start()
        else:
            print("Failed to connect to database, server not started")

    def run_server(self):
        """Chạy Flask server trong một thread riêng"""
        from werkzeug.serving import make_server
        self.server = make_server('0.0.0.0', self.port, self.app)
        self.server.serve_forever()

    def stop(self):
        """Dừng server an toàn"""
        if hasattr(self, 'server'):
            print("Shutting down Flask server...")
            self.server.shutdown()
            print("Flask server stopped")

# Giao diện chính
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Auto Typer")
        self.setGeometry(100, 100, 600, 400)
        
        # Khởi tạo các biến
        self.image_files = []
        self.worker = None
        
        # Khởi tạo web server thread
        self.web_server = WebServerThread()
        self.web_server.start()
        
        self.setup_ui()
        
    def setup_ui(self):
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

        # Kết nối các nút với hàm xử lý
        self.input_btn.clicked.connect(self.select_images)
        self.start_btn.clicked.connect(self.start_typing)
        self.cancel_btn.clicked.connect(self.cancel_process)

    def select_images(self):
        try:
            self.log_text.append("Đang xử lý...")
            files, _ = QFileDialog.getOpenFileNames(
                self, 
                "Chọn ảnh QR", 
                "", 
                "Image Files (*.png *.jpg *.jpeg *.bmp)"
            )
            
            if not files:
                return
                
            self.image_files = files
            self.image_list.clear()
            for file in files:
                self.image_list.addItem(os.path.basename(file))
                
            self.log_text.append(f"Đã chọn {len(files)} ảnh.")
            
            # Lấy số công văn từ input và truyền vào WorkerThread
            cong_van = self.cong_van_input.text().strip()
            
            # Khởi tạo và chạy worker thread với số công văn
            self.worker = WorkerThread(self.image_files, mode="read", cong_van=cong_van)
            self.worker.update_progress.connect(self.progress_bar.setValue)
            self.worker.update_log.connect(self.log_text.append)
            self.worker.finished.connect(self.read_finished)
            self.worker.start()
            
            # Cập nhật trạng thái UI
            self.input_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.start_btn.setEnabled(False)
            
        except Exception as e:
            self.log_text.append(f"Lỗi khi chọn ảnh: {str(e)}")
            self.reset_ui_state()

    def start_typing(self):
        try:
            cong_van = self.cong_van_input.text().strip()
            if not cong_van:
                self.log_text.append("Vui lòng nhập số công văn!")
                return
                
            if not os.path.exists('result_infomations.json'):
                self.log_text.append("Không tìm thấy file kết quả đọc QR!")
                return
                
            time.sleep(1)  # Đợi 1 giây trước khi bắt đầu
            
            self.worker = WorkerThread(mode="type", cong_van=cong_van)
            self.worker.update_progress.connect(self.progress_bar.setValue)
            self.worker.update_log.connect(self.log_text.append)
            self.worker.finished.connect(self.process_finished)
            self.worker.start()
            
            # Cập nhật trạng thái UI
            self.start_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.input_btn.setEnabled(False)
            
        except Exception as e:
            self.log_text.append(f"Lỗi khi bắt đầu nhập: {str(e)}")
            self.reset_ui_state()

    def cancel_process(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()  # Đợi thread kết thúc
            self.cancel_btn.setEnabled(False)
            self.log_text.append("Đã hủy quá trình!")

    def read_finished(self):
        self.reset_ui_state()
        self.status_label.setText("Đã đọc xong QR, nhấn Start Typing để nhập.")

    def process_finished(self):
        self.reset_ui_state()
        self.status_label.setText("Quá trình hoàn tất hoặc đã hủy.")

    def reset_ui_state(self):
        """Reset trạng thái UI về mặc định"""
        self.input_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        
    def closeEvent(self, event):
        """Xử lý sự kiện đóng cửa sổ"""
        try:
            # Dừng worker thread nếu đang chạy
            if self.worker and self.worker.isRunning():
                print("Stopping worker thread...")
                self.worker.stop()
                self.worker.wait()
                print("Worker thread stopped")
            
            # Dừng web server
            if hasattr(self, 'web_server'):
                print("Stopping web server...")
                self.web_server.stop()
                self.web_server.wait()
                print("Web server stopped")
                
            event.accept()
        except Exception as e:
            print(f"Error during shutdown: {str(e)}")
            event.accept()  # Vẫn chấp nhận đóng ứng dụng ngay cả khi có lỗi

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())