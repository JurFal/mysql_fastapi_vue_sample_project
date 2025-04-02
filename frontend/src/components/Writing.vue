<script setup lang="ts">
import {reactive, ref} from 'vue'
import type {FormInstance, FormRules} from 'element-plus'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {ChatWithLLM} from "@/request/api";
import MarkdownPreview from '@/components/MarkdownPreview.vue'
const router = useRouter()

const ruleFormRef = ref<FormInstance>()

const chatForm = reactive({
  prompt: '',
  response: '',
})



const submitForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate(async (valid) => {
    if (valid) {
      try {
        let res =  await ChatWithLLM({
          messages: [
            {
              role: "user",
              content: "以下是论文关键词：" + chatForm.prompt + "。生成一篇相关的论文摘要和段落大纲"
            }
          ]
        })
        chatForm.response = res.choices[0].message.content
      } catch (e) {
        console.log(e)
      }
    } else {
      return false
    }
  })
}

// 处理按下 Enter 键发送消息
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault() // 阻止默认的换行行为
    submitForm(ruleFormRef.value)
  }
}

// 处理文件上传
// 删除原来的 handleFileUpload 函数，添加下载 Markdown 文件的函数
const downloadMarkdown = () => {
  if (!chatForm.response.trim()) {
    ElMessage.warning('暂无内容可下载')
    return
  }
  
  // 创建 Blob 对象
  const blob = new Blob([chatForm.response], { type: 'text/markdown' })
  
  // 创建下载链接
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '论文大纲.md' // 设置下载文件名
  
  // 触发下载
  document.body.appendChild(a)
  a.click()
  
  // 清理
  URL.revokeObjectURL(url)
  document.body.removeChild(a)
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

    <el-form-item label="关键词" prop="prompt">
      <el-input 
        v-model="chatForm.prompt" 
        type="textarea" 
        :autosize="{ minRows: 2, maxRows: 10 }"
        autocomplete="off"
        @keydown="handleKeyDown"
      />
    </el-form-item>

    <!-- 条件渲染 MarkdownPreview -->
    <el-form-item label="回答" prop="response">
      <div v-if="chatForm.response.trim()">
        <MarkdownPreview :markdownContent="chatForm.response" />
      </div>
      <div v-else>
        <span>暂无回答</span>
      </div>
    </el-form-item>
    <!-- 将上传按钮改为下载按钮 -->
    <el-form-item label="下载回答">
      <el-button type="primary" @click="downloadMarkdown">
        下载为 Markdown 文件
      </el-button>
    </el-form-item>

    <el-form-item>
      <el-button type="success" @click="submitForm(ruleFormRef)"
      >发送
      </el-button
      >
    </el-form-item>

  </el-form>
</template>

