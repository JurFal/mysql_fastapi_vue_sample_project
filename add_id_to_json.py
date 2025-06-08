#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

def add_id_to_json_file(file_path):
    """为JSON文件中的每个数据项添加id字段"""
    print(f"处理文件: {file_path}")
    
    # 读取原始文件
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 为每个数据项添加id字段
    for i, item in enumerate(data, 1):
        item['id'] = i
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"完成处理 {file_path}，共添加了 {len(data)} 个id字段")

def main():
    # 要处理的文件列表
    files = [
        "/Users/julius/julProg/paper_writing_helper/datas/questions_q.json",
        "/Users/julius/julProg/paper_writing_helper/datas/questions_q_a_r.json",
        "/Users/julius/julProg/paper_writing_helper/datas/questions_q_a_r_ref.json"
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            add_id_to_json_file(file_path)
        else:
            print(f"文件不存在: {file_path}")
    
    print("所有文件处理完成！")

if __name__ == "__main__":
    main()