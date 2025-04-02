<template>
    <div class="markdown-body" v-html="parsedMarkdown"></div>
  </template>
  
  <script setup lang="ts">
  import { ref, watch } from 'vue'
  import { marked } from 'marked' // 修改导入方式
  import DOMPurify from 'dompurify'
  
  const props = defineProps<{
    markdownContent: string
  }>()
  
  const parsedMarkdown = ref('')
  
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
  }
  </style>