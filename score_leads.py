#!/usr/bin/env python3
"""
AI客户发现工具 - 智能评分系统
基于行业匹配度对潜在客户进行评分和优先级排序

核心功能：
1. 行业匹配度评分 (0-100分)
2. 关键决策者检测
3. 联系信息完整性评估
4. 智能标签分类

使用方法:
python score_leads.py --company-csv output/company/xxx.csv --profile profiles/solar_profile.yaml
"""

import pandas as pd
import argparse
import yaml
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

class LeadScorer:
    """智能客户评分引擎"""
    
    def __init__(self, profile_config: Dict[str, Any]):
        self.profile = profile_config
        self.scoring_method = profile_config.get('scoring_method', 'keyword')
        
        # 决策者职位关键词（权重越高越重要）
        self.decision_maker_titles = {
            'CEO': 10, 'Chief Executive Officer': 10, 'President': 9,
            'CTO': 9, 'Chief Technology Officer': 9, 'CIO': 9,
            'VP': 8, 'Vice President': 8, 'Director': 7, 'Head of': 6,
            'Manager': 5, 'Procurement': 8, 'Purchasing': 8,
            'Supply Chain': 7, 'Operations': 6, 'Sales': 5
        }
    
    def score_industry_match(self, company_text: str) -> Tuple[float, List[str]]:
        """
        计算行业匹配度得分
        
        Returns:
            tuple: (得分, 匹配的关键词列表)
        """
        if self.scoring_method == 'keyword':
            return self._score_by_keywords(company_text)
        else:
            # 未来可以扩展embedding或LLM方法
            return self._score_by_keywords(company_text)
    
    def _score_by_keywords(self, text: str) -> Tuple[float, List[str]]:
        """基于关键词的评分算法"""
        if not text:
            return 0.0, []
        
        text_lower = text.lower()
        score = 0
        matched_keywords = []
        
        # 正向关键词评分
        for keyword, weight in self.profile.get('positive_keywords', {}).items():
            count = text_lower.count(keyword.lower())
            if count > 0:
                score += count * weight
                matched_keywords.append(f"+{keyword}({count}x{weight})")
        
        # 负向关键词评分
        for keyword, weight in self.profile.get('negative_keywords', {}).items():
            count = text_lower.count(keyword.lower())
            if count > 0:
                score += count * weight  # weight already negative
                matched_keywords.append(f"{keyword}({count}x{weight})")
        
        return max(0, score), matched_keywords
    
    def score_decision_maker_presence(self, employee_data: str) -> Tuple[int, List[str]]:
        """
        评估决策者存在情况
        
        Returns:
            tuple: (得分, 发现的决策者列表)
        """
        if not employee_data:
            return 0, []
        
        score = 0
        found_titles = []
        
        for title, weight in self.decision_maker_titles.items():
            if title.lower() in employee_data.lower():
                score = max(score, weight)  # 取最高权重
                found_titles.append(title)
        
        return score, found_titles
    
    def score_contact_completeness(self, emails: str, phones: str, linkedin: str) -> Tuple[int, Dict[str, bool]]:
        """
        评估联系信息完整性
        
        Returns:
            tuple: (得分, 信息完整性字典)
        """
        score = 0
        completeness = {
            'has_email': bool(emails and emails.strip() and emails != ''),
            'has_phone': bool(phones and phones.strip() and phones != ''),
            'has_linkedin': bool(linkedin and linkedin.strip() and linkedin != '')
        }
        
        if completeness['has_email']:
            score += 30
        if completeness['has_phone']:
            score += 20
        if completeness['has_linkedin']:
            score += 15
        
        return score, completeness
    
    def generate_tags(self, company_text: str, score_data: Dict) -> List[str]:
        """
        基于公司信息和评分数据生成智能标签
        """
        tags = []
        
        # 基于行业匹配度的标签
        industry_score = score_data.get('industry_match_score', 0)
        if industry_score >= 80:
            tags.append('高匹配度')
        elif industry_score >= 60:
            tags.append('中等匹配度')
        elif industry_score >= 30:
            tags.append('低匹配度')
        else:
            tags.append('不匹配')
        
        # 基于决策者存在的标签
        if score_data.get('decision_maker_score', 0) >= 8:
            tags.append('高级决策者')
        elif score_data.get('decision_maker_score', 0) >= 5:
            tags.append('中级决策者')
        
        # 基于联系信息完整性的标签
        contact_score = score_data.get('contact_completeness_score', 0)
        if contact_score >= 50:
            tags.append('联系信息完整')
        elif contact_score >= 30:
            tags.append('联系信息部分')
        else:
            tags.append('联系信息缺失')
        
        # 基于公司规模的标签（通过关键词推断）
        if company_text:
            text_lower = company_text.lower()
            if any(kw in text_lower for kw in ['fortune 500', 'multinational', 'global', 'international']):
                tags.append('大型企业')
            elif any(kw in text_lower for kw in ['enterprise', 'corporation', 'inc', 'ltd']):
                tags.append('中型企业')
            else:
                tags.append('小型企业')
        
        return tags
    
    def calculate_final_score(self, industry_score: float, decision_maker_score: int, 
                            contact_score: int) -> float:
        """
        计算最终综合得分
        
        权重分配：
        - 行业匹配度: 60%
        - 决策者存在: 25%
        - 联系信息完整性: 15%
        """
        # 归一化各项得分到0-100
        industry_normalized = min(industry_score, 100)
        decision_normalized = min(decision_maker_score * 10, 100)  # 决策者得分*10
        contact_normalized = min(contact_score, 100)
        
        final_score = (
            industry_normalized * 0.6 +
            decision_normalized * 0.25 +
            contact_normalized * 0.15
        )
        
        return round(final_score, 2)

