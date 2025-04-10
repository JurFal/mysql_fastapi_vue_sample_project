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
    }
  }
})