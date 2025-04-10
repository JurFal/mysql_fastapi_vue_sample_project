<script setup lang="ts">
import {onBeforeMount, ref, reactive} from "vue";
import {GetUserInfoList} from "@/request/api";
import {useRouter} from "vue-router";
import { ElMessageBox, ElMessage } from 'element-plus';
// 导入用户存储
import {useUserstore} from '@/store/user';

// 导入删除用户和验证密码的API
import { DeleteUserByUsername, VerifyPassword } from "@/request/api";

// 获取用户存储
const userStore = useUserstore();

interface User {
  userName: string
  first_name: string
  last_name: string
  email: string
  avatar: string
}

const tableData = ref<User[]>([]);

let currentPage = ref(1);
let pageSize = ref(10);
let total = ref(100);

const router = useRouter()

onBeforeMount(async () => {
  let res = await GetUserInfoList({
    skip: (currentPage.value - 1) * pageSize.value,
    limit: pageSize.value,
  })
  res.users.forEach(item => {
    tableData.value.push({
      userName: item.username,
      first_name: item.first_name,
      last_name: item.last_name,
      email: item.email,
      avatar: item.avatar
    });
  });
  total.value = Math.ceil(res.total / pageSize.value)
  console.log('total_pages.value:',total.value)
})


const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage;
  fetchData();
};
const fetchData = async () => {
  // 在这里调用 API 获取数据，使用 currentPage 作为参数
  let res = await GetUserInfoList({
    skip: (currentPage.value - 1) * pageSize.value,
    limit: pageSize.value,
  })
  tableData.value=[]
  res.users.forEach(item => {
    tableData.value.push({
      userName: item.username,
      first_name: item.first_name,
      last_name: item.last_name,
      email: item.email,
      avatar: item.avatar
    });
  });
  total.value = Math.ceil(res.total / pageSize.value)
};

const handleClick = (username: string) => {
  console.log(username)
  router.push({name: 'checkUserDetail', params: {username: username}})
};


// 使用代理服务处理图片URL
const getProxiedImageUrl = (url: string) => {
  if (!url) return '';

  // 使用自建的后端代理
  return `/users_api/proxy/image?url=${encodeURIComponent(url)}`;
  
};

// 图片加载错误处理
const handleImageError = (e: Event) => {
  console.error('图片加载失败:', e);
  // 可以在这里添加额外的错误处理逻辑
};

// 添加密码验证表单
const passwordForm = reactive({
  password: ''
});

// 添加删除用户的方法
const handleDelete = (username: string) => {
  // 首先弹出密码验证对话框
  ElMessageBox.prompt(
    `请输入用户 "${username}" 的密码进行验证`,
    '安全验证',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputType: 'password',
      inputPlaceholder: '请输入密码',
      inputValidator: (value) => {
        if (!value) {
          return '密码不能为空';
        }
        return true;
      },
      type: 'warning',
    }
  )
    .then(async ({ value: password }) => {
      try {
        // 验证密码
        await VerifyPassword(username, password);
        
        // 密码验证成功后，再次确认删除操作
        return ElMessageBox.confirm(
          `密码验证成功，确定要删除用户 "${username}" 吗？此操作不可恢复。`,
          '警告',
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'warning',
            confirmButtonClass: 'el-button--danger', // 添加这一行使确认按钮显示为危险样式
          }
        );
      } catch (error) {
        console.error('密码验证失败:', error);
        ElMessage({
          type: 'error',
          message: '密码验证失败，无法删除用户',
        });
        throw new Error('密码验证失败');
      }
    })
    .then(async () => {
      try {
        // 执行删除操作
        await DeleteUserByUsername(username);
        ElMessage({
          type: 'success',
          message: '删除成功',
        });
        
        // 判断是否删除的是当前登录用户
        if (username === userStore.userName) {
          // 如果是当前登录用户，清除登录状态并跳转到登录页
          userStore.logout();
          router.push('/');
        } else {
          // 如果不是当前登录用户，只需重新加载数据
          fetchData();
        }
      } catch (error) {
        console.error('删除用户失败:', error);
        ElMessage({
          type: 'error',
          message: '删除失败，请稍后重试',
        });
      }
    })
    .catch((err) => {
      // 忽略密码验证失败的错误，因为已经显示了错误消息
      if (err.message !== '密码验证失败') {
        ElMessage({
          type: 'info',
          message: '已取消删除',
        });
      }
    });
};
</script>

<template>
  <el-row>
    <el-col :span="24">
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="userName" label="用户名" width="180"/>
        <el-table-column prop="first_name" label="名" width="180"/>
        <el-table-column prop="last_name" label="姓" width="180"/>
        <el-table-column prop="email" label="邮箱" width="360"/>
        <el-table-column label="头像" width="180">
          <template v-slot:default="scope">
            <div @click.stop class="avatar-container">
              <el-image 
                style="width: 50px; height: 50px; border-radius: 50%;" 
                :src="scope.row.avatar" 
                fit="cover"
                :preview-src-list="[scope.row.avatar]"
                :preview-teleported="true"
                :initial-index="0"
                @error="handleImageError">
                <template #error>
                  <div class="image-error">
                    <el-avatar :size="50">{{ scope.row.userName.charAt(0).toUpperCase() }}</el-avatar>
                  </div>
                </template>
              </el-image>
            </div>
          </template>
        </el-table-column>
        <el-table-column fixed="right" label="操作" min-width="180">
          <template v-slot:default="scope">
            <el-button link type="primary" size="small" @click="handleClick(scope.row.userName)">
              详细信息
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(scope.row.userName)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-col>
  </el-row>

  <el-pagination
      @current-change="handleCurrentChange"
      :current-page="currentPage"
      :page-size="pageSize"
      layout="prev, pager, next"
      :total="total"
  />

</template>

<style scoped>
.image-error {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 50px;
  height: 50px;
  background-color: #f0f2f5;
  border-radius: 50%;
}

.avatar-container {
  display: inline-block;
  cursor: pointer;
  z-index: 1;
}
</style>