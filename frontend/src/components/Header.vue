<script setup lang="ts">
import {ElMessage, ElNotification as notify} from 'element-plus'
import {LogoutApi} from "@/request/api";
import {useRouter} from 'vue-router'
import {useUserstore} from "@/store/user";
const router = useRouter()
const userStore=useUserstore()
async function logout() {
  userStore.userName = 'userName'
  userStore.token = 'token'
  ElMessage.success("登出成功")
  await router.push('/')
}
</script>

<template>
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <el-avatar :size="50" :src="userStore.avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'" />
    <div>
      <el-button type="info" @click="logout">登出</el-button>
    </div>
  </div>
</template>

<style scoped>

</style>