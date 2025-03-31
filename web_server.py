from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

app = Flask(__name__)

# Database configuration
# DB_CONFIG = {
#     'host': 'localhost',
#     'port': 3306,
#     'user': 'root',
#     'password': 'root',
#     'database': 'travel_web_app_development'
# }
DB_CONFIG = {
    'host': '14.225.206.102',
    'port': 3306,
    'user': 'user',
    'password': 'password',
    'database': 'travel_web'
}

def create_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

def init_database():
    """Initialize database table if not exists"""
    print("Starting database initialization...")
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            print("Database connected successfully")
            
            # Create users table if not exists
            create_table_query = """
            CREATE TABLE IF NOT EXISTS user_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cardID VARCHAR(20) NOT NULL UNIQUE,
                createdAtCard DATE,
                dayOfBirth DATE,
                full_name VARCHAR(255),
                gender ENUM('Nam', 'Nữ'),
                national VARCHAR(20),
                province VARCHAR(20),
                district VARCHAR(20),
                commune VARCHAR(20),
                provinceCode VARCHAR(20),
                districtCode VARCHAR(20),
                communeCode VARCHAR(20),
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP NULL DEFAULT NULL
            )
            """
            cursor.execute(create_table_query)
            connection.commit()
            print("Table created successfully")
            
        except Error as e:
            print(f"Error creating table: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("Database connection closed")

def convert_date_format(date_str):
    """Convert date from DDMMYYYY to YYYY-MM-DD format"""
    try:
        if not date_str:
            return None
        return datetime.strptime(date_str, '%d%m%Y').strftime('%Y-%m-%d')
    except ValueError:
        print(f"Invalid date format: {date_str}")
        return None

@app.route('/save_user', methods=['POST'])
def save_user():
    try:
        data = request.json
        print(data)
        # Validate required fields
        required_fields = ['ho_ten', 'cccd', 'dia_chi']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        connection = create_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor()
        
        # Convert dates
        ngay_cccd = convert_date_format(data['ngay_cccd'])
        ngay_sinh = convert_date_format(data['ngay_sinh'])
        
        if ngay_cccd is None or ngay_sinh is None:
            return jsonify({'error': 'Invalid date format. Use DDMMYYYY'}), 400

        # Construct full address
        full_address = f"{data['dia_chi']}, {data.get('xa', '')}, {data.get('huyen', '')}, {data.get('tinh', '')}"
        gioitinh = 'Nam' if data['gioi_tinh'] == 'M' else 'Nữ'
        national = ''
        ma_xa = ''
        documentNumber = 'TLT-000'        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        values = (
            documentNumber,
            data['cccd'],
            ngay_cccd,      # Đã chuyển đổi sang định dạng YYYY-MM-DD
            ngay_sinh,      # Đã chuyển đổi sang định dạng YYYY-MM-DD
            data['ho_ten'],
            gioitinh,
            national,
            data['tinh'],
            data['huyen'],
            data['xa'],
            data['ma_tinh'],
            data['ma_huyen'],
            ma_xa,
            full_address,
            current_time,
            current_time,
            None
        )
        
        # Insert user data
        # insert_query = """
        # INSERT INTO user_info (cardID, createdAtCard, dayOfBirth, full_name, gender, national, province, district, commune, provinceCode, districtCode, communeCode, address, created_at, updated_at, deleted_at)
        # VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        # """
        insert_query = """
        INSERT INTO customers (documentNumber, cardID, createdAtCard, dayOfBirth, fullName, gender, national, province, district, commune, provinceCode, districtCode, communeCode, address, createdAt, updatedAt, deletedAt)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, values)
        connection.commit()
        
        return jsonify({'message': 'User information saved successfully'}), 200
        
    except mysql.connector.IntegrityError as e:
        return jsonify({'error': 'CCCD already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/get_users', methods=['GET'])
def get_users():
    try:
        connection = create_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        
        # Get all users
        select_query = "SELECT * FROM user_info ORDER BY created_at DESC"
        cursor.execute(select_query)
        users = cursor.fetchall()
        
        # Convert datetime objects to string for JSON serialization
        for user in users:
            user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify(users), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=5000, debug=True) 