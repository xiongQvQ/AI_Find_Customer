<template>
  <div class="company-search">
    <el-card class="info-card">
      <template #header>
        <h2>🏢 传统公司搜索</h2>
        <p>使用关键词和筛选条件搜索目标公司</p>
      </template>
      
      <!-- 工作原理说明 -->
      <el-collapse v-model="activeCollapse">
        <el-collapse-item title="💡 工作原理" name="principle">
          <div class="principle-content">
            <h4>🎯 一句话概述</h4>
            <p>传统公司搜索通过关键词匹配和地域筛选，快速定位和收集目标行业的公司信息。</p>
            
            <h4>🔄 工作流程</h4>
            <el-steps :active="0" align-center>
              <el-step title="关键词设置" description="设置行业和地域关键词" icon="Setting" />
              <el-step title="搜索执行" description="通过搜索引擎获取结果" icon="Search" />
              <el-step title="结果过滤" description="按条件筛选和去重" icon="Filter" />
              <el-step title="信息整理" description="整理和展示公司信息" icon="DocumentCopy" />
            </el-steps>
            
            <h4>🔍 搜索类型</h4>
            <ul>
              <li><strong>通用搜索：</strong>使用Google搜索引擎，覆盖面更广，结果更全面</li>
              <li><strong>LinkedIn搜索：</strong>专注于职业社交平台，获取更精准的公司信息</li>
            </ul>
            
            <h4>🔧 关键技术</h4>
            <ul>
              <li><strong>关键词匹配：</strong>智能匹配行业和地域相关关键词</li>
              <li><strong>地理定位：</strong>根据国家代码和地域精准定位</li>
              <li><strong>结果去重：</strong>自动识别和清除重复的公司信息</li>
              <li><strong>数据清洗：</strong>清理格式化公司名称、地址等信息</li>
            </ul>
            
            <h4>💡 使用技巧</h4>
            <el-alert type="info" :closable="false">
              <ul>
                <li>使用具体的行业关键词，如“新能源汽车”而非“汽车”</li>
                <li>地域关键词可以是城市、省份或特定区域</li>
                <li>LinkedIn搜索适合找已建立业务模式的成熟公司</li>
                <li>通用搜索适合发现新兴公司和创业企业</li>
              </ul>
            </el-alert>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
    
    <el-card class="search-card">
      
      <el-form :model="searchForm" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="行业关键词">
              <el-input v-model="searchForm.industry" placeholder="例如: 新能源汽车" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="地区">
              <el-input v-model="searchForm.region" placeholder="例如: 北京" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="搜索类型">
              <el-select v-model="searchForm.searchType" style="width: 100%">
                <el-option label="通用搜索" value="general" />
                <el-option label="LinkedIn搜索" value="linkedin" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="国家代码">
              <el-select v-model="searchForm.gl" style="width: 100%">
                <el-option label="中国 (cn)" value="cn" />
                <el-option label="美国 (us)" value="us" />
                <el-option label="英国 (uk)" value="uk" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button type="primary" @click="search" :loading="searching">
            <el-icon><Search /></el-icon>
            开始搜索
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card v-if="results.length > 0" class="results-card">
      <template #header>
        <h3>搜索结果 ({{ results.length }} 家公司)</h3>
      </template>
      
      <el-table :data="results" style="width: 100%">
        <el-table-column prop="name" label="公司名称" width="200" />
        <el-table-column prop="industry" label="行业" width="150" />
        <el-table-column prop="location" label="位置" width="150" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="viewDetails(scope.row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Setting, Filter, DocumentCopy } from '@element-plus/icons-vue'

export default {
  name: 'CompanySearch',
  components: {
    Search, Setting, Filter, DocumentCopy
  },
  setup() {
    const activeCollapse = ref([])
    
    const searchForm = ref({
      industry: '',
      region: '',
      searchType: 'general',
      gl: 'cn'
    })
    
    const searching = ref(false)
    const results = ref([])
    
    const search = async () => {
      if (!searchForm.value.industry && !searchForm.value.region) {
        ElMessage.warning('请至少输入行业或地区关键词')
        return
      }
      
      searching.value = true
      
      try {
        // 这里应该调用后端API
        // 暂时使用模拟数据
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        results.value = [
          {
            name: '示例新能源公司',
            industry: '新能源',
            location: '北京',
            description: '专注于新能源汽车技术研发的公司'
          }
        ]
        
        ElMessage.success('搜索完成')
      } catch (error) {
        ElMessage.error('搜索失败: ' + error.message)
      } finally {
        searching.value = false
      }
    }
    
    const viewDetails = (company) => {
      ElMessage.info(`查看公司: ${company.name}`)
    }
    
    return {
      activeCollapse,
      searchForm,
      searching,
      results,
      search,
      viewDetails
    }
  }
}
</script>

<style scoped>
.company-search {
  max-width: 1200px;
  margin: 0 auto;
}

.info-card, .search-card {
  margin-bottom: 20px;
}

.principle-content {
  max-width: 800px;
}

.principle-content h4 {
  color: #409eff;
  margin: 20px 0 10px 0;
}

.principle-content ul {
  list-style-type: none;
  padding-left: 0;
}

.principle-content li {
  padding: 5px 0;
  line-height: 1.5;
}

.results-card {
  margin-top: 20px;
}
</style>