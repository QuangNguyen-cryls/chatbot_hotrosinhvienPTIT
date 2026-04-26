import mysql.connector
from mysql.connector import Error

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",        # chỉ host thôi
            port=3306,               # port để riêng
            user="root",
            password="Kuj0u Alis@ x Zer0",
            database="ChatboxDb"
        )
        if connection.is_connected():
            print("Kết nối MySQL thành công!")
    except Error as e:
        print(f"Lỗi khi kết nối MySQL: {e}")
    return connection

def test_select(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM question;")
        rows = cursor.fetchall()
        print("Dữ liệu trong bảng question:")
        for row in rows:
            print(row)
    except Error as e:
        print(f"Lỗi khi truy vấn: {e}")


if __name__ == "__main__":
    conn = create_connection()
    if conn:
        test_select(conn)
        conn.close()
        print("Đã đóng kết nối MySQL.")
