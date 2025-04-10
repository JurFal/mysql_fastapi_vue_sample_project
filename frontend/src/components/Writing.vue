<script setup lang="ts">
import { ref as vueRef, reactive, nextTick, onMounted, watch } from 'vue'
import type {FormInstance, FormRules} from 'element-plus'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {ChatWithLLM} from "@/request/api";
import PdfPreview from '@/components/PdfPreview.vue'
import MarkdownPreview from '@/components/MarkdownPreview.vue'
import axios from 'axios'

const router = useRouter()

const ruleFormRef = vueRef<FormInstance>()

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
interface Passage {
  passage_type: string
  passage_tag: string[]
  inputVisible: boolean
  inputValue: string
  showPreview: boolean
  passage_title: string
  passage: string
  references: string[]
  loading: boolean
  isGenerated: boolean
  showReferences: boolean // 新增字段，控制参考文献的折叠/展开状态
}

const passages = vueRef<Passage[]>([])
const tagInputRef = vueRef<HTMLInputElement | null>(null)

// 添加新段落
const addPassage = () => {
  passages.value.push({
    passage_type: '',
    passage_tag: [],
    inputVisible: false,
    inputValue: '',
    showPreview: false,
    passage_title: '',
    passage: '',
    references: [],
    loading: false,
    isGenerated: false,
    showReferences: false // 默认折叠参考文献
  })
  // 保存到本地存储
  savePassagesToLocalStorage()
}

// 删除段落
const removePassage = (index: number) => {
  passages.value.splice(index, 1)
  // 保存到本地存储
  savePassagesToLocalStorage()
}

// 显示标签输入框
const showTagInput = (passageIndex: number) => {
  passages.value[passageIndex].inputVisible = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

// 确认添加标签
const confirmTag = (passageIndex: number) => {
  const inputValue = passages.value[passageIndex].inputValue
  if (inputValue) {
    if (!passages.value[passageIndex].passage_tag.includes(inputValue)) {
      passages.value[passageIndex].passage_tag.push(inputValue)
    }
  }
  passages.value[passageIndex].inputVisible = false
  passages.value[passageIndex].inputValue = ''
}

// 删除标签
const removeTag = (passageIndex: number, tagIndex: number) => {
  passages.value[passageIndex].passage_tag.splice(tagIndex, 1)
}

// 生成综述段落
const generatePassage = async (passageIndex: number) => {
  const passage = passages.value[passageIndex]
  
  if (!passage.passage_type) {
    ElMessage.warning('请输入段落类型')
    return
  }
  
  if (passage.passage_tag.length === 0) {
    ElMessage.warning('请至少添加一个标签')
    return
  }
  
  passage.loading = true
  
  try {
    const response = await axios.post('/api/writing/', {
      passage_type: passage.passage_type,
      passage_tag: passage.passage_tag
    })
    
    passage.passage_title = response.data.passage_title
    passage.passage = response.data.passage
    passage.references = response.data.references
    passage.isGenerated = true // 标记为已生成
    // 不再设置 showPreview 为 true，因为我们不使用弹窗了
    
    // 保存到本地存储
    savePassagesToLocalStorage()
  } catch (error) {
    console.error('生成段落失败:', error)
    ElMessage.error('生成段落失败，请稍后重试')
  } finally {
    passage.loading = false
  }
}

// 保存段落到本地存储
const savePassagesToLocalStorage = () => {
  localStorage.setItem('paper-writing-passages', JSON.stringify(passages.value))
}

// 从本地存储加载段落
const loadPassagesFromLocalStorage = () => {
  const savedPassages = localStorage.getItem('paper-writing-passages')
  if (savedPassages) {
    passages.value = JSON.parse(savedPassages)
  }
}

// 监听段落变化，保存到本地存储
watch(passages, () => {
  savePassagesToLocalStorage()
}, { deep: true })

// 组件挂载时加载本地存储的段落
onMounted(() => {
  loadPassagesFromLocalStorage()
})

// 格式化段落内容（将换行符转换为 <br>）
const formatPassage = (text: string) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}

// 复制段落内容
const copyPassage = (passage: Passage) => {
  const content = `${passage.passage_title}\n\n${passage.passage}`
  navigator.clipboard.writeText(content)
    .then(() => {
      ElMessage.success('内容已复制到剪贴板')
    })
    .catch(() => {
      ElMessage.error('复制失败，请手动复制')
    })
}

// 切换参考文献的显示状态
const toggleReferences = (passageIndex: number) => {
  passages.value[passageIndex].showReferences = !passages.value[passageIndex].showReferences
}

