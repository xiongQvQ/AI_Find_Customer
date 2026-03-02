#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import csv
import argparse
import time
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse, urljoin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.llm_client import call_llm, is_llm_available, get_llm_model, parse_json_response

# Load environment variables from .env file
load_dotenv()

# Ensure output directories exist
OUTPUT_DIR = "output"
CONTACT_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "contact")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
if not os.path.exists(CONTACT_OUTPUT_DIR):
    os.makedirs(CONTACT_OUTPUT_DIR)
    print(f"Created output directory: {CONTACT_OUTPUT_DIR}")

class WebsiteContentExtractor:
    """Class to extract content from websites using Playwright"""
    
    def __init__(self, headless=True, timeout=30000, visit_contact_page=False):
        self.headless = headless
        self.timeout = timeout
        self.visit_contact_page = visit_contact_page  # 控制是否访问联系页面
        self.browser = None
        self.context = None
        
    def initialize_browser(self):
        """初始化浏览器实例，如果尚未创建"""
        if self.browser is None:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            # 设置浏览器上下文，增加用户代理以避免被检测为机器人
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
            )
            print("已初始化浏览器实例")
    
    def close_browser(self):
        """关闭浏览器实例和playwright"""
        if self.browser:
            self.browser.close()
            self.browser = None
        if hasattr(self, 'playwright') and self.playwright:
            self.playwright.stop()
            self.playwright = None
        print("已关闭浏览器实例")
        
    def extract_content(self, url):
        """Extract content from a website using Playwright"""
        try:
            # Import Playwright here to avoid dependency if not used
            from playwright.sync_api import sync_playwright
            
            print(f"Accessing website: {url}")
            
            # 确定是否需要创建新的浏览器实例
            new_browser_needed = self.browser is None
            
            try:
                # 如果没有现有浏览器，创建一个
                if new_browser_needed:
                    self.initialize_browser()
                
                # 创建一个新页面
                page = self.context.new_page()
                # 设置更短的默认导航超时
                page.set_default_navigation_timeout(self.timeout)
                
                try:
                    # Go to the main page with improved error handling
                    print(f"正在加载主页：{url}")
                    try:
                        # 先尝试使用domcontentloaded等待，这比networkidle更快且更可靠
                        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                        print("页面基本内容已加载")
                    except Exception as e:
                        print(f"页面加载超时，尝试无等待加载: {e}")
                        try:
                            # 最后尝试不等待特定事件的加载
                            page.goto(url, timeout=self.timeout)
                            print("页面已加载，但未等待完成")
                        except Exception as e2:
                            print(f"页面无法加载: {e2}")
                            page.close()
                            return None
                    
                    # 无论如何，等待一小段时间让页面渲染
                    page.wait_for_timeout(2000)
                    
                    # 打印页面标题用于调试
                    try:
                        title = page.title()
                        print(f"页面标题: {title}")
                    except:
                        print("无法获取页面标题")
                    
                    main_content = page.content()
                    print(f"主页内容长度: {len(main_content)} 字符")
                    
                    # Find and visit contact page if enabled
                    contact_content = None
                    if self.visit_contact_page:
                        contact_selectors = [
                            'a[href*="contact"]', 
                            'a[href*="about"]',
                            'a[href*="Contact"]',
                            'a[href*="About"]',
                            'a:text("Contact")', 
                            'a:text("Contact Us")',
                            'a:text("About")',
                            'a:text("About Us")',
                            'a:text-matches("联系", "i")',
                            'a:text-matches("关于", "i")'
                        ]
                        
                        for selector in contact_selectors:
                            print(f"尝试查找联系页面链接: {selector}")
                            contact_links = page.query_selector_all(selector)
                            if contact_links:
                                print(f"找到 {len(contact_links)} 个可能的联系页面链接")
                                for link in contact_links:
                                    href = link.get_attribute('href')
                                    if href:
                                        # 打印链接文本和URL便于调试
                                        link_text = link.inner_text().strip()
                                        print(f"联系链接: [{link_text}] -> {href}")
                                        
                                        # Handle relative URLs
                                        if not href.startswith(('http', 'https')):
                                            parsed_url = urlparse(url)
                                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                            href = urljoin(base_url, href)
                                        
                                        print(f"访问联系页面: {href}")
                                        try:
                                            # 使用更可靠的加载方式
                                            try:
                                                page.goto(href, wait_until="domcontentloaded", timeout=self.timeout)
                                            except Exception as e:
                                                print(f"联系页面加载超时，尝试无等待加载: {e}")
                                                page.goto(href, timeout=self.timeout)
                                                
                                            page.wait_for_timeout(2000)  # 等待页面渲染
                                            print(f"联系页面标题: {page.title()}")
                                            contact_content = page.content()
                                            print(f"联系页面内容长度: {len(contact_content)} 字符")
                                            break
                                        except Exception as e:
                                            print(f"访问联系页面出错: {e}")
                                
                                if contact_content:
                                    break
                        
                        if not contact_content:
                            print("未找到联系页面，或访问联系页面失败")
                    else:
                        print("跳过访问联系页面")
                    
                    # Try to extract footer which often contains contact info
                    footer_content = None
                    footer_selectors = ['footer', '.footer', '#footer', '[id*="footer"]', '[class*="footer"]', '.contact-info', '#contact-info', '[class*="contact"]']
                    
                    for selector in footer_selectors:
                        print(f"尝试提取页脚内容: {selector}")
                        footer = page.query_selector(selector)
                        if footer:
                            footer_content = footer.inner_html()
                            print(f"成功提取页脚内容，长度: {len(footer_content)} 字符")
                            break
                    
                    # 尝试查找可能包含联系信息的其他元素
                    contact_elements = []
                    contact_element_selectors = [
                        '.contact', '#contact', '[class*="contact-"]', '[id*="contact-"]',
                        '.address', '#address', '[class*="address"]',
                        '.phone', '#phone', '[class*="phone"]',
                        '.email', '#email', '[class*="email"]'
                    ]
                    
                    for selector in contact_element_selectors:
                        elements = page.query_selector_all(selector)
                        if elements:
                            print(f"找到 {len(elements)} 个可能包含联系信息的元素: {selector}")
                            for element in elements:
                                contact_elements.append(element.inner_html())
                    
                    contact_elements_content = "".join(contact_elements)
                    print(f"其他联系元素内容长度: {len(contact_elements_content)} 字符")
                    
                    # 关闭当前页面，但保留浏览器实例
                    page.close()
                    
                    # 清理HTML内容，去除不必要的CSS、JavaScript等
                    cleaned_content = self._clean_html_content(main_content)
                    cleaned_contact = self._clean_html_content(contact_content) if contact_content else None
                    cleaned_footer = self._clean_html_content(footer_content) if footer_content else None
                    cleaned_elements = self._clean_html_content("".join(contact_elements)) if contact_elements else None
                    
                    print(f"清理后主页内容长度: {len(cleaned_content)} 字符")
                    if cleaned_contact:
                        print(f"清理后联系页面内容长度: {len(cleaned_contact)} 字符")
                    if cleaned_footer:
                        print(f"清理后页脚内容长度: {len(cleaned_footer)} 字符")
                    if cleaned_elements:
                        print(f"清理后其他联系元素内容长度: {len(cleaned_elements)} 字符")
                    
                    return {
                        "main_content": cleaned_content,
                        "contact_content": cleaned_contact,
                        "footer_content": cleaned_footer,
                        "contact_elements_content": cleaned_elements
                    }
                    
                except Exception as e:
                    print(f"浏览网站时出错: {e}")
                    page.close()
                    return None
            
            except Exception as e:
                print(f"创建浏览器实例时出错: {e}")
                # 如果是我们创建的浏览器，确保关闭
                if new_browser_needed and self.browser:
                    self.close_browser()
                return None
        
        except ImportError:
            print("Playwright not installed. Please install with: pip install playwright")
            print("And then: playwright install chromium")
            return None
        except Exception as e:
            print(f"网站提取过程中发生意外错误: {e}")
            return None

    def _clean_html_content(self, html_content):
        """清理HTML内容，去除CSS、JavaScript和其他不必要的样式元素"""
        if not html_content:
            return ""
        
        try:
            from bs4 import BeautifulSoup
            
            # 创建BeautifulSoup对象解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除所有script标签
            for script in soup.find_all('script'):
                script.decompose()
            
            # 移除所有style标签
            for style in soup.find_all('style'):
                style.decompose()
            
            # 移除所有link标签（通常是CSS引入）
            for link in soup.find_all('link'):
                link.decompose()
            
            # 移除所有meta标签
            # for meta in soup.find_all('meta'):
            #     meta.decompose()
                
            # 移除所有svg标签（图形元素）
            for svg in soup.find_all('svg'):
                svg.decompose()
                
            # 移除可能的广告或不相关内容区块
            for irrelevant in soup.find_all(['iframe', 'canvas', 'noscript']):
                irrelevant.decompose()
            
            # 移除所有元素上的style属性、class属性和id属性
            for tag in soup.find_all(True):
                if tag.has_attr('style'):
                    del tag['style']
                # 保留一些可能与联系信息相关的class和id
                if tag.has_attr('class') and not any(c.lower() in ['contact', 'footer', 'address', 'phone', 'email'] for c in tag.get('class', [])):
                    del tag['class']
                if tag.has_attr('id') and not any(tag['id'].lower() in ['contact', 'footer', 'address', 'phone', 'email']):
                    del tag['id']
                # 移除其他不必要属性但保留href、src等有用的属性
                attrs_to_keep = ['href', 'src', 'alt', 'title']
                for attr in list(tag.attrs):
                    if attr not in attrs_to_keep:
                        del tag[attr]
            
            # 返回清理后的HTML字符串
            return str(soup)
        
        except ImportError:
            print("BeautifulSoup not installed. Please install with: pip install beautifulsoup4")
            return html_content
        except Exception as e:
            print(f"HTML清理过程中出错: {e}")
            return html_content

