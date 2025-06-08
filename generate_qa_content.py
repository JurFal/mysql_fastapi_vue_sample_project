#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据questions_q_a_r.json中Q字段的关键词，从向量数据库检索相关文章，
生成A字段的段落内容和R字段的引用信息。
"""

import json
import requests
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from typing import List, Dict, Any
import os
import argparse

# 配置
VECTOR_DB_HOST = 'localhost'
VECTOR_DB_PORT = 8002
# 修改为使用新的writing接口
WRITING_API_URL = 'http://127.0.0.1:8001/writing/'
# LLM_URL = 'http://10.176.64.152:11434/v1'  # 不再需要直接调用LLM
# LLM_MODEL = 'qwen2.5:7b'  # 不再需要直接调用LLM

# 配置OpenAI embedding函数
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="API_KEY_IS_NOT_NEEDED",
    api_base="http://10.176.64.152:11435/v1",
    model_name="bge-m3"
)

def load_questions_data(file_path: str) -> List[Dict[str, Any]]:
    """加载questions_q_a_r.json文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_questions_data(file_path: str, data: List[Dict[str, Any]]) -> None:
    """保存更新后的数据到文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def query_vector_db(keywords: List[str], n_results: int = 5) -> tuple:
    """从向量数据库查询相关文档"""
    try:
        # 连接向量数据库
        client = chromadb.HttpClient(host=VECTOR_DB_HOST, port=VECTOR_DB_PORT)
        collection = client.get_collection("papers_collection")
        collection._embedding_function = openai_ef
        
        # 构建查询字符串
        query = " ".join(keywords)
        
        # 查询相关文档
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # 提取文档内容和元数据
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        return documents, metadatas
        
    except Exception as e:
        print(f"查询向量数据库时出错: {str(e)}")
        return [], []

def generate_passage_with_llm(passage_type: str, keywords: List[str]) -> tuple[str, List[str]]:
    """使用新的/writing/接口生成段落内容和引用"""
    try:
        # 构建请求数据，匹配PassageIdea模式
        request_data = {
            "passage_type": passage_type,
            "passage_tag": keywords
        }
        
        # 发送请求到新的writing接口
        response = requests.post(WRITING_API_URL, json=request_data, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            # 解析PassageResponse格式
            passage_content = response_data.get("passage", "")
            references = response_data.get("references", [])
            
            # 去除"Reference n: "前缀
            cleaned_references = []
            for ref in references:
                if ref.startswith("Reference ") and ": " in ref:
                    # 找到": "的位置，提取后面的内容
                    colon_index = ref.find(": ")
                    cleaned_ref = ref[colon_index + 2:]  # +2 跳过": "
                    cleaned_references.append(cleaned_ref)
                else:
                    cleaned_references.append(ref)
            
            # 去重references
            unique_references = list(dict.fromkeys(cleaned_references))  # 保持顺序的去重
            
            return passage_content.strip(), unique_references
        else:
            print(f"Writing接口请求失败，状态码: {response.status_code}")
            return "", []
            
    except Exception as e:
        print(f"生成段落时出错: {str(e)}")
        return "", []

def process_single_question(q_data: List[List[str]]) -> tuple:
    """处理单个问题的Q数据，生成A和R"""
    a_data = []
    all_references = []
    
    for passage_info in q_data:
        passage_type = passage_info[0]
        keywords = passage_info[1]
        
        print(f"正在处理段落类型: {passage_type}, 关键词: {keywords}")
        passage_content, references = generate_passage_with_llm(passage_type, keywords)
            
        if passage_content:
            a_data.append(passage_content)
            all_references.extend(references)
        else:
            a_data.append(f"无法为{passage_type}段落生成内容")
    
    # 去重参考文献
    unique_references = list(dict.fromkeys(all_references))
    
    return a_data, unique_references

def main():
    """主函数"""
    
    # 文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, "datas/questions_q_a_r.json")
    
    # 检查文件是否存在
    if not os.path.exists(json_file_path):
        print(f"文件不存在: {json_file_path}")
        return
    
    # 加载数据
    print("加载questions_q_a_r.json文件...")
    questions_data = load_questions_data(json_file_path)
    
        # 处理所有问题
    questions_to_process = questions_data
    start_index = 0
    print(f"正常模式：处理所有 {len(questions_data)} 个问题")
    
    # 处理选定的问题
    for i, item in enumerate(questions_to_process):
        actual_index = start_index + i + 1
        print(f"\n处理第 {actual_index}/{len(questions_data)} 个问题...")
        
        q_data = item.get("Q", [])
        if not q_data:
            print(f"第 {actual_index} 个问题没有Q字段数据，跳过")
            continue
        
        # 生成A和R字段内容
        a_data, r_data = process_single_question(q_data)
        
        # 更新数据
        item["A"] = a_data
        item["R"] = r_data
        
        print(f"第 {actual_index} 个问题处理完成，生成了 {len(a_data)} 个段落和 {len(r_data)} 个参考文献")
    
    # 保存更新后的数据
    test_output_path = os.path.join(current_dir, "datas/questions_q_a_r_myapi3.json")
    print(f"\n保存结果到 {test_output_path}...")
    save_questions_data(test_output_path, questions_data)
    print(f"测试完成！结果已保存到: {test_output_path}")
    
if __name__ == "__main__":
    main()