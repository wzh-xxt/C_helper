import os
import sys
import traceback
import json

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
from flask import session
from modules.defect_detector import DefectDetector
from modules.code_explainer import CodeExplainer
from modules.debug_assistant import DebugAssistant
from utils.rag_utils import get_available_knowledge_bases, create_sample_external_defect_files
from config import api_key, test_api_connection
from auth import AuthManager, login_required, teacher_required, student_required
from user_manager import UserManager, TeacherManager
from db import get_db_connection

# 自动抓取/更新缺陷库和RAG知识库
try:
    from utils.web_crawler import auto_update_all
    print("正在自动抓取/更新缺陷库和RAG知识库...")
    auto_update_all()
except Exception as e:
    print(f"自动抓取知识库失败: {e}")
          
# 初始化应用
app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-in-production'

# 确保必要的目录存在
data_dir = os.path.join(project_root, 'data')
rag_dir = os.path.join(data_dir, 'rag_resources')
external_defect_dir = os.path.join(data_dir, 'external_defects')
vector_store_dir = os.path.join(data_dir, 'vector_store')

os.makedirs(rag_dir, exist_ok=True)
os.makedirs(external_defect_dir, exist_ok=True)
os.makedirs(vector_store_dir, exist_ok=True)

# 创建示例缺陷库和知识库文件
print("初始化缺陷库和知识库...")
create_sample_external_defect_files()

# 加载知识库信息
knowledge_bases = get_available_knowledge_bases()
print(f"已加载 {len(knowledge_bases)} 个知识库:")
for kb_name, kb_desc in knowledge_bases.items():
    print(f"  - {kb_name}: {kb_desc}")

# 初始化模块
defect_detector = DefectDetector()
code_explainer = CodeExplainer()
debug_assistant = DebugAssistant()

# 路由：首页
@app.route('/')
def index():
    return render_template('login.html')

# 路由：代码分析主页面
@app.route('/analyzer')
@login_required
def code_analyzer():
    return render_template('code_analyzer.html')

# 路由：登录页面
@app.route('/login')
def login_page():
    if AuthManager.is_logged_in():
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# 路由：注册页面
@app.route('/register')
def register_page():
    if AuthManager.is_logged_in():
        return redirect(url_for('dashboard'))
    return render_template('register.html')

