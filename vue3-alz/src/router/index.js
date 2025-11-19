import PredictView from '@/views/PredictView.vue'
import TrainView from '@/views/TrainView.vue'
import Home from '@/views/Home.vue'
import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import HistoryView from '@/views/HistoryView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: Home
    },
    {
      path: '/predict',
      component: PredictView
    },
    {
      path: '/train',
      component: TrainView
    },
    {
      path: '/login',
      component: LoginView
    },
    {
      path: '/history',
      component: HistoryView
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const publicPages = ['/', '/login']  // 无需登录就能访问的路由
  const authRequired = !publicPages.includes(to.path)
  const auth = useAuthStore()
  if (authRequired && !auth.isLoggedIn) {
    alert('请先登录')
    next('/login')
  } else {
    next()
  }
})
export default router
