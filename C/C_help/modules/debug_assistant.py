# -*- coding: utf-8 -*-
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import sys
import os
import json

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from config import deepseek_llm
from utils.llm_utils import get_completion
from utils.rag_utils import search_knowledge_base

class DebugAssistant:
    def __init__(self):
        self.prompt_template = """
        你是一个专业的C语言调试专家。请用**严格的Markdown格式**分析以下C代码和错误信息，提供调试建议，要求如下：
        
        1. 层级标题用`##`或`###`
        2. 列表用`-`或`1.`
        3. 代码块用```包裹
        4. 关键内容用**加粗**或`行内代码`
        5. 段落之间空一行
        6. 复杂结构用表格或流程图
        7. 多使用换行
        
        代码如下：
        
        ```c
        {code}
        ```
        
        错误信息或问题描述：
        
        ```
        {error_message}
        ```
        
        {knowledge_context}
        
        ## 1. 问题分析
        
        - 详细分析错误的可能原因
        
        ## 2. 调试建议
        
        - 如何定位和验证问题的具体建议
        
        ## 3. 解决方案
        
        - 提供修复代码和详细解释
        
        ## 4. 预防措施
        
        - 如何避免类似问题的建议
        
        - 如有复杂结构，请用表格或流程图展示
        
        请严格按照上述Markdown规范输出，注意多换行，内容分块清晰。
        """
        
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["code", "error_message", "knowledge_context"]
        )
        
        self.chain = LLMChain(
            llm=deepseek_llm,
            prompt=self.prompt
        )
    
    def debug_code(self, code, error_message):
        """调试C代码"""
        try:
            # 使用RAG技术搜索相关知识
            search_query = f"{code} {error_message}"
            knowledge_results = search_knowledge_base(search_query)
            knowledge_context = ""
            
            if knowledge_results:
                knowledge_context = "根据相关技术资料，以下是一些可能对调试有帮助的背景知识:\n\n"
                for idx, result in enumerate(knowledge_results):
                    knowledge_context += f"{idx+1}. {result['content']}\n\n"
                print(knowledge_context)
            
            # 生成调试建议
            prompt = self.prompt_template.format(
                code=code,
                error_message=error_message,
                knowledge_context=knowledge_context
            )
            suggestions = get_completion(prompt)
            
            # 检查是否返回了错误JSON
            if isinstance(suggestions, str) and suggestions.strip().startswith('{') and '"error":' in suggestions:
                try:
                    error_data = json.loads(suggestions)
                    if "error" in error_data:
                        return {"error": error_data["error"], "debug_suggestions": "获取调试建议时发生错误"}
                except:
                    pass
            
            # 构建响应，包含知识来源
            response = {"debug_suggestions": suggestions}
            if knowledge_results:
                response["knowledge_sources"] = [
                    {"source": result["source"], "score": result["score"]} 
                    for result in knowledge_results
                ]
            
            return response
            
        except Exception as e:
            return {"error": str(e), "debug_suggestions": "获取调试建议时发生错误"}