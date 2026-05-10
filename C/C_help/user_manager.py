import pymysql
from db import get_db_connection
from datetime import datetime

class UserManager:
    """用户管理类，处理用户相关的数据库操作"""
    
    @staticmethod
    def get_user_statistics(user_id):
        """获取用户查询统计信息"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT total_queries, defect_queries, explanation_queries, debug_queries, last_query_at
            FROM user_statistics
            WHERE user_id = %s
        ''', (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return {
                'total_queries': result[0],
                'defect_queries': result[1],
                'explanation_queries': result[2],
                'debug_queries': result[3],
                'last_query_at': result[4].strftime('%Y-%m-%d %H:%M:%S') if result[4] else None
            }
        return None
    
    @staticmethod
    def get_user_code_queries(user_id, limit=50, offset=0):
        """获取用户的代码查询记录"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cq.id, cq.code_text, cq.query_type, cq.created_at,
                   COUNT(dr.id) as defect_count
            FROM code_queries cq
            LEFT JOIN defect_results dr ON cq.id = dr.query_id
            WHERE cq.user_id = %s
            GROUP BY cq.id
            ORDER BY cq.created_at DESC
            LIMIT %s OFFSET %s
        ''', (user_id, limit, offset))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        queries = []
        for row in results:
            queries.append({
                'id': row[0],
                'code_text': row[1][:200] + '...' if len(row[1]) > 200 else row[1],  # 截断长代码
                'query_type': row[2],
                'created_at': row[3].strftime('%Y-%m-%d %H:%M:%S'),
                'defect_count': row[4]
            })
        
        return queries
    
    @staticmethod
    def get_query_defects(query_id):
        """获取特定查询的缺陷检测结果"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT defect_description, impact, suggestion, severity, created_at
            FROM defect_results
            WHERE query_id = %s
            ORDER BY severity DESC, created_at ASC
        ''', (query_id,))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        defects = []
        for row in results:
            defects.append({
                'description': row[0],
                'impact': row[1],
                'suggestion': row[2],
                'severity': row[3],
                'created_at': row[4].strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return defects
    
    @staticmethod
    def save_code_query(user_id, code_text, query_type):
        """保存代码查询记录"""
        print(f"UserManager: 开始保存查询记录 - 用户ID: {user_id}, 类型: {query_type}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 插入查询记录
            cursor.execute('''
                INSERT INTO code_queries (user_id, code_text, query_type)
                VALUES (%s, %s, %s)
            ''', (user_id, code_text, query_type))
            
            query_id = cursor.lastrowid
            print(f"UserManager: 查询记录已插入，ID: {query_id}")
            
            # 更新用户统计信息
            # 将查询类型映射到正确的列名
            column_map = {
                'defect_detection': 'defect_queries',
                'code_explanation': 'explanation_queries',
                'debug_assistant': 'debug_queries'
            }
            
            column_name = column_map.get(query_type, 'total_queries')
            update_sql = '''
                UPDATE user_statistics
                SET total_queries = total_queries + 1,
                    {} = {} + 1,
                    last_query_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            '''.format(column_name, column_name)
            print(f"UserManager: 执行统计更新SQL: {update_sql}")
            
            cursor.execute(update_sql, (user_id,))
            updated_rows = cursor.rowcount
            print(f"UserManager: 统计更新影响行数: {updated_rows}")
            
            conn.commit()
            print(f"UserManager: 查询记录保存成功，ID: {query_id}")
            return query_id
            
        except Exception as e:
            conn.rollback()
            print(f"UserManager: 保存查询记录失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def save_defect_results(query_id, defects):
        """保存缺陷检测结果"""
        print(f"UserManager: 开始保存缺陷结果 - 查询ID: {query_id}, 缺陷数量: {len(defects)}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            for i, defect in enumerate(defects):
                cursor.execute('''
                    INSERT INTO defect_results (query_id, defect_description, impact, suggestion, severity)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    query_id,
                    defect.get('description', ''),
                    defect.get('impact', ''),
                    defect.get('suggestion', ''),
                    defect.get('severity', 'medium')
                ))
                print(f"UserManager: 缺陷 {i+1} 已保存")
            
            conn.commit()
            print(f"UserManager: 所有缺陷结果保存成功")
            
        except Exception as e:
            conn.rollback()
            print(f"UserManager: 保存缺陷结果失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_user_profile(user_id):
        """获取用户详细信息"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.role, u.created_at,
                   CASE
                       WHEN u.role = 'teacher' THEN t.name
                       WHEN u.role = 'student' THEN s.name
                   END as name,
                   CASE
                       WHEN u.role = 'teacher' THEN t.department
                       WHEN u.role = 'student' THEN s.id
                   END as additional_info,
                   CASE
                       WHEN u.role = 'student' THEN s.class_name
                   END as class_name
            FROM users u
            LEFT JOIN teachers t ON u.id = t.user_id AND u.role = 'teacher'
            LEFT JOIN students s ON u.id = s.user_id AND u.role = 'student'
            WHERE u.id = %s
        ''', (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'role': result[3],
                'created_at': result[4].strftime('%Y-%m-%d %H:%M:%S'),
                'name': result[5],
                'additional_info': result[6],
                'class_name': result[7] if result[7] else None
            }
        return None

class TeacherManager:
    """教师管理类"""
    
    @staticmethod
    def get_teacher_students(teacher_id):
        """获取教师管理的学生列表"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, s.name, s.class_name, u.username, u.email,
                   us.total_queries, us.defect_queries, us.explanation_queries, us.debug_queries
            FROM students s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN user_statistics us ON s.user_id = us.user_id
            WHERE s.teacher_id = %s
            ORDER BY s.class_name, s.id
        ''', (teacher_id,))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        students = []
        for row in results:
            students.append({
                'id': row[0],
                'name': row[1],
                'student_id': str(row[0]),  # 使用id作为student_id
                'class_name': row[2],
                'username': row[3],
                'email': row[4],
                'total_queries': row[5] if row[5] else 0,
                'defect_queries': row[6] if row[6] else 0,
                'explanation_queries': row[7] if row[7] else 0,
                'debug_queries': row[8] if row[8] else 0
            })
        
        return students
    
    @staticmethod
    def add_student(teacher_id, name, class_name, username, password, email):
        """添加新学生"""
        print(f"TeacherManager.add_student: 开始添加学生 - 教师ID: {teacher_id}, 姓名: {name}, 班级: {class_name}, 用户名: {username}, 邮箱: {email}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 检查用户名是否已存在
            cursor.execute("SELECT id, role FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            print(f"TeacherManager.add_student: 检查用户名 - 结果: {existing_user}")
            
            if existing_user:
                # 用户名已存在，检查是否已经是学生角色
                user_id = existing_user[0]
                user_role = existing_user[1]
                print(f"TeacherManager.add_student: 用户已存在 - ID: {user_id}, 角色: {user_role}")
                
                if user_role != 'student':
                    return False, f"该用户名已存在，但角色是{user_role}，请选择其他用户名"
                
                # 检查该学生是否已经被其他教师管理
                cursor.execute("SELECT teacher_id FROM students WHERE user_id = %s", (user_id,))
                existing_teacher = cursor.fetchone()
                print(f"TeacherManager.add_student: 检查教师管理 - 结果: {existing_teacher}")
                
                if existing_teacher:
                    if existing_teacher[0] == teacher_id:
                        return False, "该学生已经在您的学生列表中"
                    else:
                        return False, "该学生已经被其他教师管理，请选择其他用户名"
                
                # 该学生存在但未被管理，可以添加到当前教师名下
                cursor.execute('''
                    UPDATE students
                    SET name = %s, class_name = %s, teacher_id = %s
                    WHERE user_id = %s
                ''', (name, class_name, teacher_id, user_id))
                
                updated_rows = cursor.rowcount
                print(f"TeacherManager.add_student: 更新学生信息 - 影响行数: {updated_rows}")
                
                conn.commit()
                return True, "学生添加成功（已存在的用户）"
            
            # 检查用户名是否已存在
            cursor.execute("SELECT id, role FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            print(f"TeacherManager.add_student: 检查用户名 - 结果: {existing_user}")
            
            if existing_user:
                # 用户名已存在，检查是否已经是学生角色
                user_id = existing_user[0]
                user_role = existing_user[1]
                print(f"TeacherManager.add_student: 用户已存在 - ID: {user_id}, 角色: {user_role}")
                
                if user_role != 'student':
                    return False, f"该用户名已存在，但角色是{user_role}，请选择其他用户名"
                
                # 检查该学生是否已经被其他教师管理
                cursor.execute("SELECT teacher_id FROM students WHERE user_id = %s", (user_id,))
                existing_teacher = cursor.fetchone()
                print(f"TeacherManager.add_student: 检查教师管理 - 结果: {existing_teacher}")
                
                if existing_teacher:
                    if existing_teacher[0] == teacher_id:
                        return False, "该学生已经在您的学生列表中"
                    else:
                        return False, "该学生已经被其他教师管理，请选择其他用户名"
                
                # 该学生存在但未被管理，可以添加到当前教师名下
                cursor.execute('''
                    UPDATE students
                    SET name = %s, class_name = %s, teacher_id = %s
                    WHERE user_id = %s
                ''', (name, class_name, teacher_id, user_id))
                
                updated_rows = cursor.rowcount
                print(f"TeacherManager.add_student: 更新学生信息 - 影响行数: {updated_rows}")
                
                conn.commit()
                return True, "学生添加成功（已存在的用户）"
            else:
                print(f"TeacherManager.add_student: 创建新用户 - 用户名: {username}")
                # 创建新用户账户
                from auth import AuthManager
                
                # 使用同一个数据库连接来创建用户，确保事务一致性
                # 手动执行注册逻辑，而不是调用AuthManager.register_user
                try:
                    # 检查用户名和邮箱
                    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                    if cursor.fetchone():
                        return False, "用户名已存在"
                    
                    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                    if cursor.fetchone():
                        return False, "邮箱已被使用"
                    
                    # 创建用户
                    from werkzeug.security import generate_password_hash
                    hashed_password = generate_password_hash(password)
                    cursor.execute('''
                        INSERT INTO users (username, password, email, role)
                        VALUES (%s, %s, %s, %s)
                    ''', (username, hashed_password, email, 'student'))
                    
                    user_id = cursor.lastrowid
                    print(f"TeacherManager.add_student: 新用户创建成功 - ID: {user_id}")
                    
                    # 创建学生记录
                    cursor.execute('''
                        INSERT INTO students (user_id, name, class_name)
                        VALUES (%s, %s, %s)
                    ''', (user_id, username, '未分配班级'))
                    
                    # 创建用户统计记录
                    cursor.execute('''
                        INSERT INTO user_statistics (user_id, total_queries, defect_queries, explanation_queries, debug_queries)
                        VALUES (%s, 0, 0, 0, 0)
                    ''', (user_id,))
                    
                    print(f"TeacherManager.add_student: 学生基础信息创建完成")
                    
                except Exception as e:
                    print(f"TeacherManager.add_student: 用户创建失败 - {str(e)}")
                    return False, f"用户创建失败: {str(e)}"
                
                # 更新学生信息（使用传入的真实信息，而不是默认的占位符）
                cursor.execute('''
                    UPDATE students
                    SET name = %s, class_name = %s, teacher_id = %s
                    WHERE user_id = %s
                ''', (name, class_name, teacher_id, user_id))
                
                updated_rows = cursor.rowcount
                print(f"TeacherManager.add_student: 更新新学生信息 - 影响行数: {updated_rows}")
                
                conn.commit()
                return True, "学生添加成功（新创建用户）"
            
        except Exception as e:
            conn.rollback()
            return False, f"添加学生失败: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update_student(student_id, name, student_id_num, class_name):
        """更新学生信息"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE students
                SET name = %s, class_name = %s
                WHERE id = %s
            ''', (name, class_name, student_id))
            
            conn.commit()
            return True, "学生信息更新成功"
            
        except Exception as e:
            conn.rollback()
            return False, f"更新学生信息失败: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def delete_student(student_id):
        """删除学生（同时删除用户账户）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 获取用户ID
            cursor.execute("SELECT user_id FROM students WHERE id = %s", (student_id,))
            result = cursor.fetchone()
            if not result:
                return False, "学生不存在"
            
            user_id = result[0]
            
            # 删除用户（级联删除学生记录）
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            conn.commit()
            return True, "学生删除成功"
            
        except Exception as e:
            conn.rollback()
            return False, f"删除学生失败: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_student_details(student_id):
        """获取学生详细信息"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, s.name, s.class_name, u.username, u.email, u.created_at,
                   us.total_queries, us.defect_queries, us.explanation_queries, us.debug_queries, us.last_query_at
            FROM students s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN user_statistics us ON s.user_id = us.user_id
            WHERE s.id = %s
        ''', (student_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'student_id': str(result[0]),  # 使用id作为student_id
                'class_name': result[2],
                'username': result[3],
                'email': result[4],
                'created_at': result[5].strftime('%Y-%m-%d %H:%M:%S'),
                'total_queries': result[6] if result[6] else 0,
                'defect_queries': result[7] if result[7] else 0,
                'explanation_queries': result[8] if result[8] else 0,
                'debug_queries': result[9] if result[9] else 0,
                'last_query_at': result[10].strftime('%Y-%m-%d %H:%M:%S') if result[10] else None
            }
        return None