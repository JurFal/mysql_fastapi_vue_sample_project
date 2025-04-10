


from fastapi import APIRouter, Response, Query
import requests

router = APIRouter()

@router.get("/image")
def proxy_image(url: str = Query(...)):
    try:
        # 确保使用正确的代理配置
        proxies = {
            "http": "http://localhost:7897",
            "https": "http://localhost:7897"
        }
        
        # 添加超时设置，避免请求卡住
        response = requests.get(url, proxies=proxies, timeout=10)
        
        # 检查响应状态
        response.raise_for_status()
        
        return Response(
            content=response.content,
            media_type=response.headers.get("content-type", "image/jpeg"),
            headers={"Cache-Control": "max-age=3600"}  # 添加缓存控制
        )
    except Exception as e:
        print(f"代理请求失败: {str(e)}")
        return Response(status_code=404)