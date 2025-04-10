<script setup lang="ts">
import {onBeforeMount, ref} from "vue";
import {GetUserInfoList} from "@/request/api";
import {useRouter} from "vue-router";
import { ElMessageBox, ElMessage } from 'element-plus';

// 导入删除用户的API
import { DeleteUserByUsername } from "@/request/api";

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

// 添加删除用户的方法
const handleDelete = (username: string) => {
  ElMessageBox.confirm(
    `确定要删除用户 "${username}" 吗？此操作不可恢复。`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await DeleteUserByUsername(username);
        ElMessage({
          type: 'success',
          message: '删除成功',
        });
        // 重新加载数据
        fetchData();
      } catch (error) {
        console.error('删除用户失败:', error);
        ElMessage({
          type: 'error',
          message: '删除失败，请稍后重试',
        });
      }
    })
    .catch(() => {
      ElMessage({
        type: 'info',
        message: '已取消删除',
      });
    });
};
</script>

<template>
  <el-row>
    <el-col :span="24">
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="userName" label="用户名" width="180"/>
        <el-table-column prop="first_name" label="姓" width="180"/>
        <el-table-column prop="last_name" label="名" width="180"/>
        <el-table-column prop="email" label="邮箱" width="360"/>
        <el-table-column label="头像" width="180">
          <template v-slot:default="scope">
            <el-image 
              style="width: 50px; height: 50px; border-radius: 50%;" 
              :src="getProxiedImageUrl(scope.row.avatar)" 
              fit="cover"
              :preview-src-list="[getProxiedImageUrl(scope.row.avatar)]"
              @error="handleImageError">
              <template #error>
                <div class="image-error">
                  <el-avatar :size="50">{{ scope.row.userName.charAt(0).toUpperCase() }}</el-avatar>
                </div>
              </template>
            </el-image>
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
</style>