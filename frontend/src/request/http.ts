import axios from 'axios'
import {useUserstore} from '@/store/user'
import { ElMessage } from 'element-plus'
import router from '@/router' // 添加这一行导入路由实例

// 创建axios实例
const request = axios.create({
    baseURL: '',// 所有的请求地址前缀部分
    timeout: 80000, // 请求超时时间(毫秒)
    withCredentials: true,// 异步请求携带cookie
    headers: {
        'Content-Type': 'application/json',
    }
})
request.defaults.withCredentials = true;
// request拦截器
request.interceptors.request.use(
    request => {
        const userStore=useUserstore()
        if (userStore.token !== 'token') {
            request.headers.Authorization = `Bearer ${userStore.token}`
        }
        return request
    },
    error => {
        return Promise.reject(error)
    }
)

// response 拦截器
request.interceptors.response.use(
    response => {
        // 对响应数据做点什么
        return response.data
    },
    error => {
        // 对响应错误做点什么
        return Promise.reject(error)
    }
)

// 创建 axios 实例
const service = axios.create({
  baseURL: '/api',
  timeout: 50000
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    if (token) {
      // 将 token 添加到请求头
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    return response
  },
  async error => {
    if (error.response && error.response.status === 401) {
      // token 过期，尝试刷新 token
      try {
        const refreshToken = localStorage.getItem('refreshToken')
        if (refreshToken) {
          const res = await axios.post('/api/auth/refresh', { refreshToken })
          // 保存新 token
          localStorage.setItem('token', res.data.token)
          localStorage.setItem('refreshToken', res.data.refreshToken)
          
          // 重新发送之前失败的请求
          const config = error.config
          config.headers['Authorization'] = `Bearer ${res.data.token}`
          return service(config)
        }
      } catch (refreshError) {
        // 刷新 token 失败，需要重新登录
        ElMessage.error('登录已过期，请重新登录')
        // 现在可以正确使用 router 变量
        router.push('/')
      }
    }
    return Promise.reject(error)
  }
)

export default request