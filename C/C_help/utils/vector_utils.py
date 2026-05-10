# -*- coding: utf-8 -*-
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import faiss
import pickle

class VectorStore:
    def __init__(self, store_dir: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", verbose: bool = False):
        """
        初始化向量存储
        
        Args:
            store_dir: 向量存储目录
            model_name: 使用的向量模型名称
            verbose: 是否显示详细信息
        """
        self.store_dir = store_dir
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents = []
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.verbose = verbose
        
        # 确保存储目录存在
        os.makedirs(store_dir, exist_ok=True)
        
        # 尝试加载现有索引
        self._load_index()
    
    def _load_index(self):
        """加载现有的向量索引和文档"""
        index_path = os.path.join(self.store_dir, "index.faiss")
        docs_path = os.path.join(self.store_dir, "documents.pkl")
        
        # 确保目录存在且有正确的权限
        os.makedirs(self.store_dir, exist_ok=True)
        
        if os.path.exists(index_path) and os.path.exists(docs_path):
            try:
                # 检查文件权限
                if not os.access(index_path, os.R_OK) or not os.access(docs_path, os.R_OK):
                    if self.verbose:
                        print(f"向量索引文件权限不足，请检查文件权限: {self.store_dir}")
                    self._create_new_index()
                    return
                    
                # 检查文件大小
                if os.path.getsize(index_path) == 0 or os.path.getsize(docs_path) == 0:
                    if self.verbose:
                        print("向量索引文件为空，创建新索引")
                    self._create_new_index()
                    return
                    
                self.index = faiss.read_index(index_path)
                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                if self.verbose:
                    print(f"已加载向量索引，包含 {len(self.documents)} 个文档")
            except Exception as e:
                if self.verbose:
                    print(f"加载向量索引失败: {e}")
                # 如果加载失败，尝试备份并创建新索引
                try:
                    if os.path.exists(index_path):
                        os.rename(index_path, f"{index_path}.bak")
                    if os.path.exists(docs_path):
                        os.rename(docs_path, f"{docs_path}.bak")
                except:
                    pass
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """创建新的向量索引"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        if self.verbose:
            print("创建新的向量索引")
    
    def _save_index(self):
        """保存向量索引和文档"""
        try:
            # 确保目录存在且有写入权限
            if not os.path.exists(self.store_dir):
                os.makedirs(self.store_dir, exist_ok=True)
                
            if not os.access(self.store_dir, os.W_OK):
                if self.verbose:
                    print(f"向量存储目录没有写入权限: {self.store_dir}")
                return
                
            # 保存FAISS索引
            index_path = os.path.join(self.store_dir, "index.faiss")
            temp_index_path = f"{index_path}.tmp"
            faiss.write_index(self.index, temp_index_path)
            
            # 保存文档
            docs_path = os.path.join(self.store_dir, "documents.pkl")
            temp_docs_path = f"{docs_path}.tmp"
            with open(temp_docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
                
            # 使用临时文件进行原子写入
            try:
                os.replace(temp_index_path, index_path)
                os.replace(temp_docs_path, docs_path)
                if self.verbose:
                    print(f"已保存向量索引，包含 {len(self.documents)} 个文档")
            except Exception as e:
                if self.verbose:
                    print(f"保存向量索引失败: {e}")
                # 清理临时文件
                if os.path.exists(temp_index_path):
                    os.remove(temp_index_path)
                if os.path.exists(temp_docs_path):
                    os.remove(temp_docs_path)
        except Exception as e:
            if self.verbose:
                print(f"保存向量索引失败: {e}")
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表，每个文档是一个字典，包含 'content' 和 'metadata' 字段
        """
        if not documents:
            return
            
        # 准备文本和元数据
        texts = [doc['content'] for doc in documents]
        metadatas = [doc.get('metadata', {}) for doc in documents]
        
        # 生成向量，根据verbose控制是否显示进度条
        vectors = self.model.encode(texts, show_progress_bar=self.verbose)
        
        # 添加到索引
        self.index.add(np.array(vectors).astype('float32'))
        
        # 保存文档
        for doc, metadata in zip(texts, metadatas):
            self.documents.append({
                'content': doc,
                'metadata': metadata
            })
        
        # 保存更新后的索引
        self._save_index()
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            top_k: 返回的结果数量
            
        Returns:
            相似文档列表，每个文档包含内容和相似度分数
        """
        if not self.documents:
            return []
            
        # 生成查询向量
        query_vector = self.model.encode([query])[0]
        
        # 搜索最相似的向量
        distances, indices = self.index.search(
            np.array([query_vector]).astype('float32'), 
            min(top_k, len(self.documents))
        )
        
        # 构建结果
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx]
                results.append({
                    'content': doc['content'],
                    'metadata': doc['metadata'],
                    'score': float(1 / (1 + distance))  # 将距离转换为相似度分数
                })
        
        return results
    
    def clear(self):
        """清空向量存储"""
        self._create_new_index()
        self._save_index()
        print("已清空向量存储") 