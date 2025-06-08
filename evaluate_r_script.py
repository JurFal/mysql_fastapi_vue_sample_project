#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评估脚本：计算Precision@K, Recall@K, F1@K指标
比较questions_q_a_r.json和questions_q_a_r_ref.json中R字段的相似性
"""

import json
import os
from typing import List, Dict, Tuple

def load_json_data(file_path: str) -> List[Dict]:
    """加载JSON数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_precision_at_k(predicted: List[str], actual: List[str], k: int) -> float:
    """计算Precision@K"""
    if k <= 0 or len(predicted) == 0:
        return 0.0
    
    # 取前k个预测结果
    predicted_k = predicted[:k]
    
    # 计算交集
    intersection = set(predicted_k) & set(actual)
    
    return len(intersection) / len(predicted_k)

def calculate_recall_at_k(predicted: List[str], actual: List[str], k: int) -> float:
    """计算Recall@K"""
    if k <= 0 or len(actual) == 0:
        return 0.0
    
    # 取前k个预测结果
    predicted_k = predicted[:k]
    
    # 计算交集
    intersection = set(predicted_k) & set(actual)
    
    return len(intersection) / len(actual)

def calculate_f1_at_k(predicted: List[str], actual: List[str], k: int) -> float:
    """计算F1@K"""
    precision = calculate_precision_at_k(predicted, actual, k)
    recall = calculate_recall_at_k(predicted, actual, k)
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)

def calculate_inclusion_rate_at_k(predicted: List[str], actual: List[str], k: int) -> float:
    """计算Top-K包含率（InclusionRate@K）
    
    如果预测的前K个结果完全包含在真实结果中，返回1.0，否则返回0.0
    """
    if k <= 0 or len(predicted) == 0:
        return 0.0
    
    # 取前k个预测结果
    predicted_k = predicted[:k]
    
    # 检查预测结果是否完全包含在真实结果中
    predicted_set = set(predicted_k)
    actual_set = set(actual)
    
    # 如果预测集合是真实集合的子集，返回1.0，否则返回0.0
    return 1.0 if predicted_set.issubset(actual_set) else 0.0

def evaluate_r_fields(data_file: str, ref_file: str) -> Dict:
    """评估R字段的相似性"""
    # 加载数据
    data = load_json_data(data_file)
    ref_data = load_json_data(ref_file)
    
    # 确保两个数据集长度一致
    min_len = min(len(data), len(ref_data))
    
    results = {
        'total_samples': min_len,
        'k_values': [1, 3, 5, 8],  # 不同的K值
        'metrics': {}
    }
    
    # 对每个K值计算指标
    for k in results['k_values']:
        precision_scores = []
        recall_scores = []
        f1_scores = []
        inclusion_scores = []
        
        for i in range(min_len):
            predicted_r = data[i].get('R', [])
            actual_r = ref_data[i].get('R', [])
            
            precision = calculate_precision_at_k(predicted_r, actual_r, k)
            recall = calculate_recall_at_k(predicted_r, actual_r, k)
            f1 = calculate_f1_at_k(predicted_r, actual_r, k)
            inclusion = calculate_inclusion_rate_at_k(predicted_r, actual_r, k)
            
            precision_scores.append(precision)
            recall_scores.append(recall)
            f1_scores.append(f1)
            inclusion_scores.append(inclusion)
        
        # 计算平均值
        avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0
        avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0
        avg_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0
        avg_inclusion = sum(inclusion_scores) / len(inclusion_scores) if inclusion_scores else 0
        
        results['metrics'][f'K={k}'] = {
            'Precision@K': avg_precision,
            'Recall@K': avg_recall,
            'F1@K': avg_f1,
            'InclusionRate@K': avg_inclusion,
            'individual_scores': {
                'precision': precision_scores,
                'recall': recall_scores,
                'f1': f1_scores,
                'inclusion': inclusion_scores
            }
        }
    
    return results

