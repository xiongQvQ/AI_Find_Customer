<template>
  <div class="employee-search">
    <el-card class="info-card">
      <template #header>
        <h2>👥 员工搜索</h2>
        <p>根据公司信息，精准找到关键决策者和联系人</p>
      </template>
      
      <!-- 工作原理说明 -->
      <el-collapse v-model="activeCollapse">
        <el-collapse-item title="💡 工作原理" name="principle">
          <div class="principle-content">
            <h4>🎯 一句话概述</h4>
            <p>员工搜索模块通过AI技术和多数据源整合，帮您精准找到目标公司的关键决策者和联系人。</p>
            
            <h4>🔄 工作流程</h4>
            <el-steps :active="0" align-center>
              <el-step title="公司识别" description="验证公司官网域名" icon="OfficeBuilding" />
              <el-step title="数据检索" description="多源查询员工信息" icon="Search" />
              <el-step title="AI筛选" description="智能匹配目标职位" icon="UserFilled" />
              <el-step title="信息整合" description="去重验证联系方式" icon="Checked" />
            </el-steps>
            
            <h4>🛠️ 关键技术</h4>
            <ul>
              <li><strong>官网识别：</strong>自动验证并获取公司官方网站域名</li>
              <li><strong>多源整合：</strong>结合LinkedIn、商业数据库等多个数据源</li>
              <li><strong>职位匹配：</strong>使用NLP技术理解职位描述和匹配需求</li>
              <li><strong>联系验证：</strong>验证邮箱格式和有效性</li>
            </ul>
            
            <h4>💡 使用技巧</h4>
            <el-alert type="info" :closable="false">
              <ul>
                <li>输入完整的公司名称或官网域名可提高准确性</li>
                <li>职位描述可以使用中英文，如"销售总监"或"Sales Director"</li>
                <li>可以输入多个相关职位，用逗号分隔</li>
                <li>优先选择规模较大的公司，员工信息更完整</li>
              </ul>
            </el-alert>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
    
    <el-card class="search-card">
      <!-- 搜索表单 -->
      <el-form :model="searchForm" label-width="120px" v-if="!searching && !searchResults">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="公司名称" required>
              <el-input
                v-model="searchForm.companyName"
                placeholder="例如: 腾讯科技"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公司域名">
              <el-input
                v-model="searchForm.companyDomain"
                placeholder="例如: tencent.com (可选)"
                clearable
              />
              <div class="form-help">输入域名可提高搜索精度</div>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="目标职位" required>
          <el-input
            v-model="searchForm.targetPosition"
            placeholder="例如: CTO, 技术总监, Sales Manager"
            clearable
          />
          <div class="form-help">支持多个职位，用逗号分隔</div>
        </el-form-item>
        
        <el-form-item label="搜索配置">
          <el-checkbox-group v-model="searchForm.options">
            <el-checkbox label="linkedin" border>包含LinkedIn信息</el-checkbox>
            <el-checkbox label="email" border>验证邮箱有效性</el-checkbox>
            <el-checkbox label="phone" border>查找电话号码</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            @click="startSearch"
            :disabled="!canSearch"
            size="large"
          >
            <el-icon><Search /></el-icon>
            开始搜索员工
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 搜索进行中 -->
      <div v-if="searching" class="search-progress">
        <h3>🔍 正在搜索员工信息</h3>
        
        <!-- 步骤进度条 -->
        <el-steps :active="currentStep" finish-status="success" align-center class="search-steps">
          <el-step 
            v-for="(step, index) in searchSteps" 
            :key="index"
            :title="step.title"
            :description="step.description"
            :status="getStepStatus(index)"
          />
        </el-steps>
        
        <div class="progress-details">
          <el-progress 
            :percentage="searchProgress" 
            :format="formatProgress"
            :status="searchProgress === 100 ? 'success' : undefined"
          />
          <p class="current-action">{{ currentAction }}</p>
        </div>
        
        <el-button @click="cancelSearch">取消搜索</el-button>
      </div>
      
      <!-- 搜索结果 -->
      <div v-if="searchResults && !searching" class="search-results">
        <div class="results-header">
          <h3>搜索结果</h3>
          <div class="results-stats">
            <el-tag type="success">找到 {{ searchResults.total_employees }} 名员工</el-tag>
            <el-tag type="primary" v-if="searchResults.verified_contacts">
              {{ searchResults.verified_contacts }} 个已验证联系方式
            </el-tag>
            <el-button type="primary" @click="newSearch">新搜索</el-button>
          </div>
        </div>
        
        <!-- 员工列表 -->
        <div v-if="employeeList.length > 0" class="employee-list">
          <el-row :gutter="20">
            <el-col :span="12" v-for="(employee, index) in employeeList" :key="index">
              <el-card class="employee-card" shadow="hover">
                <template #header>
                  <div class="employee-header">
                    <div class="employee-avatar">
                      <el-avatar 
                        :src="employee.avatar || ''"
                        :size="50"
                      >
                        {{ employee.name?.charAt(0) || '?' }}
                      </el-avatar>
                    </div>
                    <div class="employee-info">
                      <h4>{{ employee.name }}</h4>
                      <p class="position">{{ employee.position }}</p>
                    </div>
                    <div class="confidence-score" v-if="employee.confidence">
                      <el-tag :type="getConfidenceType(employee.confidence)">
                        {{ employee.confidence }}% 置信度
                      </el-tag>
                    </div>
                  </div>
                </template>
                
                <div class="employee-details">
                  <div class="contact-info">
                    <div v-if="employee.email" class="contact-item">
                      <el-icon><Message /></el-icon>
                      <span>{{ employee.email }}</span>
                      <el-tag 
                        v-if="employee.email_verified" 
                        :type="employee.email_verified === 'verified' ? 'success' : 'warning'"
                        size="small"
                      >
                        {{ employee.email_verified === 'verified' ? '已验证' : '待验证' }}
                      </el-tag>
                    </div>
                    
                    <div v-if="employee.phone" class="contact-item">
                      <el-icon><Phone /></el-icon>
                      <span>{{ employee.phone }}</span>
                    </div>
                    
                    <div v-if="employee.linkedin_url" class="contact-item">
                      <el-icon><Link /></el-icon>
                      <a :href="employee.linkedin_url" target="_blank">LinkedIn档案</a>
                    </div>
                  </div>
                  
                  <div v-if="employee.summary" class="employee-summary">
                    <p><strong>简介:</strong> {{ employee.summary }}</p>
                  </div>
                  
                  <!-- AI分析信息 -->
                  <div v-if="employee.ai_score !== undefined" class="ai-analysis">
                    <div class="ai-score">
                      <span class="ai-label">🤖 AI评分:</span>
                      <el-tag 
                        :type="getAiScoreType(employee.ai_score)" 
                        size="small"
                      >
                        {{ (employee.ai_score * 100).toFixed(0) }}%
                      </el-tag>
                    </div>
                    <div v-if="employee.ai_reason" class="ai-reason">
                      <span class="ai-label">💭 分析:</span>
                      <span class="ai-reason-text">{{ employee.ai_reason }}</span>
                    </div>
                  </div>
                  
                  <div class="employee-source">
                    <el-text type="info" size="small">
                      数据来源: {{ employee.source || 'Multiple Sources' }}
                    </el-text>
                  </div>
                </div>
                
                <div class="employee-actions">
                  <el-button size="small" @click="copyContact(employee)">
                    <el-icon><CopyDocument /></el-icon>
                    复制联系方式
                  </el-button>
                  <el-button size="small" type="success" @click="addToList(employee)">
                    <el-icon><Plus /></el-icon>
                    加入客户列表
                  </el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
        
        <!-- 导出功能 -->
        <el-divider />
        <div class="export-section">
          <h4>📥 导出员工数据</h4>
          <el-button-group>
            <el-button @click="exportEmployees('csv')" :icon="Download">导出CSV</el-button>
            <el-button @click="exportEmployees('json')" :icon="Download">导出JSON</el-button>
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
import { 
  Search, Download, Message, Phone, Link, CopyDocument, Plus,
  OfficeBuilding, UserFilled, Checked
} from '@element-plus/icons-vue'