# 路由：用户中心
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        current_user = AuthManager.get_current_user()
        print(f"Dashboard路由: 当前用户: {current_user}")
        
        user_profile = UserManager.get_user_profile(current_user['user_id'])
        print(f"Dashboard路由: 用户配置文件: {user_profile}")
        
        if not user_profile:
            print(f"Dashboard路由: 无法获取用户配置文件，用户ID: {current_user['user_id']}")
            return "用户配置文件不存在", 500
            
        user_stats = UserManager.get_user_statistics(current_user['user_id'])
        print(f"Dashboard路由: 用户统计: {user_stats}")
        
        if not user_stats:
            print(f"Dashboard路由: 无法获取用户统计，用户ID: {current_user['user_id']}")
            # 创建默认统计
            user_stats = {
                'total_queries': 0,
                'defect_queries': 0,
                'explanation_queries': 0,
                'debug_queries': 0,
                'last_query_at': None
            }
        
        recent_queries = UserManager.get_user_code_queries(current_user['user_id'], limit=10)
        recent_defects = []
        
        # 获取最近的缺陷记录
        for query in recent_queries[:5]:
            if query['defect_count'] > 0:
                defects = UserManager.get_query_defects(query['id'])
                recent_defects.extend(defects)
        
        return render_template('dashboard.html',
                             user_name=user_profile['name'],
                             user_role=user_profile['role'],
                             register_time=user_profile['created_at'],
                             total_queries=user_stats['total_queries'],
                             defect_queries=user_stats['defect_queries'],
                             explanation_queries=user_stats['explanation_queries'],
                             debug_queries=user_stats['debug_queries'],
                             last_query_time=user_stats['last_query_at'],
                             recent_queries=recent_queries,
                             recent_defects=recent_defects[:10],
                             user_profile=user_profile)
                             
    except Exception as e:
        print(f"Dashboard路由错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Dashboard加载失败: {str(e)}", 500

# 路由：教师管理中心
@app.route('/teacher')
@teacher_required
def teacher_dashboard():
    current_user = AuthManager.get_current_user()
    
    # 获取教师信息
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, department FROM teachers WHERE user_id = %s", (current_user['user_id'],))
    teacher_info = cursor.fetchone()
    cursor.close()
    conn.close()
    if not teacher_info:
        return redirect(url_for('dashboard'))
    
    teacher_id, teacher_name, department = teacher_info
    
    # 获取学生列表
    students = TeacherManager.get_teacher_students(teacher_id)
    
    # 获取统计信息
    total_students = len(students)
    total_queries = sum(student['total_queries'] for student in students)
    total_defects = sum(student['defect_queries'] for student in students)
    
    # 获取班级列表
    classes = list(set(student['class_name'] for student in students))
    
    # 学生活跃度排行
    activity_ranking = sorted(students, key=lambda x: x['total_queries'], reverse=True)[:10]
    
    return render_template('teacher_dashboard.html',
                         teacher_name=teacher_name,
                         department=department,
                         total_students=total_students,
                         total_queries=total_queries,
                         total_defects=total_defects,
                         students=students,
                         classes=classes,
                         activity_ranking=activity_ranking)

# 路由：静态文件
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# API路由：状态检查
@app.route('/api/status')
def api_status():
    status, message = test_api_connection()
    if status:
        return jsonify({"status": "ok", "message": message})
    else:
        return jsonify({"status": "error", "message": message})

# API路由：代码缺陷检测
@app.route('/api/detect_defects', methods=['POST'])
@login_required
def api_detect_defects():
    try:
        # 打印原始请求数据，帮助调试
        print(f"缺陷检测路由: 接收到请求数据")
        
        # 尝试解析JSON
        data = request.json
        if data is None:
            print("缺陷检测路由: 无法解析JSON数据")
            return jsonify({"error": "无法解析JSON数据，请检查请求格式", "defects": []}), 200
            
        # 检查'code'字段是否存在
        if 'code' not in data:
            print("缺陷检测路由: 请求中没有'code'字段")
            return jsonify({"error": "请提供代码", "defects": []}), 200
        
        # 检查'code'字段是否为空
        code = data['code']
        if not code or not isinstance(code, str):
            print("缺陷检测路由: 代码为空或不是字符串")
            return jsonify({"error": "代码不能为空且必须是字符串", "defects": []}), 200
        
        print(f"缺陷检测路由: 开始缺陷检测，代码长度: {len(code)} 字符")
        
        # 获取当前用户信息
        current_user = AuthManager.get_current_user()
        user_id = current_user['user_id']
        print(f"缺陷检测路由: 当前用户ID: {user_id}")
        
        # 保存查询记录
        try:
            query_id = UserManager.save_code_query(user_id, code, 'defect_detection')
            print(f"缺陷检测路由: 查询记录已保存，ID: {query_id}")
        except Exception as save_error:
            print(f"缺陷检测路由: 保存查询记录失败: {str(save_error)}")
            import traceback
            traceback.print_exc()
            # 不再静默忽略错误，让调用方知道有问题
            return jsonify({"error": f"保存查询记录失败: {str(save_error)}", "defects": []}), 500
        
        # 调用缺陷检测模块
        try:
            result = defect_detector.detect_defects(code)
            print(f"缺陷检测路由: 获取到模块返回结果: {json.dumps(result)[:100]}...")
            
            # 检查结果格式
            if not isinstance(result, dict):
                print(f"缺陷检测路由: 结果格式错误，非字典类型: {type(result)}")
                return jsonify({"error": "检测结果格式错误", "defects": []}), 200
                
            # 确保结果中包含defects字段
            if "defects" not in result:
                print("缺陷检测路由: 结果中缺少defects字段，添加空数组")
                result["defects"] = []
                
            # 确保defects是数组
            if not isinstance(result["defects"], list):
                print(f"缺陷检测路由: defects字段不是数组: {type(result['defects'])}")
                result["defects"] = []
            
            # 保存缺陷检测结果
            if result.get("defects") and len(result["defects"]) > 0:
                try:
                    UserManager.save_defect_results(query_id, result["defects"])
                    print(f"缺陷检测路由: 缺陷检测结果已保存，共 {len(result['defects'])} 个缺陷")
                except Exception as defect_save_error:
                    print(f"缺陷检测路由: 保存缺陷检测结果失败: {str(defect_save_error)}")
                    import traceback
                    traceback.print_exc()
                    # 继续返回结果，不中断流程
                
            print(f"缺陷检测路由: 成功检测到 {len(result.get('defects', []))} 个缺陷")
            return jsonify(result), 200
            
        except Exception as module_error:
            error_detail = traceback.format_exc()
            error_msg = f"缺陷检测模块错误: {str(module_error)}"
            print(f"缺陷检测路由: {error_msg}")
            print(f"错误详情:\n{error_detail}")
            return jsonify({"error": error_msg, "defects": []}), 200
            
    except Exception as e:
        error_detail = traceback.format_exc()
        error_msg = f"缺陷检测内部错误: {str(e)}"
        print(f"缺陷检测路由: {error_msg}")
        print(f"错误详情:\n{error_detail}")
        return jsonify({"error": "内部服务器错误", "details": str(e), "defects": []}), 200

# API路由：代码功能解释
@app.route('/api/explain_code', methods=['POST'])
@login_required
def api_explain_code():
    try:
        data = request.json
        if not data or 'code' not in data:
            return jsonify({"error": "请提供代码"}), 400
        
        code = data['code']
        query = data.get('query', '')
        
        # 获取当前用户信息
        current_user = AuthManager.get_current_user()
        user_id = current_user['user_id']
        
        # 保存查询记录
        try:
            query_id = UserManager.save_code_query(user_id, code, 'code_explanation')
            print(f"代码解释路由: 查询记录已保存，ID: {query_id}")
        except Exception as save_error:
            print(f"代码解释路由: 保存查询记录失败: {str(save_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"保存查询记录失败: {str(save_error)}", "explanation": ""}), 500
        
        result = code_explainer.explain_code(code, query)
        return jsonify(result)
        
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"代码解释路由错误: {str(e)}")
        print(f"错误详情:\n{error_detail}")
        return jsonify({"error": "内部服务器错误", "details": str(e)}), 500

# API路由：智能调试与Debug
@app.route('/api/debug_code', methods=['POST'])
@login_required
def api_debug_code():
    try:
        data = request.json
        if not data or 'code' not in data:
            return jsonify({"error": "请提供代码"}), 400
        
        if 'error_message' not in data:
            return jsonify({"error": "请提供错误信息或问题描述"}), 400
        
        code = data['code']
        error_message = data['error_message']
        
        # 获取当前用户信息
        current_user = AuthManager.get_current_user()
        user_id = current_user['user_id']
        
        # 保存查询记录（包含错误信息）
        full_code = f"// 错误信息: {error_message}\n\n{code}"
        try:
            query_id = UserManager.save_code_query(user_id, full_code, 'debug_assistant')
            print(f"调试助手路由: 查询记录已保存，ID: {query_id}")
        except Exception as save_error:
            print(f"调试助手路由: 保存查询记录失败: {str(save_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"保存查询记录失败: {str(save_error)}", "debug_suggestions": ""}), 500
        
        result = debug_assistant.debug_code(code, error_message)
        return jsonify(result)
        
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"调试助手路由错误: {str(e)}")
        print(f"错误详情:\n{error_detail}")
        return jsonify({"error": "内部服务器错误", "details": str(e)}), 500

# API路由：文件上传处理
@app.route('/api/upload_file', methods=['POST'])
def api_upload_file():
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({"error": "未找到文件"}), 400
    
    file = request.files['file']
    
    # 检查文件名
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400
    
    # 验证文件类型
    allowed_extensions = {'.c', '.cpp', '.h'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({"error": "不支持的文件类型"}), 400
    
    # 读取文件内容
    try:
        # 先尝试以UTF-8读取
        try:
            file_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            # 如果UTF-8读取失败，回到文件开头并尝试GBK编码
            file.seek(0)
            try:
                file_content = file.read().decode('gbk')
            except UnicodeDecodeError:
                # 如果GBK也失败，尝试GB18030
                file.seek(0)
                try:
                    file_content = file.read().decode('gb18030')
                except UnicodeDecodeError:
                    # 最后尝试GB2312
                    file.seek(0)
                    file_content = file.read().decode('gb2312', errors='replace')
        
        return jsonify({
            "status": "success",
            "filename": file.filename,
            "content": file_content
        })
    except Exception as e:
        # 记录文件处理异常
        print(f"文件处理错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"文件处理失败: {str(e)}"}), 500

# API路由：用户登录
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'success': False, 'message': '请提供用户名和密码'}), 400
    
    success, message = AuthManager.login_user(data['username'], data['password'])
    return jsonify({'success': success, 'message': message})

# API路由：用户注册
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    if not data or 'username' not in data or 'password' not in data or 'email' not in data or 'role' not in data:
        return jsonify({'success': False, 'message': '请提供完整的注册信息'}), 400
    
    success, message = AuthManager.register_user(
        data['username'],
        data['password'],
        data['email'],
        data['role']
    )
    return jsonify({'success': success, 'message': message})

# API路由：用户登出
@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    AuthManager.logout_user()
    return jsonify({'success': True, 'message': '登出成功'})

# API路由：获取当前用户信息
@app.route('/api/user/info', methods=['GET'])
@login_required
def api_user_info():
    current_user = AuthManager.get_current_user()
    user_profile = UserManager.get_user_profile(current_user['user_id'])
    return jsonify({'success': True, 'data': user_profile})

# API路由：更新用户信息
@app.route('/api/profile/update', methods=['POST'])
@login_required
def api_update_profile():
    current_user = AuthManager.get_current_user()
    data = request.json
    
    # 这里可以实现用户信息更新逻辑
    # 为了简化，暂时返回成功
    return jsonify({'success': True, 'message': '个人信息更新成功'})

# API路由：教师添加学生
@app.route('/api/teacher/student', methods=['POST'])
@teacher_required
def api_add_student():
    try:
        current_user = AuthManager.get_current_user()
        print(f"添加学生API: 当前用户: {current_user}")
        
        # 获取教师ID
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (current_user['user_id'],))
        teacher_info = cursor.fetchone()
        cursor.close()
        conn.close()
        if not teacher_info:
            return jsonify({'success': False, 'message': '教师信息不存在'}), 404
        
        teacher_id = teacher_info[0]
        data = request.json
        print(f"添加学生API: 接收到的数据: {data}")
        
        required_fields = ['name', 'class_name', 'username', 'password', 'email']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': '请提供完整的学生信息'}), 400
        
        success, message = TeacherManager.add_student(
            teacher_id,
            data['name'],
            data['class_name'],
            data['username'],
            data['password'],
            data['email']
        )
        
        print(f"添加学生API: 结果: success={success}, message={message}")
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        print(f"添加学生API错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'系统错误: {str(e)}'}), 500

# API路由：教师删除学生
@app.route('/api/teacher/student/<int:student_id>', methods=['DELETE'])
@teacher_required
def api_delete_student(student_id):
    success, message = TeacherManager.delete_student(student_id)
    return jsonify({'success': success, 'message': message})

# API路由：获取学生详细信息
@app.route('/api/teacher/student/<int:student_id>', methods=['GET'])
@teacher_required
def api_get_student_details(student_id):
    student_details = TeacherManager.get_student_details(student_id)
    if student_details:
        # 获取学生的用户ID，然后查询该用户的代码查询记录
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM students WHERE id = %s", (student_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            user_id = result[0]
            # 获取学生的查询记录
            code_queries = UserManager.get_user_code_queries(user_id, limit=20)
            # 为每个查询获取详细的缺陷信息
            for query in code_queries:
                if query['defect_count'] > 0:
                    defects = UserManager.get_query_defects(query['id'])
                    query['defects'] = defects
            student_details['recent_queries'] = code_queries
            return jsonify({'success': True, 'data': student_details})
        else:
            return jsonify({'success': False, 'message': '无法获取学生用户信息'}), 404
    else:
        return jsonify({'success': False, 'message': '学生不存在'}), 404

# 路由：学生详情页面
@app.route('/teacher/student/<int:student_id>')
@teacher_required
def student_details_page(student_id):
    """学生详情页面"""
    current_user = AuthManager.get_current_user()
    
    # 验证该学生是否属于当前教师
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.name, s.class_name, u.username, u.email, u.created_at,
               us.total_queries, us.defect_queries, us.explanation_queries, us.debug_queries, us.last_query_at
        FROM students s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN user_statistics us ON s.user_id = us.user_id
        JOIN teachers t ON s.teacher_id = t.id
        WHERE s.id = %s AND t.user_id = %s
    ''', (student_id, current_user['user_id']))
    
    student_info = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not student_info:
        return "无权查看该学生信息或学生不存在", 403
    
    # 构建学生详情数据
    student_details = {
        'id': student_info[0],
        'name': student_info[1],
        'student_id': str(student_info[0]),  # 使用id作为student_id
        'class_name': student_info[2],
        'username': student_info[3],
        'email': student_info[4],
        'created_at': student_info[5].strftime('%Y-%m-%d %H:%M:%S'),
        'total_queries': student_info[6] if student_info[6] else 0,
        'defect_queries': student_info[7] if student_info[7] else 0,
        'explanation_queries': student_info[8] if student_info[8] else 0,
        'debug_queries': student_info[9] if student_info[9] else 0,
        'last_query_at': student_info[10].strftime('%Y-%m-%d %H:%M:%S') if student_info[10] else None
    }
    
    # 获取学生的查询记录
    user_id = student_info[0]  # 这里需要获取用户ID，不是学生ID
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM students WHERE id = %s", (student_id,))
    user_result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user_result:
        user_id = user_result[0]
        code_queries = UserManager.get_user_code_queries(user_id, limit=20)
        # 为每个查询获取详细的缺陷信息
        for query in code_queries:
            if query['defect_count'] > 0:
                defects = UserManager.get_query_defects(query['id'])
                query['defects'] = defects
    else:
        code_queries = []
    
    return render_template('student_details.html',
                         student=student_details,
                         recent_queries=code_queries)

# 主函数
if __name__ == '__main__':
    print("C语言程序开发智能助手启动中...")
    print(f"DeepSeek API Key: {'已配置' if api_key else '未配置'}")
    print("访问 http://localhost:8080 使用系统")
    app.run(debug=False, port=8080)