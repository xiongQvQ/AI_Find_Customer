#!/usr/bin/env python3
"""
测试增强版意图识别功能
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_search.nodes.enhanced_intent_recognition import enhanced_intent_recognition_node
from langgraph_search.state import create_initial_state

def test_intent_recognition():
    """测试意图识别功能"""
    
    test_cases = [
        "深圳的智能机器人创业公司",
        "腾讯的技术总监联系方式",
        "北京新能源汽车公司的销售经理",
        "上海软件公司",
        "广州制造业企业的CEO"
    ]
    
    print("开始测试增强版意图识别功能...")
    print("=" * 60)
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {query}")
        print("-" * 40)
        
        try:
            # 创建初始状态
            state = create_initial_state(query)
            
            # 执行意图识别
            result = enhanced_intent_recognition_node.execute(state)
            
            # 输出结果
            print(f"识别意图: {result.get('detected_intent', 'unknown')}")
            print(f"置信度: {result.get('intent_confidence', 0):.2f}")
            
            if 'parsed_query' in result:
                parsed = result['parsed_query']
                print("解析结果:")
                print(f"  - 地理位置: {parsed.get('location', '未指定')}")
                print(f"  - 行业领域: {parsed.get('industry', '未指定')}")
                print(f"  - 公司类型: {parsed.get('company_type', '未指定')}")
                print(f"  - 目标职位: {parsed.get('target_position', '未指定')}")
                print(f"  - 特定公司: {parsed.get('specific_company', '未指定')}")
            
            if 'errors' in result and result['errors']:
                print(f"错误信息: {result['errors']}")
                
        except Exception as e:
            print(f"测试失败: {e}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_intent_recognition()