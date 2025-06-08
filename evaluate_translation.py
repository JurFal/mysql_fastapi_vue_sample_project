#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用BLEU和Rouge评估翻译准确度
"""

import json
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from bert_score import score
import jieba
import re
import os

# 设置huggingface镜像 - 使用多种环境变量确保生效
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HUGGINGFACE_HUB_CACHE'] = os.path.expanduser('~/.cache/huggingface')
os.environ['TRANSFORMERS_CACHE'] = os.path.expanduser('~/.cache/huggingface/transformers')
os.environ['HF_HUB_OFFLINE'] = '0'

# 导入transformers相关模块前设置镜像
try:
    from transformers import AutoTokenizer, AutoModel
    # 设置transformers使用镜像
    import transformers
    transformers.utils.hub.HUGGINGFACE_CO_URL_TEMPLATE = "https://hf-mirror.com/{repo_id}/resolve/{revision}/{filename}"
except ImportError:
    pass

def preprocess_chinese_text(text):
    """预处理中文文本"""
    # 去除标点符号和特殊字符
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
    # 使用jieba分词
    words = jieba.lcut(text)
    # 过滤空字符串
    words = [word.strip() for word in words if word.strip()]
    return words

def calculate_bleu_score(reference, candidate):
    """计算BLEU分数"""
    # 预处理文本
    ref_tokens = preprocess_chinese_text(reference)
    cand_tokens = preprocess_chinese_text(candidate)
    
    # 使用平滑函数避免零分
    smoothing = SmoothingFunction().method1
    
    # 计算BLEU-1到BLEU-4
    bleu_scores = {}
    for n in range(1, 5):
        weights = [1.0/n] * n + [0] * (4-n)
        try:
            score = sentence_bleu([ref_tokens], cand_tokens, weights=weights, smoothing_function=smoothing)
            bleu_scores[f'BLEU-{n}'] = score
        except:
            bleu_scores[f'BLEU-{n}'] = 0.0
    
    return bleu_scores

def calculate_rouge_score(reference, candidate):
    """计算Rouge分数"""
    # 预处理文本，转换为空格分隔的字符串
    ref_tokens = preprocess_chinese_text(reference)
    cand_tokens = preprocess_chinese_text(candidate)
    
    ref_text = ' '.join(ref_tokens)
    cand_text = ' '.join(cand_tokens)
    
    # 创建Rouge评分器
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=False)
    
    # 计算Rouge分数
    scores = scorer.score(ref_text, cand_text)
    
    rouge_scores = {}
    for metric, score in scores.items():
        rouge_scores[f'{metric.upper()}-P'] = score.precision
        rouge_scores[f'{metric.upper()}-R'] = score.recall
        rouge_scores[f'{metric.upper()}-F'] = score.fmeasure
    
    return rouge_scores

def calculate_bert_score(references, candidates):
    """计算BERTScore分数"""
    try:
        # 临时设置镜像环境变量
        original_endpoint = os.environ.get('HF_ENDPOINT')
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        
        # 使用本地模型路径或指定镜像源的模型
        # 尝试使用预下载的模型或通过镜像下载
        P, R, F1 = score(
            candidates, 
            references, 
            lang='zh', 
            verbose=True,  # 显示详细信息以便调试
            model_type='bert-base-chinese',
            device='cpu'  # 强制使用CPU避免GPU相关问题
        )
        
        bert_scores = {
            'BERTScore-P': P.mean().item(),
            'BERTScore-R': R.mean().item(), 
            'BERTScore-F1': F1.mean().item()
        }
        
        # 恢复原始环境变量
        if original_endpoint:
            os.environ['HF_ENDPOINT'] = original_endpoint
        
        return bert_scores
    except Exception as e:
        print(f"BERTScore计算出错: {e}")
        print("尝试跳过BERTScore计算...")
        return {
            'BERTScore-P': 0.0,
            'BERTScore-R': 0.0,
            'BERTScore-F1': 0.0
        }

def load_json_data(file_path):
    """加载JSON数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # 打开输出文件
    output_file = '/Users/julius/julProg/paper_writing_helper/evaluate_result_myapi3.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # 重定向print输出到文件
        import sys
        original_stdout = sys.stdout
        sys.stdout = f
        
        try:
            # 加载数据
            original_data = load_json_data('/Users/julius/julProg/paper_writing_helper/datas/questions_q_a_r_myapi3.json')
            reference_data = load_json_data('/Users/julius/julProg/paper_writing_helper/datas/questions_q_a_r_ref.json')
            
            print("BLEU和Rouge评估结果 - 全部记录的A字段")
            print("=" * 60)
    
            # 评估全部记录
            total_records = min(len(original_data), len(reference_data))
            print(f"总共评估 {total_records} 条记录")
            
            # 用于存储所有记录的总体评估结果
            overall_bleu_scores = {'BLEU-1': 0, 'BLEU-2': 0, 'BLEU-3': 0, 'BLEU-4': 0}
            overall_rouge_scores = {
                'ROUGE1-P': 0, 'ROUGE1-R': 0, 'ROUGE1-F': 0,
                'ROUGE2-P': 0, 'ROUGE2-R': 0, 'ROUGE2-F': 0,
                'ROUGEL-P': 0, 'ROUGEL-R': 0, 'ROUGEL-F': 0
            }
            overall_bert_scores = {'BERTScore-P': 0, 'BERTScore-R': 0, 'BERTScore-F1': 0}
            total_paragraphs = 0
            
            for i in range(total_records):
                print(f"\n第{i+1}条记录评估结果:")
                print("-" * 40)
                
                # 在第164行之前添加检查
                if 'A' not in original_data[i]:
                    print(f"跳过第{i+1}条记录：缺少A字段")
                    continue
                    
                original_a = original_data[i]['A']
                reference_a = reference_data[i]['A']
                
                # 确保两个列表长度相同
                min_len = min(len(original_a), len(reference_a))
                
                total_bleu_scores = {'BLEU-1': 0, 'BLEU-2': 0, 'BLEU-3': 0, 'BLEU-4': 0}
                total_rouge_scores = {
                    'ROUGE1-P': 0, 'ROUGE1-R': 0, 'ROUGE1-F': 0,
                    'ROUGE2-P': 0, 'ROUGE2-R': 0, 'ROUGE2-F': 0,
                    'ROUGEL-P': 0, 'ROUGEL-R': 0, 'ROUGEL-F': 0
                }
                
                # 收集所有段落用于BERTScore批量计算
                reference_texts = []
                candidate_texts = []
                
                # 逐段落评估
                for j in range(min_len):
                    reference_text = reference_a[j]
                    candidate_text = original_a[j]
                    
                    # 收集文本用于BERTScore
                    reference_texts.append(reference_text)
                    candidate_texts.append(candidate_text)
                    
                    # 计算BLEU分数
                    bleu_scores = calculate_bleu_score(reference_text, candidate_text)
                    
                    # 计算Rouge分数
                    rouge_scores = calculate_rouge_score(reference_text, candidate_text)
                    
                    print(f"  段落{j+1}:")
                    print(f"    BLEU-1: {bleu_scores['BLEU-1']:.4f}")
                    print(f"    BLEU-2: {bleu_scores['BLEU-2']:.4f}")
                    print(f"    BLEU-3: {bleu_scores['BLEU-3']:.4f}")
                    print(f"    BLEU-4: {bleu_scores['BLEU-4']:.4f}")
                    print(f"    ROUGE-1 F1: {rouge_scores['ROUGE1-F']:.4f}")
                    print(f"    ROUGE-2 F1: {rouge_scores['ROUGE2-F']:.4f}")
                    print(f"    ROUGE-L F1: {rouge_scores['ROUGEL-F']:.4f}")
                    
                    # 累加分数
                    for key in total_bleu_scores:
                        total_bleu_scores[key] += bleu_scores[key]
                    for key in total_rouge_scores:
                        total_rouge_scores[key] += rouge_scores[key]
        
                # 计算BERTScore
                # bert_scores = calculate_bert_score(reference_texts, candidate_texts)
                
                # 只显示前5条记录的详细结果
                if i < 5:
                    '''print(f"\n  BERTScore:")
                    print(f"    Precision: {bert_scores['BERTScore-P']:.4f}")
                    print(f"    Recall: {bert_scores['BERTScore-R']:.4f}")
                    print(f"    F1: {bert_scores['BERTScore-F1']:.4f}")
                    '''
                    # 计算平均分数
                    print(f"\n  平均分数:")
                    for key in total_bleu_scores:
                        avg_score = total_bleu_scores[key] / min_len
                        print(f"    {key}: {avg_score:.4f}")
                    
                    print(f"    ROUGE-1 F1: {total_rouge_scores['ROUGE1-F'] / min_len:.4f}")
                    print(f"    ROUGE-2 F1: {total_rouge_scores['ROUGE2-F'] / min_len:.4f}")
                    print(f"    ROUGE-L F1: {total_rouge_scores['ROUGEL-F'] / min_len:.4f}")
                    # print(f"    BERTScore F1: {bert_scores['BERTScore-F1']:.4f}")
                else:
                    # 对于其他记录，只显示进度
                    if (i + 1) % 10 == 0 or i == total_records - 1:
                        print(f"已处理 {i + 1}/{total_records} 条记录...")
                
                # 累加到总体分数
                for key in overall_bleu_scores:
                    overall_bleu_scores[key] += total_bleu_scores[key] / min_len
                for key in overall_rouge_scores:
                    overall_rouge_scores[key] += total_rouge_scores[key] / min_len
                # for key in overall_bert_scores:
                #    overall_bert_scores[key] += bert_scores[key]
                total_paragraphs += min_len
            
            # 计算并显示总体平均分数
            print("\n" + "=" * 60)
            print("总体评估结果 (所有记录的平均分数):")
            print("-" * 40)
            
            for key in overall_bleu_scores:
                avg_score = overall_bleu_scores[key] / total_records
                print(f"{key}: {avg_score:.4f}")
            
            print(f"ROUGE-1 F1: {overall_rouge_scores['ROUGE1-F'] / total_records:.4f}")
            print(f"ROUGE-2 F1: {overall_rouge_scores['ROUGE2-F'] / total_records:.4f}")
            print(f"ROUGE-L F1: {overall_rouge_scores['ROUGEL-F'] / total_records:.4f}")
            
            # print(f"BERTScore Precision: {overall_bert_scores['BERTScore-P'] / total_records:.4f}")
            # print(f"BERTScore Recall: {overall_bert_scores['BERTScore-R'] / total_records:.4f}")
            # print(f"BERTScore F1: {overall_bert_scores['BERTScore-F1'] / total_records:.4f}")
    
            print(f"\n总共评估了 {total_records} 条记录，{total_paragraphs} 个段落")
            print("=" * 60)
            print("评估完成!")
            
        finally:
            # 恢复标准输出
            sys.stdout = original_stdout
    
    # 输出完成信息到控制台
    print(f"评估结果已保存到: {output_file}")

if __name__ == "__main__":
    main()