export default {
  name: 'EmployeeSearch',
  components: {
    Search, Download, Message, Phone, Link, CopyDocument, Plus,
    OfficeBuilding, UserFilled, Checked
  },
  setup() {
    const activeCollapse = ref([])
    
    const searchForm = ref({
      companyName: '',
      companyDomain: '',
      targetPosition: '',
      options: ['linkedin', 'email']
    })
    
    const searching = ref(false)
    const searchProgress = ref(0)
    const currentStep = ref(0)
    const currentAction = ref('')
    const searchResults = ref(null)
    
    const searchSteps = ref([
      { title: '公司验证', description: '验证公司信息和官网' },
      { title: '数据检索', description: '搜索员工信息' },
      { title: 'AI筛选', description: '匹配目标职位' },
      { title: '信息整合', description: '验证和整合结果' }
    ])
    
    const canSearch = computed(() => {
      return searchForm.value.companyName.trim() && searchForm.value.targetPosition.trim()
    })
    
    const employeeList = computed(() => {
      return searchResults.value?.employees || []
    })
    
    const startSearch = async () => {
      if (!canSearch.value) {
        ElMessage.warning('请填写公司名称和目标职位')
        return
      }
      
      searching.value = true
      searchProgress.value = 0
      currentStep.value = 0
      currentAction.value = '开始搜索...'
      
      try {
        // 模拟搜索进度
        const progressSteps = [
          { step: 0, progress: 20, action: '正在验证公司信息...' },
          { step: 1, progress: 40, action: '正在检索员工数据...' },
          { step: 2, progress: 70, action: 'AI正在筛选匹配职位...' },
          { step: 3, progress: 90, action: '正在整合和验证信息...' }
        ]
        
        for (const stepInfo of progressSteps) {
          await new Promise(resolve => setTimeout(resolve, 1500))
          currentStep.value = stepInfo.step
          searchProgress.value = stepInfo.progress
          currentAction.value = stepInfo.action
        }
        
        // 调用后端API
        const response = await axios.post('http://localhost:8000/api/employee/search', {
          company_name: searchForm.value.companyName,
          company_domain: searchForm.value.companyDomain,
          target_positions: searchForm.value.targetPosition.split(',').map(p => p.trim()).filter(p => p),
          search_options: searchForm.value.options,
          country_code: 'us',  // 默认美国，后续可添加国家选择
          max_results: 10,
          use_llm_optimization: true  // 启用LLM优化
        })
        
        searchProgress.value = 100
        currentAction.value = '搜索完成!'
        
        await new Promise(resolve => setTimeout(resolve, 500))
        
        searchResults.value = response.data
        ElMessage.success(`搜索完成! 找到 ${response.data.total_found} 名员工`)
        
      } catch (error) {
        console.error('员工搜索失败:', error)
        ElMessage.error('搜索失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        searching.value = false
      }
    }
    
    const cancelSearch = () => {
      searching.value = false
      searchProgress.value = 0
      currentStep.value = 0
    }
    
    const newSearch = () => {
      searchResults.value = null
      searchForm.value = {
        companyName: '',
        companyDomain: '',
        targetPosition: '',
        options: ['linkedin', 'email']
      }
    }
    
    const getStepStatus = (index) => {
      if (currentStep.value > index) return 'finish'
      if (currentStep.value === index && searching.value) return 'process'
      return 'wait'
    }
    
    const formatProgress = (percentage) => `${percentage}%`
    
    const getConfidenceType = (confidence) => {
      if (confidence >= 80) return 'success'
      if (confidence >= 60) return 'warning'
      return 'info'
    }
    
    const getAiScoreType = (score) => {
      if (score >= 0.8) return 'success'
      if (score >= 0.6) return 'warning'
      if (score >= 0.4) return 'info'
      return 'danger'
    }
    
    const copyContact = async (employee) => {
      const contactInfo = []
      if (employee.name) contactInfo.push(`姓名: ${employee.name}`)
      if (employee.position) contactInfo.push(`职位: ${employee.position}`)
      if (employee.email) contactInfo.push(`邮箱: ${employee.email}`)
      if (employee.phone) contactInfo.push(`电话: ${employee.phone}`)
      if (employee.linkedin_url) contactInfo.push(`LinkedIn: ${employee.linkedin_url}`)
      
      const text = contactInfo.join('\n')
      
      try {
        await navigator.clipboard.writeText(text)
        ElMessage.success('联系方式已复制到剪贴板')
      } catch (error) {
        ElMessage.error('复制失败')
      }
    }
    
    const addToList = (employee) => {
      ElMessage.success(`${employee.name} 已加入客户列表`)
      // TODO: 实现加入客户列表功能
    }
    
    const exportEmployees = async (format) => {
      try {
        if (!searchResults.value || searchResults.value.length === 0) {
          ElMessage.warning('没有员工数据可导出')
          return
        }

        let exportData, mimeType, fileName
        
        if (format === 'json') {
          exportData = JSON.stringify(searchResults.value, null, 2)
          mimeType = 'application/json'
          fileName = `employee_search_results.json`
        } else if (format === 'csv') {
          // 转换为CSV格式
          const csvHeaders = ['Name', 'Position', 'Email', 'Phone', 'LinkedIn URL', 'AI Score', 'Relevance Score', 'Source']
          const csvRows = [csvHeaders.join(',')]
          
          searchResults.value.forEach(employee => {
            const row = [
              `"${employee.name || ''}"`,
              `"${employee.position || ''}"`,
              `"${employee.email || ''}"`,
              `"${employee.phone || ''}"`,
              `"${employee.linkedin_url || ''}"`,
              employee.ai_score || '',
              employee.relevance_score || '',
              `"${employee.source || ''}"`
            ]
            csvRows.push(row.join(','))
          })
          
          exportData = csvRows.join('\n')
          mimeType = 'text/csv'
          fileName = `employee_search_results.csv`
        }
        
        // 触发下载
        const blob = new Blob([exportData], { type: mimeType })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = fileName
        a.click()
        window.URL.revokeObjectURL(url)
        
        ElMessage.success(`${format.toUpperCase()} 文件导出成功`)
      } catch (error) {
        ElMessage.error('导出失败: ' + error.message)
      }
    }
    
    return {
      activeCollapse,
      searchForm,
      searching,
      searchProgress,
      currentStep,
      currentAction,
      searchResults,
      searchSteps,
      canSearch,
      employeeList,
      startSearch,
      cancelSearch,
      newSearch,
      getStepStatus,
      formatProgress,
      getConfidenceType,
      getAiScoreType,
      copyContact,
      addToList,
      exportEmployees
    }
  }
}
</script>

<style scoped>
.employee-search {
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

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.search-progress {
  text-align: center;
  padding: 40px 20px;
}

.search-steps {
  margin: 30px 0;
}

.progress-details {
  margin: 30px 0;
}

.current-action {
  margin: 15px 0;
  font-size: 16px;
  color: #606266;
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

.employee-list {
  margin-bottom: 30px;
}

.employee-card {
  margin-bottom: 20px;
  height: 100%;
}

.employee-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.employee-avatar {
  flex-shrink: 0;
}

.employee-info {
  flex-grow: 1;
}

.employee-info h4 {
  margin: 0 0 5px 0;
  color: #303133;
}

.position {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.confidence-score {
  flex-shrink: 0;
}

.employee-details {
  padding: 15px 0;
}

.contact-info {
  margin-bottom: 15px;
}

.contact-item {
  display: flex;
  align-items: center;
  margin: 8px 0;
  gap: 8px;
}

.contact-item a {
  color: #409eff;
  text-decoration: none;
}

.employee-summary {
  margin: 15px 0;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;
}

.ai-analysis {
  margin: 15px 0;
  padding: 10px;
  background: #f0f9ff;
  border: 1px solid #e1f5fe;
  border-radius: 4px;
  font-size: 14px;
}

.ai-score {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}

.ai-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.ai-label {
  font-weight: 500;
  color: #2196f3;
  flex-shrink: 0;
}

.ai-reason-text {
  color: #666;
  line-height: 1.4;
}

.employee-source {
  margin-top: 10px;
  text-align: right;
}

.employee-actions {
  margin-top: 15px;
  text-align: center;
}

.employee-actions .el-button {
  margin: 0 5px;
}

.export-section {
  text-align: center;
  padding: 20px 0;
}
</style>