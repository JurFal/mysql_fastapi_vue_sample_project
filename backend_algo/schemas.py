from typing import List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class Conversation(BaseModel):
    messages: List[Message]


class ConversationResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ConversationResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str]


class ConversationResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    system_fingerprint: str
    choices: List[ConversationResponseChoice]
    usage: ConversationResponseUsage

class PassageIdea(BaseModel):
    passage_type: str
    passage_tag: List[str]

class PassageResponse(BaseModel):
    passage_type: str
    passage_title: str
    passage: str
    references: List[str]

class PassageForOutput(BaseModel):
    passage_type: str
    passage_title: str
    passage: str
    references: List[str] = []

class LatexOutputRequest(BaseModel):
    passages: List[PassageForOutput]
    template_type: str = "article"  # 默认使用 article 模板
    paper_title: str = "论文标题"
    author_name: str = "作者姓名"

class LatexOutputResponse(BaseModel):
    tex_content: str
    pdf_url: str
