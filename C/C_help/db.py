import pymysql

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        database='code_defect',
        charset='utf8mb4'
    )

# 为了向后兼容，保留全局连接
conn = get_db_connection()
cursor = conn.cursor()