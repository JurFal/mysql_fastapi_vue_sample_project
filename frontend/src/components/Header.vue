<script setup lang="ts">
import {ElMessage, ElNotification as notify} from 'element-plus'
import {LogoutApi} from "@/request/api";
import {useRouter} from 'vue-router'
import {useUserstore} from "@/store/user";
const router = useRouter()
const userStore = useUserstore()
async function logout() {
  try {
    // 调用后端登出API
    // 使用store中的logout方法清除用户信息
    userStore.logout()
    ElMessage.success("登出成功")
    await router.push('/')
  } catch (error) {
    console.error('登出失败:', error)
    ElMessage.error("登出失败，请重试")
  }
}

// 添加导航到index页面的函数
function navigateToIndex() {
  router.push('/index/')
}
</script>

<template>
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <el-avatar 
      :size="50" 
      :src="userStore.avatar || 'https://avatars.githubusercontent.com/u/112413958?s=400&u=24970d0e0773bb7d637374458fca9e8f12a06591&v=4'" 
      @click="navigateToIndex"
      style="cursor: pointer;"
    />
    <div>
      <el-button type="info" @click="logout">登出</el-button>
    </div>
  </div>
</template>

<style scoped>

</style>