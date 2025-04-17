<script setup lang="ts">
// 导入 ref, reactive, nextTick, onMounted, watch, computed
import { ref as vueRef, reactive, nextTick, onMounted, watch, computed } from 'vue'
// 导入 ElMessage, ElContainer, ElAside, ElMain
import {ElMessage, ElContainer, ElAside, ElMain} from 'element-plus'
import MarkdownPreview from '@/components/MarkdownPreview.vue'
import axios from 'axios'
// 导入用户存储
import {useUserstore} from '@/store/user'
// 导入历史记录侧边栏组件
import WritingHistory from '@/components/WritingHistory.vue'
// 导入 debounce
import { debounce } from 'lodash-es';

// 获取用户存储
const userStore = useUserstore()

interface Passage {
  passage_type: string
  passage_tag: string[]
  inputVisible: boolean
  inputValue: string
  showPreview: boolean // 这个字段似乎不再使用，可以考虑移除
  passage_title: string
  passage: string
  references: string[]
  loading: boolean
  isGenerated: boolean
  showReferences: boolean
}

const passages = vueRef<Passage[]>([])
const tagInputRef = vueRef<HTMLInputElement | null>(null)

// 新增：当前编辑的历史记录ID
const currentHistoryId = vueRef<number | null>(null)

// --- 将导出相关的变量声明移到这里 ---
const paperTitle = vueRef<string>('论文标题')
const authorName = vueRef<string>('作者姓名')
const templateType = vueRef<string>('article')
const pdfUrl = vueRef<string>('')
const texContent = vueRef<string>('')
const showExportDialog = vueRef<boolean>(false)
const isGenerating = vueRef<boolean>(false)
const loading = vueRef<boolean>(false); // 添加全局 loading 状态

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
    showReferences: false
  })
  // 自动保存会处理
  // savePassagesToLocalStorage() // 移除显式调用
}

// 删除段落
const removePassage = (index: number) => {
  passages.value.splice(index, 1)
  // 自动保存会处理
  // savePassagesToLocalStorage() // 移除显式调用
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
    
    // 保存到本地存储 -> 修改为调用新的保存函数
    saveCurrentWritingState(); // <--- 修改点: 调用重命名后的函数
  } catch (error) {
    console.error('生成段落失败:', error)
    ElMessage.error('生成段落失败，请稍后重试')
  } finally {
    passage.loading = false
  }
}

// 重命名函数并修改逻辑：保存当前写作状态到数据库
const saveCurrentWritingState = async () => {
  // 只有登录用户才保存数据
  if (!userStore.userName) return;

  // 检查：如果是新建状态且没有任何段落，则不保存
  if (
    currentHistoryId.value === null &&
    (passages.value.length === 0 ||
      (passages.value.length === 1 &&
        !passages.value[0].passage_type &&
        !passages.value[0].passage_title &&
        !passages.value[0].passage))
  ) {
    // 空内容不保存
    return;
  }

  // 组装要保存的数据
  const writingData = JSON.stringify({
    paperTitle: paperTitle.value,
    authorName: authorName.value,
    templateType: templateType.value,
    passages: passages.value,
  });

  try {
    if (currentHistoryId.value === null) {
      // 新建历史记录
      const response = await axios.post(
        '/users_api/create/writing/',
        { writing_data: writingData },
        {
          headers: {
            Authorization: `Bearer ${userStore.token}`,
          },
        }
      );
      // 保存新建的ID
      if (response.data && response.data.id) {
        currentHistoryId.value = response.data.id;
      }
    } else {
      // 更新已有历史记录
      await axios.put(
        `/users_api/update/writing/${currentHistoryId.value}/`,
        { writing_data: writingData },
        {
          headers: {
            Authorization: `Bearer ${userStore.token}`,
          },
        }
      );
    }
    // 新增：保存成功后刷新左侧历史列表
    WritingHistory.value?.fetchHistories?.();
    // 新增：如果当前分支被删除（即 currentHistoryId 已经不存在于 histories），自动切换到最新分支
    // 需要先刷新历史列表
    const histories = await writingHistoryRef.value?.fetchHistories?.();
    // histories 可能未返回，保险起见再取一次
    
    await writingHistoryRef.value?.deleteAllUntitledHistories?.();
    let latest = null;
    if (histories && histories.length > 0) {
      latest = histories[0];
    }
    if (latest && currentHistoryId.value !== latest.id) {
      currentHistoryId.value = latest.id;
      // 主动加载最新分支内容
      // 你可以直接调用 handleSelectHistory 或 loadHistoryData
      handleSelectHistory(latest);
      writingHistoryRef.value?.setActiveHistoryId(latest.id);
    }
  } catch (e: any) {
    console.error('保存写作历史失败:', e);
    ElMessage.error('保存写作历史失败，请稍后重试');
  }
}

