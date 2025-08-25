#!/usr/bin/env python3
"""
多语言管理系统
支持中英文切换功能
"""

import streamlit as st
import json
from typing import Dict, Any
from pathlib import Path

class LanguageManager:
    """语言管理器"""
    
    def __init__(self):
        self.supported_languages = {
            'zh': '中文',
            'en': 'English'
        }
        self.current_language = self._get_current_language()
        self.translations = self._load_translations()
    
    def _get_current_language(self) -> str:
        """获取当前语言设置"""
        try:
            if hasattr(st, 'session_state') and 'language' not in st.session_state:
                st.session_state.language = 'zh'  # 默认中文
            return getattr(st.session_state, 'language', 'zh')
        except:
            # 如果在非Streamlit环境中运行，返回默认值
            return 'zh'
    
    def _load_translations(self) -> Dict[str, Dict[str, Any]]:
        """加载翻译文件"""
        translations = {
            'zh': self._get_chinese_translations(),
            'en': self._get_english_translations()
        }
        return translations
    
    def _get_chinese_translations(self) -> Dict[str, Any]:
        """中文翻译"""
        return {
            # 主页面
            'main': {
                'title': 'AI Customer Finder',
                'subtitle': '开源B2B客户智能工具',
                'description': {
                    'intro': '此工具帮助您：',
                    'search': '🔍 **智能公司搜索** - 按行业和地区查找目标客户',
                    'contact': '📧 **联系信息提取** - 自动从网站提取邮箱、电话',
                    'employee': '👥 **员工搜索** - 定位决策者和关键联系人'
                },
                'quick_start': {
                    'title': '快速开始',
                    'step1': '在**系统设置**中配置API密钥（推荐）或`.env`文件',
                    'step2': '从左侧导航中选择所需功能',
                    'step3': '填写搜索条件并执行',
                    'step4': '查看结果并下载数据'
                },
                'output_location': {
                    'title': '输出文件位置',
                    'description': '所有结果保存在`output/`目录：',
                    'company': '公司搜索结果：`output/company/`',
                    'contact': '联系信息：`output/contact/`',
                    'employee': '员工信息：`output/employee/`'
                },
                'features': {
                    'title': '可用功能',
                    'company_search': {
                        'title': '🔍 公司搜索',
                        'description': '按以下条件搜索公司：\n- 行业关键词\n- 地理位置\n- 自定义搜索查询\n- **+ AI分析集成**',
                        'link': '前往公司搜索 →'
                    },
                    'ai_search': {
                        'title': '🤖 **新功能：AI智能搜索**',
                        'description': '**自然语言理解，多智能体协作**\n- 用自然语言描述需求\n- AI自动生成搜索策略\n- 实时智能评分匹配\n- 5个专业智能体协作',
                        'link': '前往AI智能搜索 → **🔥 推荐**'
                    },
                    'contact_extraction': {
                        'title': '📧 联系信息提取',
                        'description': '从以下来源提取联系信息：\n- 单个网站URL\n- 批量CSV处理\n- 公司搜索结果\n- 联系页面爬取',
                        'link': '前往联系信息提取 →'
                    },
                    'employee_search': {
                        'title': '👥 员工搜索',
                        'description': '按以下条件查找员工：\n- 公司名称\n- 职位/头衔\n- 地点筛选\n- **+ AI分析集成**',
                        'link': '前往员工搜索 →'
                    },
                    'system_settings': {
                        'title': '⚙️ 系统设置',
                        'description': '配置系统设置：\n- API密钥管理\n- LLM提供商选择\n- 应用程序首选项\n- 连接测试',
                        'link': '前往系统设置 →'
                    },
                    'ai_dashboard': {
                        'title': '📊 **新功能：AI分析仪表板**',
                        'description': '**深度数据洞察与趋势分析**\n- 搜索结果可视化分析\n- AI性能指标监控\n- 智能优化建议\n- 趋势预测与洞察',
                        'link': '前往AI分析仪表板 → **📈 新功能**'
                    }
                },
                'usage_stats': {
                    'title': '使用统计',
                    'company_files': '公司文件',
                    'contact_files': '联系文件',
                    'employee_files': '员工文件',
                    'no_files': '尚未生成输出文件。从搜索公司开始！'
                },
                'api_config': {
                    'missing_key': '⚠️ 缺少必需的API密钥：SERPER_API_KEY',
                    'recommended': '💡 **推荐方式**：使用系统设置界面配置',
                    'goto_settings': '🔗 前往系统设置',
                    'manual_config': '📝 或手动配置 .env 文件'
                }
            },
            
            # AI智能搜索页面
            'intelligent_search': {
                'title': 'AI智能搜索',
                'subtitle': '自然语言理解，多智能体协作',
                'tabs': {
                    'search': '🔍 智能搜索',
                    'results': '📊 搜索结果',
                    'history': '📈 搜索历史'
                },
                'input': {
                    'title': '请用自然语言描述您的采购需求：',
                    'placeholder': '例如：我想找卖数位板的公司，要求支持4K分辨率，价格1000-3000元，深圳地区',
                    'help': 'AI会智能理解您的需求，自动生成搜索策略和评分标准'
                },
                'examples': {
                    'title': '💡 搜索示例',
                    'select': '选择示例需求（可直接使用或修改）',
                    'use_button': '使用此示例',
                    'list': [
                        '我需要太阳能板供应商，功率300W以上，价格合理，华东地区优先',
                        '寻找LED显示屏制造商，户外P10规格，深圳或广州的厂家',
                        '需要工业机器人供应商，6轴关节机器人，负载20kg，江浙沪地区',
                        '找做软件开发的公司，有区块链经验，团队50人以上，北京上海',
                        '寻找化工原料供应商，聚氨酯材料，有环保认证，华南地区'
                    ]
                },
                'search_control': {
                    'title': '🚀 开始搜索',
                    'start_button': '🔍 启动AI智能搜索',
                    'stop_button': '⏹️ 停止搜索',
                    'in_progress': '🔄 AI智能体正在协作中...',
                    'stopped': '搜索已停止'
                },
                'agents': {
                    'requirement_analyst': '需求分析专家',
                    'search_strategist': '搜索策略专家', 
                    'search_executor': '搜索执行专家',
                    'ai_scorer': 'AI评分分析师',
                    'result_optimizer': '结果优化专家'
                },
                'agent_descriptions': {
                    'requirement_analyst': '解析用户需求',
                    'search_strategist': '制定搜索策略',
                    'search_executor': '执行搜索任务', 
                    'ai_scorer': '智能评分分析',
                    'result_optimizer': '优化推荐结果'
                },
                'progress': {
                    'initializing': '🚀 启动AI多智能体系统...',
                    'running': '🤖 {agent} 正在执行任务...',
                    'completed': '✅ AI智能体协作完成！',
                    'success': '🎉 搜索成功完成！找到 {count} 家推荐公司，用时 {time:.1f}秒',
                    'failed': '❌ 搜索失败: {error}',
                    'error': '❌ 搜索执行失败: {error}'
                }
            },
            
            # AI分析仪表板页面
            'ai_dashboard': {
                'title': 'AI分析仪表板',
                'subtitle': '深度数据洞察与趋势分析'
            },
            
            # 通用组件
            'common': {
                'language': '语言',
                'settings': '设置',
                'help': '帮助',
                'about': '关于',
                'loading': '加载中...',
                'error': '错误',
                'success': '成功',
                'warning': '警告',
                'info': '信息',
                'confirm': '确认',
                'cancel': '取消',
                'save': '保存',
                'delete': '删除',
                'edit': '编辑',
                'view': '查看',
                'download': '下载',
                'upload': '上传',
                'search': '搜索',
                'filter': '筛选',
                'export': '导出',
                'import': '导入'
            }
        }
    
    def _get_english_translations(self) -> Dict[str, Any]:
        """英文翻译"""
        return {
            # 主页面
            'main': {
                'title': 'AI Customer Finder',
                'subtitle': 'Open-Source B2B Customer Intelligence Tool',
                'description': {
                    'intro': 'This tool helps you:',
                    'search': '🔍 **Smart Company Search** - Find target customers by industry and region',
                    'contact': '📧 **Contact Extraction** - Automatically extract emails, phones from websites',
                    'employee': '👥 **Employee Search** - Locate decision makers and key contacts'
                },
                'quick_start': {
                    'title': 'Quick Start',
                    'step1': 'Configure API keys in **System Settings** (recommended) or `.env` file',
                    'step2': 'Select desired function from left navigation',
                    'step3': 'Fill in search criteria and execute',
                    'step4': 'View results and download data'
                },
                'output_location': {
                    'title': 'Output File Location',
                    'description': 'All results are saved in `output/` directory:',
                    'company': 'Company search results: `output/company/`',
                    'contact': 'Contact information: `output/contact/`',
                    'employee': 'Employee information: `output/employee/`'
                },
                'features': {
                    'title': 'Available Features',
                    'company_search': {
                        'title': '🔍 Company Search',
                        'description': 'Search for companies by:\n- Industry keywords\n- Geographic location\n- Custom search queries\n- **+ AI Analysis Integration**',
                        'link': 'Go to Company Search →'
                    },
                    'ai_search': {
                        'title': '🤖 **NEW: AI Intelligent Search**',
                        'description': '**Natural Language Understanding, Multi-Agent Collaboration**\n- Describe needs in natural language\n- AI auto-generates search strategies\n- Real-time intelligent scoring\n- 5 professional agents collaboration',
                        'link': 'Go to AI Intelligent Search → **🔥 Recommended**'
                    },
                    'contact_extraction': {
                        'title': '📧 Contact Extraction',
                        'description': 'Extract contact info from:\n- Single website URL\n- Batch CSV processing\n- Company search results\n- Contact pages crawling',
                        'link': 'Go to Contact Extraction →'
                    },
                    'employee_search': {
                        'title': '👥 Employee Search',
                        'description': 'Find employees by:\n- Company name\n- Job position/title\n- Location filtering\n- **+ AI Analysis Integration**',
                        'link': 'Go to Employee Search →'
                    },
                    'system_settings': {
                        'title': '⚙️ System Settings',
                        'description': 'Configure system settings:\n- API keys management\n- LLM provider selection\n- Application preferences\n- Connection testing',
                        'link': 'Go to System Settings →'
                    },
                    'ai_dashboard': {
                        'title': '📊 **NEW: AI Analytics Dashboard**',
                        'description': '**Deep Data Insights & Trend Analysis**\n- Search results visualization\n- AI performance monitoring\n- Intelligent optimization suggestions\n- Trend prediction & insights',
                        'link': 'Go to AI Analytics Dashboard → **📈 New Feature**'
                    }
                },
                'usage_stats': {
                    'title': 'Usage Statistics',
                    'company_files': 'Company Files',
                    'contact_files': 'Contact Files',
                    'employee_files': 'Employee Files',
                    'no_files': 'No output files generated yet. Start by searching for companies!'
                },
                'api_config': {
                    'missing_key': '⚠️ Missing required API key: SERPER_API_KEY',
                    'recommended': '💡 **Recommended**: Use System Settings interface',
                    'goto_settings': '🔗 Go to System Settings',
                    'manual_config': '📝 Or manually configure .env file'
                }
            },
            
            # AI智能搜索页面
            'intelligent_search': {
                'title': 'AI Intelligent Search',
                'subtitle': 'Natural Language Understanding, Multi-Agent Collaboration',
                'tabs': {
                    'search': '🔍 Intelligent Search',
                    'results': '📊 Search Results',
                    'history': '📈 Search History'
                },
                'input': {
                    'title': 'Describe your procurement needs in natural language:',
                    'placeholder': 'e.g., I need digital tablet suppliers with 4K resolution support, price range 1000-3000 yuan, in Shenzhen area',
                    'help': 'AI will intelligently understand your needs and auto-generate search strategies and scoring criteria'
                },
                'examples': {
                    'title': '💡 Search Examples',
                    'select': 'Select example requirement (can use directly or modify)',
                    'use_button': 'Use This Example',
                    'list': [
                        'I need solar panel suppliers, power above 300W, reasonable price, East China region preferred',
                        'Looking for LED display manufacturers, outdoor P10 specification, factories in Shenzhen or Guangzhou',
                        'Need industrial robot suppliers, 6-axis articulated robots, 20kg payload, Jiangsu-Zhejiang-Shanghai region',
                        'Looking for software development companies with blockchain experience, team of 50+ people, Beijing Shanghai',
                        'Seeking chemical raw material suppliers, polyurethane materials, with environmental certification, South China region'
                    ]
                },
                'search_control': {
                    'title': '🚀 Start Search',
                    'start_button': '🔍 Launch AI Intelligent Search',
                    'stop_button': '⏹️ Stop Search',
                    'in_progress': '🔄 AI agents are collaborating...',
                    'stopped': 'Search stopped'
                },
                'agents': {
                    'requirement_analyst': 'Requirement Analyst',
                    'search_strategist': 'Search Strategist', 
                    'search_executor': 'Search Executor',
                    'ai_scorer': 'AI Scoring Analyst',
                    'result_optimizer': 'Result Optimizer'
                },
                'agent_descriptions': {
                    'requirement_analyst': 'Analyze user needs',
                    'search_strategist': 'Design search strategy',
                    'search_executor': 'Execute search tasks', 
                    'ai_scorer': 'Intelligent scoring',
                    'result_optimizer': 'Optimize recommendations'
                },
                'progress': {
                    'initializing': '🚀 Launching AI multi-agent system...',
                    'running': '🤖 {agent} is executing tasks...',
                    'completed': '✅ AI agent collaboration completed!',
                    'success': '🎉 Search completed successfully! Found {count} recommended companies in {time:.1f}s',
                    'failed': '❌ Search failed: {error}',
                    'error': '❌ Search execution failed: {error}'
                }
            },
            
            # AI分析仪表板页面
            'ai_dashboard': {
                'title': 'AI Analytics Dashboard',
                'subtitle': 'Deep Data Insights & Trend Analysis'
            },
            
            # 通用组件
            'common': {
                'language': 'Language',
                'settings': 'Settings',
                'help': 'Help',
                'about': 'About',
                'loading': 'Loading...',
                'error': 'Error',
                'success': 'Success',
                'warning': 'Warning',
                'info': 'Information',
                'confirm': 'Confirm',
                'cancel': 'Cancel',
                'save': 'Save',
                'delete': 'Delete',
                'edit': 'Edit',
                'view': 'View',
                'download': 'Download',
                'upload': 'Upload',
                'search': 'Search',
                'filter': 'Filter',
                'export': 'Export',
                'import': 'Import'
            }
        }
    
    def get_text(self, key_path: str) -> str:
        """
        获取翻译文本
        
        Args:
            key_path: 点分隔的键路径，如 'main.title'
        
        Returns:
            翻译后的文本
        """
        keys = key_path.split('.')
        text = self.translations[self.current_language]
        
        try:
            for key in keys:
                text = text[key]
            return text
        except (KeyError, TypeError):
            # 如果找不到翻译，返回键路径作为fallback
            return key_path
    
    def set_language(self, language: str):
        """设置当前语言"""
        if language in self.supported_languages:
            try:
                if hasattr(st, 'session_state'):
                    st.session_state.language = language
                    self.current_language = language
                    st.rerun()
            except:
                # 在非Streamlit环境中，只更新内部状态
                self.current_language = language
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        return self.current_language
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表"""
        return self.supported_languages
    
    def render_language_selector(self):
        """渲染语言选择器"""
        try:
            col1, col2 = st.columns([3, 1])
            
            with col2:
                selected_lang = st.selectbox(
                    self.get_text('common.language'),
                    options=list(self.supported_languages.keys()),
                    format_func=lambda x: self.supported_languages[x],
                    index=list(self.supported_languages.keys()).index(self.current_language),
                    key="language_selector"
                )
                
                if selected_lang != self.current_language:
                    self.set_language(selected_lang)
        except:
            # 在非Streamlit环境中，不渲染选择器
            pass

# 全局语言管理器实例
_language_manager = None

def get_language_manager() -> LanguageManager:
    """获取全局语言管理器实例"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager

def t(key_path: str) -> str:
    """
    快捷翻译函数
    
    Args:
        key_path: 点分隔的键路径
    
    Returns:
        翻译后的文本
    """
    return get_language_manager().get_text(key_path)