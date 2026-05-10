import pymysql
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
import functools

class AuthManager:
    """用户认证管理类"""
    
    @staticmethod
    def register_user(username, password, email, role='student'):
        """注册新用户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return False, "用户名已存在"
            
            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return False, "邮箱已被使用"
            
            # 创建用户
            hashed_password = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (username, password, email, role)
                VALUES (%s, %s, %s, %s)
            ''', (username, hashed_password, email, role))
            
            user_id = cursor.lastrowid
            
            # 根据角色创建对应的教师或学生记录
            if role == 'teacher':
                cursor.execute('''
                    INSERT INTO teachers (user_id, name, department)
                    VALUES (%s, %s, %s)
                ''', (user_id, username, '计算机系'))
            else:
                cursor.execute('''
                    INSERT INTO students (user_id, name, class_name)
                    VALUES (%s, %s, %s)
                ''', (user_id, username, '未分配班级'))
            
            # 创建用户统计记录
            cursor.execute('''
                INSERT INTO user_statistics (user_id, total_queries, defect_queries, explanation_queries, debug_queries)
                VALUES (%s, 0, 0, 0, 0)
            ''', (user_id,))
            
            conn.commit()
            return True, "注册成功"
            
        except Exception as e:
            conn.rollback()
            return False, f"注册失败: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def login_user(username, password):
        """用户登录"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, username, password, role
                FROM users
                WHERE username = %s
            ''', (username,))
            
            user = cursor.fetchone()
            if not user:
                return False, "用户名不存在"
            
            user_id, db_username, db_password, role = user
            
            if not check_password_hash(db_password, password):
                return False, "密码错误"
            
            # 登录成功，创建session
            session['user_id'] = user_id
            session['username'] = db_username
            session['role'] = role
            
            return True, "登录成功"
            
        except Exception as e:
            return False, f"登录失败: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def logout_user():
        """用户登出"""
        session.clear()
    
    @staticmethod
    def get_current_user():
        """获取当前登录用户信息"""
        if 'user_id' in session:
            return {
                'user_id': session['user_id'],
                'username': session['username'],
                'role': session['role']
            }
        return None
    
    @staticmethod
    def is_logged_in():
        """检查用户是否已登录"""
        return 'user_id' in session
    
    @staticmethod
    def is_teacher():
        """检查当前用户是否为教师"""
        return session.get('role') == 'teacher'
    
    @staticmethod
    def is_student():
        """检查当前用户是否为学生"""
        return session.get('role') == 'student'

def login_required(f):
    """登录装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthManager.is_logged_in():
            from flask import jsonify
            return jsonify({'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    """教师权限装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthManager.is_logged_in():
            from flask import jsonify
            return jsonify({'error': '请先登录'}), 401
        if not AuthManager.is_teacher():
            from flask import jsonify
            return jsonify({'error': '需要教师权限'}), 403
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """学生权限装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthManager.is_logged_in():
            from flask import jsonify
            return jsonify({'error': '请先登录'}), 401
        if not AuthManager.is_student():
            from flask import jsonify
            return jsonify({'error': '需要学生权限'}), 403
        return f(*args, **kwargs)
    return decorated_function