// 使用 debounce 包装保存函数，延迟 1.5 秒执行
const debouncedSave = debounce(saveCurrentWritingState, 1500); // <--- 修改点: 包装重命名后的函数

// 修改：从数据库加载指定的或最新的历史记录
// (loadHistoryData 函数保持不变)
const loadHistoryData = (data: any) => {
    if (data) {
        const parsedData = JSON.parse(data.writing_data);
        if (parsedData.passages && Array.isArray(parsedData.passages)) {
            passages.value = parsedData.passages;
            paperTitle.value = parsedData.paperTitle || '论文标题';
            authorName.value = parsedData.authorName || '作者姓名';
            templateType.value = parsedData.templateType || 'article';
            currentHistoryId.value = data.id; // 设置当前加载的历史记录ID
            return true; // 加载成功
        }
    }
    return false; // 加载失败或数据无效
}

// 新增：处理从侧边栏选择历史记录的事件
const handleSelectHistory = (history: any) => {
  console.log("Selected history:", history.id, "Is new:", history.isNew); // 打印接收到的 history 对象
  if (!loadHistoryData(history)) {
      ElMessage.error('加载选定的历史记录失败');
      // 加载失败，可以选择清空或保持当前状态
      handleCreateNew(); // 回到新建状态
  } else {
      // 加载成功后，检查是否是新创建的
      if (history.isNew === true) {
          console.log("Adding default passage for new history.");
          // 添加一个默认段落
          passages.value.push({
              passage_type: '引言', // 默认类型
              passage_tag: ['默认'], // 默认标签
              inputVisible: false,
              inputValue: '',
              showPreview: false, // 确保与 Passage 接口一致
              passage_title: '', // 初始为空
              passage: '',       // 初始为空
              references: [],    // 初始为空
              loading: false,
              isGenerated: false,
              showReferences: false
          });
          // 可以在这里触发一次保存，以将这个默认段落存入数据库
          saveCurrentWritingState(); // 或者等待 debouncedSave 自动触发
      }
  }
}

// 新增：处理新建历史记录的事件 (这个函数现在主要用于清空状态)
const handleCreateNew = () => {
  console.log("Clearing state for new history / load failure.");
  passages.value = [];
  paperTitle.value = '论文标题';
  authorName.value = '作者姓名';
  templateType.value = 'article';
  currentHistoryId.value = null; // 清除当前ID，表示新建状态
  // 清空导出对话框状态 (如果需要)
  texContent.value = '';
  pdfUrl.value = '';
  isGenerating.value = false;
  showExportDialog.value = false;
}

