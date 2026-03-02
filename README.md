# AI 企业与联系人智能搜索工具

[English Version](README_en.md) | [Web 界面说明](README_WEB.md) | [Docker 部署](DOCKER_DEPLOY.md)

一套强大的Python工具集，用于自动化外贸与B2B销售中的客户开发流程。该工具通过搜索引擎API和AI技术，帮助您快速找到目标企业、提取联系方式并识别关键决策者。支持命令行和Web界面两种使用方式。

> **想要开箱即用的托管版本？** 欢迎访问 **[B2BInsights.io](https://b2binsights.io)** —— 基于本项目能力打造的AI智能体B2B客户开发平台，无需任何配置即可使用。

> **推荐阅读**: 如果您不熟悉搜索引擎的高级用法，建议先阅读这篇[搜索引擎高级使用教程](https://zhuanlan.zhihu.com/p/1908208213234554242)，它将帮助您更有效地构建搜索查询。

## 项目功能

### 核心功能

本项目提供**两种使用方式**：

#### 1. 命令行工具（适合技术用户）
包含三个主要Python脚本，各自解决销售流程中的不同环节：

- **企业搜索** (`serper_company_search.py`)
  - 基于行业、地区和关键词搜索目标企业
  - 支持自定义搜索查询，完全控制搜索内容
  - 自动提取企业网站、域名和基本信息
  - 支持普通搜索和LinkedIn企业专项搜索

- **联系方式提取** (`extract_contact_info.py`)
  - 从企业网站自动提取联系信息
  - 识别电子邮箱、电话号码、实际地址
  - 收集社交媒体账号（LinkedIn、Twitter、Facebook、Instagram）
  - 支持多URL批量处理，并优化浏览器资源使用
  - 可将结果与输入CSV文件合并，便于数据整合

- **员工与决策者搜索** (`serper_employee_search.py`)
  - 基于公司名称和职位搜索目标企业的员工
  - 识别关键决策者和潜在联系人
  - 提取员工LinkedIn个人资料信息

#### 2. Web界面（适合非技术用户）
基于Streamlit的现代化Web界面，提供：

- **可视化操作界面** - 无需命令行知识即可使用
- **实时结果展示** - 即时查看搜索和提取结果
- **批量处理管理** - 轻松管理多个批量任务
- **数据导出功能** - 一键下载CSV/JSON格式结果
- **Docker部署支持** - 快速部署到任何服务器

## 解决的问题

- **降低客户开发成本**：减少手动搜索和数据收集时间，提高销售团队效率
- **提高客户精准度**：精确定位符合目标行业和地区的企业客户
- **简化联系流程**：直接获取有效联系信息，无需在多个平台间切换
- **识别关键决策者**：直接找到企业中的关键职位人员，缩短销售周期

## 技术实现

- **搜索技术**：使用Serper.dev API进行高效的搜索引擎查询
- **网页内容提取**：使用Playwright自动化浏览器渲染和提取网站内容
- **AI内容分析**：通过多种LLM模型（OpenAI、火山引擎、Anthropic、Google）分析网页内容提取结构化信息
- **并行处理**：优化浏览器实例管理，支持高效批量处理
- **容错机制**：包含超时处理、内容清理和错误恢复功能

## 安装指南

### 前提条件

- Python 3.8+
- Serper.dev API密钥 ([申请免费密钥](https://serper.dev/))
- (可选) LLM API密钥（推荐使用国内火山引擎API）
- (可选) Docker和Docker Compose（用于容器化部署）

### 方法一：本地安装

1. 克隆或下载项目文件

2. 安装依赖包：
```bash
pip install -r requirements.txt
```

3. 安装Playwright浏览器（用于网站内容提取）：
```bash
playwright install chromium
```

4. 创建`.env`配置文件（在项目根目录）：
```
# 必须配置：Serper API密钥
SERPER_API_KEY=your_serper_api_key_here

# LLM配置（以下选择一种）
LLM_PROVIDER=huoshan  # 选项: openai, anthropic, google, huoshan, none

# 火山引擎配置（推荐国内用户使用）
ARK_API_KEY=your_ark_api_key_here
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=doubao-1-5-pro-256k-250115

# 或者使用其他LLM服务
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here

# 网站提取配置
HEADLESS=true
TIMEOUT=15000
VISIT_CONTACT_PAGE=false
```

### 方法二：Docker快速部署（推荐）

使用Docker可以避免环境配置问题，特别适合生产环境部署：

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env文件，添加您的API密钥

# 2. 使用部署脚本（推荐）
chmod +x docker_deploy.sh
./docker_deploy.sh

# 或手动使用docker-compose
docker-compose up -d
```

部署完成后，访问 `http://localhost:8501` 即可使用Web界面。

详细的Docker部署说明请参考[Docker部署指南](DOCKER_DEPLOY.md)。

## 使用指南

### Web界面使用（推荐新手）

1. **启动Web服务**：
```bash
# 本地启动
streamlit run streamlit_app.py

# 或使用Docker
docker-compose up -d
```

2. **访问界面**：在浏览器中打开 `http://localhost:8501`

3. **使用功能**：
   - 从左侧菜单选择功能（企业搜索、联系提取、员工搜索）
   - 填写搜索条件
   - 点击执行并查看结果
   - 下载CSV或JSON格式数据

详细的Web界面使用说明请参考[Web界面指南](README_WEB.md)。

### 命令行使用

#### 1. 企业搜索

使用`serper_company_search.py`脚本搜索企业信息：

#### 基于行业和地区搜索企业：
```bash
python serper_company_search.py --general-search --industry "solar energy" --region "California" --gl "us"
```

#### 使用自定义查询（完全控制查询内容）：
```bash
python serper_company_search.py --general-search --custom-query "top solar panel manufacturers California renewable energy" --gl "us"
```

#### 参数说明：
- `--general-search`: 使用普通搜索模式
- `--linkedin-search`: 使用LinkedIn企业专项搜索模式
- `--industry`: 目标行业关键词
- `--region`: 目标地区/城市
- `--custom-query`: 完全自定义的搜索查询（覆盖industry、region和默认关键词）
- `--gl`: 地区代码（如"us"、"uk"、"cn"等）
- `--num`: 返回结果数量（默认30）
- `--keywords`: 附加关键词（逗号分隔）
- `--output`: 自定义输出文件名

#### 结果：
结果将保存在`output/company/`目录下，CSV和JSON格式。文件名根据搜索参数自动生成。CSV文件包含以下列：
- Company Name：企业名称
- Search Query：搜索查询
- URL：企业网站链接
- Domain：企业域名
- LinkedIn：LinkedIn链接（如果可用）
- GL：地区代码参数
- 以及其他详细信息

#### 2. 联系方式提取

使用`extract_contact_info.py`脚本从网站中提取联系信息：

#### 处理单个网站：
```bash
python extract_contact_info.py --url example.com --headless
```

#### 处理多个网站（从文本文件）：
```bash
python extract_contact_info.py --url-list urls.txt --timeout 15000
```

#### 处理企业搜索结果：
```bash
python extract_contact_info.py --csv output/company/general_solar_energy_california_us_1234567890.csv --url-column Domain
```

> **注意**：当使用`--csv`参数但不指定`--output`时，输出文件将自动命名为"contact_info_"加原始CSV文件名。例如，输入`general_custom_project_us_1234567890.csv`将生成`contact_info_general_custom_project_us_1234567890.csv`。

#### 处理CSV并合并结果：
```bash
python extract_contact_info.py --csv companies.csv --url-column Domain --merge-results
```

#### 参数说明：
- `--url`: 单个网站URL
- `--url-list`: 包含多个URL的文本文件（每行一个URL）
- `--csv`: 包含URL列的CSV文件
- `--url-column`: CSV文件中URL列的名称（默认"URL"）
- `--domain-column`: 备选域名列名（默认"Domain"）
- `--output`: 自定义输出文件名
- `--headless`: 使用无头模式运行浏览器（无界面）
- `--timeout`: 页面加载超时时间（毫秒）
- `--visit-contact`: 启用联系页面访问（更全面但更慢）
- `--merge-results`: 将提取的联系信息与输入CSV合并（仅适用于`--csv`选项）

#### 结果：
- 基本联系信息结果保存在`output/contact/`目录下，包含以下信息：
  - 公司名称
  - 电子邮件地址
  - 电话号码
  - 实际地址
  - 社交媒体链接（LinkedIn、Twitter、Facebook、Instagram）
  
- 当使用`--merge-results`时，会生成额外的`*_merged.csv`文件，其中包含原始CSV数据加上提取的联系信息。

#### 3. 员工搜索

使用`serper_employee_search.py`脚本查找企业员工和决策者：

#### 搜索特定企业的员工：
```bash
python serper_employee_search.py --company "Tesla" --position "sales manager" --location "California"
```

#### 处理企业列表（从搜索结果）：
```bash
python serper_employee_search.py --input-file general_solar_energy_california_us_1234567890.csv --position "CEO" --country "United States"
```

> **注意**：使用`--input-file`参数时，CSV文件必须包含`Company Name`列（公司名称），脚本将使用此列查找企业的员工。CSV文件也可以包含可选的`Location`列，用于定位员工。

#### 参数说明：
- `--company`: 目标公司名称
- `--input-file`: 包含公司信息的CSV文件（位于output目录）
- `--position`: 目标职位/职务
- `--location`: 地点/城市
- `--country`: 国家
- `--keywords`: 附加关键词（逗号分隔）
- `--output`: 自定义输出文件名
- `--gl`: 地区代码（如"us"、"uk"等）
- `--num`: 返回结果数量（默认30）

#### 结果：
结果将保存在`output/employee/`目录下，包含员工姓名、职位、LinkedIn链接和其他可用信息。

## 高级使用技巧

### 完整销售流程自动化：

1. 使用自定义查询搜索目标企业：
```bash
python serper_company_search.py --general-search --custom-query "renewable energy companies Texas usa" --gl "us" --output texas_renewable.csv
```

2. 从搜索结果提取联系信息并合并：
```bash
python extract_contact_info.py --csv output/company/texas_renewable.csv --headless --merge-results
```

3. 查找关键决策者：
```bash
python serper_employee_search.py --input-file texas_renewable.csv --position "purchasing manager" --country "United States"
```

### 批量处理脚本：

项目提供了批量处理脚本，用于自动化处理多个文件：

- **`process_all_companies.py`** - 批量处理所有企业CSV文件（中文版）
- **`process_all_companies_en.py`** - 批量处理所有企业CSV文件（英文版）

```bash
# 批量处理output/company/目录下的所有CSV文件
python process_all_companies.py

# 会自动：
# 1. 读取output/company/目录下的所有CSV文件
# 2. 对每个文件提取联系信息
# 3. 生成对应的联系信息文件到output/contact/
```

### 优化联系人提取：

- 对于加载较慢的网站，可增加超时时间：
```bash
python extract_contact_info.py --url slowwebsite.com --timeout 30000
```

- 对于特殊网站结构，可开启访问联系页面功能：
```bash
python extract_contact_info.py --url example.com --visit-contact
```

- 批量处理多个URL时性能优化：
```bash
# 脚本会自动重用浏览器实例，提高处理效率
python extract_contact_info.py --url-list many_urls.txt --headless --timeout 10000
```

## 注意事项与限制

- Serper.dev API有免费额度限制，请合理控制查询频率
- 部分网站可能禁止自动化访问，可能需要调整请求头或使用代理
- 联系信息提取准确度取决于网站结构和内容质量
- 使用时请遵守相关法律法规和各平台使用条款
- 对于较大批量的处理，建议控制并发和添加足够的延时

## 常见问题

**Q: 无法提取某些网站的联系信息**  
A: 尝试使用`--visit-contact`参数启用联系页面访问，或调整`--timeout`参数增加加载时间。

**Q: 浏览器窗口频繁打开关闭**  
A: 添加`--headless`参数使用无头模式，提高运行效率。批量处理多URL时，系统会自动优化浏览器实例使用。

**Q: 如何处理CSV数据中的联系信息**  
A: 使用`--merge-results`参数将提取的联系信息与原始CSV合并，生成包含所有数据的新文件。

**Q: API密钥配置问题**  
A: 确保`.env`文件中的API密钥格式正确，且不包含引号或额外空格。

## 联系方式

<div style="display: flex; justify-content: space-between;">
  <div style="text-align: center; margin-right: 20px;">
    <h3>个人微信</h3>
    <img src="img/me_code.jpg" width="200" alt="个人微信二维码">
  </div>
  <div style="text-align: center; margin-right: 20px;">
    <h3>微信交流群</h3>
    <img src="img/group_code.jpg" width="200" alt="微信群二维码">
  </div>
  <div style="text-align: center;">
    <h3>电报群</h3>
    <a href="https://t.me/+jjmdspjqpbcwOGFl">加入电报群</a>
  </div>
</div>

---

**想省去部署配置的麻烦？** 欢迎体验 [B2BInsights.io](https://b2binsights.io)，AI智能体驱动的B2B客户开发SaaS平台，开箱即用。