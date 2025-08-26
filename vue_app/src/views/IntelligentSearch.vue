<template>
  <div class="intelligent-search">
    <el-card class="search-card">
      <template #header>
        <h2>🔍 LangGraph智能搜索</h2>
        <p>描述您的搜索需求，AI将帮您找到最匹配的目标客户</p>
      </template>
      
      <!-- 搜索表单 -->
      <el-form v-if="!searching && !searchResults" :model="searchForm" label-width="140px">
        <el-form-item label="搜索描述">
          <el-input
            v-model="searchForm.query"
            type="textarea"
            :rows="4"
            placeholder="例如: 我想搜索深圳的智能机器人创业公司，或者搜索某公司的技术总监，或者新能源汽车行业的销售经理"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="基础选项">
          <el-checkbox v-model="searchForm.aiEvaluation">启用AI评估</el-checkbox>
          <el-checkbox v-model="searchForm.employeeSearch">搜索员工信息</el-checkbox>
          <el-checkbox v-model="searchForm.enableOptimization">启用搜索优化</el-checkbox>
        </el-form-item>

        <el-form-item label="搜索策略" v-if="searchForm.employeeSearch">
          <el-select v-model="searchForm.preferredStrategy" placeholder="自动选择最佳策略">
            <el-option label="自适应策略 (推荐)" value="adaptive" />
            <el-option label="公司优先策略" value="company_first" />
            <el-option label="员工优先策略" value="employee_first" />
            <el-option label="平衡策略" value="balanced" />
          </el-select>
        </el-form-item>

        <el-form-item label="搜索模式">
          <el-radio-group v-model="searchForm.searchMode">
            <el-radio label="enhanced">增强搜索 (LLM驱动)</el-radio>
            <el-radio label="async">异步搜索 (实时进度)</el-radio>
            <el-radio label="standard">标准搜索</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            @click="startSearch"
            :disabled="!searchForm.query.trim()"
            size="large"
          >
            <el-icon><Search /></el-icon>
            开始智能搜索
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 搜索进行中 -->
      <div v-if="searching" class="search-progress">
        <el-result icon="loading" title="正在进行智能搜索..." sub-title="请稍候，AI正在分析您的需求并搜索匹配的客户">
          <template #extra>
            <el-progress :percentage="searchProgress" :format="formatProgress" :status="progressStatus" />
            <div class="progress-details">
              <p class="progress-info">
                <el-tag :type="getStatusTagType(searchStatus)" v-if="searchStatus">
                  {{ getStatusText(searchStatus) }}
                </el-tag>
                {{ currentStep }}
              </p>
              
              <!-- 实时搜索统计 -->
              <div v-if="searchStats" class="search-stats">
                <el-row :gutter="20">
                  <el-col :span="8" v-if="searchStats.companies_found !== undefined">
                    <el-statistic title="已找到公司" :value="searchStats.companies_found" />
                  </el-col>
                  <el-col :span="8" v-if="searchStats.qualified_companies !== undefined">
                    <el-statistic title="符合条件" :value="searchStats.qualified_companies" />
                  </el-col>
                  <el-col :span="8" v-if="searchStats.employees_found !== undefined">
                    <el-statistic title="找到员工" :value="searchStats.employees_found" />
                  </el-col>
                </el-row>
              </div>

              <!-- 搜索策略信息 -->
              <div v-if="searchStrategy" class="strategy-info">
                <el-alert 
                  :title="`使用策略: ${searchStrategy.name}`" 
                  :description="searchStrategy.description" 
                  type="info" 
                  :closable="false"
                />
              </div>
            </div>
            
            <el-button @click="cancelSearch" type="warning">取消搜索</el-button>
          </template>
        </el-result>
      </div>
      
      <!-- 搜索结果 -->
      <div v-if="searchResults && !searching" class="search-results">
        <div class="results-header">
          <h3>搜索结果</h3>
          <div class="results-stats">
            <el-tag type="success">找到 {{ searchResults.total_companies_found }} 家公司</el-tag>
            <el-tag type="primary" v-if="searchResults.qualified_companies_count">
              {{ searchResults.qualified_companies_count }} 家符合条件
            </el-tag>
            <el-button type="primary" @click="newSearch">新搜索</el-button>
          </div>
        </div>
        
        <!-- 合格公司列表 -->
        <div v-if="qualifiedCompanies.length > 0" class="qualified-companies">
          <h4>💎 推荐公司 (AI评分 ≥ 70)</h4>
          <el-row :gutter="20">
            <el-col :span="12" v-for="(company, index) in qualifiedCompanies" :key="index">
              <el-card class="company-card qualified" shadow="hover">
                <template #header>
                  <div class="company-header">
                    <h4>{{ company.name }}</h4>
                    <el-tag type="success" v-if="company.ai_score">
                      AI评分: {{ company.ai_score }}
                    </el-tag>
                  </div>
                </template>
                
                <div class="company-info">
                  <p v-if="company.industry"><strong>行业:</strong> {{ company.industry }}</p>
                  <p v-if="company.location"><strong>位置:</strong> {{ company.location }}</p>
                  <p v-if="company.size"><strong>规模:</strong> {{ company.size }}</p>
                  <p v-if="company.description" class="description">
                    <strong>描述:</strong> {{ company.description }}
                  </p>
                  <p v-if="company.ai_reason" class="ai-reason">
                    <strong>AI分析:</strong> {{ company.ai_reason }}
                  </p>
                </div>
                
                <div class="company-actions">
                  <el-button size="small" v-if="company.website_url" @click="openUrl(company.website_url)">
                    访问网站
                  </el-button>
                  <el-button size="small" v-if="company.linkedin_url" @click="openUrl(company.linkedin_url)">
                    LinkedIn
                  </el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
        
        <!-- 导出功能 -->
        <el-divider />
        <div class="export-section">
          <h4>📥 导出数据</h4>
          <el-button-group>
            <el-button @click="exportData('csv')" :icon="Download">导出CSV</el-button>
            <el-button @click="exportData('json')" :icon="Download">导出JSON</el-button>
          </el-button-group>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'

