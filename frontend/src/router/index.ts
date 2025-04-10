import {createRouter, createWebHistory} from "vue-router";

import Login from '@/pages/Login.vue';
import Index from "@/pages/Index.vue";
import Test from "@/pages/Test.vue";
import CheckUserInfo from "@/components/CheckUserInfo.vue";
import Profile from "@/components/Profile.vue";
import AddUser from "@/components/AddUser.vue";
import Chat from "@/components/Chat.vue";
import Writing from "@/components/Writing.vue";
import Register from "@/pages/Register.vue";
import {useUserstore} from "@/store/user";

const routes =
    [
        {
            path: '/',
            name: 'Login',
            component: Login
        },
        {
            path: '/register',
            name: 'Register',
            component: Register
        },
        {
            path: '/index',
            name: 'Index',
            component: Index,
            meta: { requiresAuth: true }, // 添加需要认证的标记
            children: [
                {
                    path: '',
                    name:'IndexMain',
                    component: Profile,
                },
                {
                    path: 'checkUserInfo/:username',
                    name: 'checkUserDetail',
                    component: Profile,
                    props: true
                },
                {
                    path: 'checkUserInfo',
                    component: CheckUserInfo,
                },
                {
                    path: 'addUser',
                    component: AddUser,
                },
                {
                    path: 'modifyProfile',
                    component: AddUser,
                },
                {
                    path: 'chat',
                    component: Chat,
                },
                {
                    path: 'writing',
                    component: Writing,
                },
            ]

        },
        {
            path: '/test',
            name: 'Test',
            component: Test
        }
    ];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: routes
})

// 添加全局前置守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserstore()
  
  // 检查该路由是否需要登录
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!userStore.token) {
      next({
        path: '/',
      })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
