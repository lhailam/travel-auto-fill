from qreader import QReader
import cv2
import json
import os

qreader = QReader()

def find_code_by_name(name, refer_code, file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            result_data = json.load(file)
    except Exception as err:
        print("Error reading file:", err)
        return ""
    
    # Chuyển name về chữ thường để so sánh không phân biệt hoa/thường
    name_lower = name.lower()

    # Lọc các item có key chứa tên cần tìm
    result = [
        item for item in result_data
        if any(name_lower in key.lower() for key in item.keys())
    ]

    # Nếu không tìm thấy kết quả
    if not result:
        return ""

    # Nếu chỉ có 1 kết quả
    if len(result) == 1:
        key = next((k for k in result[0] if name_lower in k.lower()), None)
        if key:
            values = result[0][key].split(", ")
            return values[0] if len(values) > 1 else result[0][key]

    # Nếu có nhiều kết quả, tìm theo refer_code
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

def qr_code_reader(path):
    try:
        image = cv2.imread(path)
        if image is None:
            return "Không thể đọc file ảnh"
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        decoded_text = qreader.detect_and_decode(image=image)
        
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

        ma_tinh = find_code_by_name(tinh, None, 'data/tinh_tp.json')
        ma_huyen = find_code_by_name(huyen, ma_tinh, 'data/quan_huyen.json')
        ma_xa = find_code_by_name(xa_phuong_name, ma_huyen, 'data/xa_phuong.json')

        result = {
            "cccd": fields[0],
            "ngay_cccd": ngaycccd,
            "ten": fields[2],
            "ngay_sinh": fields[3],
            "gioi_tinh": fields[4],
            "tinh": tinh,
            "ma_tinh": ma_tinh,
            "huyen": huyen,
            "ma_huyen": ma_huyen,
            "xa": xa_phuong_name,
            "ma_xa": ma_xa,
            "dia_chi": dia_chi,
            "data": qr_data
        }
        return result
    except Exception as e:
        return f"Error: {str(e)}"

image_folder = "images"

results = {}
error_images = {}

for filename in os.listdir(image_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        file_path = os.path.join(image_folder, filename)
        try:
            qr_result = qr_code_reader(file_path)
            if isinstance(qr_result, str):  # Nếu kết quả là string, nghĩa là có lỗi
                error_images[filename] = qr_result
                print(f"Error processing {filename}: {qr_result}")
            else:  # Nếu kết quả là dict, xử lý thành công
                results[filename] = qr_result
                print(f"Processed {filename}: {qr_result}")
        except Exception as e:
            error_images[filename] = f"Error: {str(e)}"
            print(f"Error processing {filename}: {str(e)}")

with open('result_infomations.json', 'w', encoding='utf-8') as json_file:
    json.dump(results, json_file, ensure_ascii=False, indent=4)

if error_images:
    with open('error_images.json', 'w', encoding='utf-8') as error_file:
        json.dump(error_images, error_file, ensure_ascii=False, indent=4)
    print(f"Found {len(error_images)} error images. Details saved to error_images.json")
else:
    print("No error images found")

print("All results have been saved to result_infomations.json")