// 添加导出为 LaTeX 文档的函数
// 修改导出相关的变量和函数
const paperTitle = vueRef<string>('论文标题')
const authorName = vueRef<string>('作者姓名')
const templateType = vueRef<string>('article')
const exportLoading = vueRef<boolean>(false)
const pdfUrl = vueRef<string>('')
const texContent = vueRef<string>('')
const showExportDialog = vueRef<boolean>(false)
const isGenerating = vueRef<boolean>(false) // 新增：控制生成状态

// 修改导出函数：只显示对话框，不立即发送请求
const exportToLatex = () => {
  if (passages.value.length === 0) {
    ElMessage.warning('请至少添加一个段落')
    return
  }
  
  // 检查是否有未生成的段落
  const hasUngenerated = passages.value.some(p => !p.isGenerated)
  if (hasUngenerated) {
    ElMessage.warning('存在未生成的段落，请先生成所有段落')
    return
  }
  
  // 重置状态
  texContent.value = ''  // 确保这里设置为空字符串
  pdfUrl.value = ''
  isGenerating.value = false
  
  // 显示导出对话框
  showExportDialog.value = true
}

// 新增：生成LaTeX文档的函数
const generateLatexDocument = async () => {
  if (!paperTitle.value.trim()) {
    ElMessage.warning('请输入论文标题')
    return
  }
  
  if (!authorName.value.trim()) {
    ElMessage.warning('请输入作者姓名')
    return
  }
  
  isGenerating.value = true
  
  try {
    // 准备请求数据
    const passagesForExport = passages.value.map(p => ({
      passage_type: p.passage_type,
      passage_title: p.passage_title,
      passage: p.passage,
      references: p.references
    }))
    
    const response = await axios.post('/api/writing/output/', {
      passages: passagesForExport,
      template_type: templateType.value,
      paper_title: paperTitle.value,
      author_name: authorName.value
    })
    
    texContent.value = response.data.tex_content
    pdfUrl.value = response.data.pdf_url
    
    ElMessage.success('LaTeX 文档生成成功')
  } catch (error) {
    console.error('生成 LaTeX 文档失败:', error)
    ElMessage.error('生成 LaTeX 文档失败，请稍后重试')
  } finally {
    isGenerating.value = false
  }
}