class UnifiedLLMProcessor:
    """Unified LLM processor for contact extraction — backed by litellm via core/llm_client."""

    _SYSTEM_PROMPT = (
        "You are an expert at extracting contact information from website HTML content. "
        "Your task is to analyze the HTML and find the company's contact details."
    )

    _USER_TEMPLATE = (
        "Extract the following information from the HTML content:\n"
        "1. Company name\n"
        "2. Email addresses (focus on contact/info/support emails, not personal emails)\n"
        "3. Phone numbers (with country codes if available)\n"
        "4. Physical address\n"
        "5. Social media URLs (LinkedIn, Twitter/X, Facebook, Instagram)\n\n"
        "Return ONLY a JSON object with these fields: "
        "company_name, email, phone, address, linkedin, twitter, facebook, instagram.\n"
        "If you can't find certain information, leave that field as an empty string.\n"
        "Do not include explanations, just the JSON object.\n\n"
        "HTML Content:\n{content}"
    )

    def __init__(self):
        self.available = is_llm_available()
        if not self.available:
            model = get_llm_model()
            if model:
                print(f"Warning: LLM_MODEL='{model}' but the required API key is missing. LLM extraction disabled.")
            else:
                print("LLM processing is disabled (LLM_MODEL not set). Contact extraction will use regex only.")

    def extract_contact_info(self, website_content, url):
        """Extract contact information from website content using LLM."""
        if not website_content or not self.available:
            print("无法提取联系信息: LLM未配置或缺少网站内容")
            return self._get_empty_result(url)

        # Combine content sections with priority
        content = ""
        for key, label in [
            ("contact_content", "联系页面内容"),
            ("footer_content", "页脚内容"),
            ("contact_elements_content", "联系元素内容"),
        ]:
            if website_content.get(key):
                content += "\n" + website_content[key]
                print(f"使用{label}进行解析")
        if website_content.get("main_content") and len(content) < 10000:
            content += "\n" + website_content["main_content"]
            print("使用主页内容进行解析")

        print(f"发送给LLM的内容总长度: {len(content)} 字符")
        content = self._truncate_content(content)
        print(f"截断后的内容长度: {len(content)} 字符")

        try:
            model = get_llm_model()
            print(f"正在使用 {model} 处理内容...")
            raw = call_llm(
                system=self._SYSTEM_PROMPT,
                user=self._USER_TEMPLATE.format(content=content),
                temperature=0.3,
                max_tokens=800,
            )
            result = parse_json_response(raw)
            if result and isinstance(result, dict):
                print("LLM成功提取了联系信息")
                result["website"] = url
                return result
            print("LLM未能提取联系信息")
            return self._get_empty_result(url)
        except Exception as e:
            print(f"LLM处理过程中出错: {e}")
            return self._get_empty_result(url)

    def _get_empty_result(self, url):
        """Return an empty result structure."""
        return {
            "company_name": "",
            "email": "",
            "phone": "",
            "address": "",
            "linkedin": "",
            "twitter": "",
            "facebook": "",
            "instagram": "",
            "website": url,
        }

    def _truncate_content(self, content, max_length=32000):
        """Truncate content to fit within LLM context limits."""
        if len(content) <= max_length:
            return content
        start_size = max_length // 2
        end_size = max_length - start_size
        return content[:start_size] + "\n...[content truncated]...\n" + content[-end_size:]

