<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const username = ref('')
const password = ref('')
const loading = ref(false)
const router = useRouter()
const auth = useAuthStore()

const onLogin = async () => {
    if (!username.value || !password.value) {
        alert('请输入用户名和密码')
        return
    }
    loading.value = true
    try {
        const res = await axios.post('http://localhost:8000/login', {
            username: username.value,
            password: password.value
        })
        if (res.data && res.data.success) {
            auth.setAuth(res.data.token, username.value)
            router.push('/predict')
        } else {
            alert('登陆失败')
        }
    } catch (err) {
        const msg = err.response?.data?.detail || err.message || '登录请求错误'
        alert('登录失败: ' + msg)
    } finally {
        loading.value = false
    }
}
</script>

<template>
  <div class="login">
    <div class="login-card">
        <h1>Login</h1>
        <div class="input-box">
            <img src="/username.png" alt="username" class="icon">
            <input id="username" type="text" v-model="username" required />
            <label>Username</label>
        </div>
        <div class="input-box">
            <img src="/password.png" alt="password" class="icon">
            <input id="password" type="password" v-model="password" required />
            <label>Password</label>
        </div>

        <button @click="onLogin" class="btn" :disabled="loading">
            {{ loading ? '登陆中...' : '登录' }}
        </button>
    </div>
  </div>
</template>

<style scoped>
.login{
    position: absolute;
    top: 0;
    left: 250px;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #282a37;
    background-size: cover;
    background-position: center;
}
h1{
    font-size: 2.3em;
    font-weight: bold;
    text-align: center;
    color: #fff;
    margin: 0 0 20px 0;
}
.login-card{
    width: 400px;
    height: 450px;
    background: #3e404d;
    border: 2px solid rgba(255, 255, 255, 0.5);
    border-radius: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(15px);
    padding: 0 20px;
}
.login-card:hover{
    box-shadow: 0 0 40px rgba(255, 255, 255, 0.5);
    background: #46474e;
}

.input-box{
    position: relative;
    width: 310px;
    margin: 30px 0;
    border-bottom: 2px solid #fff;
}
.input-box input{
    width: 100%;
    height: 50px;
    background: transparent;
    outline: none;
    border: none;
    font-size: 1em;
    color: #fff;
    padding: 0 40px 0 5px;
    font-size: 1.1em;
    font-weight: 500;
}
.input-box label{
    position: absolute;
    top: 50%;
    left: 5px;
    transform: translateY(-50%);
    font-size: 1.1em;
    font-weight: 500;
    color: #fff;
    pointer-events: none;
    transition: 0.5s;
}
.input-box input:focus ~ label,
.input-box input:valid ~ label{
    top: -5px;
}
.input-box .icon{
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    width: 24px;
    height: 24px;
    object-fit: contain;
}
.btn{
    width: 310px;
    height: 40px;
    background: #fff;
    outline: none;
    border: none;
    border-radius: 40px;
    font-weight: 600;
    cursor: pointer;
    font-size: 1.2em;
    font-weight: 500;
    margin-top: 10px;
}
.btn:hover{
    background: #ffffea;
}

</style>