export default {
  name: 'IntelligentSearch',
  components: {
    Search,
    Download
  },
  setup() {
    const searchForm = ref({
      query: '',
      aiEvaluation: true,
      employeeSearch: false,
      enableOptimization: true,
      preferredStrategy: 'adaptive',
      searchMode: 'enhanced'  // enhanced, async, standard
    })
    
    const searching = ref(false)
    const searchProgress = ref(0)
    const progressStatus = ref('')
    const currentStep = ref('')
    const searchResults = ref(null)
    const searchStatus = ref('')
    const searchStats = ref(null)
    const searchStrategy = ref(null)
    const currentSearchId = ref('')
    let eventSource = null
    
    const qualifiedCompanies = computed(() => {
      if (!searchResults.value?.search_results?.companies) return []
      return searchResults.value.search_results.companies.filter(
        company => company.is_qualified
      )
    })
    
    const startSearch = async () => {
      if (!searchForm.value.query.trim()) {
        ElMessage.warning('请输入搜索描述')
        return
      }
      
      // 重置搜索状态
      resetSearchState()
      searching.value = true
      
      try {
        if (searchForm.value.searchMode === 'async') {
          await startAsyncSearch()
        } else if (searchForm.value.searchMode === 'enhanced') {
          await startEnhancedSearch()
        } else {
          await startStandardSearch()
        }
      } catch (error) {
        console.error('搜索失败:', error)
        ElMessage.error('搜索失败: ' + (error.response?.data?.detail || error.message))
        searching.value = false
      }
    }

    const startAsyncSearch = async () => {
      try {
        // 启动异步搜索
        const response = await axios.post('http://localhost:8000/async-search', {
          query: searchForm.value.query,
          ai_evaluation_enabled: searchForm.value.aiEvaluation,
          employee_search_enabled: searchForm.value.employeeSearch,
          preferred_strategy: searchForm.value.preferredStrategy,
          enable_optimization: searchForm.value.enableOptimization
        })

        currentSearchId.value = response.data.search_id
        currentStep.value = '搜索已启动，连接实时进度...'
        
        // 建立SSE连接获取实时进度
        setupEventSource(response.data.search_id)
        
      } catch (error) {
        throw error
      }
    }

    const startEnhancedSearch = async () => {
      try {
        searchProgress.value = 10
        currentStep.value = '启动增强搜索...'
        
        const response = await axios.post('http://localhost:8000/enhanced-search', {
          query: searchForm.value.query,
          ai_evaluation_enabled: searchForm.value.aiEvaluation,
          employee_search_enabled: searchForm.value.employeeSearch,
          preferred_strategy: searchForm.value.preferredStrategy,
          enable_optimization: searchForm.value.enableOptimization,
          max_optimization_rounds: 2
        })

        searchProgress.value = 100
        searchResults.value = response.data
        currentStep.value = '搜索完成!'
        
        const totalCompanies = response.data.search_results?.qualified_companies_count || 0
        ElMessage.success(`增强搜索完成! 找到 ${totalCompanies} 家符合条件的公司`)
        
      } catch (error) {
        throw error
      } finally {
        searching.value = false
      }
    }

    const startStandardSearch = async () => {
      try {
        // 模拟搜索进度
        const progressSteps = [
          { progress: 20, step: '分析搜索需求...' },
          { progress: 40, step: '搜索公司信息...' },
          { progress: 60, step: 'AI评估分析中...' },
          { progress: 80, step: '整理搜索结果...' },
          { progress: 100, step: '搜索完成!' }
        ]
        
        for (const step of progressSteps) {
          await new Promise(resolve => setTimeout(resolve, 1000))
          searchProgress.value = step.progress
          currentStep.value = step.step
        }
        
        // 调用标准搜索API
        const response = await axios.post('http://localhost:8000/intelligent-search', {
          query: searchForm.value.query,
          ai_evaluation_enabled: searchForm.value.aiEvaluation,
          employee_search_enabled: searchForm.value.employeeSearch
        })
        
        searchResults.value = response.data
        const totalCompanies = response.data.search_results?.qualified_companies_count || 0
        ElMessage.success(`标准搜索完成! 找到 ${totalCompanies} 家符合条件的公司`)
        
      } catch (error) {
        throw error
      } finally {
        searching.value = false
      }
    }
    
    const setupEventSource = (searchId) => {
      // 清理之前的EventSource连接
      if (eventSource) {
        eventSource.close()
      }

      const url = `http://localhost:8000/async-search/${searchId}/progress`
      eventSource = new EventSource(url)

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          updateProgress(data)
        } catch (error) {
          console.error('解析进度数据失败:', error)
        }
      }

      eventSource.onerror = (error) => {
        console.error('EventSource连接错误:', error)
        ElMessage.error('实时进度连接失败')
        eventSource.close()
        
        // 尝试轮询获取结果
        pollForResults(searchId)
      }
    }

    const updateProgress = (data) => {
      searchStatus.value = data.status || ''
      currentStep.value = data.message || ''
      
      // 更新进度百分比
      const statusProgressMap = {
        'pending': 10,
        'analyzing': 20,
        'searching': 50,
        'evaluating': 70,
        'filtering': 85,
        'completed': 100,
        'failed': 0
      }
      
      searchProgress.value = statusProgressMap[data.status] || 0
      progressStatus.value = data.status === 'failed' ? 'exception' : ''
      
      // 更新实时统计
      if (data.data) {
        searchStats.value = {
          companies_found: data.data.companies_found,
          qualified_companies: data.data.qualified_companies,
          employees_found: data.data.employees_found
        }
        
        if (data.data.strategy) {
          searchStrategy.value = data.data.strategy
        }
      }

      // 搜索完成
      if (data.status === 'completed') {
        eventSource.close()
        fetchSearchResults(currentSearchId.value)
      } else if (data.status === 'failed') {
        eventSource.close()
        searching.value = false
        ElMessage.error(`搜索失败: ${data.message}`)
      }
    }

    const pollForResults = async (searchId) => {
      let attempts = 0
      const maxAttempts = 30
      
      const poll = async () => {
        try {
          const response = await axios.get(`http://localhost:8000/async-search/${searchId}/results`)
          searchResults.value = response.data
          searching.value = false
          
          const totalCompanies = response.data.search_results?.qualified_companies_count || 0
          ElMessage.success(`异步搜索完成! 找到 ${totalCompanies} 家符合条件的公司`)
        } catch (error) {
          attempts++
          if (attempts < maxAttempts && error.response?.status === 202) {
            setTimeout(poll, 2000) // 2秒后重试
          } else {
            searching.value = false
            ElMessage.error('获取搜索结果失败')
          }
        }
      }
      
      poll()
    }

    const fetchSearchResults = async (searchId) => {
      try {
        const response = await axios.get(`http://localhost:8000/async-search/${searchId}/results`)
        searchResults.value = response.data
        
        const totalCompanies = response.data.search_results?.qualified_companies_count || 0
        ElMessage.success(`异步搜索完成! 找到 ${totalCompanies} 家符合条件的公司`)
      } catch (error) {
        ElMessage.error('获取搜索结果失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        searching.value = false
      }
    }

    const resetSearchState = () => {
      searchProgress.value = 0
      progressStatus.value = ''
      currentStep.value = ''
      searchStatus.value = ''
      searchStats.value = null
      searchStrategy.value = null
      currentSearchId.value = ''
      
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
    }

    const cancelSearch = async () => {
      if (currentSearchId.value && searchForm.value.searchMode === 'async') {
        try {
          await axios.delete(`http://localhost:8000/async-search/${currentSearchId.value}`)
          ElMessage.info('搜索已取消')
        } catch (error) {
          console.error('取消搜索失败:', error)
        }
      }
      
      resetSearchState()
      searching.value = false
    }

    const getStatusTagType = (status) => {
      const statusTypes = {
        'pending': 'info',
        'analyzing': 'warning',
        'searching': 'primary',
        'evaluating': 'primary',
        'filtering': 'success',
        'completed': 'success',
        'failed': 'danger'
      }
      return statusTypes[status] || 'info'
    }

    const getStatusText = (status) => {
      const statusTexts = {
        'pending': '等待中',
        'analyzing': '分析中',
        'searching': '搜索中',
        'evaluating': '评估中',
        'filtering': '筛选中',
        'completed': '已完成',
        'failed': '失败'
      }
      return statusTexts[status] || status
    }
    
    const newSearch = () => {
      searchResults.value = null
      searchForm.value.query = ''
    }
    
    const formatProgress = (percentage) => {
      return `${percentage}%`
    }
    
    const openUrl = (url) => {
      window.open(url, '_blank')
    }
    
    const exportData = async (format) => {
      try {
        const response = await axios.get(`http://localhost:8000/export/${format}`, {
          params: { 
            search_id: searchResults.value?.search_id,
            type: 'qualified'
          }
        })
        
        // 触发下载
        const blob = new Blob([format === 'json' ? JSON.stringify(response.data, null, 2) : response.data])
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `search_results.${format}`
        a.click()
        window.URL.revokeObjectURL(url)
        
        ElMessage.success(`${format.toUpperCase()} 文件导出成功`)
      } catch (error) {
        ElMessage.error('导出失败: ' + error.message)
      }
    }
    
    return {
      searchForm,
      searching,
      searchProgress,
      progressStatus,
      currentStep,
      searchResults,
      searchStatus,
      searchStats,
      searchStrategy,
      qualifiedCompanies,
      startSearch,
      cancelSearch,
      newSearch,
      formatProgress,
      openUrl,
      exportData,
      getStatusTagType,
      getStatusText
    }
  }
}
</script>

<style scoped>
.intelligent-search {
  max-width: 1200px;
  margin: 0 auto;
}

.search-card {
  margin-bottom: 20px;
}

.search-progress {
  text-align: center;
  padding: 40px 20px;
}

.progress-details {
  margin: 20px 0;
  text-align: center;
}

.progress-info {
  margin: 15px 0;
  font-size: 16px;
  color: #606266;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.search-stats {
  margin: 20px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.strategy-info {
  margin: 15px 0;
  text-align: left;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-stats .el-tag {
  margin-right: 10px;
}

.qualified-companies {
  margin-bottom: 30px;
}

.company-card {
  margin-bottom: 20px;
  height: 100%;
}

.company-card.qualified {
  border-left: 4px solid #67c23a;
}

.company-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.company-header h4 {
  margin: 0;
  color: #303133;
}

.company-info p {
  margin: 8px 0;
  color: #606266;
}

.description {
  font-size: 14px;
  line-height: 1.4;
}

.ai-reason {
  background: #f0f9ff;
  padding: 10px;
  border-radius: 4px;
  font-size: 14px;
  border-left: 3px solid #409eff;
}

.company-actions {
  margin-top: 15px;
}

.export-section {
  text-align: center;
  padding: 20px 0;
}
</style>