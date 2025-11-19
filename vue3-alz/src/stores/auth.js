import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '',      
    username: ''    
  }),
  getters: {
    isLoggedIn: (state) => !!state.token
  },
  actions: {
    setAuth(token, username) {
      this.token = token || ''
      this.username = username || ''
      
      localStorage.setItem('auth_token', this.token)
      localStorage.setItem('auth_username', this.username)
      // 把 token 注入 axios header 便于后端校验
      if (this.token) axios.defaults.headers.common['x-token'] = this.token
      else delete axios.defaults.headers.common['x-token']
    },
    logout() {
      this.token = ''
      this.username = ''
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_username')
      delete axios.defaults.headers.common['x-token']
    },
    initFromStorage() {
      // 页面加载时从 localStorage 恢复
      const t = localStorage.getItem('auth_token')
      const u = localStorage.getItem('auth_username')
      if (t) {
        this.token = t
        this.username = u || ''
        axios.defaults.headers.common['x-token'] = t
      }
    }
  }
})