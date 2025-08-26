<template>
  <el-container class="layout-container">
    <el-aside width="250px">
      <el-menu
        default-active="/"
        class="sidebar-menu"
        :router="true"
        background-color="#545c64"
        text-color="#fff"
        active-text-color="#ffd04b"
      >
        <div class="logo">
          <h2>🤖 AI客户发现</h2>
        </div>
        
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <span>主页</span>
        </el-menu-item>
        
        <el-menu-item index="/intelligent-search">
          <el-icon><Search /></el-icon>
          <span>智能搜索</span>
        </el-menu-item>
        
        <el-menu-item index="/company-search">
          <el-icon><OfficeBuilding /></el-icon>
          <span>公司搜索</span>
        </el-menu-item>
        
        <el-menu-item index="/employee-search">
          <el-icon><User /></el-icon>
          <span>员工搜索</span>
        </el-menu-item>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script>
import { House, Search, OfficeBuilding, User, Setting } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    House,
    Search,
    OfficeBuilding,
    User,
    Setting
  }
}
</script>

<style>
body {
  margin: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.layout-container {
  height: 100vh;
}

.sidebar-menu {
  height: 100vh;
  border-right: none;
}

.logo {
  text-align: center;
  padding: 20px 0;
  border-bottom: 1px solid #434a50;
  margin-bottom: 10px;
}

.logo h2 {
  color: #fff;
  margin: 0;
  font-size: 18px;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>