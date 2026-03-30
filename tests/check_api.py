# test_api.py
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# 加载环境变量
load_dotenv(override=True)

model_name = os.getenv("MODEL_NAME")
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE")

print(model_name)
print(api_key)
print(base_url)

print(f"正在测试 API Key: {api_key[:8]}... (已隐藏后缀)")
print(f"API Base URL: {base_url}")

model = init_chat_model(
        model_name,
        model_provider="openai",
        temperature=0.7,
        api_key=api_key,
        base_url=base_url,
    )

try:
    # response = client.chat.completions.create(
    #     model="Qwen/Qwen2.5-7B-Instruct", # 或者你在 .env 里配置的模型名
    #     messages=[{"role": "user", "content": "你好"}],
    #     max_tokens=50
    # )
    response = model.invoke("你好")
    print("\n✅ API Key 有效！模型回复：")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"\n❌ API 调用失败: {e}")
