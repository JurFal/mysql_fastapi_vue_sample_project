<script setup lang="ts">
import {reactive, ref, nextTick, watch, onMounted, onUnmounted} from 'vue'
import type {FormInstance, FormRules} from 'element-plus'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {ChatWithLLM, GetUserInfoByUserName} from "@/request/api";
import {useUserstore} from '@/store/user'

const router = useRouter()
const userStore = useUserstore()
const ruleFormRef = ref<FormInstance>()

// 添加用户头像
const userAvatar = ref('');

// 获取用户头像
const fetchUserAvatar = async () => {
  try {
    if (userStore.userName) {
      const userInfo = await GetUserInfoByUserName({ userName: userStore.userName });
      userAvatar.value = userInfo.avatar || '';
    }
  } catch (e) {
    console.error('获取用户头像失败:', e);
  }
};

// 在组件挂载时获取用户头像
onMounted(() => {
  loadChatHistory();
  fetchUserAvatar();
});

// AI 头像 URL
const aiAvatar = 'https://img.alicdn.com/imgextra/i4/O1CN01EfJVFQ1uZPd7W4W6i_!!6000000006051-2-tps-112-112.png';

const chatForm = reactive({
  prompt: '',
  response: '',
})

// 定义消息类型接口
interface ChatMessage {
  role: string;
  content: string;
}

// 存储对话历史，指定类型为 ChatMessage 数组
const chatHistory = ref<ChatMessage[]>([]);
const isTyping = ref(false);

// 从 localStorage 加载对话历史
const loadChatHistory = () => {
  const username = userStore.userName;
  if (!username) return;
  
  const savedHistory = localStorage.getItem(`chat_history_${username}`);
  if (savedHistory) {
    try {
      const parsedHistory = JSON.parse(savedHistory);
      chatHistory.value = parsedHistory;
    } catch (e) {
      console.error('加载对话历史失败:', e);
    }
  }
};

// 保存对话历史到 localStorage
const saveChatHistory = () => {
  const username = userStore.userName;
  if (!username) return;
  
  try {
    // 只保存必要的字段
    const historyToSave = chatHistory.value.map(msg => ({
      role: msg.role,
      content: msg.content
    }));
    localStorage.setItem(`chat_history_${username}`, JSON.stringify(historyToSave));
  } catch (e) {
    console.error('保存对话历史失败:', e);
  }
};

// 清除对话历史
const clearChatHistory = () => {
  chatHistory.value = [];
  saveChatHistory();
  ElMessage.success('对话历史已清除');
};

// 监听对话历史变化，自动保存
watch(chatHistory, () => {
  if (!isTyping.value) {
    saveChatHistory();
  }
}, { deep: true });

// 组件挂载时加载对话历史
onMounted(() => {
  loadChatHistory();
});

// 添加一个新的状态变量，表示是否所有响应都已完成
const responseComplete = ref(true);

