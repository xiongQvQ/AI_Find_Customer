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
            
            <h4>🔍 搜索方式</h4>
            <ul>
              <li><strong>LinkedIn搜索：</strong>专注于职业社交平台，获取最精准的公司信息和商业数据</li>
              <li><strong>优势：</strong>数据质量高、公司信息准确、商业匹配度更好</li>
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
                <li>使用具体的行业关键词，如"新能源汽车"而非"汽车"</li>
                <li>地域关键词可以是城市、省份或特定区域</li>
                <li>LinkedIn搜索能找到最真实可靠的商业公司信息</li>
                <li>特别适合B2B客户开发和商业合作伙伴搜索</li>
              </ul>
            </el-alert>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
    
    <el-card class="search-card">
      <!-- 搜索表单 -->
      <el-form :model="searchForm" label-width="120px" v-if="!searching && results.length === 0">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="行业关键词">
              <el-input v-model="searchForm.industry" placeholder="例如: 新能源汽车" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="国家">
              <el-select 
                v-model="searchForm.country" 
                placeholder="请选择国家" 
                @change="onCountryChange" 
                filterable 
                style="width: 100%"
              >
                <el-option 
                  v-for="country in countryList" 
                  :key="country.code" 
                  :label="country.name" 
                  :value="country.code"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="地区/城市">
              <el-select v-model="searchForm.region" placeholder="请先选择国家" :disabled="!searchForm.country" filterable style="width: 100%">
                <el-option 
                  v-for="region in availableRegions" 
                  :key="region.value" 
                  :label="region.label" 
                  :value="region.value" 
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="搜索类型">
              <el-select v-model="searchForm.searchType" style="width: 100%">
                <el-option label="LinkedIn搜索 (推荐)" value="linkedin" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button 
            type="primary" 
            @click="search" 
            :disabled="!searchForm.industry && !searchForm.region"
            size="large"
          >
            <el-icon><Search /></el-icon>
            开始搜索
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 搜索进行中 -->
      <div v-if="searching" class="search-progress">
        <h3>🔍 正在搜索公司信息</h3>
        
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
    </el-card>
    
    <el-card v-if="results.length > 0" class="results-card">
      <template #header>
        <div class="results-header">
          <h3>搜索结果 ({{ results.length }} 家公司)</h3>
          <el-button type="primary" @click="newSearch">新搜索</el-button>
        </div>
      </template>
      
      <el-table :data="results" style="width: 100%">
        <el-table-column prop="name" label="公司名称" width="200" />
        <el-table-column prop="industry" label="行业" width="150" />
        <el-table-column prop="location" label="位置" width="150" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        
        <!-- AI分析列 -->
        <el-table-column label="AI分析" width="120">
          <template #default="scope">
            <div v-if="scope.row.ai_score !== undefined">
              <el-tag :type="getScoreTagType(scope.row.ai_score)" size="small">
                {{ Math.round(scope.row.ai_score * 100) }}%
              </el-tag>
              <br />
              <el-tag v-if="scope.row.is_company" type="success" size="mini">公司</el-tag>
              <el-tag v-else type="warning" size="mini">疑似</el-tag>
            </div>
            <el-tag v-else type="info" size="small">未分析</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="相关性" width="100">
          <template #default="scope">
            <div v-if="scope.row.relevance_score !== undefined">
              <el-progress 
                :percentage="Math.round(scope.row.relevance_score * 100)" 
                :stroke-width="8"
                :show-text="false"
                :color="getProgressColor(scope.row.relevance_score)"
              />
              <small>{{ Math.round(scope.row.relevance_score * 100) }}%</small>
            </div>
            <span v-else class="text-gray-500">-</span>
          </template>
        </el-table-column>
        
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Setting, Filter, DocumentCopy } from '@element-plus/icons-vue'

