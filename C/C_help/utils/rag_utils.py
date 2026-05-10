# -*- coding: utf-8 -*-
import os
import sys
import json
from typing import List, Dict, Any, Optional
import traceback

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.vector_utils import VectorStore
from config import VECTOR_DB_PATH, EMBEDDING_MODEL

# 定义知识库目录
RAG_DIR = os.path.join(project_root, 'data', 'rag_resources')
EXTERNAL_DEFECT_DIR = os.path.join(project_root, 'data', 'external_defects')

# 确保目录存在
os.makedirs(RAG_DIR, exist_ok=True)
os.makedirs(EXTERNAL_DEFECT_DIR, exist_ok=True)

# 知识库映射
KNOWLEDGE_FILES = {
    # 知识库
    'stackoverflow.txt': r"D:\pythonStudy\C_defect\C_help\utils\data\rag_resources\stackoverflow.txt",
    'cppreference.txt': r"D:\pythonStudy\C_defect\C_help\utils\data\rag_resources\cppreference.txt",
    
    # 外部缺陷库
    'clang_analyzer.txt': r"D:\pythonStudy\C_defect\C_help\utils\data\external_defects\clang_analyzer.txt",
    'cppcheck.txt': r"D:\pythonStudy\C_defect\C_help\utils\data\external_defects\cppcheck.txt",
}

# 初始化向量存储
vector_store = VectorStore(VECTOR_DB_PATH, EMBEDDING_MODEL, verbose=True)

def update_vector_store():
    """更新向量存储中的文档"""
    try:
        # 清空现有存储
        vector_store.clear()
        
        # 从所有知识库文件加载文档
        documents = []
        for file_name, file_path in KNOWLEDGE_FILES.items():
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 将内容按段落分割
                    paragraphs = content.split('\n\n')
                    
                    # 添加每个段落到文档列表
                    for paragraph in paragraphs:
                        if paragraph.strip():
                            documents.append({
                                'content': paragraph.strip(),
                                'metadata': {
                                    'source': file_name,
                                    'type': 'knowledge_base'
                                }
                            })
                except Exception as e:
                    print(f"处理知识文件时出错 {file_path}: {str(e)}")
                    traceback.print_exc()
        
        # 将文档添加到向量存储
        if documents:
            print(f"正在更新向量存储，添加 {len(documents)} 个文档...")
            vector_store.add_documents(documents)
            print("向量存储更新完成")
        else:
            print("没有找到可用的文档")
            
    except Exception as e:
        print(f"更新向量存储时出错: {str(e)}")
        traceback.print_exc()

def search_knowledge_base(query: str, top_k: int = 15) -> List[Dict[str, Any]]:
    """
    使用向量存储搜索知识库，返回相关度最高的文档
    
    Args:
        query: 搜索查询
        top_k: 返回的结果数量
        
    Returns:
        匹配的文档列表，每个文档包含内容、来源和匹配分数
    """
    try:
        print(f"RAG工具: 正在搜索知识库，查询: '{query[:50]}...' (如果较长)")
        
        # 确保查询非空
        if not query or not isinstance(query, str):
            print("RAG工具: 查询为空或非字符串类型")
            return []
        
        # 使用向量存储搜索
        results = vector_store.search(query, top_k)
        
        # 转换结果格式
        formatted_results = []
        for result in results:
            formatted_results.append({
                'content': result['content'],
                'source': result['metadata']['source'],
                'score': result['score']
            })
        
        print(f"RAG工具: 找到 {len(formatted_results)} 个相关知识片段")
        return formatted_results
        
    except Exception as e:
        print(f"RAG工具: 搜索知识库时出错: {str(e)}")
        traceback.print_exc()
        return []

def get_available_knowledge_bases() -> Dict[str, str]:
    """
    获取所有可用的知识库文件及其描述
    
    Returns:
        知识库文件名和描述的字典
    """
    knowledge_bases = {}
    
    # 检查每个知识库文件是否存在
    for file_name, file_path in KNOWLEDGE_FILES.items():
        if os.path.exists(file_path):
            # 根据文件名生成描述
            if 'stackoverflow' in file_name:
                description = "Stack Overflow C/C++问答集合"
            elif 'cppreference' in file_name:
                description = "C/C++参考文档"
            elif 'clang_analyzer' in file_name:
                description = "Clang Static Analyzer静态分析规则"
            elif 'cppcheck' in file_name:
                description = "Cppcheck静态分析器常见问题"
            else:
                description = "通用C语言编程知识"
                
            knowledge_bases[file_name] = description
    
    return knowledge_bases