// 修改提交表单函数
const submitForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate(async (valid) => {
    if (valid) {
      try {
        // 检查是否正在接收响应，如果是则不处理新请求
        if (isTyping.value || !responseComplete.value) {
          ElMessage.warning('AI 正在回复中，请稍候...');
          return;
        }
        
        // 检查输入是否为空
        if (!chatForm.prompt.trim()) {
          ElMessage.warning('请输入问题内容');
          return;
        }
        
        // 设置响应未完成状态
        responseComplete.value = false;
        
        // 保存当前用户输入到历史记录
        const userMessage: ChatMessage = {
          role: "user",
          content: chatForm.prompt
        };
        
        // 构建完整的消息历史
        const messages = [...chatHistory.value, userMessage].map(({role, content}) => ({role, content}));
        
        // 将用户消息添加到历史记录
        chatHistory.value.push(userMessage);
        
        // 清空输入框，准备下一轮对话
        chatForm.prompt = '';
        
        // 创建一个空的助手消息，用于流式显示
        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: ""
        };
        
        // 将AI回复添加到历史记录
        chatHistory.value.push(assistantMessage);
        
        // 滚动到底部
        await nextTick();
        scrollToBottom();
        
        // 设置正在输入状态
        isTyping.value = true;
        
        // 使用fetch API直接处理流式响应
        const response = await fetch('/api/chat/stream/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${userStore.token}`
          },
          body: JSON.stringify({ messages })
        });
        
        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('无法读取响应流');
        }
        
        let decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          
          // 处理缓冲区中的每一行
          let lines = buffer.split('\n');
          buffer = lines.pop() || ''; // 最后一行可能不完整，保留到下一次处理
          
          for (const line of lines) {
            if (line.trim() === '') continue;
            
            try {
              if (line.startsWith('data: ')) {
                const data = line.substring(6);
                if (data === '[DONE]') {
                  // 流结束
                  isTyping.value = false;
                  responseComplete.value = true;
                  saveChatHistory();
                  break;
                }
                
                try {
                  const json = JSON.parse(data);
                  if (json.choices && json.choices[0]) {
                    let content = '';
                    
                    // 处理不同的响应格式
                    if (json.choices[0].delta && json.choices[0].delta.content) {
                      content = json.choices[0].delta.content;
                    } else if (json.choices[0].message && json.choices[0].message.content) {
                      content = json.choices[0].message.content;
                    }
                    
                    if (content) {
                      // 直接更新内容
                      assistantMessage.content += content;
                      // 滚动到底部以显示最新内容
                      scrollToBottom();
                    }
                  }
                } catch (parseError) {
                  console.error('解析JSON失败:', parseError, data);
                }
              }
            } catch (e) {
              console.error('处理流数据失败:', e, line);
            }
          }
        }
        
      } catch (e) {
        console.log(e)
        isTyping.value = false;
        responseComplete.value = true; // 确保出错时也重置状态
        ElMessage.error('请求失败，请稍后再试');
      }
    } else {
      return false
    }
  })
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    const chatHistoryEl = document.querySelector('.chat-history');
    if (chatHistoryEl) {
      chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
    }
  });
};
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
    <div class="chat-history-header" v-if="chatHistory.length > 0">
      <h3>对话历史</h3>
      <el-button type="danger" size="small" @click="clearChatHistory">清除历史</el-button>
    </div>
    
    <div class="chat-history" v-if="chatHistory.length > 0">
      <div v-for="(message, index) in chatHistory" :key="index" 
           :class="['message', message.role === 'user' ? 'user-message' : 'assistant-message']">
        <div class="message-avatar">
          <img :src="message.role === 'user' ? userAvatar : aiAvatar" 
               :alt="message.role === 'user' ? '用户头像' : 'AI头像'" 
               class="avatar-img" />
        </div>
        <div class="message-bubble">
          <div class="message-header">{{ message.role === 'user' ? '我' : 'AI助手' }}</div>
          <div class="message-content">
            {{ message.content }}
            <span v-if="isTyping && index === chatHistory.length - 1 && message.role === 'assistant'" class="typing-cursor">|</span>
          </div>
        </div>
      </div>
    </div>

    <el-form-item label="提问" prop="prompt">
      <el-input 
        v-model="chatForm.prompt" 
        type="text" 
        autocomplete="off"
        :disabled="isTyping || !responseComplete"
        placeholder="请输入您的问题..."
      />
    </el-form-item>

    <el-form-item>
      <el-button 
        type="success" 
        @click="submitForm(ruleFormRef)" 
        :disabled="isTyping || !responseComplete || !chatForm.prompt.trim()"
      >
        {{ isTyping ? '正在回复...' : (responseComplete ? '发送' : '处理中...') }}
      </el-button>
    </el-form-item>

  </el-form>
</template>

<style scoped>
.chat-history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.chat-history {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 20px;
}

.message {
  display: flex;
  margin-bottom: 15px;
  align-items: flex-start;
}

.message-avatar {
  flex-shrink: 0;
  margin-right: 10px;
}

.avatar-img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  object-position: center;
}

.message-bubble {
  flex-grow: 1;
  padding: 10px;
  border-radius: 8px;
}

.user-message .message-bubble {
  background-color: #e6f7ff;
  margin-left: 0;
}

.assistant-message .message-bubble {
  background-color: #f6ffed;
  margin-right: 0;
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