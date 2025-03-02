from pynput.keyboard import Controller, Key
import time
import json
from datetime import datetime

keyboard = Controller()

def type_vietnamese(text):
    for char in text:
        keyboard.press(char)
        keyboard.release(char)
        time.sleep(0.15)

def vietnamese_to_telex(text):
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

def press_tab():
    keyboard.press(Key.tab)
    keyboard.release(Key.tab)
    time.sleep(0.1)

def press_enter():
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    time.sleep(0.1)

try:
    with open('result_infomations.json', 'r', encoding='utf-8') as json_file:
        results_data = json.load(json_file)
except Exception as e:
    print(f"Error reading result_infomations.json: {str(e)}")
    exit()

current_date = datetime.now().strftime("%d%m%Y")
all_forms = []
for filename, data in results_data.items():
    form = [
        {"text": "TLT-011", "tab": True, "enter": None},
        {"text": vietnamese_to_telex(data["ho_ten"]), "tab": True, "enter": None},
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
        {"text": vietnamese_to_telex(data["dia_chi"]), "tab": True, "enter": None},
        {"text": "", "tab": True, "enter": None},
        {"text": "1", "tab": True, "enter": None},
        {"text": "2", "tab": True, "enter": None},
        {"text": vietnamese_to_telex("tự do"), "tab": True, "enter": None},
        {"text": "", "tab": True, "enter": None},
        {"text": "", "tab": True, "enter": None},
        {"text": "", "tab": True, "enter": None},
        {"text": "", "tab": True, "enter": None},
        {"text": current_date, "tab": None, "enter": True}
    ]
    all_forms.append(form)

print("Chuẩn bị gõ tự động sau 5 giây...")
time.sleep(5)
total_all_forms = len(all_forms)
for form_idx, form_data in enumerate(all_forms):
    total_form_data = len(form_data)
    for i, field in enumerate(form_data):
        text = field["text"]
        should_tab = field.get("tab")
        should_enter = field.get("enter")
        type_vietnamese(text)
        if form_idx == (total_all_forms-1) and i == (total_form_data-1):
            break
        if should_tab:
            press_tab()
        elif should_enter:
            press_enter()
    if form_idx < len(all_forms) - 1:
        print(f"Đã xong Form {form_idx + 1}. Chờ 2 giây để sang form tiếp theo...")
        time.sleep(1)

print("Đã gõ xong tất cả các form!")