# 创建新的缺陷库和知识库文件
def create_sample_external_defect_files():
    """创建Clang Analyzer和Cppcheck缺陷库文件，以及Stack Overflow和cppreference知识库文件"""
    
    # 删除旧的知识库文件
    old_files = [
        os.path.join(RAG_DIR, 'buffer_overflow.txt'),
        os.path.join(RAG_DIR, 'memory_leaks.txt'),
        os.path.join(RAG_DIR, 'null_pointer.txt'),
        os.path.join(EXTERNAL_DEFECT_DIR, 'cwe_top25.txt'),
        os.path.join(EXTERNAL_DEFECT_DIR, 'owasp_c_guide.txt'),
        os.path.join(EXTERNAL_DEFECT_DIR, 'cert_c_standards.txt')
    ]
    
    for old_file in old_files:
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
                print(f"RAG工具: 已删除旧文件: {old_file}")
            except Exception as e:
                print(f"RAG工具: 删除旧文件时出错 {old_file}: {str(e)}")
    
    # Clang Static Analyzer内容
    clang_content = """Clang Static Analyzer: core.DivideZero
描述: 检测除零错误，当代码尝试将一个值除以零时，将导致未定义行为
例子: int x = 5 / 0; 或者 float y = 10.0 / val; 当val可能为0时
严重性: 高
缓解: 在执行除法操作前添加检查以确保除数不为零

Clang Static Analyzer: core.NullDereference
描述: 检测对空指针的解引用，这会导致程序崩溃
例子: int *p = NULL; *p = 5;
严重性: 高
缓解: 在使用指针前总是检查它是否为NULL

Clang Static Analyzer: core.UndefinedBinaryOperatorResult
描述: 检测可能导致未定义行为的二元运算，如有符号整数溢出
例子: int x = INT_MAX + 1;
严重性: 中
缓解: 使用边界检查或更大的数据类型

Clang Static Analyzer: unix.Malloc
描述: 检测与内存分配相关的错误，如内存泄漏、双重释放和使用已释放的内存
例子: void *p = malloc(10); free(p); free(p); // 双重释放
严重性: 高
缓解: 仔细跟踪内存分配和释放，使用智能指针

Clang Static Analyzer: security.insecureAPI
描述: 检测不安全API的使用，如strcpy、gets等
例子: char buf[10]; strcpy(buf, user_input); // 可能缓冲区溢出
严重性: 高
缓解: 使用安全的替代函数，如strncpy、fgets，并包含适当的边界检查"""

    # Cppcheck内容
    cppcheck_content = """Cppcheck: uninitvar
描述: 检测使用未初始化的变量，这可能导致不可预测的行为
例子: int x; if(x == 5) {} // x未初始化
严重性: 高
修复: 在使用前初始化所有变量

Cppcheck: memleak
描述: 检测内存泄漏，即分配的内存未被释放
例子: char* p = malloc(10); p = NULL; // 内存泄漏
严重性: 高
修复: 确保所有分配的内存都被适当释放

Cppcheck: bufferAccessOutOfBounds
描述: 检测缓冲区越界访问
例子: int arr[5]; arr[10] = 0; // 越界访问
严重性: 高
修复: 确保所有数组访问都在有效范围内

Cppcheck: nullPointer
描述: 检测空指针的解引用
例子: int* p = NULL; *p = 10; // 空指针解引用
严重性: 高
修复: 在解引用前检查指针是否为NULL

Cppcheck: useClosedFile
描述: 检测对已关闭文件的使用
例子: FILE* f = fopen("file.txt", "r"); fclose(f); fprintf(f, "text"); // 使用已关闭文件
严重性: 中
修复: 确保不在关闭文件后使用文件句柄"""

    # Stack Overflow内容
    stackoverflow_content = """Stack Overflow: 如何防止C语言中的缓冲区溢出？
问题: 我正在编写一个需要处理用户输入的C程序，我想确保避免缓冲区溢出漏洞。有什么最佳实践吗？
回答: 
1. 使用边界检查的字符串函数如strncpy、strncat而不是strcpy、strcat
2. 总是验证用户输入的长度，并确保它不超过缓冲区大小
3. 考虑使用更安全的字符串库如strlcpy(BSD)
4. 避免gets函数，使用fgets代替
5. 编译时启用堆栈保护选项如-fstack-protector

Stack Overflow: C/C++中检测内存泄漏的工具
问题: 我的C++程序可能有内存泄漏。有哪些工具可以帮助我检测它们？
回答:
1. Valgrind Memcheck是最常用的工具之一，它可以检测内存泄漏、使用未初始化的内存等问题
2. AddressSanitizer(ASAN)是一个快速的内存错误检测器，集成在GCC和Clang中
3. DrMemory是Windows下的一个好选择
4. C++中可以考虑使用智能指针(unique_ptr, shared_ptr)避免手动内存管理错误
5. 使用静态分析工具如Cppcheck或Clang Static Analyzer也可以在编译时捕获一些内存问题

Stack Overflow: 为什么我的C程序崩溃在指针操作上？
问题: 我的程序在运行时崩溃，错误是"段错误"。代码围绕指针操作，我不确定问题出在哪里。
回答:
1. 最常见的原因是解引用空指针或无效指针
2. 数组越界访问也会导致类似问题
3. 使用已释放的内存(use-after-free)
4. 栈溢出(递归太深或大型局部数组)
5. 调试技巧：使用GDB、Valgrind或AddressSanitizer跟踪崩溃点
6. 添加断言和指针有效性检查可以帮助定位问题"""

    # Cppreference内容
    cppreference_content = """Cppreference: C标准库函数 - 字符串处理
strcpy(char* dest, const char* src)
描述: 将src指向的以null结尾的字符串复制到dest指向的数组
注意事项: 不执行边界检查，可能导致缓冲区溢出。目标缓冲区必须足够大以容纳源字符串。
安全替代: strncpy()或使用C++的std::string

strncpy(char* dest, const char* src, size_t count)
描述: 复制最多count个字符从src到dest
注意事项: 如果src的长度小于count，剩余空间将填充null字符。如果src的长度大于或等于count，不会添加结束的null字符。

memcpy(void* dest, const void* src, size_t count)
描述: 从src复制count个字节到dest
注意事项: 不检查源和目标内存区域是否重叠，如果重叠行为未定义。对于重叠内存区域，应使用memmove()。

Cppreference: C动态内存管理
malloc(size_t size)
描述: 分配size字节的未初始化内存
返回值: 成功时返回指向分配内存的指针，失败时返回NULL
注意事项: 分配的内存不会初始化，应当检查返回值是否为NULL

free(void* ptr)
描述: 释放之前由malloc()、calloc()或realloc()分配的内存
注意事项: 如果ptr为NULL，函数不执行任何操作。对已释放的内存再次调用free()，或使用已释放的内存导致未定义行为。

calloc(size_t num, size_t size)
描述: 分配num个元素的数组，每个元素size字节，并初始化所有位为零
返回值: 成功时返回指向分配内存的指针，失败时返回NULL

Cppreference: C标准库 - 文件操作
fopen(const char* filename, const char* mode)
描述: 打开文件，mode指定访问模式("r"读, "w"写, "a"追加等)
返回值: 成功时返回FILE指针，失败时返回NULL
注意事项: 总是检查返回值确保文件成功打开

fclose(FILE* stream)
描述: 关闭文件
返回值: 成功时返回0，失败时返回EOF
注意事项: 未关闭的文件可能导致资源泄漏"""

    # 创建Clang Analyzer文件
    clang_path = KNOWLEDGE_FILES['clang_analyzer.txt']
    if not os.path.exists(clang_path) or os.path.getsize(clang_path) == 0:
        try:
            with open(clang_path, 'w', encoding='utf-8') as f:
                f.write(clang_content)
            print(f"RAG工具: 已创建Clang Static Analyzer示例文件: {clang_path}")
        except Exception as e:
            print(f"RAG工具: 创建Clang Static Analyzer文件时出错: {str(e)}")
            traceback.print_exc()

    # 创建Cppcheck文件
    cppcheck_path = KNOWLEDGE_FILES['cppcheck.txt']
    if not os.path.exists(cppcheck_path) or os.path.getsize(cppcheck_path) == 0:
        try:
            with open(cppcheck_path, 'w', encoding='utf-8') as f:
                f.write(cppcheck_content)
            print(f"RAG工具: 已创建Cppcheck示例文件: {cppcheck_path}")
        except Exception as e:
            print(f"RAG工具: 创建Cppcheck文件时出错: {str(e)}")
            traceback.print_exc()
            
    # 创建Stack Overflow文件
    stackoverflow_path = KNOWLEDGE_FILES['stackoverflow.txt']
    if not os.path.exists(stackoverflow_path) or os.path.getsize(stackoverflow_path) == 0:
        try:
            with open(stackoverflow_path, 'w', encoding='utf-8') as f:
                f.write(stackoverflow_content)
            print(f"RAG工具: 已创建Stack Overflow示例文件: {stackoverflow_path}")
        except Exception as e:
            print(f"RAG工具: 创建Stack Overflow文件时出错: {str(e)}")
            traceback.print_exc()
            
    # 创建Cppreference文件
    cppreference_path = KNOWLEDGE_FILES['cppreference.txt']
    if not os.path.exists(cppreference_path) or os.path.getsize(cppreference_path) == 0:
        try:
            with open(cppreference_path, 'w', encoding='utf-8') as f:
                f.write(cppreference_content)
            print(f"RAG工具: 已创建Cppreference示例文件: {cppreference_path}")
        except Exception as e:
            print(f"RAG工具: 创建Cppreference文件时出错: {str(e)}")
            traceback.print_exc()

    # 在创建完文件后更新向量存储
    update_vector_store()

# 自动创建样本文件
create_sample_external_defect_files() 