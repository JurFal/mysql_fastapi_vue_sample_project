from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import schemas
import requests
import os
import subprocess
import tempfile
import uuid
from typing import List
import json
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from langchain_community.vectorstores import Chroma
# 假设您已经有了向量数据库的配置



openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="API_KEY_IS_NOT_NEEDED",
    api_base="http://10.176.64.152:11435/v1",
    model_name="bge-m3"
)

app = FastAPI()


URL = 'http://10.176.64.152:11434/v1'
MODEL = 'qwen2.5:7b'


# 在app = FastAPI()之后添加以下代码
app = FastAPI()

# 创建静态文件目录（如果不存在）
os.makedirs("static/output", exist_ok=True)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/chat/stream/")
async def chat_stream(conversation: schemas.Conversation):

    def generator():
        with requests.post(f'{URL}/chat/completions', json={
            'model': MODEL,
            'stream': True,
            'messages': [m.model_dump() for m in conversation.messages],
        }, stream=True, timeout=60) as resp:
            for raw_line in resp.iter_lines():
                line = raw_line.decode('utf-8').strip()
                if line == '':
                    continue
                if line.startswith('data: '):
                    line = line[len('data: '):]
                    if line == '[DONE]':
                        yield raw_line + b'\n'
                        break
                else:
                    yield raw_line + b'\n'
                    break
                # print(json.loads(line))
                yield raw_line + b'\n'
    
    return StreamingResponse(generator())


@app.post("/chat/", response_model=schemas.ConversationResponse)
async def chat(conversation: schemas.Conversation):
    resp = requests.post(f'{URL}/chat/completions', json={
        'model': MODEL,
        'stream': False,
        'messages': [m.model_dump() for m in conversation.messages],
    }, stream=False, timeout=60)
    return resp.json()



# /writing/ 接口
@app.post("/writing/", response_model=schemas.PassageResponse)

async def writing(passage_idea: schemas.PassageIdea):
    
    def generator(conversation):
        with requests.post(f'{URL}/chat/completions', json={
            'model': MODEL,
            'stream': True,
            'messages': [m.model_dump() for m in conversation.messages],
        }, stream=True, timeout=60) as resp:
            for raw_line in resp.iter_lines():
                line = raw_line.decode('utf-8').strip()
                if line == '':
                    continue
                if line.startswith('data: '):
                    line = line[len('data: '):]
                    if line == '[DONE]':
                        yield raw_line + b'\n'
                        break
                else:
                    yield raw_line + b'\n'
                    break
                # print(json.loads(line))
                yield raw_line + b'\n'

    # 1. 从向量数据库中查找相关文本
    embeddings = openai_ef  # 使用适合您项目的嵌入模型

    # 使用 chromadb 客户端连接到向量数据库
    client = chromadb.HttpClient(host='localhost', port=8002)
    collection = client.get_collection("papers_collection")
    # 移除这一行，它可能导致问题
    collection._embedding_function = openai_ef
    
    # 使用 passage_tag 作为查询关键词
    query = " ".join(passage_idea.passage_tag)
    
    # 简化查询，不设置额外参数
    results = collection.query(
        query_texts=[query],
        n_results=10
    )
    
    # 提取文本内容
    passage_sentences = results.get("documents", [[]])[0]
    metadata = results.get("metadatas", [[]])[0]
    references = [f"Reference {i+1}: {meta.get('source', 'Unknown')}" for i, meta in enumerate(metadata)]
    
    # 2. 构建提示词
    prompt = f"请根据关键词：{', '.join(passage_idea.passage_tag)}，以markdown格式写作文献综述中的'{passage_idea.passage_type}'段落。\n\n以下是文献综述参考文本内容："
    for i, sentence in enumerate(passage_sentences):
        prompt += f"文本{i+1}: {sentence}\n"
    
    # 3. 发送到本地 /chat 接口
    conversation = schemas.Conversation(
        messages=[
            schemas.Message(role="system", content="你是一个专业的学术论文写作助手，擅长根据参考文献生成高质量的论文段落。"),
            schemas.Message(role="user", content=prompt)
        ]
    )
    
    # 使用流式接口并收集完整响应
    full_response = ""
    with requests.post(f'{URL}/chat/completions', json={
        'model': MODEL,
        'stream': True,
        'messages': [m.model_dump() for m in conversation.messages],
    }, stream=True, timeout=60) as resp:
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode('utf-8')
            if line.startswith('data: '):
                line = line[len('data: '):]
                if line == '[DONE]':
                    break
                try:
                    data = json.loads(line)
                    content = data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                    if content:
                        full_response += content
                except json.JSONDecodeError:
                    continue
    
    ai_response_initial = full_response
    
    # 3.5 将AI输出的内容再次发送给AI进行改进和格式化
    improvement_prompt = f"""请根据以下内容，按照要求进行改进和格式化：
        1. 使用简体中文markdown格式
        2. 仅生成一个段落
        3. 确保有明确的标题（使用markdown的#格式）
        4. 标题应该简洁明了地概括内容
        5. 内容应该保持学术性和专业性
        6. 内容须符合段落主题：{passage_idea.passage_type}

        原始内容：
        {ai_response_initial}
        """
    
    improvement_conversation = schemas.Conversation(
        messages=[
            schemas.Message(role="system", content="你是一个专业的学术论文写作助手，擅长格式化和改进学术文本。"),
            schemas.Message(role="user", content=improvement_prompt)
        ]
    )
    
    # 获取改进后的响应
    resp = requests.post(f'{URL}/chat/completions', json={
        'model': MODEL,
        'stream': False,
        'messages': [m.model_dump() for m in improvement_conversation.messages],
    }, stream=False, timeout=60)
    
    response_data = resp.json()
    ai_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    # 4. 解析AI响应，提取标题和段落
    # 现在假设AI返回的格式是"# 标题\n\n正文"（markdown格式）
    try:
        lines = ai_response.split("\n")
        # 固定title_line为第一行
        title_line = lines[0] if lines else ""
        # 设置passage_title为除了'# '之外的内容
        passage_title = title_line.replace('#', '').strip() if '#' in title_line else "未命名段落"
        
        # 提取正文内容
        passage_content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        
        return schemas.PassageResponse(
            passage_type=passage_idea.passage_type,
            passage_title=passage_title,
            passage=passage_content,
            references=references
        )
    except Exception as e:
        # 如果解析失败，返回原始响应
        return schemas.PassageResponse(
            passage_type=passage_idea.passage_type,
            passage_title="生成的段落",
            passage=ai_response,
            references=references
        )


