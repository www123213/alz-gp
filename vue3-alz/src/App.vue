<script setup>
import { KeepAlive } from 'vue';
import { RouterView } from 'vue-router'
</script>

<template>

    <nav class="sidenav">
     <div class="sidenav-title">阿尔茨海默诊断系统</div>
      <ul>
        <li>
            <RouterLink to="/" exact-active-class="nav-active" :class="{ 'nav-link': true }">
              首页
            </RouterLink>
        </li>
        <li>
            <RouterLink to="/detect" active-class="nav-active" :class="{ 'nav-link': true }">
              目标检测
            </RouterLink>
        </li>
        <li>
            <RouterLink to="/train" active-class="nav-active" :class="{ 'nav-link': true }">
              模型训练
            </RouterLink>
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
  padding: 0;
  left: 0;
  top: 0;
  position: fixed;
  display: flex;
  background: #2d3a4b;
  color: #fff;
  flex-direction: column;
  align-items: center;
}
.sidenav-title {
  font-size: 24px;
  font-weight: bold;
  letter-spacing: 2px;
  height: 60px;
  align-items: center;
  display: flex;
  justify-content: center;
  width: 100%;
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
  transition: background 0.2s;
  color: #06d6a0;
  position: relative;
}
.sidenav li a {
  display: block;
  width: 100%;
  height: 100%;
  padding: 20px 0;
  color: inherit;
  text-decoration: none;
}
.nav-link:hover {
  background: #3498db;
  color: #ffffff;
}
.nav-active {
  background: #3498db;
  color: #ffffff !important;
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
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 3px solid #3498db; 
  grid-column: 1 / -1;
  font-weight: bold;
}
</style>
