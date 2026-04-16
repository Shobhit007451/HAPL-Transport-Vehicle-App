import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        # First try to connect without database to create it if it doesn't exist
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS transport_db")
            cursor.close()
            connection.database = 'transport_db'
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
            """)
            # Attendance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255),
                    punch_in DATETIME,
                    punch_out DATETIME,
                    location VARCHAR(255),
                    image_in LONGTEXT,
                    image_out LONGTEXT
                )
            """)
            conn.commit()
            print("Database initialized successfully.")
        except Error as e:
            print(f"Error initializing database: {e}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    init_db()
