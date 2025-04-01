pyinstaller --onefile --icon=icon.ico --add-data "data/tinh_tp.json;data" --add-data "data/quan_huyen.json;data" --add-data "data/xa_phuong.json;data" --add-data "data/ky_tu_tinh.json;data" --hidden-import=PyQt5.QtWidgets --hidden-import=pynput --hidden-import=opencv-python --hidden-import=qreader --hidden-import=torch --hidden-import=chardet --hidden-import=google-cloud-vision --hidden-import=ftfy --add-binary "D:\TLT\travel-auto-fill\venv\Lib\site-packages\pyzbar\libiconv.dll;." --add-binary "D:\TLT\travel-auto-fill\venv\Lib\site-packages\pyzbar\libzbar-64.dll;." -n "QR-Auto-Typer" ui_main.py




pip install pyinstaller fastapi uvicorn sqlalchemy psycopg2-binary requests PyQt5
 pip install flask mysql-connector-python requests