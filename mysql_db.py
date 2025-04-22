import pymysql
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

def init_db():
    conn = pymysql.connect(
        host='localhost',  # 修正：分开指定 host 和 port
        port=3306,
        user='admin',
        password='12345678'
    )
    with conn.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS medical_qa")
    conn.close()

def get_db():
    return pymysql.connect(
        host='localhost',  # 修正：分开指定 host 和 port
        port=3306,
        user='admin',
        password='12345678',
        database='medical_qa',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# 初始化用户表
init_db()
with get_db() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()