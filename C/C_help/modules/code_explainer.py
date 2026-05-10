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

class CodeExplainer:
    def __init__(self):
        self.prompt_template = """
你是一个专业的C语言代码解释专家。请用**严格的Markdown格式**解释以下C代码的功能，要求如下：

- 只输出标准Markdown内容，不要输出"markdown"或"markdown:"等前缀
- 层级标题用`##`或`###`
- 列表用`-`或`1.`
- 代码块用```包裹
- 关键内容用**加粗**或`行内代码`
- 段落之间空一行
- 复杂结构用表格或流程图
- 多使用换行

代码如下：

```c
{code}
```

## 1. 代码主要功能概述

简要说明代码整体作用。

## 2. 关键函数与结构分析

### 2.1 主要函数列表

| 函数名 | 作用说明 |
| ------ | -------- |
|        |          |

### 2.2 重要数据结构

- 结构体/变量名：说明

## 3. 主要处理流程

1. 步骤一
2. 步骤二

## 4. 亮点、注意事项与复杂结构

- 亮点/注意事项
- 易错点或安全隐患

{query_instruction}

**请严格按照上述Markdown规范输出，内容分块清晰，禁止输出任何多余的说明、格式标记或"markdown"前缀。**
"""
        
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["code", "query_instruction"]
        )
        
        self.chain = LLMChain(
            llm=deepseek_llm,
            prompt=self.prompt
        )
    
    def explain_code(self, code, query=""):
        """解释C代码的功能"""
        query_instruction = f"此外，用户有以下特定问题，请重点解答: {query}" if query else ""
        
        # 使用RAG技术搜索相关知识
        knowledge_results = search_knowledge_base(code + " " + query if query else code)
        knowledge_context = ""
        
        if knowledge_results:
            knowledge_context = "根据相关技术资料，以下是一些可能对理解代码有帮助的背景知识:\n\n"
            for idx, result in enumerate(knowledge_results):
                knowledge_context += f"{idx+1}. {result['content']}\n\n"
        
        try:
            prompt = self.prompt_template.format(
                code=code,
                query_instruction=query_instruction,
                knowledge_context=knowledge_context
            )
            explanation = get_completion(prompt)
            
            # 检查是否返回了错误JSON
            if isinstance(explanation, str) and explanation.strip().startswith('{') and '"error":' in explanation:
                try:
                    error_data = json.loads(explanation)
                    if "error" in error_data:
                        return {"error": error_data["error"], "explanation": "获取代码解释时发生错误"}
                except:
                    pass
                    
            # 构建响应，包含知识来源
            response = {"explanation": explanation}
            if knowledge_results:
                response["knowledge_sources"] = [
                    {"source": result["source"], "score": result["score"]} 
                    for result in knowledge_results
                ]
            
            return response
            
        except Exception as e:
            return {"error": str(e), "explanation": "获取代码解释时发生错误"}