def merge_data_files(company_file: str, contact_file: str = None, employee_file: str = None) -> pd.DataFrame:
    """
    合并公司、联系信息和员工数据
    """
    # 读取公司数据
    df_company = pd.read_csv(company_file)
    
    # 合并联系信息数据（如果提供）
    if contact_file and os.path.exists(contact_file):
        df_contact = pd.read_csv(contact_file)
        # 基于domain字段合并
        df_company = pd.merge(df_company, df_contact, on='domain', how='left')
    
    # 合并员工数据（如果提供）
    if employee_file and os.path.exists(employee_file):
        # 员工数据需要按公司聚合
        df_employee = pd.read_csv(employee_file)
        # 将同一公司的员工信息聚合成文本
        employee_grouped = df_employee.groupby('company_name')['title'].apply(
            lambda x: ' | '.join(x.astype(str))
        ).reset_index()
        employee_grouped.rename(columns={'title': 'employee_titles'}, inplace=True)
        
        df_company = pd.merge(df_company, employee_grouped, 
                            left_on='name', right_on='company_name', how='left')
    
    return df_company

def main():
    parser = argparse.ArgumentParser(
        description="AI客户发现工具 - 智能评分系统",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--company-csv", required=True,
                       help="公司数据CSV文件路径")
    parser.add_argument("--profile", required=True,
                       help="目标客户画像配置文件路径 (YAML)")
    parser.add_argument("--contact-csv", default=None,
                       help="联系信息CSV文件路径 (可选)")
    parser.add_argument("--employee-csv", default=None,
                       help="员工信息CSV文件路径 (可选)")
    parser.add_argument("--output-dir", default="output/scored",
                       help="评分结果输出目录")
    parser.add_argument("--min-score", type=float, default=0,
                       help="最低分数阈值，低于此分数的客户将被过滤")
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.company_csv):
        print(f"错误：公司数据文件不存在 - {args.company_csv}")
        return
    
    if not os.path.exists(args.profile):
        print(f"错误：配置文件不存在 - {args.profile}")
        return
    
    # 创建输出目录
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # 加载配置文件
    with open(args.profile, 'r', encoding='utf-8') as f:
        profile_config = yaml.safe_load(f)
    
    print(f"📊 使用配置: {profile_config.get('profile_name', '未命名')}")
    print(f"📁 处理文件: {args.company_csv}")
    
    # 合并数据
    df = merge_data_files(args.company_csv, args.contact_csv, args.employee_csv)
    print(f"📈 加载了 {len(df)} 家公司数据")
    
    # 初始化评分器
    scorer = LeadScorer(profile_config)
    
    # 处理每家公司
    results = []
    
    for idx, row in df.iterrows():
        # 构建公司描述文本（合并多个字段）
        company_text = ' '.join([
            str(row.get('name', '')),
            str(row.get('title', '')),
            str(row.get('description', '')),
        ])
        
        # 计算各项得分
        industry_score, matched_keywords = scorer.score_industry_match(company_text)
        
        decision_maker_score, found_titles = scorer.score_decision_maker_presence(
            str(row.get('employee_titles', ''))
        )
        
        contact_score, contact_completeness = scorer.score_contact_completeness(
            str(row.get('emails', '')),
            str(row.get('phones', '')),
            str(row.get('linkedin', ''))
        )
        
        # 计算最终得分
        final_score = scorer.calculate_final_score(
            industry_score, decision_maker_score, contact_score
        )
        
        # 生成评分详情
        score_data = {
            'industry_match_score': round(industry_score, 2),
            'decision_maker_score': decision_maker_score,
            'contact_completeness_score': contact_score,
            'final_score': final_score
        }
        
        # 生成标签
        tags = scorer.generate_tags(company_text, score_data)
        
        # 构建结果记录
        result = row.to_dict()
        result.update({
            'final_score': final_score,
            'industry_match_score': score_data['industry_match_score'],
            'decision_maker_score': decision_maker_score,
            'contact_completeness_score': contact_score,
            'matched_keywords': ' | '.join(matched_keywords),
            'found_decision_makers': ' | '.join(found_titles),
            'contact_completeness': json.dumps(contact_completeness, ensure_ascii=False),
            'tags': ' | '.join(tags),
            'score_reason': f"行业匹配:{score_data['industry_match_score']}, 决策者:{decision_maker_score}, 联系信息:{contact_score}",
            'scoring_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        results.append(result)
    
    # 转换为DataFrame并按得分排序
    df_scored = pd.DataFrame(results)
    df_scored = df_scored.sort_values('final_score', ascending=False)
    
    # 过滤低分客户
    if args.min_score > 0:
        original_count = len(df_scored)
        df_scored = df_scored[df_scored['final_score'] >= args.min_score]
        print(f"🔍 应用最低分数阈值 {args.min_score}，过滤后剩余 {len(df_scored)}/{original_count} 家公司")
    
    # 生成输出文件名
    company_filename = Path(args.company_csv).stem
    profile_name = profile_config.get('profile_name', 'unknown').replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    output_file = f"{args.output_dir}/scored_{company_filename}_{profile_name}_{timestamp}.csv"
    
    # 保存结果
    df_scored.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # 输出统计信息
    print(f"\n🎯 评分完成！结果保存至: {output_file}")
    print(f"📊 统计信息:")
    print(f"   总计: {len(df_scored)} 家公司")
    print(f"   平均得分: {df_scored['final_score'].mean():.2f}")
    print(f"   最高得分: {df_scored['final_score'].max():.2f}")
    print(f"   得分 >= 80: {len(df_scored[df_scored['final_score'] >= 80])} 家")
    print(f"   得分 >= 60: {len(df_scored[df_scored['final_score'] >= 60])} 家")
    
    # 显示前5名
    print(f"\n🏆 评分前5名:")
    for idx, row in df_scored.head(5).iterrows():
        print(f"   {row['name'][:30]:<30} | 得分: {row['final_score']:.1f} | {row['tags']}")

if __name__ == "__main__":
    main()