// 修改：加载初始数据 (最新历史记录)
const loadInitialData = async () => {
  if (userStore.userName) {
    loading.value = true; // 可以添加一个全局 loading 状态
    try {
      // 尝试从后端API加载所有历史记录，然后选最新的
      const response = await axios.get('/users_api/get/writing/all/', {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      });

      if (response.data && Array.isArray(response.data) && response.data.length > 0) {
        // 按更新时间排序，最新的在前面
        const sortedHistories = response.data.sort((a: any, b: any) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        );
        // 加载最新的历史记录
        if (!loadHistoryData(sortedHistories[0])) {
            // 如果最新的记录加载失败，则创建新的
            handleCreateNew();
        }
      } else {
        // 没有历史记录，创建新的
        handleCreateNew();
      }
    } catch (e) {
      console.error('加载初始写作历史失败:', e);
      ElMessage.error('加载历史记录失败');
      // 加载失败也进入新建状态
      handleCreateNew();
    } finally {
        loading.value = false;
    }
  } else {
    // 未登录时清空数据
    handleCreateNew();
  }
}

// 移除 clearPassages 函数，其逻辑合并到 handleCreateNew

// 修改：监听段落和元数据变化，使用 debounce 自动保存
// 现在 paperTitle, authorName, templateType 已经在此之前声明了
const writingHistoryRef = vueRef<any>(null); // 1. 声明 ref

watch([passages, paperTitle, authorName, templateType], () => {
  saveCurrentWritingState();
  // 2. 变动时调用 fetchHistories
  writingHistoryRef.value?.fetchHistories?.();
}, { deep: true })

// 修改：监听用户登录状态变化
watch(() => userStore.userName, (newUserName, oldUserName) => {
  if (newUserName) {
    // 用户登录或切换账号，加载对应的最新段落数据
    loadInitialData()
  } else {
    // 用户登出，清除段落数据
    handleCreateNew()
  }
}, { immediate: true }) // 保持 immediate: true 以处理初始加载

// 修改：组件挂载时加载数据 (如果用户已登录)
onMounted(() => {
  // loadInitialData 会在 watch immediate:true 中被调用，这里无需重复调用
  // if (userStore.userName) {
  //   loadInitialData()
  // }
})

writingHistoryRef.value?.setActiveHistoryId(currentHistoryId.value);

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


// 添加导出JSON配置的函数
const exportConfig = () => {
  if (passages.value.length === 0) {
    ElMessage.warning('没有可导出的段落')
    return
  }
  
  // 准备导出数据
  const exportData = {
    paperTitle: paperTitle.value,
    authorName: authorName.value,
    templateType: templateType.value,
    passages: passages.value
  }
  
  // 创建Blob对象
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  
  // 创建下载链接
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `paper-config-${Date.now()}.json`
  // 触发下载
  document.body.appendChild(a)
  a.click()
  
  // 清理
  URL.revokeObjectURL(url)
  document.body.removeChild(a)
  
  ElMessage.success('配置已导出')
}

// 添加导入JSON配置的函数
const importConfig = (event: Event) => {
  const fileInput = event.target as HTMLInputElement
  const file = fileInput.files?.[0]
  
  if (!file) {
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const content = e.target?.result as string
      const importedData = JSON.parse(content)
      
      // 验证导入的数据格式
      if (!importedData.passages || !Array.isArray(importedData.passages)) {
        ElMessage.error('导入的配置格式不正确')
        return
      }
      
      // 更新数据
      passages.value = importedData.passages
      
      // 如果有其他配置数据，也一并导入
      if (importedData.paperTitle) paperTitle.value = importedData.paperTitle
      if (importedData.authorName) authorName.value = importedData.authorName
      if (importedData.templateType) templateType.value = importedData.templateType
      
      ElMessage.success('配置已导入')
      
      // 保存到本地存储
      saveCurrentWritingState()
    } catch (error) {
      console.error('导入配置失败:', error)
      ElMessage.error('导入配置失败，请检查文件格式')
    }
    
    // 重置文件输入，以便可以重复导入同一个文件
    fileInput.value = ''
  }
  
  reader.readAsText(file)
}

// 创建一个隐藏的文件输入元素
const fileInputRef = vueRef<HTMLInputElement | null>(null)
const pdfInputRef = vueRef<HTMLInputElement | null>(null) // 新增PDF文件上传输入

