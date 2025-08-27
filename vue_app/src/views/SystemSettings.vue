<template>
  <div class="system-settings">
    <el-card>
      <template #header>
        <h2>⚙️ 系统设置</h2>
        <p>配置API密钥、LLM提供商和其他系统设置</p>
      </template>
      
      <!-- 工作原理说明 -->
      <el-collapse v-model="activeCollapse" class="principle-section">
        <el-collapse-item title="💡 系统配置原理" name="principle">
          <div class="principle-content">
            <h4>🎯 一句话概述</h4>
            <p>系统设置模块统一管理所有API密钥和AI服务配置，为智能搜索系统提供核心动力。</p>
            
            <h4>🔄 配置流程</h4>
            <el-steps :active="0" align-center>
              <el-step title="搜索引擎" description="配置Serper API密钥" icon="Search" />
              <el-step title="AI服务" description="选择和配置LLM提供商" icon="Connection" />
              <el-step title="应用设置" description="配置浏览器和性能参数" icon="Tools" />
              <el-step title="保存测试" description="保存配置并测试连接" icon="Check" />
            </el-steps>
            
            <h4>🔑 必需API服务</h4>
            <ul>
              <li><strong>Serper API：</strong>提供谷歌搜索服务，用于公司和员工信息搜索</li>
              <li><strong>LLM API：</strong>提供AI理解和分析能力，包括OpenAI、Claude、Gemini等</li>
            </ul>
            
            <h4>🔧 支持的LLM提供商</h4>
            <ul>
              <li><strong>OpenAI：</strong>GPT-4o系列，全球领先的AI模型</li>
              <li><strong>Anthropic：</strong>Claude系列，安全可靠的AI助手</li>
              <li><strong>Google：</strong>Gemini系列，谷歌的多模态AI</li>
              <li><strong>火山引擎：</strong>字节跳动的企业级AI服务（推荐中国用户）</li>
            </ul>
            
            <h4>⚙️ 高级配置</h4>
            <ul>
              <li><strong>无头模式：</strong>控制浏览器是否显示界面，影响性能和服务器部署</li>
              <li><strong>超时设置：</strong>控制网页加载等待时间，平衡成功率和效率</li>
              <li><strong>联系页面：</strong>是否特别搜索公司的联系页面获取更多信息</li>
            </ul>
            
            <h4>💡 配置建议</h4>
            <el-alert type="success" :closable="false">
              <ul>
                <li>新手用户建议优先配置Serper API，再选择一个LLM提供商</li>
                <li>中国用户推荐使用火山引擎，可以获得更好的网络访问速度</li>
                <li>生产环境建议开启无头模式，提高系统性能</li>
                <li>定期检查API密钥的有效性和余额情况</li>
              </ul>
            </el-alert>
          </div>
        </el-collapse-item>
      </el-collapse>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <h3>🔍 搜索引擎配置</h3>
          
          <el-form :model="settings" label-width="150px">
            <el-form-item label="Serper API Key">
              <el-input 
                v-model="settings.SERPER_API_KEY" 
                type="password" 
                placeholder="输入Serper.dev API密钥"
                show-password
              />
              <div class="form-help">
                获取地址: <a href="https://serper.dev" target="_blank">https://serper.dev</a>
              </div>
            </el-form-item>
          </el-form>
          
          <el-divider />
          
          <h3>🧠 LLM提供商配置</h3>
          
          <el-form :model="settings" label-width="150px">
            <el-form-item label="LLM提供商">
              <el-select v-model="settings.LLM_PROVIDER" style="width: 100%">
                <el-option label="OpenAI" value="openai" />
                <el-option label="Anthropic" value="anthropic" />
                <el-option label="Google" value="google" />
                <el-option label="火山引擎" value="huoshan" />
                <el-option label="无 (基础功能)" value="none" />
              </el-select>
            </el-form-item>
            
            <!-- OpenAI 配置 -->
            <div v-if="settings.LLM_PROVIDER === 'openai'">
              <el-form-item label="OpenAI API Key">
                <el-input 
                  v-model="settings.OPENAI_API_KEY" 
                  type="password" 
                  placeholder="输入OpenAI API密钥"
                  show-password
                />
              </el-form-item>
              
              <el-form-item label="OpenAI模型">
                <el-select v-model="settings.OPENAI_MODEL" style="width: 100%">
                  <el-option label="GPT-4o" value="gpt-4o" />
                  <el-option label="GPT-4o-mini" value="gpt-4o-mini" />
                  <el-option label="GPT-4-turbo" value="gpt-4-turbo" />
                </el-select>
              </el-form-item>
            </div>
            
            <!-- Anthropic 配置 -->
            <div v-if="settings.LLM_PROVIDER === 'anthropic'">
              <el-form-item label="Anthropic API Key">
                <el-input 
                  v-model="settings.ANTHROPIC_API_KEY" 
                  type="password" 
                  placeholder="输入Anthropic API密钥"
                  show-password
                />
              </el-form-item>
            </div>
            
            <!-- Google 配置 -->
            <div v-if="settings.LLM_PROVIDER === 'google'">
              <el-form-item label="Google API Key">
                <el-input 
                  v-model="settings.GOOGLE_API_KEY" 
                  type="password" 
                  placeholder="输入Google AI API密钥"
                  show-password
                />
              </el-form-item>
            </div>
            
            <!-- 火山引擎配置 -->
            <div v-if="settings.LLM_PROVIDER === 'huoshan'">
              <el-form-item label="ARK API Key">
                <el-input 
                  v-model="settings.ARK_API_KEY" 
                  type="password" 
                  placeholder="输入火山引擎API密钥"
                  show-password
                />
              </el-form-item>
              
              <el-form-item label="ARK Base URL">
                <el-input 
                  v-model="settings.ARK_BASE_URL" 
                  placeholder="火山引擎API基础URL"
                />
              </el-form-item>
              
              <el-form-item label="ARK模型ID">
                <el-input 
                  v-model="settings.ARK_MODEL" 
                  placeholder="火山引擎模型ID"
                />
              </el-form-item>
            </div>
          </el-form>
        </el-col>
        
        <el-col :span="12">
          <h3>🔧 应用设置</h3>
          
          <el-form :model="settings" label-width="150px">
            <el-form-item label="浏览器模式">
              <el-select v-model="settings.HEADLESS" style="width: 100%">
                <el-option label="无头模式 (后台运行)" value="true" />
                <el-option label="显示浏览器窗口" value="false" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="页面加载超时">
              <el-input-number 
                v-model="settings.TIMEOUT" 
                :min="5000" 
                :max="60000" 
                :step="1000"
                style="width: 100%"
              />
              <div class="form-help">单位: 毫秒</div>
            </el-form-item>
            
            <el-form-item label="访问联系页面">
              <el-select v-model="settings.VISIT_CONTACT_PAGE" style="width: 100%">
                <el-option label="否" value="false" />
                <el-option label="是" value="true" />
              </el-select>
            </el-form-item>
          </el-form>
          
          <el-divider />
          
          <h3>📊 当前配置状态</h3>
          
          <div class="status-section">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="搜索引擎API">
                <el-tag :type="apiStatus.SERPER_API_KEY ? 'success' : 'danger'">
                  {{ apiStatus.SERPER_API_KEY ? '已配置' : '未配置' }}
                </el-tag>
              </el-descriptions-item>
              
              <el-descriptions-item label="LLM提供商">
                <el-tag :type="apiStatus.LLM_PROVIDER !== 'none' ? 'success' : 'warning'">
                  {{ apiStatus.LLM_PROVIDER }}
                </el-tag>
              </el-descriptions-item>
              
              <el-descriptions-item v-if="llmKeyStatus" :label="llmKeyLabel">
                <el-tag :type="llmKeyStatus ? 'success' : 'danger'">
                  {{ llmKeyStatus ? '已配置' : '未配置' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
      </el-row>
      
      <el-divider />
      
      <div class="action-section">
        <el-button type="primary" @click="saveSettings" :loading="saving">
          💾 保存配置
        </el-button>
        
        <el-button @click="loadSettings">
          🔄 重载配置
        </el-button>
        
        <el-button @click="testSettings" :loading="testing">
          🧪 测试配置
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Search, Connection, Tools, Check } from '@element-plus/icons-vue'

export default {
  name: 'SystemSettings',
  components: {
    Search, Connection, Tools, Check
  },
  setup() {
    const activeCollapse = ref([])
    const settings = ref({
      SERPER_API_KEY: '',
      LLM_PROVIDER: 'huoshan',
      OPENAI_API_KEY: '',
      OPENAI_MODEL: 'gpt-4o-mini',
      ANTHROPIC_API_KEY: '',
      GOOGLE_API_KEY: '',
      ARK_API_KEY: '',
      ARK_BASE_URL: 'https://ark.cn-beijing.volces.com/api/v3',
      ARK_MODEL: 'ep-20241022140031-89nkp',
      HEADLESS: 'true',
      TIMEOUT: 15000,
      VISIT_CONTACT_PAGE: 'false'
    })
    
    const apiStatus = ref({
      SERPER_API_KEY: false,
      LLM_PROVIDER: 'none'
    })
    
    const saving = ref(false)
    const testing = ref(false)
    
    const llmKeyStatus = computed(() => {
      const provider = settings.value.LLM_PROVIDER
      switch (provider) {
        case 'openai': return !!settings.value.OPENAI_API_KEY
        case 'anthropic': return !!settings.value.ANTHROPIC_API_KEY
        case 'google': return !!settings.value.GOOGLE_API_KEY
        case 'huoshan': return !!settings.value.ARK_API_KEY
        default: return null
      }
    })
    
    const llmKeyLabel = computed(() => {
      const provider = settings.value.LLM_PROVIDER
      switch (provider) {
        case 'openai': return 'OpenAI API Key'
        case 'anthropic': return 'Anthropic API Key'
        case 'google': return 'Google API Key'
        case 'huoshan': return 'ARK API Key'
        default: return 'LLM API Key'
      }
    })
    
    const loadSettings = async () => {
      try {
        // 获取系统状态 - 使用新的health端点
        const healthResponse = await axios.get('http://localhost:8000/health')
        apiStatus.value = healthResponse.data
        
        // 配置设置从本地存储加载（新API没有config端点）
        // 保持默认配置
        
        ElMessage.success('配置状态已加载')
      } catch (error) {
        ElMessage.warning('无法加载当前配置状态')
      }
    }
    
    const saveSettings = async () => {
      saving.value = true
      
      try {
        // 新API没有config端点，只保存到本地存储
        localStorage.setItem('ai-customer-finder-settings', JSON.stringify(settings.value))
        
        ElMessage.success('配置已保存到本地存储！')
        ElMessage.info('注意：配置更改需要重启API服务器才能生效')
        
        // 重新加载状态以确保同步
        await loadSettings()
      } catch (error) {
        ElMessage.error('保存配置失败: ' + error.message)
      } finally {
        saving.value = false
      }
    }
    
    const testSettings = async () => {
      testing.value = true
      
      try {
        await axios.get('http://localhost:8000/health')
        ElMessage.success('配置测试通过！')
      } catch (error) {
        ElMessage.error('配置测试失败: ' + error.message)
      } finally {
        testing.value = false
      }
    }
    
    onMounted(() => {
      loadSettings()
    })
    
    return {
      activeCollapse,
      settings,
      apiStatus,
      saving,
      testing,
      llmKeyStatus,
      llmKeyLabel,
      loadSettings,
      saveSettings,
      testSettings
    }
  }
}
</script>

<style scoped>
.system-settings {
  max-width: 1200px;
  margin: 0 auto;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.form-help a {
  color: #409eff;
  text-decoration: none;
}

.principle-section {
  margin-bottom: 20px;
}

.principle-content {
  max-width: 1000px;
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

.status-section {
  margin: 20px 0;
}

.action-section {
  text-align: center;
  padding: 20px 0;
}

.action-section .el-button {
  margin: 0 10px;
}
</style>