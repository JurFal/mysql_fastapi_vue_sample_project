<script setup lang="ts">
import {reactive, ref} from 'vue'
import type {FormInstance, FormRules} from 'element-plus'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {RegisterApi} from "@/request/api";
const router = useRouter()

const ruleFormRef = ref<FormInstance>()

const registerForm = reactive({
  userName: '',
  password: '',
  first_name:'',
  last_name:'',
  email:'',
  avatar:'',
})

// 重新定义验证函数
const checkUserName = (rule: any, value: any, callback: any) => {
  if (value === '') {
    return callback(new Error('请输入用户名'))
  } else {
    callback()
  }
}

const checkPassword = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else {
    callback()
  }
}

const rules = reactive<FormRules<typeof registerForm>>({
  userName: [{required: true, validator: checkUserName, trigger: 'blur'}],
  password: [{required: true, validator: checkPassword, trigger: 'blur'}],
  // 添加邮箱验证规则
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  // 添加姓名验证规则
  first_name: [
    { required: true, message: '请输入名', trigger: 'blur' }
  ],
  last_name: [
    { required: true, message: '请输入姓', trigger: 'blur' }
  ],
})

const submitForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate(async (valid) => {
    if (valid) {
      try {
        let res = await RegisterApi({
          username: registerForm.userName,
          password: registerForm.password,
          first_name: registerForm.first_name,
          last_name: registerForm.last_name,
          email: registerForm.email,
          avatar: registerForm.avatar
        })
        ElMessage.success('注册成功')
        await router.push('/');
      } catch (e) {
        console.log(e)
        ElMessage.error('注册失败请重新输入')
      }
    } else {
      ElMessage.error('注册失败请重新输入')
      return false
    }
  })
}

function jumpToLogin() {
  router.push('/')
}


</script>

<template>
  <el-form
      ref="ruleFormRef"
      :model="registerForm"
      :rules="rules"
      style="max-width: 600px"
      label-width="auto"
      class="demo-ruleForm"
  >

    <el-form-item label="用户名" prop="userName">
      <el-input v-model="registerForm.userName" type="text" autocomplete="off"/>
    </el-form-item>

    <el-form-item label="密码" prop="password">
      <el-input v-model="registerForm.password" type="password" autocomplete="off"/>
    </el-form-item>

    <el-form-item label="名" prop="first_name">
      <el-input v-model="registerForm.first_name" type="text" autocomplete="off"/>
    </el-form-item>

    <el-form-item label="姓" prop="last_name">
      <el-input v-model="registerForm.last_name" type="text" autocomplete="off"/>
    </el-form-item>

    <el-form-item label="邮箱" prop="email">
      <el-input v-model="registerForm.email" type="text" autocomplete="off"/>
    </el-form-item>

    <el-form-item label="头像（URL）" prop="avatar">
      <el-input v-model="registerForm.avatar" type="text" autocomplete="off"/>
    </el-form-item>

    <el-form-item>
      <el-button type="success" @click="submitForm(ruleFormRef)"
      >注册
      </el-button
      >
      <el-button type="primary" @click="jumpToLogin()"
      >登录
      </el-button
      >
    </el-form-item>

  </el-form>
</template>

<style scoped>


</style>