def save_results_to_file(results: Dict, output_file: str):
    """将结果保存到文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("R字段评估结果 - Precision@K, Recall@K, F1@K\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"总样本数: {results['total_samples']}\n\n")
        
        # 写入汇总表格
        f.write("汇总结果:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'K值':<8} {'Precision@K':<15} {'Recall@K':<15} {'F1@K':<15} {'InclusionRate@K':<15}\n")
        f.write("-" * 80 + "\n")
        
        for k_val in results['k_values']:
            metrics = results['metrics'][f'K={k_val}']
            f.write(f"{k_val:<8} {metrics['Precision@K']:<15.4f} {metrics['Recall@K']:<15.4f} {metrics['F1@K']:<15.4f} {metrics['InclusionRate@K']:<15.4f}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("详细结果:\n")
        f.write("=" * 80 + "\n\n")
        
        # 写入详细结果
        for k_val in results['k_values']:
            f.write(f"K = {k_val}:\n")
            f.write("-" * 40 + "\n")
            
            metrics = results['metrics'][f'K={k_val}']
            f.write(f"平均 Precision@{k_val}: {metrics['Precision@K']:.4f}\n")
            f.write(f"平均 Recall@{k_val}: {metrics['Recall@K']:.4f}\n")
            f.write(f"平均 F1@{k_val}: {metrics['F1@K']:.4f}\n")
            f.write(f"平均 InclusionRate@{k_val}: {metrics['InclusionRate@K']:.4f}\n")
            
            # 统计信息
            precision_scores = metrics['individual_scores']['precision']
            recall_scores = metrics['individual_scores']['recall']
            f1_scores = metrics['individual_scores']['f1']
            inclusion_scores = metrics['individual_scores']['inclusion']
            
            f.write(f"\n统计信息:\n")
            f.write(f"  Precision@{k_val} - 最大值: {max(precision_scores):.4f}, 最小值: {min(precision_scores):.4f}\n")
            f.write(f"  Recall@{k_val} - 最大值: {max(recall_scores):.4f}, 最小值: {min(recall_scores):.4f}\n")
            f.write(f"  F1@{k_val} - 最大值: {max(f1_scores):.4f}, 最小值: {min(f1_scores):.4f}\n")
            f.write(f"  InclusionRate@{k_val} - 最大值: {max(inclusion_scores):.4f}, 最小值: {min(inclusion_scores):.4f}\n")
            
            # 完美匹配统计
            perfect_precision = sum(1 for score in precision_scores if score == 1.0)
            perfect_recall = sum(1 for score in recall_scores if score == 1.0)
            perfect_f1 = sum(1 for score in f1_scores if score == 1.0)
            perfect_inclusion = sum(1 for score in inclusion_scores if score == 1.0)
            
            f.write(f"\n完美匹配样本数:\n")
            f.write(f"  Precision@{k_val} = 1.0: {perfect_precision} 个样本\n")
            f.write(f"  Recall@{k_val} = 1.0: {perfect_recall} 个样本\n")
            f.write(f"  F1@{k_val} = 1.0: {perfect_f1} 个样本\n")
            f.write(f"  InclusionRate@{k_val} = 1.0: {perfect_inclusion} 个样本\n")
            
            f.write("\n" + "="*40 + "\n\n")
        
        # 添加一些分析
        f.write("分析总结:\n")
        f.write("-" * 40 + "\n")
        
        best_k_precision = max(results['k_values'], key=lambda k: results['metrics'][f'K={k}']['Precision@K'])
        best_k_recall = max(results['k_values'], key=lambda k: results['metrics'][f'K={k}']['Recall@K'])
        best_k_f1 = max(results['k_values'], key=lambda k: results['metrics'][f'K={k}']['F1@K'])
        
        f.write(f"最佳 Precision@K: K={best_k_precision} ({results['metrics'][f'K={best_k_precision}']['Precision@K']:.4f})\n")
        f.write(f"最佳 Recall@K: K={best_k_recall} ({results['metrics'][f'K={best_k_recall}']['Recall@K']:.4f})\n")
        f.write(f"最佳 F1@K: K={best_k_f1} ({results['metrics'][f'K={best_k_f1}']['F1@K']:.4f})\n")

def main():
    """主函数"""
    # 文件路径
    data_file = "/Users/julius/julProg/paper_writing_helper/datas/questions_q_a_r_myapi3.json"
    ref_file = "/Users/julius/julProg/paper_writing_helper/datas/questions_q_a_r_ref.json"
    output_file = "/Users/julius/julProg/paper_writing_helper/evaluate_r_result_myapi3.txt"
    
    # 检查文件是否存在
    if not os.path.exists(data_file):
        print(f"错误: 找不到文件 {data_file}")
        return
    
    if not os.path.exists(ref_file):
        print(f"错误: 找不到文件 {ref_file}")
        return
    
    print("开始评估R字段...")
    
    # 执行评估
    results = evaluate_r_fields(data_file, ref_file)
    
    # 保存结果
    save_results_to_file(results, output_file)
    
    print(f"评估完成！结果已保存到: {output_file}")
    
    # 打印简要结果
    print("\n简要结果:")
    print("-" * 50)
    for k_val in results['k_values']:
        metrics = results['metrics'][f'K={k_val}']
        print(f"K={k_val}: P@K={metrics['Precision@K']:.4f}, R@K={metrics['Recall@K']:.4f}, F1@K={metrics['F1@K']:.4f}")

if __name__ == "__main__":
    main()