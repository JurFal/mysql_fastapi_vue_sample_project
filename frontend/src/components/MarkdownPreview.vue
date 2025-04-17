<template>
  <div v-if="!isEditing" class="markdown-body" v-html="parsedMarkdown" @click="startEditing"></div>
  <div v-else class="markdown-editor">
    <el-input
      type="textarea"
      v-model="editableContent"
      :rows="10"
      resize="both"
      placeholder="请输入Markdown内容"
    ></el-input>
    <div class="editor-actions">
      <el-button type="primary" @click="saveEdit">保存</el-button>
      <el-button @click="cancelEdit">取消</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { marked } from 'marked' // 修改导入方式
import DOMPurify from 'dompurify'
import { ElInput, ElButton } from 'element-plus'

const props = defineProps<{
  markdownContent: string
}>()

const emit = defineEmits(['update:markdownContent'])

const parsedMarkdown = ref('')
const isEditing = ref(false)
const editableContent = ref('')

// 解析并清理 Markdown 内容
const parseMarkdown = async () => {
  try {
    const html = await marked.parse(props.markdownContent) // 使用 await 等待解析结果
    parsedMarkdown.value = DOMPurify.sanitize(html)
  } catch (error) {
    console.error('Markdown 解析失败:', error)
    parsedMarkdown.value = '' // 如果解析失败，清空内容
  }
}

// 开始编辑
const startEditing = () => {
  editableContent.value = props.markdownContent
  isEditing.value = true
}

// 保存编辑
const saveEdit = () => {
  emit('update:markdownContent', editableContent.value)
  isEditing.value = false
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
}

// 监听 props 变化并重新解析
watch(() => props.markdownContent, () => {
  parseMarkdown()
})

// 初始化时解析一次
parseMarkdown()
</script>

<style scoped>
.markdown-body {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 980px;
  margin: 0 auto;
  padding: 45px;
  cursor: pointer; /* 添加指针样式提示可点击 */
}

.markdown-body:hover {
  background-color: #f8f9fa;
}

.markdown-editor {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 980px;
  margin: 0 auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.editor-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>