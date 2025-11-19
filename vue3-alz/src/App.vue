<script setup>
import { KeepAlive } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const onLogout = () => {
  auth.logout()
  router.push('/login')
  alert('用户已注销')
}
</script>

<template>
    <nav class="sidenav">
     <div class="sidenav-title">阿尔茨海默诊断系统</div>

     <div class="nav-wrapper">
      <ul class="main-nav">
        <li>
          <RouterLink to="/" exact-active-class="nav-active" :class="{ 'nav-link': true }">
            首页
          </RouterLink>
        </li>
        
        <li>
            <RouterLink to="/predict" active-class="nav-active" :class="{ 'nav-link': true }">
              目标检测
            </RouterLink>
        </li>
        <li>
          <RouterLink to="/history" active-class="nav-active" :class="{ 'nav-link': true }">
            检测记录
          </RouterLink>
        </li>
        <li>
            <RouterLink to="/train" active-class="nav-active" :class="{ 'nav-link': true }">
              模型训练
            </RouterLink>
        </li>
      </ul>
     </div>

     <ul class="auth-nav">
        <li>
          <RouterLink to="/login" active-class="nav-active" :class="{ 'nav-link': true }">
            {{ auth.username ? auth.username : '请先登录' }}
          </RouterLink>
        </li>

        <li>
          <a @click="onLogout" :class="{ 'nav-link': true }">
            注销
          </a>
        </li>
     </ul>


    </nav>
    
    <div class="main-content">
        <RouterView v-slot="{ Component }">
          <KeepAlive>
            <component :is="Component" :key="$route.name" />
          </KeepAlive>
        </RouterView>
    </div>

    <footer class="footer">
        <div class="footer-content">
            <span>基于YOLOv8的阿尔茨海默症辅助诊断系统 | 系统检测结果仅供参考</span>
        </div>
    </footer>
</template>

<style>
 body {
    margin: 0 auto;
    max-width: 1800px;
    background: #E4E9F7;
 }

 @media screen and (max-width: 960px) { 
    body {
        max-width: 950px;
    }
}

.main-content{
    margin-left: 250px;
    padding: 20px;
    min-height: 100vh;
    box-sizing: border-box;
}

.sidenav {
  width: 250px;
  height: 100vh;
  padding: 0 10px;
  left: 0;
  top: 0;
  position: fixed;
  display: flex;
  flex-direction: column;
  background: #F6F5FF;
  color: #fff;
  flex-direction: column;
  align-items: center;
  padding-bottom: 40px;
}
.nav-wrapper{
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  width: 100%;
}
.sidenav-title {
  font-size: 22px;
  font-weight: bold;
  letter-spacing: 2px;
  height: 60px;
  align-items: center;
  display: flex;
  justify-content: center;
  width: 100%;
  color: #695CFE;
  background: #d4cbff;
  border-radius: 8px;
  margin-top: 18px;
  padding: 5px;
}
.sidenav ul {
  list-style: none;
  padding: 0;
  margin: 0;
  width: 100%;
}
.sidenav li {
  width: 100%;
  text-align: center;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.5s;
  color: #707070;
  position: relative;
  font-size: 18px;
}
.sidenav li a {
  display: block;
  width: 100%;
  height: 100%;
  margin: 20px 0;
  padding: 10px;
  color: inherit;
  text-decoration: none;
  font-weight: 500;
  border-radius: 8px;
}
.nav-link:hover {
  background: #695CFE;
  color: #DDD;
}
.nav-active {
  background: #695CFE;
  color: #DDD !important;
}

.footer {
  width: 100%;
  background: #4b2d2d;
  color: #fff;
  padding: 12px 0;
  text-align: center;
  position: fixed;
  left: 0;
  bottom: 0;
  z-index: 10;
}
.footer-content {
  font-size: 15px;
  letter-spacing: 1px;
}

h2 {
  font-size: 24px;
  color: #2c3e50; 
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 3px solid #3498db; 
  grid-column: 1 / -1;
  font-weight: bold;
}

</style>
