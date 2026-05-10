# -*- coding: utf-8 -*-
import json
import sys
import os
import traceback
import re

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from config import deepseek_llm

def sanitize_text(text):
    """
    清理文本，去除可能导致JSON解析错误的字符，但保留换行符和回车符
    """
    if not isinstance(text, str):
        return text
    # 只移除除\n和\r以外的控制字符
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    return text.strip()

def get_completion(prompt: str):
    """
    使用配置好的LLM获取文本补全。
    
    Args:
        prompt: 发送给LLM的提示。
        
    Returns:
        LLM的响应字符串，或者在出错时返回包含错误信息的JSON字符串。
    """
    try:
        print("LLM工具: 正在调用LLM API...")
        # 调用LLM API
        response = deepseek_llm.invoke(prompt)
        
        # 处理响应
        if hasattr(response, 'content'):
            content = sanitize_text(response.content)
            print(f"LLM工具: 获取到API响应，内容长度: {len(content)} 字符")
            print(f"LLM工具: 响应内容示例: {content[:100]}...")
            return content
        elif isinstance(response, str):
            content = sanitize_text(response)
            print(f"LLM工具: 获取到API响应(字符串)，内容长度: {len(content)} 字符")
            print(f"LLM工具: 响应内容示例: {content[:100]}...")
            return content
        else:
            print(f"LLM工具: 获取到未知类型的API响应: {type(response)}")
            # 尝试将任何类型的响应转换为字符串
            try:
                content = sanitize_text(str(response))
                return content
            except:
                # 如果转换失败，返回一个默认响应
                return json.dumps({"defects": [], "error": "无法处理的响应类型"})
                
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"LLM工具: API调用失败: {str(e)}")
        print(f"LLM工具: 错误详情:\n{error_detail}")
        
        # 返回一个JSON格式的错误信息
        error_response = {
            "error": f"LLM API调用失败: {str(e)}",
            "defects": []  # 确保有defects字段
        }
        return json.dumps(error_response)