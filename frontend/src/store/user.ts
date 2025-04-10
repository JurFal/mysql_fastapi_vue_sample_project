import { defineStore } from 'pinia'

export const useUserstore = defineStore('user', {
  state: () => ({
    userName: localStorage.getItem('userName') || '',
    token: localStorage.getItem('token') || '',
    avatar: localStorage.getItem('avatar') || ''
  }),
  actions: {
    setUserName(userName: string) {
      this.userName = userName
      localStorage.setItem('userName', userName)
    },
    setToken(token: string) {
      this.token = token
      localStorage.setItem('token', token)
    },
    setAvatar(avatar: string) {
      this.avatar = avatar
      localStorage.setItem('avatar', avatar)
    },
    logout() {
      this.token = ''
      this.userName = ''
      this.avatar = ''
      localStorage.removeItem('token')
      localStorage.removeItem('userName')
      localStorage.removeItem('avatar')
      
      // 清除所有与用户相关的本地存储
      // 清除可能存在的其他用户相关数据
      const userRelatedKeys = Object.keys(localStorage).filter(key => 
        key.includes('paper-writing') || 
        key.includes('user-') || 
        key.includes('session')
      )
      
      userRelatedKeys.forEach(key => {
        localStorage.removeItem(key)
      })
      
      // 添加一个标记表示已登出
      sessionStorage.setItem('userLoggedOut', 'true')
    },
    
    // 添加登录方法，同时设置用户名、令牌和头像
    login(userData: { userName: string; token: string; avatar: string }) {
      this.setUserName(userData.userName)
      this.setToken(userData.token)
      this.setAvatar(userData.avatar)
      // 清除登出标记
      sessionStorage.removeItem('userLoggedOut')
    },
    
    // 添加检查是否真正登录的方法
    isLoggedIn() {
      // 检查是否有token且没有登出标记
      return !!this.token && !sessionStorage.getItem('userLoggedOut')
    },
    
    // 添加清除用户信息的方法（用于删除用户时）
    clearUserInfo() {
      this.logout()
    }
  }
})