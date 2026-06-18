import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Upload',
      component: () => import('@/views/UploadPage.vue'),
    },
    {
      path: '/Result',
      name: 'Result',
      component: () => import('@/views/ResultPage.vue'),
    },
  ],
})

export default router
