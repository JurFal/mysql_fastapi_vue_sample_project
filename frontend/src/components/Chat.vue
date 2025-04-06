<script setup lang="ts">
import {reactive, ref, nextTick, watch} from 'vue'
import type {FormInstance, FormRules} from 'element-plus'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {ChatWithLLM} from "@/request/api";
const router = useRouter()

const ruleFormRef = ref<FormInstance>()

const chatForm = reactive({
  prompt: '',
  response: '',
})

// 定义消息类型接口
interface ChatMessage {
  role: string;
  content: string;
  isTyping: boolean;
  displayedContent: string;
}

// 存储对话历史，指定类型为 ChatMessage 数组
const chatHistory = ref<ChatMessage[]>([]);
const isTyping = ref(false);

// 改进的打字效果函数
const startTypeEffect = async (messageIndex: number) => {
  const message = chatHistory.value[messageIndex];
  if (!message || message.role !== 'assistant') return;
  
  isTyping.value = true;
  message.isTyping = true;
  message.displayedContent = '';
  
  const fullContent = message.content;
  let currentIndex = 0;
  
  const typeNextChar = () => {
    if (currentIndex < fullContent.length) {
      // 添加下一个字符
      message.displayedContent += fullContent[currentIndex];
      currentIndex++;
      
      // 继续打字
      setTimeout(typeNextChar, 30);
    } else {
      // 打字完成
      message.isTyping = false;
      isTyping.value = false;
    }
  };
  
  // 开始打字
  typeNextChar();
};

const submitForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate(async (valid) => {
    if (valid) {
      try {
        if (isTyping.value) return; // 如果正在打字，不处理新的请求
        
        // 保存当前用户输入到历史记录
        const userMessage: ChatMessage = {
          role: "user",
          content: chatForm.prompt,
          isTyping: false,
          displayedContent: chatForm.prompt
        };
        
        // 构建完整的消息历史
        const messages = [...chatHistory.value, userMessage].map(({role, content}) => ({role, content}));
        
        // 将用户消息添加到历史记录
        chatHistory.value.push(userMessage);
        
        // 清空输入框，准备下一轮对话
        chatForm.prompt = '';
        
        let res = await ChatWithLLM({
          messages: messages
        });
        
        // 获取AI回复
        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: res.choices[0].message.content,
          isTyping: true,
          displayedContent: ''
        };
        
        // 将AI回复添加到历史记录
        chatHistory.value.push(assistantMessage);
        
        // 更新响应显示
        chatForm.response = res.choices[0].message.content;
        
        // 滚动到底部
        await nextTick();
        const chatHistoryEl = document.querySelector('.chat-history');
        if (chatHistoryEl) {
          chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
        }
        
        // 开始打字效果
        startTypeEffect(chatHistory.value.length - 1);
      } catch (e) {
        console.log(e)
        ElMessage.error('请求失败，请稍后再试');
      }
    } else {
      return false
    }
  })
}
</script>

<template>
  <el-form
      ref="ruleFormRef"
      :model="chatForm"
      style="max-width: 600px"
      label-width="auto"
      class="demo-ruleForm"
  >
    <!-- 添加对话历史显示区域 -->
    <div class="chat-history" v-if="chatHistory.length > 0">
      <div v-for="(message, index) in chatHistory" :key="index" 
           :class="['message', message.role === 'user' ? 'user-message' : 'assistant-message']">
        <div class="message-header">{{ message.role === 'user' ? '我' : 'AI助手' }}</div>
        <div class="message-content">
          {{ message.displayedContent }}
          <span v-if="message.isTyping" class="typing-cursor">|</span>
        </div>
      </div>
    </div>

    <el-form-item label="提问" prop="prompt">
      <el-input v-model="chatForm.prompt" type="text" autocomplete="off"/>
    </el-form-item>

    <el-form-item>
      <el-button type="success" @click="submitForm(ruleFormRef)" :disabled="isTyping">
        {{ isTyping ? '正在回复...' : '发送' }}
      </el-button>
    </el-form-item>

  </el-form>
</template>

<style scoped>
.chat-history {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 20px;
}

.message {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 8px;
}

.user-message {
  background-color: #e6f7ff;
  margin-left: 20px;
}

.assistant-message {
  background-color: #f6ffed;
  margin-right: 20px;
}

.message-header {
  font-weight: bold;
  margin-bottom: 5px;
}

.message-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.typing-cursor {
  display: inline-block;
  animation: blink 0.7s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>