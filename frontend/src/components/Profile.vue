<script setup lang="ts">
import {GetUserInfoByUserName} from "@/request/api";
import {ElMessage} from "element-plus";
import {onBeforeMount, ref} from "vue";
import {useUserstore} from '@/store/user'
import {useRoute} from "vue-router";

const userStore=useUserstore()
const route = useRoute()

let user = ref({
  username: '',
  first_name: '',
  last_name: '',
  email: '',
  avatar: 'https://avatars.githubusercontent.com/u/112413958?s=400&u=24970d0e0773bb7d637374458fca9e8f12a06591&v=4', // 假设的头像URL
})

async function getUserInfo() {
  try {
    let username = userStore.userName
    console.log(route.params)
    if ('username' in route.params) {
      console.log(route.params.username)
      // 修复类型错误：确保 username 是字符串类型
      username = Array.isArray(route.params.username) 
        ? route.params.username[0] 
        : route.params.username
    }
    let res = await GetUserInfoByUserName({
      userName: username
    })
    console.log(res)
    user.value.username = res.username
    if (res.email === "")
      user.value.email = res.first_name + res.last_name + "@example.com"
    else
      user.value.email = res.email
    user.value.first_name = res.first_name
    user.value.last_name = res.last_name
    if (res.avatar !== null)
      user.value.avatar = res.avatar
  } catch (e) {
    console.log(e)
    ElMessage.error('个人信息查询失败')
  }
}

onBeforeMount(() => {
  getUserInfo()
});


</script>

<template>
  <div class="user-profile">
    <img :src="user.avatar" alt="User Avatar" class="avatar"/>
    <h2>{{ user.username }}</h2>
    <p><strong>Full Name:</strong> {{ user.first_name }} {{ user.last_name }}</p>
    <p><strong>Email:</strong> {{ user.email }}</p>
  </div>
</template>

<style scoped>
.user-profile {
  max-width: 300px;
  margin: 20px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 10px;
  text-align: center;
}

.user-profile .avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  margin-bottom: 20px;
}
</style>