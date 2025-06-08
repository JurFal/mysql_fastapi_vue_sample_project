# 实现‘/writing/’接口功能

## 接口输入输出

post传入json格式的class PassageIdea(BaseModel):
    passage_type: str
    passage_tag: List[str]
传回json格式的class PassageResponse(BaseModel):
    passage_type: str
    passage_title: str
    passage: str
    references: List[str]

## 过程

* 根据passage_tag，在向量数据库"papers_collection"中查找最相关的前n（n=10）条文本（写法参考），保存到{passage_sentences}。
* 编写提示词：'请根据以下十条文本和关键词{passage_tags}，输出一段合理的论文综述\'{passage_type}\'段落和标题：{passage_sentences}'并通过post请求发送到/chat接口
* 输出响应为passage和passage_title，{passage_sentences}为references
