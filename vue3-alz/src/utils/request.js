import { useAuthStore } from "@/stores/auth";
import axios from "axios";
import { ElMessage } from "element-plus";

// 1. 创建axios实例
const httpRequest = axios.create({
    baseURL: 'http://localhost:8000',
    timeout: 20000
})

// 2.请求拦截器
httpRequest.interceptors.request.use((config) => {
    const authStore = useAuthStore
    if (authStore.token) {
        config.headers['x-token'] = authStore.token
    }
    return config
}, (error) => { return Promise.reject(error) })

// 3. 响应拦截器 统一处理错误
httpRequest.interceptors.response.use((response) => {
    return response
}, (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
})

export default httpRequest