import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  // 1.定义状态(state) 初始化时尝试从localStorage读取
  const token = ref(localStorage.getItem('auth_token') || '')
  const username = ref(localStorage.getItem('auth_username') || '')

  // 2.定义动作(actions)
  const isLoggedIn = computed(() => !!token.value)

  const setAuth = (newToken, newUsername) => {
    token.value = newToken
    username.value = newUsername
  }

  const logout = () => {
    token.value = ''
    username.value = ''
  }

  // 3.使用watch自动处理副作用
  // 只要token发生变化（无论是登录、注销还是初始化），都会自动执行
  watch(token, (newToken) => {
    if (newToken) {
      localStorage.setItem('auth_token', newToken)
      axios.defaults.headers.common['x-token'] = newToken
    } else {
      localStorage.removeItem('auth_token')
      delete axios.defaults.headers.common['x-token']
    }
  }, { immediate: true })  // immediate: true 保证刷新页面时也会立即执行一次

  watch(username, (newName) => {
    if (newName) localStorage.setItem('auth_username', newName)
    else localStorage.removeItem('auth_username')
  }, { immediate: true })

  return { token, username, isLoggedIn, setAuth, logout }
})