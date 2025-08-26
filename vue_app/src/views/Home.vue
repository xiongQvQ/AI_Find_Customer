<template>
  <div class="home">
    <el-card class="welcome-card">
      <template #header>
        <h1>🤖 AI客户发现工具</h1>
        <p class="subtitle">智能化B2B客户开发与分析平台</p>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="feature-list">
            <h3>✨ 核心功能</h3>
            <ul>
              <li>🔍 智能公司搜索与筛选</li>
              <li>📧 自动提取联系信息</li>
              <li>👥 关键决策者识别</li>
              <li>🤖 AI驱动的匹配分析</li>
            </ul>
          </div>
        </el-col>
        
        <el-col :span="12">
          <div class="quick-start">
            <h3>🚀 快速开始</h3>
            <el-steps direction="vertical" :active="0">
              <el-step title="配置API密钥" description="设置搜索和AI分析所需的API" />
              <el-step title="开始智能搜索" description="描述您的目标客户需求" />
              <el-step title="查看分析结果" description="获取AI评分和推荐结果" />
              <el-step title="导出客户数据" description="下载CSV/JSON格式数据" />
            </el-steps>
          </div>
        </el-col>
      </el-row>
      
      <el-divider />
      
      <el-row :gutter="20" class="action-cards">
        <el-col :span="8">
          <el-card shadow="hover" class="action-card">
            <template #header>
              <el-icon><Search /></el-icon>
              <span>智能搜索</span>
            </template>
            <p>使用AI驱动的智能搜索，快速找到符合您需求的目标客户</p>
            <el-button type="primary" @click="$router.push('/intelligent-search')">
              开始搜索
            </el-button>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card shadow="hover" class="action-card">
            <template #header>
              <el-icon><OfficeBuilding /></el-icon>
              <span>公司搜索</span>
            </template>
            <p>传统关键词搜索，按行业、地区等条件筛选目标公司</p>
            <el-button @click="$router.push('/company-search')">
              公司搜索
            </el-button>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card shadow="hover" class="action-card">
            <template #header>
              <el-icon><User /></el-icon>
              <span>员工搜索</span>
            </template>
            <p>精准找到目标公司的关键决策者和联系人</p>
            <el-button @click="$router.push('/employee-search')">
              员工搜索
            </el-button>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card shadow="hover" class="action-card">
            <template #header>
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </template>
            <p>配置API密钥、LLM提供商和其他系统设置</p>
            <el-button @click="$router.push('/settings')">
              进入设置
            </el-button>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script>
import { Search, OfficeBuilding, User, Setting } from '@element-plus/icons-vue'

export default {
  name: 'Home',
  components: {
    Search,
    OfficeBuilding,
    User,
    Setting
  }
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 20px;
}

.subtitle {
  color: #666;
  margin: 10px 0;
  font-size: 16px;
}

.feature-list ul {
  list-style: none;
  padding: 0;
}

.feature-list li {
  padding: 8px 0;
  font-size: 16px;
}

.quick-start {
  padding-left: 20px;
}

.action-cards {
  margin-top: 20px;
}

.action-card {
  text-align: center;
  height: 200px;
}

.action-card .el-card__header {
  text-align: center;
  font-weight: bold;
}

.action-card .el-icon {
  margin-right: 8px;
  font-size: 18px;
}
</style>