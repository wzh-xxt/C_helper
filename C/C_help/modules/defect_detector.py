# -*- coding: utf-8 -*-
from typing import Dict, List, Any, Optional
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import sys
import os
import json
import re
import traceback

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from config import deepseek_llm
from utils.llm_utils import get_completion
from utils.rag_utils import search_knowledge_base, get_available_knowledge_bases

class DefectDetector:
    """缺陷检测器类，用于分析C代码中的潜在缺陷"""
    
    def __init__(self):
        self.prompt_template = """
你是一个专业的C语言代码安全审计专家，请分析下面的C代码并检测可能存在的缺陷和问题。

代码:
```c
{code}
```

{knowledge_context}

{user_query}

参考外部缺陷库包括：
1. Clang Static Analyzer - 检测C/C++代码中的静态缺陷
2. Cppcheck - 检测C/C++代码中的常见问题

请从内存安全、类型安全、逻辑错误等角度进行分析。对于每个检测到的缺陷，提供以下信息：
1. 缺陷描述：简要说明问题
2. 影响：分析该缺陷可能导致的影响
3. 修复建议：如何修复这个问题

以下是你需要返回的JSON格式示例:

如果找到缺陷:
```
{{"defects": [
  {{"description": "缺陷描述1", "impact": "影响1", "suggestion": "建议1"}},
  {{"description": "缺陷描述2", "impact": "影响2", "suggestion": "建议2"}}
]}}
```

如果没有找到缺陷:
```
{{"defects": []}}
```

请务必确保返回的JSON格式正确，不要包含任何其他文本。
回答必须限制为一个有效的JSON对象，不要有任何额外的解释或介绍文字。
"""
        
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["code", "user_query", "knowledge_context"]
        )
        
        self.chain = LLMChain(
            llm=deepseek_llm,
            prompt=self.prompt
        )
        
        # 获取可用的知识库列表
        self.knowledge_bases = get_available_knowledge_bases()
        print(f"缺陷检测模块：已加载 {len(self.knowledge_bases)} 个知识库")
        for kb_name, kb_desc in self.knowledge_bases.items():
            print(f"  - {kb_name}: {kb_desc}")

    def create_default_response(self):
        """创建默认的空缺陷响应"""
        return {"defects": []}

    def extract_json_from_text(self, text):
        """
        从LLM响应中提取JSON对象
        
        Args:
            text: LLM返回的文本
            
        Returns:
            提取的JSON对象，如果无法提取则返回默认响应
        """
        if not text:
            print("响应为空，返回默认响应")
            return self.create_default_response()
        
        # 尝试直接解析整个响应
        try:
            json_obj = json.loads(text)
            if isinstance(json_obj, dict) and "defects" in json_obj:
                return json_obj
        except json.JSONDecodeError:
            pass
        
        # 尝试查找JSON块
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        json_match = re.search(json_pattern, text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1).strip()
            try:
                json_obj = json.loads(json_str)
                if isinstance(json_obj, dict) and "defects" in json_obj:
                    return json_obj
            except json.JSONDecodeError:
                pass
                
        # 尝试匹配不带格式标记的JSON对象
        obj_pattern = r'\{.*"defects"\s*:\s*\[.*\].*\}'
        obj_match = re.search(obj_pattern, text, re.DOTALL)
        
        if obj_match:
            json_str = obj_match.group(0).strip()
            try:
                json_obj = json.loads(json_str)
                if isinstance(json_obj, dict) and "defects" in json_obj:
                    return json_obj
            except json.JSONDecodeError:
                pass
        
        # 尝试提取defects数组内容
        defects_pattern = r'"defects"\s*:\s*\[\s*(.*?)\s*\]'
        defects_match = re.search(defects_pattern, text, re.DOTALL)
        
        if defects_match:
            defects_content = defects_match.group(1).strip()
            if not defects_content:
                # 空数组
                return {"defects": []}
            
            try:
                # 尝试解析 defects 内容
                json_defects = json.loads(f"[{defects_content}]")
                return {"defects": json_defects}
            except json.JSONDecodeError:
                pass
        
        # 所有方法都失败，返回默认响应
        print("无法从响应中提取有效的JSON，返回空缺陷列表")
        return self.create_default_response()

    def extract_json_from_text(self, text):
        """
        从LLM响应中提取JSON对象
        
        Args:
            text: LLM返回的文本
            
        Returns:
            提取的JSON对象，如果无法提取则返回默认响应
        """
        if not text:
            print("响应为空，返回默认响应")
            return self.create_default_response()
        
        # 尝试直接解析整个响应
        try:
            json_obj = json.loads(text)
            if isinstance(json_obj, dict) and "defects" in json_obj:
                return json_obj
        except json.JSONDecodeError:
            pass
        
        # 尝试查找JSON块
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        json_match = re.search(json_pattern, text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1).strip()
            try:
                json_obj = json.loads(json_str)
                if isinstance(json_obj, dict) and "defects" in json_obj:
                    return json_obj
            except json.JSONDecodeError:
                pass
                
        # 尝试匹配不带格式标记的JSON对象
        obj_pattern = r'\{.*"defects"\s*:\s*\[.*\].*\}'
        obj_match = re.search(obj_pattern, text, re.DOTALL)
        
        if obj_match:
            json_str = obj_match.group(0).strip()
            try:
                json_obj = json.loads(json_str)
                if isinstance(json_obj, dict) and "defects" in json_obj:
                    return json_obj
            except json.JSONDecodeError:
                pass
        
        # 尝试提取defects数组内容
        defects_pattern = r'"defects"\s*:\s*\[\s*(.*?)\s*\]'
        defects_match = re.search(defects_pattern, text, re.DOTALL)
        
        if defects_match:
            defects_content = defects_match.group(1).strip()
            if not defects_content:
                # 空数组
                return {"defects": []}
            
            try:
                # 尝试解析 defects 内容
                json_defects = json.loads(f"[{defects_content}]")
                return {"defects": json_defects}
            except json.JSONDecodeError:
                pass
        
        # 所有方法都失败，返回默认响应
        print("无法从响应中提取有效的JSON，返回空缺陷列表")
        return self.create_default_response()

    def detect_defects(self, code: str, query: Optional[str] = None) -> Dict[str, Any]:
        """
        分析C代码中的潜在缺陷
        
        Args:
            code: 需要分析的C代码
            query: 可选的用户查询，以引导分析方向
            
        Returns:
            检测到的缺陷信息
        """
        # 准备用户查询部分
        user_query_text = f"用户查询: {query}" if query else ""
        
        # 使用RAG技术搜索相关知识
        search_query = f"{code} {query} + 重点根据Clang的规则和CppCheck的规则来判断缺陷" if query else code
        knowledge_results = search_knowledge_base(search_query)
        knowledge_context = ""
        
        if knowledge_results:
            knowledge_context = "参考以下缺陷库和安全知识进行分析:\n\n"
            for idx, result in enumerate(knowledge_results):
                knowledge_context += f"{idx+1}. {result['content']}\n\n"
            print(knowledge_context)
        
        # 准备提示
        prompt = self.prompt_template.format(
            code=code,
            user_query=user_query_text,
            knowledge_context=knowledge_context
        )
        
        try:
            # 获取响应
            print("调用LLM API获取缺陷检测结果...")
            response = get_completion(prompt)
            print(f"原始响应长度: {len(response) if response else 0}字符")
            if response and isinstance(response, str) and len(response) > 100:
                print(f"响应前100字符: {response[:100]}")
                print(f"响应后100字符: {response[-100:]}")
            
            # 处理响应
            try:
                result = self.extract_json_from_text(response)
                # 确保结果有正确的结构
                if not isinstance(result, dict):
                    print(f"提取的结果不是字典类型: {type(result)}")
                    result = self.create_default_response()
                
                # 确保有defects字段且为列表
                if "defects" not in result:
                    print("结果中没有defects字段，添加默认字段")
                    result["defects"] = []
                elif not isinstance(result["defects"], list):
                    print(f"defects字段不是列表类型: {type(result['defects'])}")
                    result["defects"] = []
                
                # 添加知识来源
                if knowledge_results:
                    result["knowledge_sources"] = [
                        {"source": result["source"], "score": result["score"]} 
                        for result in knowledge_results
                    ]
                
                print(f"提取到的缺陷数量: {len(result['defects'])}")
                return result
                
            except Exception as parse_error:
                error_detail = traceback.format_exc()
                print(f"解析响应时出错: {str(parse_error)}")
                print(f"错误详情:\n{error_detail}")
                return {"defects": [], "error": f"解析响应时出错: {str(parse_error)}"}
                
        except Exception as e:
            error_detail = traceback.format_exc()
            print(f"调用缺陷检测API时出错: {str(e)}")
            print(f"错误详情:\n{error_detail}")
            return {"defects": [], "error": f"调用API时出错: {str(e)}"}

   