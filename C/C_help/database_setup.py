import pymysql
from db import get_db_connection
from werkzeug.security import generate_password_hash

def create_tables():
    """创建数据库表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            role ENUM('student', 'teacher') DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        ''')
        
        # 教师表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            department VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # 学生表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            class_name VARCHAR(50),
            teacher_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
        )
        ''')
        
        # 代码查询记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS code_queries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            code_text TEXT NOT NULL,
            query_type ENUM('defect_detection', 'code_explanation', 'debug_assistant') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_created_at (created_at)
        )
        ''')
        
        # 缺陷检测结果表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS defect_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            query_id INT NOT NULL,
            defect_description TEXT,
            impact TEXT,
            suggestion TEXT,
            severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (query_id) REFERENCES code_queries(id) ON DELETE CASCADE,
            INDEX idx_query_id (query_id)
        )
        ''')
        
        # 用户查询统计表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_statistics (
            user_id INT PRIMARY KEY,
            total_queries INT DEFAULT 0,
            defect_queries INT DEFAULT 0,
            explanation_queries INT DEFAULT 0,
            debug_queries INT DEFAULT 0,
            last_query_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        print("数据库表创建成功！")
        
    except Exception as e:
        conn.rollback()
        print(f"创建表失败: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def insert_sample_data():
    """插入示例数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            print("数据库中已有数据，跳过示例数据插入")
            return
        
        # 插入示例用户
        sample_users = [
            ('admin', 'admin123', 'admin@example.com', 'teacher'),
            ('teacher1', 'teacher123', 'teacher1@example.com', 'teacher'),
            ('student1', 'student123', 'student1@example.com', 'student'),
            ('student2', 'student123', 'student2@example.com', 'student'),
            ('student3', 'student123', 'student3@example.com', 'student')
        ]
        
        for username, password, email, role in sample_users:
            hashed_password = generate_password_hash(password)
            cursor.execute('''
            INSERT INTO users (username, password, email, role)
            VALUES (%s, %s, %s, %s)
            ''', (username, hashed_password, email, role))
        
        # 插入教师信息
        cursor.execute('''
        INSERT INTO teachers (user_id, name, department)
        VALUES
        ((SELECT id FROM users WHERE username='admin'), '管理员', '计算机系'),
        ((SELECT id FROM users WHERE username='teacher1'), '张老师', '软件工程系')
        ''')
        
        # 插入学生信息
        cursor.execute('''
        INSERT INTO students (user_id, name, class_name, teacher_id)
        VALUES
        ((SELECT id FROM users WHERE username='student1'), '李同学', '软件工程1班',
         (SELECT id FROM teachers WHERE user_id=(SELECT id FROM users WHERE username='teacher1'))),
        ((SELECT id FROM users WHERE username='student2'), '王同学', '软件工程1班',
         (SELECT id FROM teachers WHERE user_id=(SELECT id FROM users WHERE username='teacher1'))),
        ((SELECT id FROM users WHERE username='student3'), '张同学', '软件工程2班',
         (SELECT id FROM teachers WHERE user_id=(SELECT id FROM users WHERE username='teacher1')))
        ''')
        
        # 插入用户统计信息
        cursor.execute('''
        INSERT INTO user_statistics (user_id, total_queries, defect_queries, explanation_queries, debug_queries)
        SELECT id, 0, 0, 0, 0 FROM users
        ''')
        
        conn.commit()
        print("示例数据插入成功！")
        
    except Exception as e:
        conn.rollback()
        print(f"插入示例数据失败: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    try:
        create_tables()
        insert_sample_data()
        print("数据库初始化完成！")
    except Exception as e:
        print(f"数据库初始化失败: {e}")