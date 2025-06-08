import os
import uuid
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz  # 新增
import requests  # 新增
import base64  # 新增

# 配置OpenAI embedding函数
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="API_KEY_IS_NOT_NEEDED",
    api_base="http://10.176.64.152:11435/v1",
    model_name="bge-m3"
)

# 连接到向量数据库
client = chromadb.HttpClient(host='localhost', port=8002)

# 获取或创建collection
collection_name = "papers_collection"
try:
    collection = client.get_collection(name=collection_name, embedding_function=openai_ef)
    print(f"使用已存在的collection: {collection_name}")
except:
    collection = client.create_collection(name=collection_name, embedding_function=openai_ef)
    print(f"创建新的collection: {collection_name}")

def extract_text_and_formula_from_pdf(pdf_path):
    """从PDF文件中提取文本和公式（公式图片用Mathpix识别为LaTeX）"""
    doc = fitz.open(pdf_path)
    content_blocks = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")
        for b in blocks:
            block_type = b[6] if len(b) > 6 else 0
            if block_type == 0:  # 文本块
                text = b[4].strip()
                if text:
                    content_blocks.append(text)
            elif block_type == 1:  # 图片块，可能为公式
                img = page.get_pixmap(clip=fitz.Rect(b[:4]))
                img_bytes = img.tobytes("png")
                latex = mathpix_ocr_formula(img_bytes)
                if latex:
                    content_blocks.append(f"[公式]{latex}")
    return "\n".join(content_blocks)

# Mathpix OCR API调用
MATHPIX_APP_ID = os.getenv("MATHPIX_APP_ID", "your_app_id")
MATHPIX_APP_KEY = os.getenv("MATHPIX_APP_KEY", "your_app_key")
def mathpix_ocr_formula(img_bytes):
    url = "https://api.mathpix.com/v3/latex"
    img_b64 = base64.b64encode(img_bytes).decode()
    headers = {
        "app_id": MATHPIX_APP_ID,
        "app_key": MATHPIX_APP_KEY,
        "Content-type": "application/json"
    }
    data = {
        "src": f"data:image/png;base64,{img_b64}",
        "ocr": ["math", "text"],
        "formats": ["latex_styled"]
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            return result.get("latex_styled")
    except Exception as e:
        print(f"Mathpix识别出错: {e}")
    return None

def add_pdf_to_vectordb(pdf_path):
    """将PDF文件添加到向量数据库"""
    # 提取文件名作为元数据
    filename = os.path.basename(pdf_path)
    
    try:
        # 提取文本
        text = extract_text_and_formula_from_pdf(pdf_path)
        
        # 分割文本
        chunks = split_text(text)
        
        # 准备数据
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": filename, "chunk": i} for i in range(len(chunks))]
        
        # 添加到向量数据库
        collection.add(
            ids=ids,
            documents=chunks,
            metadatas=metadatas
        )
        
        print(f"已将 {filename} 添加到向量数据库，共 {len(chunks)} 个文本块")
    except Exception as e:
        print(f"处理文件 {filename} 时出错: {e}")

def split_text(text, chunk_size=200, chunk_overlap=50):
    """将文本分割成适当大小的块"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    return chunks

def process_pdf_directory(directory_path):
    """处理目录中的所有PDF文件"""
    for filename in os.listdir(directory_path):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(directory_path, filename)
            print(f"处理文件: {filename}")
            add_pdf_to_vectordb(pdf_path)

if __name__ == "__main__":
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 指定PDF文件所在目录（在backend_algo目录下创建papers文件夹）
    pdf_directory = os.path.join(current_dir, "papers")
    
    # 确保目录存在
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)
        print(f"创建目录: {pdf_directory}")
    
    # 处理目录中的所有PDF文件
    process_pdf_directory(pdf_directory)
    
    # 测试查询
    query_result = collection.query(
        query_texts=["这篇论文的主要贡献是什么?"],
        n_results=3
    )
    
    print("\n查询结果示例:")
    for i, doc in enumerate(query_result['documents'][0]):
        print(f"结果 {i+1}:")
        print(f"文档: {doc[:100]}...")
        print(f"来源: {query_result['metadatas'][0][i]['source']}")
        print(f"块号: {query_result['metadatas'][0][i]['chunk']}")
        print("-" * 50)