// 触发文件选择对话框
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

// 触发PDF文件选择对话框
const triggerPdfInput = () => {
  pdfInputRef.value?.click()
}

// 上传PDF文件到论文库
const uploadPaperToDB = async (event: Event) => {
  const fileInput = event.target as HTMLInputElement
  const file = fileInput.files?.[0]
  
  if (!file) {
    return
  }
  
  // 检查文件类型
  if (file.type !== 'application/pdf') {
    ElMessage.error('只支持上传PDF格式的论文')
    fileInput.value = ''
    return
  }
  
  // 创建FormData对象
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    // 显示上传中提示
    const loadingInstance = ElMessage({
      message: '正在上传论文并解析到向量数据库...',
      type: 'info',
      duration: 0
    })
    
    // 发送上传请求
    const response = await axios.post('/api/papers/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    // 关闭上传中提示
    loadingInstance.close()
    
    // 显示成功消息
    ElMessage.success(`论文《${response.data.title || file.name}》上传成功`)
  } catch (error) {
    console.error('上传论文失败:', error)
    ElMessage.error('上传论文失败，请稍后重试')
  } finally {
    // 重置文件输入，以便可以重复上传同一个文件
    fileInput.value = ''
  }
}

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
  <el-container class="writing-container-layout">
    <!-- 侧边栏 -->
    <el-aside width="300px" class="history-aside">
      <WritingHistory ref="writingHistoryRef"
        @select-history="handleSelectHistory" 
        @create-new="handleCreateNew" 
      />
    </el-aside>

    <!-- 主内容区域 -->
    <el-main class="writing-main">
      <div class="writing-content">
        <!-- 添加导出和导入按钮 -->
        <div class="top-actions">
          <el-button type="primary" @click="addPassage">新建段落</el-button>
          <el-button type="info" @click="exportConfig">导出配置</el-button>
          <el-button type="warning" @click="triggerFileInput">导入配置</el-button>
          <el-button type="success" @click="triggerPdfInput">上传至论文库...</el-button>
          <input
            type="file"
            ref="fileInputRef"
            style="display: none"
            accept=".json"
            @change="importConfig"
          />
          <input
            type="file"
            ref="pdfInputRef"
            style="display: none"
            accept=".pdf"
            @change="uploadPaperToDB"
          />
        </div>
        
        <!-- 段落列表 -->
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
                <MarkdownPreview v-model:markdownContent="passage.passage" />
                
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
        
        <!-- 导出对话框 -->
        <el-dialog
          v-model="showExportDialog"
          title="LaTeX 文档导出"
          width="80%"
        >
          <!-- ... 对话框内部内容保持不变 ... -->
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
                  <a :href="pdfUrl" :download="`${paperTitle || '论文'}.pdf`" style="text-decoration: none; color: inherit;">
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
    </el-main>
  </el-container>
</template>

<style scoped>
/* 新增布局样式 */
.writing-container-layout {
  height: 100vh; /* 让容器占满整个视口高度 */
}

.history-aside {
  border-right: 1px solid #ebeef5;
  height: 100%; /* 侧边栏高度占满容器 */
  display: flex; /* 使用 flex 布局 */
  flex-direction: column; /* 垂直排列 */
}

.writing-main {
  padding: 0; /* 移除 el-main 的默认内边距 */
  height: 100%; /* 主区域高度占满容器 */
  overflow-y: auto; /* 如果内容超出，允许主区域滚动 */
}

.writing-content {
  padding: 20px; /* 将原来的内边距移到这里 */
}

/* 添加顶部操作按钮的样式 */
.top-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap; /* 确保在小屏幕上按钮可以换行 */
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

/* 导出对话框内的样式 */
.generating-placeholder {
  text-align: center;
  padding: 20px;
}
.generating-text {
  margin-top: 15px;
  color: #606266;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}
</style>