// 下载 LaTeX 文件
const downloadLatex = () => {
  if (!texContent.value) {
    ElMessage.warning('没有可下载的 LaTeX 内容')
    return
  }
  
  const blob = new Blob([texContent.value], { type: 'application/x-tex' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${paperTitle.value || '论文'}.tex`
  
  document.body.appendChild(a)
  a.click()
  
  URL.revokeObjectURL(url)
  document.body.removeChild(a)
}
</script>

<template>
  <div class="writing-container">
    <el-button type="primary" @click="addPassage">新建段落</el-button>
    
    <div v-for="(passage, index) in passages" :key="index" class="passage-item">
      <el-card class="passage-card">
        <div class="passage-header">
          <h3>段落{{ index + 1 }}</h3>
          <el-button type="danger" size="small" @click="removePassage(index)">删除段落</el-button>
        </div>
        
        <el-form :model="passage" label-width="100px">
          <el-form-item label="段落类型">
            <el-input v-model="passage.passage_type" placeholder="请输入段落类型，如：引言、方法、结果等"></el-input>
          </el-form-item>
          
          <el-form-item label="标签">
            <div class="tags-container">
              <el-tag
                v-for="(tag, tagIndex) in passage.passage_tag"
                :key="tagIndex"
                closable
                @close="removeTag(index, tagIndex)"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
              
              <el-input
                v-if="passage.inputVisible"
                ref="tagInputRef"
                v-model="passage.inputValue"
                class="tag-input"
                size="small"
                @keyup.enter="confirmTag(index)"
                @blur="confirmTag(index)"
              />
              
              <el-button v-else class="button-new-tag" size="small" @click="showTagInput(index)">
                + 添加标签
              </el-button>
            </div>
          </el-form-item>
          
          <el-form-item>
            <el-button type="success" :loading="passage.loading" @click="generatePassage(index)">
              {{ passage.isGenerated ? '重新生成' : '生成综述段落' }}
            </el-button>
          </el-form-item>
          
          <!-- 直接显示生成的段落内容 -->
          <div v-if="passage.isGenerated" class="generated-content">
            <h2>{{ passage.passage_title }}</h2>
            
            <!-- 使用MarkdownPreview组件显示段落内容 -->
            <MarkdownPreview :markdownContent="passage.passage" />
            
            <div v-if="passage.references && passage.references.length > 0" class="references">
              <div class="references-header" @click="toggleReferences(index)">
                <h3>参考文献 ({{ passage.references.length }})</h3>
                <el-icon class="toggle-icon">
                  <el-icon-arrow-down v-if="!passage.showReferences" />
                  <el-icon-arrow-up v-else />
                </el-icon>
              </div>
              
              <transition name="fade">
                <ol v-if="passage.showReferences" class="references-list">
                  <li v-for="(ref, refIndex) in passage.references" :key="refIndex">
                    {{ ref }}
                  </li>
                </ol>
              </transition>
            </div>
            
            <div class="content-actions">
              <el-button type="primary" size="small" @click="copyPassage(passage)">
                复制内容
              </el-button>
            </div>
          </div>
        </el-form>
      </el-card>
    </div>
    
    <!-- 添加导出按钮 -->
    <div class="action-buttons">
      <el-button type="primary" @click="addPassage">新建段落</el-button>
      <el-button 
        type="success" 
        @click="exportToLatex" 
        :disabled="passages.length === 0">
        导出为 LaTeX 文档
      </el-button>
    </div>
    
    <!-- 修改导出对话框 -->
    <el-dialog
      v-model="showExportDialog"
      title="LaTeX 文档导出"
      width="80%"
    >
      <!-- 表单部分 -->
      <el-form label-width="100px">
        <el-form-item label="论文标题">
          <el-input v-model="paperTitle" :disabled="isGenerating || !!texContent" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="authorName" :disabled="isGenerating || !!texContent" />
        </el-form-item>
        <el-form-item label="模板类型">
          <el-select v-model="templateType" style="width: 100%" :disabled="isGenerating || !!texContent">
            <el-option label="文章 (article)" value="article" />
            <el-option label="报告 (report)" value="report" />
            <el-option label="书籍 (book)" value="book" />
          </el-select>
        </el-form-item>
        
        <!-- 生成按钮 -->
        <el-form-item v-if="!texContent">
          <el-button 
            type="primary" 
            @click="generateLatexDocument" 
            :loading="isGenerating"
            :disabled="isGenerating">
            生成 LaTeX 文档
          </el-button>
        </el-form-item>
        
        <!-- 生成结果展示 -->
        <div v-if="texContent || isGenerating">
          <el-divider>生成结果</el-divider>
          
          <el-tabs v-if="texContent">
            <el-tab-pane label="LaTeX 代码">
              <el-input
                type="textarea"
                v-model="texContent"
                :rows="15"
                readonly
              />
            </el-tab-pane>
            <el-tab-pane label="PDF 预览" v-if="pdfUrl">
              <iframe :src="pdfUrl" style="width: 100%; height: 600px; border: none;"></iframe>
            </el-tab-pane>
          </el-tabs>
          
          <div v-else-if="isGenerating" class="generating-placeholder">
            <el-skeleton :rows="10" animated />
            <div class="generating-text">正在生成 LaTeX 文档，请稍候...</div>
          </div>
        </div>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showExportDialog = false">关闭</el-button>
          <template v-if="texContent">
            <el-button type="primary" @click="downloadLatex">
              下载 LaTeX 文件
            </el-button>
            <el-button type="success" v-if="pdfUrl">
              <a :href="pdfUrl" download :filename="`${paperTitle || '论文'}.pdf`" style="text-decoration: none; color: inherit;">
                下载 PDF 文件
              </a>
            </el-button>
            <el-button type="info" v-if="pdfUrl">
              <a :href="pdfUrl" target="_blank" style="text-decoration: none; color: inherit;">
                在新窗口查看 PDF
              </a>
            </el-button>
          </template>
        </span>
      </template>
    </el-dialog>
  </div>
</template>



<style scoped>
.writing-container {
  padding: 20px;
}

.passage-item {
  margin-top: 20px;
}

.passage-card {
  margin-bottom: 20px;
}

.passage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.tag-item {
  margin-right: 10px;
  margin-bottom: 10px;
}

.tag-input {
  width: 100px;
  margin-right: 10px;
  vertical-align: bottom;
}

.generated-content {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #eaeaea;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.references {
  margin-top: 30px;
  padding-top: 10px;
  border-top: 1px solid #eee;
}

.references-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 5px 0;
}

.references-header:hover {
  background-color: #f5f5f5;
}

.toggle-icon {
  font-size: 16px;
  transition: transform 0.3s;
}

.references-list {
  margin-top: 10px;
  padding-left: 20px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

