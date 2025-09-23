import DetectView from '@/views/DetectView.vue'
import TrainView from '@/views/TrainView.vue'
import Home from '@/views/Home.vue'
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: Home,
    },
    {
      path: '/detect',
      component: DetectView
    },
    {
      path: '/train',
      component: TrainView
    }
  ]
})

export default router