@app.post("/writing/output/", response_model=schemas.LatexOutputResponse)
async def generate_latex_output(request: schemas.LatexOutputRequest):
    # 1. 构建提示词，要求模型生成 LaTeX 文档
    passages_text = ""
    for i, passage in enumerate(request.passages):
        passages_text += f"段落{i+1} - {passage.passage_type}:\n"
        passages_text += f"标题: {passage.passage_title}\n"
        passages_text += f"内容: {passage.passage}\n"
        if passage.references:
            passages_text += "参考文献:\n"
            for ref in passage.references:
                passages_text += f"- {ref}\n"
        passages_text += "\n"
    
    prompt = f"""请根据以下内容生成一个完整的 LaTeX 文档:

论文标题: {request.paper_title}
作者: {request.author_name}
模板类型: {request.template_type}

段落内容:
{passages_text}

请生成一个完整的、可编译的 LaTeX 文档，包括以下要求:
1. 使用 {request.template_type} 文档类
2. 包含所有必要的宏包和设置
3. 正确设置中文支持（使用 ctex 宏包）
4. 按照提供的段落顺序组织文档
5. 为每个段落创建适当的章节结构
6. 包含所有参考文献
7. 确保文档可以直接编译成 PDF

只需返回完整的 LaTeX 代码，不需要解释。
"""
    
    # 2. 发送到本地 /chat 接口
    conversation = schemas.Conversation(
        messages=[
            schemas.Message(role="system", content="你是一个专业的 LaTeX 文档生成助手，擅长将文本内容转换为格式良好的 LaTeX 文档。"),
            schemas.Message(role="user", content=prompt)
        ]
    )
    
    resp = requests.post(f'{URL}/chat/completions', json={
        'model': MODEL,
        'stream': False,
        'messages': [m.model_dump() for m in conversation.messages],
    }, stream=False, timeout=120)
    
    response_data = resp.json()
    latex_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    # 3. 提取 LaTeX 代码（如果模型返回的内容包含代码块标记）
    if "```latex" in latex_content and "```" in latex_content.split("```latex", 1)[1]:
        latex_content = latex_content.split("```latex", 1)[1].split("```", 1)[0].strip()
    elif "```" in latex_content and "```" in latex_content.split("```", 1)[1]:
        latex_content = latex_content.split("```", 1)[1].split("```", 1)[0].strip()
    
    # 4. 生成唯一的文件名
    file_id = str(uuid.uuid4())
    tex_filename = f"{file_id}.tex"
    pdf_filename = f"{file_id}.pdf"
    
    # 确保输出目录存在
    os.makedirs("static/output", exist_ok=True)
    
    tex_path = os.path.join("static/output", tex_filename)
    pdf_path = os.path.join("static/output", pdf_filename)
    
    # 5. 保存 LaTeX 文件
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_content)
    
    # 6. 编译 LaTeX 文件生成 PDF
    try:
        # 创建临时目录用于编译
        with tempfile.TemporaryDirectory() as tmpdir:
            # 复制 tex 文件到临时目录
            tmp_tex_path = os.path.join(tmpdir, tex_filename)
            with open(tmp_tex_path, "w", encoding="utf-8") as f:
                f.write(latex_content)
            
            # 在临时目录中编译
            subprocess.run(
                ["xelatex", "-interaction=nonstopmode", tex_filename],
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            
            # 如果生成了 PDF，复制到目标位置
            tmp_pdf_path = os.path.join(tmpdir, pdf_filename)
            if os.path.exists(tmp_pdf_path):
                with open(tmp_pdf_path, "rb") as src, open(pdf_path, "wb") as dst:
                    dst.write(src.read())
    except Exception as e:
        # 如果编译失败，记录错误但继续返回 tex 内容
        print(f"PDF 编译失败: {str(e)}")
    
    # 7. 返回 tex 内容和 PDF 文件的 URL
    # 修改返回的URL路径，确保前端可以正确访问
    pdf_url = f"/api/static/output/{pdf_filename}" if os.path.exists(pdf_path) else ""
    
    return schemas.LatexOutputResponse(
        tex_content=latex_content,
        pdf_url=pdf_url
    )

