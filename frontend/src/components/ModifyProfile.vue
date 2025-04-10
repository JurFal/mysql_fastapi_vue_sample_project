<script setup lang="ts">
import {reactive, ref, onMounted} from 'vue'
import type {FormInstance, FormRules} from 'element-plus'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {GetUserInfoByUserName, UpdateUserInfo, VerifyPassword} from "@/request/api";
import {useUserstore} from '@/store/user'

const userStore = useUserstore()
const router = useRouter()

const ruleFormRef = ref<FormInstance>()

// 添加旧密码字段
const userForm = reactive({
  userName: '',
  oldPassword: '', // 新增旧密码字段
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
  ],
  // 修改旧密码验证规则，使用validator而不是required函数
  oldPassword: [
    { 
      validator: (rule, value, callback) => {
        if (userForm.password && !value) {
          callback(new Error('如需修改密码，请输入旧密码'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ]
})

// 密码修改标志
const isChangingPassword = ref(false)

// 监听新密码输入，如果有输入则需要验证旧密码
const handlePasswordInput = () => {
  isChangingPassword.value = !!userForm.password.trim()
}

const submitForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate(async (valid) => {
    if (valid) {
      try {
        // 创建更新数据对象
        const updateData: any = {
          first_name: userForm.first_name,
          last_name: userForm.last_name,
          email: userForm.email
        }
        
        // 只有当头像字段有值时才包含
        if (userForm.avatar) {
          updateData.avatar = userForm.avatar
        }
        
        // 如果用户输入了新密码，需要先验证旧密码
        if (userForm.password && userForm.password.trim() !== '') {
          // 确保用户输入了旧密码
          if (!userForm.oldPassword) {
            ElMessage.error('请输入旧密码以验证身份')
            return
          }
          
          try {
            // 验证旧密码
            await VerifyPassword(userForm.userName, userForm.oldPassword)
            // 密码验证成功，将新密码添加到更新数据中
            updateData.password = userForm.password
          } catch (error) {
            ElMessage.error('旧密码验证失败，无法修改密码')
            return
          }
        }
        
        // 调用后端API
        await UpdateUserInfo(userForm.userName, updateData)
        
        ElMessage.success('更新成功')
        // 更新本地存储的用户名（如果有变化）
        if (userForm.userName !== userStore.userName) {
          userStore.setUserName(userForm.userName)
        }
        
        // 清空密码字段
        userForm.password = ''
        userForm.oldPassword = ''
        isChangingPassword.value = false
        
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

    <!-- 添加旧密码输入框，仅当用户输入新密码时显示 -->
    <el-form-item label="旧密码" prop="oldPassword" v-if="isChangingPassword">
      <el-input v-model="userForm.oldPassword" type="password" autocomplete="off" placeholder="请输入旧密码以验证身份"/>
    </el-form-item>

    <el-form-item label="新密码" prop="password">
      <el-input 
        v-model="userForm.password" 
        type="password" 
        autocomplete="off" 
        placeholder="如需修改密码请输入新密码"
        @input="handlePasswordInput"
      />
    </el-form-item>

    <!-- 其他表单项保持不变 -->
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
      <el-button type="primary" @click="submitForm(ruleFormRef)">更新</el-button>
    </el-form-item>

  </el-form>
</template>

<style scoped>


</style>