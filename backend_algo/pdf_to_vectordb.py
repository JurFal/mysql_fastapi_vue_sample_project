import os
import uuid
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

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

def extract_text_from_pdf(pdf_path):
    """从PDF文件中提取文本"""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        try:
            page_text = page.extract_text()
            # 清理文本中的无效Unicode字符
            page_text = page_text.encode('utf-8', errors='ignore').decode('utf-8')
            text += page_text + "\n"
        except Exception as e:
            print(f"处理页面时出错: {e}")
            continue
    return text

def add_pdf_to_vectordb(pdf_path):
    """将PDF文件添加到向量数据库"""
    # 提取文件名作为元数据
    filename = os.path.basename(pdf_path)
    
    try:
        # 提取文本
        text = extract_text_from_pdf(pdf_path)
        
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

def split_text(text, chunk_size=1000, chunk_overlap=200):
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