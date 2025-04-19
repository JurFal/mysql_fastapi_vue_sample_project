<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue' // Ensure computed is imported
import { ElMessage, ElMessageBox, ElIcon } from 'element-plus' // Import ElIcon if needed for Delete
import { Delete } from '@element-plus/icons-vue' // Import Delete icon
import axios from 'axios'
import { useUserstore } from '@/store/user'

// 获取用户存储
const userStore = useUserstore()

// 定义历史记录类型
interface WritingHistory {
  id: number
  title: string
  created_at: string
  updated_at: string
  writing_data: string
}

// 状态变量
const histories = ref<WritingHistory[]>([])
const loading = ref(false)
const currentHistoryId = ref<number | null>(null) // Initialize with null for potential initial "new" state
const searchQuery = ref('')

// 获取所有历史记录
const fetchHistories = async () => {
  if (!userStore.token) return
  
  loading.value = true
  try {
    const response = await axios.get('/users_api/get/writing/all/', {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    if (response.data && Array.isArray(response.data)) {
      histories.value = response.data.map((item: any) => {
        let title = '新建综述'
        try {
          const data = JSON.parse(item.writing_data)
          if (data.paperTitle && data.paperTitle.trim()) {
            title = data.paperTitle
          }
        } catch (e) {
          console.error('解析writing_data失败:', e)
        }
        return {
          ...item,
          title
        }
      })
      
      // 按创建时间排序，最新的在前面
      histories.value.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
      currentHistoryId.value = histories.value.length > 0 ? 
        histories.value.slice().sort((a, b) => 
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        )[0].id : null;
    }
  } catch (error) {
    console.error('获取历史记录失败:', error)
    ElMessage.error('获取历史记录失败')
  } finally {
    loading.value = false
  }
}

// 选择历史记录
const selectHistory = async (history: WritingHistory) => {
  try {
    // 新增：根据 id 请求详细内容
    const response = await axios.get(`/users_api/get/writing/${history.id}/`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    // 发出事件通知父组件加载选定的历史记录（用后端返回的完整数据）
    emit('select-history', response.data)
    currentHistoryId.value = history.id // Update internal state for highlighting
  } catch (error) {
    console.error('选择历史记录失败:', error)
    ElMessage.error('选择历史记录失败')
  }
}

// 新建历史记录 - 修改后
const createNewHistory = async () => {
  if (!userStore.token) {
    ElMessage.warning('请先登录');
    return;
  }
  try {
    const defaultWritingData = JSON.stringify({ paperTitle: '新建写作' });
    const response = await axios.post('/users_api/create/writing/',
      { writing_data: defaultWritingData },
      {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      }
    );

    const newHistory: WritingHistory = response.data;

    // 1. 刷新历史记录列表
    await fetchHistories();

    // 2. 恢复：将新创建的历史记录设为当前活动项
    currentHistoryId.value = newHistory.id;

    // 3. 恢复：触发 select-history 事件，通知父组件加载这个新记录
    // 需要确保 newHistory 包含从 writing_data 解析出的 title
    // fetchHistories 已经更新了 histories 列表，从中找到新项以确保 title 正确
    // 注意：此时 histories 可能过滤掉了未命名项，所以找不到，直接用 newHistory
    emit('select-history', { ...newHistory, isNew: true });

    ElMessage.success('新的写作已创建');
  } catch (error) {
    console.error('创建新写作历史失败:', error);
    ElMessage.error('创建新写作历史失败');
  }
}

// 删除历史记录
const deleteHistory = async (history: WritingHistory, event: Event) => {
  // 阻止事件冒泡，避免触发选择事件
  event.stopPropagation()

  // 新增：如果只有一条历史，禁止删除
  if (histories.value.length === 1) {
    ElMessage.warning('不能删除唯一的历史记录');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除写作历史 "${history.title}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await axios.delete(`/users_api/delete/writing/${history.id}/`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    const deletedId = history.id;
    // 从列表中移除
    histories.value = histories.value.filter(h => h.id !== deletedId)
    
    // 如果删除的是当前选中的历史记录，则切换到最新一条（如果有）
    if (currentHistoryId.value === deletedId) {
      if (histories.value.length > 0) {
        // 找到更新时间最新的那一条
        const latest = histories.value.slice().sort((a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        )[0];
        selectHistory(latest);
      } else {
        // 没有历史记录，切换到新建状态但不新建
        currentHistoryId.value = null;
        emit('select-history', null);
      }
    }
    
    ElMessage.success('历史记录已删除')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除历史记录失败:', error)
      ElMessage.error('删除历史记录失败')
    }
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', { // Use Chinese locale for formatting
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 过滤历史记录
const filteredHistories = computed(() => {
  if (!searchQuery.value) return histories.value
  
  const query = searchQuery.value.toLowerCase().trim() // Trim search query
  if (!query) return histories.value; // Return all if query is empty after trim

  return histories.value.filter(history => 
    history.title.toLowerCase().includes(query)
  )
})

// 监听用户登录状态变化
watch(() => userStore.token, (newToken) => {
  if (newToken) {
    fetchHistories()
    // When logging in, default to the "new" state visually unless parent specifies otherwise
    currentHistoryId.value = null; 
  } else {
    histories.value = []
    currentHistoryId.value = null
  }
}, { immediate: true })

// 组件挂载时获取历史记录 (handled by watch immediate)
// onMounted(() => {
//   if (userStore.token) {
//     fetchHistories()
//   }
// })

// 定义事件
const emit = defineEmits(['select-history', 'create-new'])

// Public method for parent component to set the active history ID
// This helps synchronize state if the parent loads a specific history initially
const setActiveHistoryId = (id: number | null) => {
  currentHistoryId.value = id;
}

// 删除所有新建写作分支
const deleteAllUntitledHistories = async () => {
  const untitled = histories.value.filter(h => h.title === '新建写作');
  for (const history of untitled) {
    try {
      await axios.delete(`/users_api/delete/writing/${history.id}/`, {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      });
    } catch (e) {
      // 可以选择静默处理
      console.error('删除新建写作失败:', e);
    }
  }
  // 删除后刷新列表
  await fetchHistories();
};

defineExpose({
  setActiveHistoryId,
  fetchHistories,
  deleteAllUntitledHistories // 新增暴露
});

</script>

<template>
  <div class="writing-history-sidebar">
    <div class="history-header">
      <h3>写作历史</h3>
      <el-button
        type="primary"
        size="small"
        @click="createNewHistory"
        :class="{ 'active-button': currentHistoryId === null }"
      >
        新建
      </el-button>
    </div>

    <el-input
      v-model="searchQuery"
      placeholder="搜索历史记录..."
      prefix-icon="el-icon-search"
      clearable
      class="search-input"
    />

    <div class="history-list" v-loading="loading">
      <div v-if="!userStore.token" class="login-prompt">
        <p>请登录以查看您的写作历史</p>
      </div>

      <div v-else-if="filteredHistories.length === 0 && !loading" class="empty-prompt">
        <p>{{ searchQuery ? '没有匹配的历史记录' : '暂无写作历史记录' }}</p>
        <el-button v-if="!searchQuery" type="primary" plain size="small" @click="createNewHistory">
          开始新的写作
        </el-button>
      </div>

      <div
        v-for="history in filteredHistories"
        :key="history.id"
        class="history-item"
        :class="{ 'active': currentHistoryId === history.id }"
        @click="selectHistory(history)"
        :title="history.title"
      >
        <div class="history-item-content">
          <div class="history-title">{{ history.title }}</div>
          <div class="history-date">{{ formatDate(history.updated_at) }}</div>
        </div>
        <div class="history-actions">
          <el-button
            type="danger"
            size="small"
            :icon="Delete"
            circle
            @click="deleteHistory(history, $event)"
            title="删除此历史记录"
          >
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.writing-history-sidebar {
  height: 100%;
  /* border-right: 1px solid #ebeef5; */ /* Removed border, handled by parent layout */
  padding: 15px;
  display: flex;
  flex-direction: column;
  background-color: #fcfcfc; /* Slightly different background */
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0; /* Add a subtle separator */
}

.history-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.search-input {
  margin-bottom: 15px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  /* Custom scrollbar styling (optional) */
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: #ddd;
    border-radius: 3px;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: #ccc;
  }
}

.history-item {
  padding: 10px 12px; /* Adjusted padding */
  border-radius: 4px;
  margin-bottom: 5px; /* Reduced margin */
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s ease-in-out, border-left 0.2s ease-in-out;
  border-left: 3px solid transparent; /* Add transparent border for smooth transition */
}

.history-item:hover {
  background-color: #f0f2f5; /* Slightly different hover */
}

/* Style for the active history item */
.history-item.active {
  background-color: #e6f0ff; /* Adjusted active background */
  border-left: 3px solid #409eff;
  font-weight: 500; /* Make text slightly bolder */
}
.history-item.active .history-title {
  color: #3a8ee6; /* Change title color when active */
}


.history-item-content {
  flex: 1;
  overflow: hidden;
  margin-right: 8px; /* Add space between content and actions */
}

.history-title {
  font-size: 14px; /* Slightly larger title */
  color: #454749; /* Darker title */
  margin-bottom: 4px; /* Reduced margin */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-date {
  font-size: 11px; /* Smaller date */
  color: #a8abb2; /* Lighter date color */
}

.history-actions {
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}

.history-item:hover .history-actions,
.history-item.active .history-actions 
{
  opacity: 1;
}

/* Style for the active "New" button */
.active-button {
  border-color: #79bbff;
  background-color: #ecf5ff;
  color: #409eff;
  font-weight: 500; /* Make button text bolder when active */
}
/* Optional: Adjust hover style for active button */
.active-button:hover {
  border-color: #409eff;
  background-color: #d9ecff;
}


.login-prompt,
.empty-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px; /* Added padding */
  color: #909399;
  text-align: center;
  font-size: 14px;
}

.empty-prompt p {
  margin-bottom: 15px;
}
</style>