from reader_qr import qr_code_reader
import os
import json

image_folder = "images"

results = {}
error_images = {}

for filename in os.listdir(image_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        file_path = os.path.join(image_folder, filename)
        try:
            qr_result = qr_code_reader(file_path)
            # Giả sử qr_code_reader trả về dict khi thành công và string khi lỗi
            if isinstance(qr_result, dict):  # Chỉ lưu nếu là kết quả hợp lệ
                results[filename] = qr_result
                print(f"Processed {filename}: {qr_result}")
            else:  # Nếu là string (lỗi), lưu vào error_images
                error_images[filename] = qr_result
                print(f"Error processing {filename}: {qr_result}")
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