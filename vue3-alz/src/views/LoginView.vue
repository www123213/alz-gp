<script setup>
import { ElButton, ElInput } from 'element-plus';
import { ref } from 'vue'

const input1 = ref('')
const input2 = ref('')
</script>

<template>
  <div class="login">
    <div class="login-card">
        <h2>用户登录</h2>
        <div class="input-group">
            <span class="label">用户名：</span>
            <ElInput v-model="input1" class="input-container" placeholder="请输入用户名" />
        </div>
        <div class="input-group">
            <span class="label">密码：</span>
            <ElInput v-model="input2" class="input-container" type="password" placeholder="请输入密码" show-password="" />
        </div>
        <div class="login-btn">
            <ElButton type="primary">登录</ElButton>
        </div>
    </div>
  </div>
</template>

<style scoped>
.login{
    min-height: calc(100vh - 80px);
    display: flex;
    align-items: center;
    justify-content: center;
}
h2{
    text-align: center;
}
.login-card{
    background-color: #f8f9fa;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(174, 174, 174, 0.5);
    flex: 0 0 auto;
}
.input-group{
    display: flex;
    align-items: center;
    margin: 10px 0;
}
.login-btn{
    text-align: center;
    margin-top: 20px;
}
.label{
    width: 60px;
    text-align: right;
    margin-right: 10px;
    color: #606266;
}
.input-container{
    width: 200px;
}
</style>