# writing.vue

## 功能

点击“新建段落”按钮后，出现“段落n”“段落类型”输入框和“添加标签”按钮，“删除段落”按钮及“生成综述段落”按钮。“添加标签“按钮点击后出现“标签x”输入框（可删除该框）。“生成综述段落”按钮将类型和标签发送POST请求对接算法后端/api/writing/接口（输入：class PassageIdea(BaseModel):
    passage_type: str
    passage_tag: List[str]，输出：class PassageResponse(BaseModel):
    passage_type: str
    passage_title: str
    passage: str
    references: List[str]），生成完毕后，显示可以关闭的带段落标题的预览
    