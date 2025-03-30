from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'travel_web_app_development'
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
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Create users table if not exists
            create_table_query = """
            CREATE TABLE IF NOT EXISTS user_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                cccd VARCHAR(20) NOT NULL UNIQUE,
                address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)
            connection.commit()
            
        except Error as e:
            print(f"Error creating table: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

@app.route('/save_user', methods=['POST'])
def save_user():
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['ho_ten', 'cccd', 'dia_chi']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        connection = create_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor()
        
        # Insert user data
        insert_query = """
        INSERT INTO user_info (full_name, cccd, address)
        VALUES (%s, %s, %s)
        """
        
        # Construct full address
        full_address = f"{data['dia_chi']}, {data.get('xa', '')}, {data.get('huyen', '')}, {data.get('tinh', '')}"
        
        values = (data['ho_ten'], data['cccd'], full_address)
        
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