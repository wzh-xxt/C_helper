# -*- coding: utf-8 -*-
import os
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv, find_dotenv

# 读取 .env 中的密钥
_ = load_dotenv(find_dotenv())
api_key = os.environ["DEEPSEEK_API_KEY"]


# 验证API密钥格式
def is_valid_api_key(key):
    return key and key.startswith("sk-") and len(key) >= 32

# 基础配置
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DB_PATH = os.path.join(project_root, "data", "vector_store")
RAG_RESOURCES_PATH = os.path.join(project_root, "data", "rag_resources")
EMBEDDING_MODEL = r"D:\huggingface\hub\models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\snapshots\86741b4e3f5cb7765a600d3a3d55a0f6a6cb443d"

# LLM配置
llm_config = {
    "model_name": "deepseek-chat",
    "temperature": 0.1,
    "max_tokens": 1024,
}

# 初始化大模型
try:
    deepseek_llm = ChatOpenAI(
        model_name=llm_config["model_name"],
        temperature=llm_config["temperature"],
        max_tokens=llm_config["max_tokens"],
        openai_api_base="https://api.deepseek.com",
        openai_api_key=api_key
    )
except Exception as e:
    print(f"初始化LLM时出错: {str(e)}")
    # 创建一个简单的模拟接口
    from unittest.mock import MagicMock
    class MockResponse:
        def __init__(self, content):
            self.content = content
    
    deepseek_llm = MagicMock()
    deepseek_llm.invoke = lambda _: MockResponse("""{"defects": [], "error": "API连接失败，请检查API密钥和网络连接"}""")


# 测试API连接
def test_api_connection():
    try:
        response = deepseek_llm.invoke("Hello")
        return True, "API连接正常"
    except Exception as e:
        return False, f"API连接失败: {str(e)}"