export default {
  name: 'CompanySearch',
  components: {
    Search, Setting, Filter, DocumentCopy
  },
  setup() {
    const activeCollapse = ref([])
    
    // 完整的国家列表（基于CSV文件）
    const countryList = ref([
      { name: '中国', code: 'cn' },
      { name: '美国', code: 'us' },
      { name: '英国', code: 'gb' },
      { name: '德国', code: 'de' },
      { name: '日本', code: 'jp' },
      { name: '新加坡', code: 'sg' },
      { name: '澳大利亚', code: 'au' },
      { name: '加拿大', code: 'ca' },
      { name: '法国', code: 'fr' },
      { name: '意大利', code: 'it' },
      { name: '西班牙', code: 'es' },
      { name: '荷兰', code: 'nl' },
      { name: '瑞士', code: 'ch' },
      { name: '瑞典', code: 'se' },
      { name: '挪威', code: 'no' },
      { name: '丹麦', code: 'dk' },
      { name: '芬兰', code: 'fi' },
      { name: '比利时', code: 'be' },
      { name: '奥地利', code: 'at' },
      { name: '韩国', code: 'kr' },
      { name: '印度', code: 'in' },
      { name: '泰国', code: 'th' },
      { name: '马来西亚', code: 'my' },
      { name: '印度尼西亚', code: 'id' },
      { name: '菲律宾', code: 'ph' },
      { name: '越南', code: 'vn' },
      { name: '台湾', code: 'tw' },
      { name: '俄罗斯', code: 'ru' },
      { name: '巴西', code: 'br' },
      { name: '墨西哥', code: 'mx' },
      { name: '阿根廷', code: 'ar' },
      { name: '智利', code: 'cl' },
      { name: '哥伦比亚', code: 'co' },
      { name: '南非', code: 'za' },
      { name: '埃及', code: 'eg' },
      { name: '尼日利亚', code: 'ng' },
      { name: '肯尼亚', code: 'ke' },
      { name: '以色列', code: 'il' },
      { name: '阿联酋', code: 'ae' },
      { name: '沙特阿拉伯', code: 'sa' },
      { name: '土耳其', code: 'tr' },
      { name: '波兰', code: 'pl' },
      { name: '捷克', code: 'cz' },
      { name: '匈牙利', code: 'hu' },
      { name: '罗马尼亚', code: 'ro' },
      { name: '保加利亚', code: 'bg' },
      { name: '克罗地亚', code: 'hr' },
      { name: '斯洛文尼亚', code: 'si' },
      { name: '斯洛伐克', code: 'sk' },
      { name: '爱尔兰', code: 'ie' },
      { name: '葡萄牙', code: 'pt' },
      { name: '希腊', code: 'gr' },
      { name: '新西兰', code: 'nz' },
      { name: '阿富汗', code: 'af' },
      { name: '阿尔巴尼亚', code: 'al' },
      { name: '阿尔及利亚', code: 'dz' },
      { name: '安道尔', code: 'ad' },
      { name: '安哥拉', code: 'ao' },
      { name: '阿塞拜疆', code: 'az' },
      { name: '亚美尼亚', code: 'am' },
      { name: '巴哈马', code: 'bs' },
      { name: '巴林', code: 'bh' },
      { name: '孟加拉国', code: 'bd' },
      { name: '巴巴多斯', code: 'bb' },
      { name: '白俄罗斯', code: 'by' },
      { name: '不丹', code: 'bt' },
      { name: '玻利维亚', code: 'bo' },
      { name: '波黑', code: 'ba' },
      { name: '博茨瓦纳', code: 'bw' },
      { name: '文莱', code: 'bn' },
      { name: '布基纳法索', code: 'bf' },
      { name: '布隆迪', code: 'bi' },
      { name: '柬埔寨', code: 'kh' },
      { name: '喀麦隆', code: 'cm' },
      { name: '佛得角', code: 'cv' },
      { name: '中非', code: 'cf' },
      { name: '乍得', code: 'td' },
      { name: '科摩罗', code: 'km' },
      { name: '刚果共和国', code: 'cg' },
      { name: '刚果民主共和国', code: 'cd' },
      { name: '哥斯达黎加', code: 'cr' },
      { name: '科特迪瓦', code: 'ci' },
      { name: '古巴', code: 'cu' },
      { name: '塞浦路斯', code: 'cy' },
      { name: '吉布提', code: 'dj' },
      { name: '多米尼克', code: 'dm' },
      { name: '多米尼加', code: 'do' },
      { name: '厄瓜多尔', code: 'ec' },
      { name: '萨尔瓦多', code: 'sv' },
      { name: '赤道几内亚', code: 'gq' },
      { name: '厄立特里亚', code: 'er' },
      { name: '爱沙尼亚', code: 'ee' },
      { name: '埃塞俄比亚', code: 'et' },
      { name: '斐济', code: 'fj' },
      { name: '加蓬', code: 'ga' },
      { name: '冈比亚', code: 'gm' },
      { name: '格鲁吉亚', code: 'ge' },
      { name: '加纳', code: 'gh' },
      { name: '格林纳达', code: 'gd' },
      { name: '危地马拉', code: 'gt' },
      { name: '几内亚', code: 'gn' },
      { name: '几内亚比绍', code: 'gw' },
      { name: '圭亚那', code: 'gy' },
      { name: '海地', code: 'ht' },
      { name: '洪都拉斯', code: 'hn' },
      { name: '冰岛', code: 'is' },
      { name: '伊朗', code: 'ir' },
      { name: '伊拉克', code: 'iq' },
      { name: '牙买加', code: 'jm' },
      { name: '约旦', code: 'jo' },
      { name: '哈萨克斯坦', code: 'kz' },
      { name: '科威特', code: 'kw' },
      { name: '吉尔吉斯斯坦', code: 'kg' },
      { name: '老挝', code: 'la' },
      { name: '拉脱维亚', code: 'lv' },
      { name: '黎巴嫩', code: 'lb' },
      { name: '莱索托', code: 'ls' },
      { name: '利比里亚', code: 'lr' },
      { name: '利比亚', code: 'ly' },
      { name: '列支敦士登', code: 'li' },
      { name: '立陶宛', code: 'lt' },
      { name: '卢森堡', code: 'lu' },
      { name: '马达加斯加', code: 'mg' },
      { name: '马拉维', code: 'mw' },
      { name: '马尔代夫', code: 'mv' },
      { name: '马里', code: 'ml' },
      { name: '马耳他', code: 'mt' },
      { name: '毛里塔尼亚', code: 'mr' },
      { name: '毛里求斯', code: 'mu' },
      { name: '摩尔多瓦', code: 'md' },
      { name: '摩纳哥', code: 'mc' },
      { name: '蒙古', code: 'mn' },
      { name: '黑山', code: 'me' },
      { name: '摩洛哥', code: 'ma' },
      { name: '莫桑比克', code: 'mz' },
      { name: '缅甸', code: 'mm' },
      { name: '纳米比亚', code: 'na' },
      { name: '瑙鲁', code: 'nr' },
      { name: '尼泊尔', code: 'np' },
      { name: '尼加拉瓜', code: 'ni' },
      { name: '尼日尔', code: 'ne' },
      { name: '阿曼', code: 'om' },
      { name: '巴基斯坦', code: 'pk' },
      { name: '巴拿马', code: 'pa' },
      { name: '巴布亚新几内亚', code: 'pg' },
      { name: '巴拉圭', code: 'py' },
      { name: '秘鲁', code: 'pe' },
      { name: '卡塔尔', code: 'qa' },
      { name: '卢旺达', code: 'rw' },
      { name: '圣基茨和尼维斯', code: 'kn' },
      { name: '圣卢西亚', code: 'lc' },
      { name: '圣文森特和格林纳丁斯', code: 'vc' },
      { name: '萨摩亚', code: 'ws' },
      { name: '圣马力诺', code: 'sm' },
      { name: '圣多美和普林西比', code: 'st' },
      { name: '塞内加尔', code: 'sn' },
      { name: '塞尔维亚', code: 'rs' },
      { name: '塞舌尔', code: 'sc' },
      { name: '塞拉利昂', code: 'sl' },
      { name: '索马里', code: 'so' },
      { name: '斯里兰卡', code: 'lk' },
      { name: '苏丹', code: 'sd' },
      { name: '苏里南', code: 'sr' },
      { name: '斯威士兰', code: 'sz' },
      { name: '叙利亚', code: 'sy' },
      { name: '塔吉克斯坦', code: 'tj' },
      { name: '坦桑尼亚', code: 'tz' },
      { name: '东帝汶', code: 'tl' },
      { name: '多哥', code: 'tg' },
      { name: '汤加', code: 'to' },
      { name: '特立尼达和多巴哥', code: 'tt' },
      { name: '突尼斯', code: 'tn' },
      { name: '土库曼斯坦', code: 'tm' },
      { name: '图瓦卢', code: 'tv' },
      { name: '乌干达', code: 'ug' },
      { name: '乌克兰', code: 'ua' },
      { name: '乌拉圭', code: 'uy' },
      { name: '乌兹别克斯坦', code: 'uz' },
      { name: '瓦努阿图', code: 'vu' },
      { name: '委内瑞拉', code: 've' },
      { name: '也门', code: 'ye' },
      { name: '赞比亚', code: 'zm' },
      { name: '津巴布韦', code: 'zw' }
    ])
    
    const searchForm = ref({
      industry: '',
      country: '',
      region: '',
      searchType: 'linkedin',
      gl: 'cn'
    })
    
    const searching = ref(false)
    const results = ref([])
    const searchProgress = ref(0)
    const currentStep = ref(0)
    const currentAction = ref('')
    
    const searchSteps = ref([
      { title: '搜索准备', description: '分析关键词和搜索范围' },
      { title: 'LinkedIn检索', description: '从LinkedIn获取公司数据' },
      { title: '数据处理', description: '清洗和格式化公司信息' },
      { title: '结果整理', description: '去重和最终整理' }
    ])
    
    // 定义各国家对应的地区数据
    const regionsByCountry = {
      us: [
        { label: '加利福尼亚州 (California / 硅谷)', value: '美国加利福尼亚' },
        { label: '纽约州 (New York)', value: '美国纽约' },
        { label: '德克萨斯州 (Texas)', value: '美国德州' },
        { label: '佛罗里达州 (Florida)', value: '美国佛罗里达' },
        { label: '华盛顿州 (Washington)', value: '美国华盛顿' },
        { label: '马萨诸塞州 (Massachusetts)', value: '美国马萨诸塞' },
        { label: '伊利诺伊州 (Illinois)', value: '美国伊利诺伊' },
        { label: '宾夕法尼亚州 (Pennsylvania)', value: '美国宾夕法尼亚' },
        { label: '俄亥俄州 (Ohio)', value: '美国俄亥俄' },
        { label: '佐治亚州 (Georgia)', value: '美国佐治亚' }
      ],
      cn: [
        { label: '北京市', value: '中国北京' },
        { label: '上海市', value: '中国上海' },
        { label: '深圳市', value: '中国深圳' },
        { label: '广州市', value: '中国广州' },
        { label: '杭州市', value: '中国杭州' },
        { label: '苏州市', value: '中国苏州' },
        { label: '南京市', value: '中国南京' },
        { label: '成都市', value: '中国成都' },
        { label: '武汉市', value: '中国武汉' },
        { label: '天津市', value: '中国天津' },
        { label: '重庆市', value: '中国重庆' },
        { label: '西安市', value: '中国西安' }
      ],
      uk: [
        { label: '伦敦 (London)', value: '英国伦敦' },
        { label: '曼彻斯特 (Manchester)', value: '英国曼彻斯特' },
        { label: '伯明翰 (Birmingham)', value: '英国伯明翰' },
        { label: '爱丁堡 (Edinburgh)', value: '英国爱丁堡' },
        { label: '利物浦 (Liverpool)', value: '英国利物浦' }
      ],
      de: [
        { label: '柏林 (Berlin)', value: '德国柏林' },
        { label: '慕尼黑 (Munich)', value: '德国慕尼黑' },
        { label: '汉堡 (Hamburg)', value: '德国汉堡' },
        { label: '法兰克福 (Frankfurt)', value: '德国法兰克福' },
        { label: '科隆 (Cologne)', value: '德国科隆' }
      ],
      jp: [
        { label: '东京 (Tokyo)', value: '日本东京' },
        { label: '大阪 (Osaka)', value: '日本大阪' },
        { label: '名古屋 (Nagoya)', value: '日本名古屋' },
        { label: '横滨 (Yokohama)', value: '日本横滨' },
        { label: '京都 (Kyoto)', value: '日本京都' }
      ],
      sg: [
        { label: '新加坡', value: '新加坡' }
      ],
      au: [
        { label: '悉尼 (Sydney)', value: '澳大利亚悉尼' },
        { label: '墨尔本 (Melbourne)', value: '澳大利亚墨尔本' },
        { label: '布里斯班 (Brisbane)', value: '澳大利亚布里斯班' },
        { label: '珀斯 (Perth)', value: '澳大利亚珀斯' }
      ],
      ca: [
        { label: '多伦多 (Toronto)', value: '加拿大多伦多' },
        { label: '温哥华 (Vancouver)', value: '加拿大温哥华' },
        { label: '蒙特利尔 (Montreal)', value: '加拿大蒙特利尔' },
        { label: '卡尔加里 (Calgary)', value: '加拿大卡尔加里' }
      ],
      tw: [
        { label: '台北', value: '台湾台北' },
        { label: '台中', value: '台湾台中' },
        { label: '高雄', value: '台湾高雄' },
        { label: '新竹', value: '台湾新竹' }
      ],
      other: [
        { label: '自定义地区', value: 'custom' }
      ]
    }
    
    const availableRegions = ref([])
    
    // 从国家代码直接映射，简化逻辑
    const getCountryCode = (countryCode) => {
      // 直接使用选择的国家代码
      return countryCode || 'us'
    }
    
    // 国家选择变化处理
    const onCountryChange = (country) => {
      // 重置地区选择
      searchForm.value.region = ''
      // 更新可用地区列表
      availableRegions.value = regionsByCountry[country] || []
      // 直接使用选择的国家代码
      searchForm.value.gl = getCountryCode(country)
      console.log(`选择国家: ${country}, 自动设置国家代码: ${searchForm.value.gl}`)
    }
    
    // URL解码函数
    const decodeUrlString = (str) => {
      if (!str) return str
      try {
        // 解码URL编码的字符串
        return decodeURIComponent(str)
      } catch (error) {
        console.warn('URL解码失败:', error)
        return str
      }
    }
    
    const search = async () => {
      if (!searchForm.value.industry && !searchForm.value.region) {
        ElMessage.warning('请至少输入行业或选择地区')
        return
      }
      
      if (!searchForm.value.country) {
        ElMessage.warning('请选择国家')
        return
      }
      
      searching.value = true
      searchProgress.value = 0
      currentStep.value = 0
      currentAction.value = '开始搜索...'
      
      try {
        // 模拟搜索进度
        const progressSteps = [
          { step: 0, progress: 20, action: '正在分析搜索关键词...' },
          { step: 1, progress: 50, action: '正在从LinkedIn检索公司数据...' },
          { step: 2, progress: 80, action: '正在处理和清洗数据...' },
          { step: 3, progress: 95, action: '正在整理搜索结果...' }
        ]
        
        // 启动进度模拟
        const progressPromise = (async () => {
          for (const stepInfo of progressSteps) {
            await new Promise(resolve => setTimeout(resolve, 1000))
            currentStep.value = stepInfo.step
            searchProgress.value = stepInfo.progress
            currentAction.value = stepInfo.action
          }
        })()
        
        // 同时发起API请求
        const apiPromise = fetch('http://localhost:8000/api/company/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            industry: searchForm.value.industry || null,
            region: searchForm.value.region || null,
            search_type: searchForm.value.searchType,
            country_code: searchForm.value.gl,
            max_results: 30,
            use_llm_optimization: true
          })
        })
        
        // 等待两个Promise完成
        const [, response] = await Promise.all([progressPromise, apiPromise])
        
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || '搜索请求失败')
        }
        
        const data = await response.json()
        
        searchProgress.value = 100
        currentAction.value = '搜索完成!'
        
        await new Promise(resolve => setTimeout(resolve, 500))
        
        if (data.success) {
          // 转换API响应数据格式为前端显示格式，并进行URL解码
          results.value = data.companies.map(company => ({
            name: decodeUrlString(company.name) || '未知公司',
            industry: decodeUrlString(company.industry) || decodeUrlString(searchForm.value.industry) || '未知行业',
            location: decodeUrlString(company.location) || decodeUrlString(searchForm.value.region) || '未知位置', 
            description: decodeUrlString(company.description) || '暂无描述',
            url: company.website_url || company.url || '',
            domain: decodeUrlString(company.domain) || '',
            linkedin: company.linkedin_url || company.linkedin || '',
            type: decodeUrlString(company.type) || '',
            // AI分析字段
            ai_score: company.ai_score,
            is_company: company.is_company,
            ai_reason: company.ai_reason,
            relevance_score: company.relevance_score,
            analysis_confidence: company.analysis_confidence
          }))
          
          ElMessage.success(`搜索完成，找到 ${data.total_companies} 家公司`)
        } else {
          throw new Error(data.error || '搜索失败')
        }
      } catch (error) {
        console.error('搜索错误:', error)
        ElMessage.error('搜索失败: ' + error.message)
        results.value = []
      } finally {
        searching.value = false
      }
    }
    
    const cancelSearch = () => {
      searching.value = false
      searchProgress.value = 0
      currentStep.value = 0
    }
    
    const getStepStatus = (index) => {
      if (currentStep.value > index) return 'finish'
      if (currentStep.value === index && searching.value) return 'process'
      return 'wait'
    }
    
    const formatProgress = (percentage) => `${percentage}%`
    
    const viewDetails = (company) => {
      // 创建详细信息内容 (数据已经解码过了)
      let detailsHtml = `
        <div style="text-align: left; max-width: 500px;">
          <h4 style="margin: 0 0 10px 0; color: #409eff;">${company.name}</h4>
          <p><strong>行业：</strong>${company.industry}</p>
          <p><strong>位置：</strong>${company.location}</p>
          <p><strong>描述：</strong>${company.description}</p>
      `
      
      if (company.url) {
        detailsHtml += `<p><strong>网站：</strong><a href="${company.url}" target="_blank" style="color: #409eff;">${company.url}</a></p>`
      }
      
      if (company.linkedin) {
        detailsHtml += `<p><strong>LinkedIn：</strong><a href="${company.linkedin}" target="_blank" style="color: #409eff;">查看LinkedIn主页</a></p>`
      }
      
      if (company.domain) {
        detailsHtml += `<p><strong>域名：</strong>${company.domain}</p>`
      }
      
      // AI分析信息
      if (company.ai_score !== undefined) {
        detailsHtml += `<hr style="margin: 15px 0; border: none; border-top: 1px solid #eee;">`
        detailsHtml += `<h4 style="margin: 10px 0; color: #409eff;">🤖 AI分析结果</h4>`
        detailsHtml += `<p><strong>AI评分：</strong>${Math.round(company.ai_score * 100)}%</p>`
        detailsHtml += `<p><strong>是否为公司：</strong>${company.is_company ? '✅ 是' : '⚠️ 疑似'}</p>`
        
        if (company.relevance_score !== undefined) {
          detailsHtml += `<p><strong>相关性：</strong>${Math.round(company.relevance_score * 100)}%</p>`
        }
        
        if (company.analysis_confidence !== undefined) {
          detailsHtml += `<p><strong>分析置信度：</strong>${Math.round(company.analysis_confidence * 100)}%</p>`
        }
        
        if (company.ai_reason) {
          detailsHtml += `<p><strong>分析理由：</strong>${company.ai_reason}</p>`
        }
      }
      
      detailsHtml += `</div>`
      
      // 使用MessageBox显示详细信息
      ElMessageBox({
        title: '公司详细信息',
        message: detailsHtml,
        dangerouslyUseHTMLString: true,
        confirmButtonText: '关闭',
        showCancelButton: false,
        center: true
      })
    }
    
    const newSearch = () => {
      results.value = []
      searchForm.value = {
        industry: '',
        country: '',
        region: '',
        searchType: 'linkedin',
        gl: 'cn'
      }
      availableRegions.value = []
    }
    
    // AI分析相关的helper方法
    const getScoreTagType = (score) => {
      if (score >= 0.8) return 'success'
      if (score >= 0.6) return 'warning'
      return 'danger'
    }
    
    const getProgressColor = (score) => {
      if (score >= 0.8) return '#67c23a'
      if (score >= 0.6) return '#e6a23c'
      return '#f56c6c'
    }
    
    return {
      activeCollapse,
      countryList,
      searchForm,
      searching,
      results,
      searchProgress,
      currentStep,
      currentAction,
      searchSteps,
      availableRegions,
      onCountryChange,
      search,
      cancelSearch,
      getStepStatus,
      formatProgress,
      newSearch,
      viewDetails,
      getScoreTagType,
      getProgressColor
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
}

.results-card {
  margin-top: 20px;
}
</style>