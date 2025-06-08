# 测试数据文档

## 问答数据集格式

问答数据 questions.json：

[

{

"Q": [["段落类型", ["段落标签1", "段落标签2", ...]], ...],

"A": ["段落内容", ...],

"R": [[int, 生成这章需要参考的论文编号列表], ...]

}, ...

]

论文库 papers.json：

[

{

"id": int 论文编号,

"path": "论文相对路径 papers/xxx.pdf",

}, ...

]

论文文件夹，名为papers：

xxx.pdf

yyy.pdf

...

指标：

对于论文（字段R）：

Precision@K, Recall@K, F1@K, ...

对于模型生成的回答：

BERTScore, BLEU, Rouge等翻译指标

语言：中文或中英双语

注意：生成的内容需要有引用