class ContactExtractor:
    def __init__(self, output_file=None, visit_contact_page=False, merge_with_input=False):
        # Set default output file with timestamp if none provided
        if output_file is None:
            timestamp = int(time.time())
            self.output_file = os.path.join(CONTACT_OUTPUT_DIR, f"contact_info_{timestamp}.csv")
        else:
            self.output_file = os.path.join(CONTACT_OUTPUT_DIR, output_file)
        
        # Initialize extractors
        headless_value = os.getenv("HEADLESS", "true").lower()
        headless = headless_value == "true" or headless_value == "1" or headless_value == "yes"
        
        # 修复TIMEOUT环境变量解析问题
        timeout_str = os.getenv("TIMEOUT", "30000")
        # 如果包含空格或注释，只取第一部分数字
        if " " in timeout_str:
            timeout_str = timeout_str.split()[0]
        try:
            timeout = int(timeout_str)
        except ValueError:
            print(f"Warning: Invalid TIMEOUT value '{timeout_str}', using default 30000")
            timeout = 30000
        
        # 是否访问联系页面，优先使用传入的参数，否则使用环境变量    
        if not visit_contact_page:
            visit_contact = os.getenv("VISIT_CONTACT_PAGE", "false").lower()
            visit_contact_page = visit_contact == "true" or visit_contact == "1" or visit_contact == "yes"
            
        self.website_extractor = WebsiteContentExtractor(
            headless=headless,
            timeout=timeout,
            visit_contact_page=visit_contact_page
        )
        self.llm_processor = UnifiedLLMProcessor()
        
        # 是否与输入文件合并结果
        self.merge_with_input = merge_with_input
        
        # Results list
        self.results = []
        
        # 存储原始CSV数据和URL/结果映射，用于合并结果
        self.original_csv_data = []
        self.original_csv_headers = []
        self.url_to_result_map = {}
    
    def process_url(self, url):
        """Process a single URL to extract contact information"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        print(f"\nProcessing: {url}")
        
        # Extract website content
        website_content = self.website_extractor.extract_content(url)
        
        if website_content:
            # Process with LLM to extract contact info
            contact_info = self.llm_processor.extract_contact_info(website_content, url)
            
            if contact_info:
                print(f"✓ Found contact information:")
                for key, value in contact_info.items():
                    if value and key != "website":
                        print(f"  - {key}: {value}")
                
                self.results.append(contact_info)
                return contact_info
            else:
                print(f"✗ No contact information found for {url}")
                # Add minimal result
                minimal_result = {
                    "company_name": "",
                    "email": "",
                    "phone": "",
                    "address": "",
                    "linkedin": "",
                    "twitter": "",
                    "facebook": "",
                    "instagram": "",
                    "website": url
                }
                self.results.append(minimal_result)
                return minimal_result
        else:
            print(f"✗ Failed to extract content from {url}")
            # Add minimal result
            minimal_result = {
                "company_name": "",
                "email": "",
                "phone": "",
                "address": "",
                "linkedin": "",
                "twitter": "",
                "facebook": "",
                "instagram": "",
                "website": url
            }
            self.results.append(minimal_result)
            return minimal_result
    
    def process_url_list(self, urls):
        """Process a list of URLs to extract contact information"""
        try:
            # 初始化浏览器一次，用于处理所有URL
            self.website_extractor.initialize_browser()
            
            for url in urls:
                self.process_url(url.strip())
        
        except Exception as e:
            print(f"处理URL列表时出错: {e}")
        
        finally:
            # 确保浏览器在所有情况下都被关闭
            self.website_extractor.close_browser()
    
    def process_csv_file(self, csv_file, url_column='URL', domain_column='Domain'):
        """Process URLs from a CSV file"""
        urls_processed = []
        
        try:
            # 初始化浏览器一次，用于处理CSV中的所有URL
            self.website_extractor.initialize_browser()
            
            # 读取原始CSV文件数据，用于后续可能的合并
            if self.merge_with_input:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.original_csv_headers = reader.fieldnames.copy() if reader.fieldnames else []
                    self.original_csv_data = list(reader)
                print(f"Read {len(self.original_csv_data)} rows from original CSV for merging")
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Check that the required column exists
                fieldnames = reader.fieldnames
                if url_column in fieldnames:
                    # Process using URL column
                    for row in reader:
                        url = row.get(url_column, '').strip()
                        if url and url not in urls_processed:
                            result = self.process_url(url)
                            if self.merge_with_input and result:
                                # 存储URL与结果的映射关系
                                self.url_to_result_map[url] = result
                            urls_processed.append(url)
                
                elif domain_column in fieldnames:
                    # Process using Domain column
                    for row in reader:
                        domain = row.get(domain_column, '').strip()
                        if domain and domain not in urls_processed:
                            # Add https:// if needed
                            if not domain.startswith(('http://', 'https://')):
                                url = f"https://{domain}"
                            else:
                                url = domain
                                
                            result = self.process_url(url)
                            if self.merge_with_input and result:
                                # 存储Domain与结果的映射关系
                                self.url_to_result_map[domain] = result
                            urls_processed.append(url)
                
                else:
                    raise ValueError(f"CSV file does not contain required column: {url_column} or {domain_column}")
                    
        
        except Exception as e:
            print(f"Error processing CSV file: {e}")
        
        finally:
            # 确保浏览器在所有情况下都被关闭
            self.website_extractor.close_browser()
    
    def save_results(self):
        """Save contact information results to CSV and JSON files"""
        if not self.results:
            print("No results to save.")
            return
        
        merged_output_file = None
        
        # 检查是否需要与输入CSV合并结果
        if self.merge_with_input and self.original_csv_data and self.original_csv_headers:
            # 确定合并后的输出文件名
            merged_output_file = self.output_file.replace('.csv', '_merged.csv')
            print(f"准备合并结果到文件: {merged_output_file}")
            print(f"原始数据行数: {len(self.original_csv_data)}")
            print(f"URL映射数量: {len(self.url_to_result_map)}")
            print(f"URL映射键: {list(self.url_to_result_map.keys())[:5]}...")
            
            try:
                # 合并结果
                with open(merged_output_file, 'w', newline='', encoding='utf-8') as f:
                    # 确定新的列头：原始列 + 联系信息列
                    contact_headers = ['ContactInfo_Company', 'ContactInfo_Email', 'ContactInfo_Phone', 'ContactInfo_Address', 
                                      'ContactInfo_LinkedIn', 'ContactInfo_Twitter', 'ContactInfo_Facebook', 'ContactInfo_Instagram']
                    merged_headers = self.original_csv_headers + contact_headers
                    
                    writer = csv.DictWriter(f, fieldnames=merged_headers)
                    writer.writeheader()
                    
                    # 遍历原始数据，添加联系信息
                    matches_found = 0
                    for row in self.original_csv_data:
                        merged_row = row.copy()  # 复制原始行数据
                        
                        # 获取URL或域名 - 尝试多种格式匹配
                        url_key = None
                        url_candidates = []
                        
                        # 尝试从URL列获取
                        if 'URL' in row and row['URL']:
                            url_raw = row['URL'].strip()
                            url_candidates.append(url_raw)
                            # 也尝试添加和移除 https:// 和 www.
                            if url_raw.startswith('https://'):
                                url_candidates.append(url_raw[8:])  # 移除 https://
                            elif not url_raw.startswith(('http://', 'https://')):
                                url_candidates.append('https://' + url_raw)  # 添加 https://
                        
                        # 尝试从Domain列获取
                        if 'Domain' in row and row['Domain']:
                            domain_raw = row['Domain'].strip()
                            url_candidates.append(domain_raw)
                            # 也尝试添加和移除 https:// 和 www.
                            if domain_raw.startswith('https://'):
                                url_candidates.append(domain_raw[8:])  # 移除 https://
                            elif not domain_raw.startswith(('http://', 'https://')):
                                url_candidates.append('https://' + domain_raw)  # 添加 https://
                        
                        # 移除重复项
                        url_candidates = list(set(url_candidates))
                        
                        # 尝试所有可能的URL格式进行匹配
                        matched_result = None
                        for candidate in url_candidates:
                            if candidate in self.url_to_result_map:
                                matched_result = self.url_to_result_map[candidate]
                                url_key = candidate
                                break
                        
                        if matched_result:
                            matches_found += 1
                            # 添加联系信息到合并行
                            merged_row['ContactInfo_Company'] = matched_result.get('company_name', '')
                            merged_row['ContactInfo_Email'] = matched_result.get('email', '')
                            merged_row['ContactInfo_Phone'] = matched_result.get('phone', '')
                            merged_row['ContactInfo_Address'] = matched_result.get('address', '')
                            merged_row['ContactInfo_LinkedIn'] = matched_result.get('linkedin', '')
                            merged_row['ContactInfo_Twitter'] = matched_result.get('twitter', '')
                            merged_row['ContactInfo_Facebook'] = matched_result.get('facebook', '')
                            merged_row['ContactInfo_Instagram'] = matched_result.get('instagram', '')
                        else:
                            # 如果没有找到对应的联系信息，填充空值
                            for header in contact_headers:
                                merged_row[header] = ''
                        
                        writer.writerow(merged_row)
                    
                print(f"成功合并 {matches_found} 条联系信息到原始数据中")
                print(f"\nMerged results saved to: {merged_output_file}")
            except Exception as e:
                print(f"合并结果时出错: {e}")
                print(f"尝试继续保存常规结果...")
        
        # 常规保存结果
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                'Company Name', 'Email', 'Phone', 'Address', 
                'LinkedIn', 'Twitter', 'Facebook', 'Instagram', 'Website'
            ])
            # Write data
            for result in self.results:
                writer.writerow([
                    result.get('company_name', ''),
                    result.get('email', ''),
                    result.get('phone', ''),
                    result.get('address', ''),
                    result.get('linkedin', ''),
                    result.get('twitter', ''),
                    result.get('facebook', ''),
                    result.get('instagram', ''),
                    result.get('website', '')
                ])
        
        # Save to JSON
        json_output_file = self.output_file.replace('.csv', '.json')
        with open(json_output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to:")
        print(f"- CSV: {self.output_file}")
        print(f"- JSON: {json_output_file}")
        
        if merged_output_file:
            return self.output_file, json_output_file, merged_output_file
        return self.output_file, json_output_file

def main():
    parser = argparse.ArgumentParser(description="Extract contact information from company websites")
    
    # Input methods (choose one)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--url', help="Single website URL to process")
    input_group.add_argument('--url-list', help="Text file with list of website URLs (one per line)")
    input_group.add_argument('--csv', help="CSV file containing website URLs")
    
    # Additional options
    parser.add_argument('--output', '-o', help="Output CSV file name")
    parser.add_argument('--url-column', default='URL', help="CSV column name containing URLs (default: URL)")
    parser.add_argument('--domain-column', default='Domain', help="Alternative CSV column for domains (default: Domain)")
    parser.add_argument('--visit-contact', action='store_true', help="Visit contact pages (slower but might find more information)")
    parser.add_argument('--timeout', type=int, help="Page load timeout in milliseconds (default from .env or 30000)")
    parser.add_argument('--headless', action='store_true', help="Run browser in headless mode (no visible UI)")
    parser.add_argument('--merge-results', action='store_true', help="Merge contact info results with input CSV file")
    
    args = parser.parse_args()
    
    # 处理命令行参数
    visit_contact_page = args.visit_contact
    
    # 处理超时参数
    timeout = None
    if args.timeout:
        os.environ["TIMEOUT"] = str(args.timeout)
    
    # 处理headless参数
    if args.headless:
        os.environ["HEADLESS"] = "true"
    
    # 根据输入CSV文件生成输出文件名
    output_file = args.output
    if args.csv and not output_file:
        # 从CSV文件路径中提取文件名
        csv_filename = os.path.basename(args.csv)
        # 添加contact_info_前缀
        output_file = f"contact_info_{csv_filename}"
    
    # Create extractor
    extractor = ContactExtractor(
        output_file=output_file, 
        visit_contact_page=visit_contact_page,
        merge_with_input=args.merge_results and args.csv
    )
    
    if args.url:
        # Process single URL
        extractor.process_url(args.url)
    
    elif args.url_list:
        # Process URL list from text file
        try:
            with open(args.url_list, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
                extractor.process_url_list(urls)
        except Exception as e:
            print(f"Error reading URL list file: {e}")
    
    elif args.csv:
        # Process URLs from CSV file
        extractor.process_csv_file(
            args.csv, 
            url_column=args.url_column,
            domain_column=args.domain_column
        )
    
    # Save results
    extractor.save_results()

if __name__ == "__main__":
    main() 