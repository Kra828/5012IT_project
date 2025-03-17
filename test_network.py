import requests
import os
import sys
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_basic_network():
    print("===== 基本网络连接测试 =====")
    try:
        r = requests.get('https://www.baidu.com', timeout=5)
        print(f"百度连接状态: {r.status_code}")
        return True
    except Exception as e:
        print(f"网络连接失败: {str(e)}")
        return False

def test_openai_connection():
    print("\n===== OpenAI API连接测试 =====")
    try:
        r = requests.get('https://api.openai.com/v1/models', timeout=5)
        print(f"OpenAI API连接状态: {r.status_code}")
        if r.status_code == 401:
            print("连接成功但需要认证，这是正常的")
            return True
        else:
            print(f"连接返回非预期状态码: {r.status_code}")
            return r.status_code < 500  # 服务器错误返回False
    except Exception as e:
        print(f"OpenAI API连接失败: {str(e)}")
        return False

def test_openai_api():
    print("\n===== OpenAI API调用测试 =====")
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("未找到OPENAI_API_KEY环境变量")
        return False
    
    print(f"API密钥: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=10
        )
        print(f"API调用成功! 回复: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"API调用失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始网络测试...\n")
    
    if not test_basic_network():
        print("\n基本网络连接失败，请检查您的网络连接")
        sys.exit(1)
    
    if not test_openai_connection():
        print("\nOpenAI API连接失败，可能是网络问题或API端点被屏蔽")
        sys.exit(1)
    
    if not test_openai_api():
        print("\nOpenAI API调用失败，请检查您的API密钥和网络连接")
        sys.exit(1)
    
    print("\n所有测试通过! 您的网络和API配置正常工作") 