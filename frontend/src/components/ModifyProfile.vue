<script setup lang="ts">
import {reactive, ref, onMounted} from 'vue'
import type {FormInstance, FormRules} from 'element-plus'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {GetUserInfoByUserName} from "@/request/api";
import {useUserstore} from '@/store/user'

const userStore = useUserstore()
const router = useRouter()

const ruleFormRef = ref<FormInstance>()

const userForm = reactive({
  userName: '',
  password: '',
  first_name:'',
  last_name:'',
  email:'',
  avatar:'',
})

// 在组件挂载时获取当前用户信息
onMounted(async () => {
  try {
    if (userStore.userName) {
      const userInfo = await GetUserInfoByUserName({ userName: userStore.userName })
      userForm.userName = userInfo.username
      userForm.first_name = userInfo.first_name
      userForm.last_name = userInfo.last_name
      userForm.email = userInfo.email
      userForm.avatar = userInfo.avatar || ''
    } else {
      ElMessage.warning('请先登录')
      router.push('/')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('获取用户信息失败')
  }
})

// 表单验证规则
const rules = reactive<FormRules>({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  first_name: [
    { required: true, message: '请输入名', trigger: 'blur' }
  ],
  last_name: [
    { required: true, message: '请输入姓', trigger: 'blur' }
  ]
})

const submitForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate(async (valid) => {
    if (valid) {
      try {
        // 注意：后端目前没有提供更新用户信息的API
        // 这里只是前端模拟更新成功
        ElMessage.success('更新成功')
        // 更新本地存储的用户名（如果有变化）
        if (userForm.userName !== userStore.userName) {
          userStore.setUserName(userForm.userName)
        }
      } catch (e) {
        console.error(e)
        ElMessage.error('更新失败，请重试')
      }
    } else {
      ElMessage.error('表单验证失败，请检查输入')
      return false
    }
  })
}


</script>

<template>
  <el-form
      ref="ruleFormRef"
      :model="userForm"
      :rules="rules"
      style="max-width: 600px"
      label-width="auto"
      class="demo-ruleForm"
  >

    <el-form-item label="用户名" prop="userName">
      <el-input v-model="userForm.userName" type="text" autocomplete="off" disabled/>
    </el-form-item>

    <el-form-item label="密码" prop="password">
      <el-input v-model="userForm.password" type="password" autocomplete="off" placeholder="如需修改密码请输入新密码"/>
    </el-form-item>

    <el-form-item label="名" prop="first_name">
      <el-input v-model="userForm.first_name" type="text" autocomplete="off"/>
    </el-form-item>

    <el-form-item label="姓" prop="last_name">
      <el-input v-model="userForm.last_name" type="text" autocomplete="off"/>
    </el-form-item>

    <el-form-item label="邮箱" prop="email">
      <el-input v-model="userForm.email" type="text" autocomplete="off"/>
    </el-form-item>

    <el-form-item label="头像" prop="avatar">
      <el-input v-model="userForm.avatar" type="text" autocomplete="off"/>
    </el-form-item>

    <el-form-item>
      <el-button type="primary" @click="submitForm(ruleFormRef)"
      >更新
      </el-button
      >
    </el-form-item>

  </el-form>
</template>

<style scoped>


</style>