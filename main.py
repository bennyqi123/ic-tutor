import streamlit as st
from openai import OpenAI
import os
import re # 用来提取代码块的

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="IC 芯手村 - 集成电路全能导师", 
    page_icon="chip", 
    layout="wide"
)

# ==================== 样式优化 ====================
st.markdown("""
<style>
    .stButton>button {
        border-radius: 20px;
        background-color: #f0f2f6;
        border: none;
        color: #31333F;
    }
    .stButton>button:hover {
        background-color: #ff4b4b;
        color: white;
    }
    .chat-container {
        border-radius: 10px;
        padding: 20px;
        background-color: #ffffff;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ==================== 侧边栏配置 ====================
with st.sidebar:
    st.title("⚙️ 芯手村控制台")
    
    # 1. 简单的 API Key 输入 (你要求的)
    api_key = st.text_input("🔑 DeepSeek API Key", type="password", help="在此输入你的 sk- 开头的密钥")
    
    st.markdown("---")
    
    # 2. 学习模式
    st.markdown("### 🎓 选择段位")
    difficulty = st.radio(
        "当前身份：", 
        ["小白入门 (通俗比喻+表情包)", "进阶学习 (原理+核心公式)", "专家深究 (参数+良率痛点)"],
        index=0
    )
    
    st.markdown("### 🧭 探索领域")
    # 这里定义领域，后面会联动推荐问题
    domain = st.selectbox(
        "你想了解哪个方向？", 
        ["工艺原理 (光刻/刻蚀...)", "半导体物理 (能带/PN结...)", "设备构造 (EUV/PVD...)", "故障分析 (划痕/空洞...)", "行业职场 (薪资/前景...)"]
    )

# ==================== 动态推荐问题逻辑 ====================
# 这是一个字典，根据上面的 domain 自动切换问题
question_bank = {
    "工艺原理 (光刻/刻蚀...)": [
        "🍟 芯片制造全流程 (用做菜比喻)",
        "📷 光刻机到底在干什么？",
        "⚡ 为什么刻蚀像'雕刻'？",
        "💧 清洗工艺真的很重要吗？"
    ],
    "半导体物理 (能带/PN结...)": [
        "🧱 为什么硅是半导体的神？",
        "⚡ 什么是 PN 结？(用水流比喻)",
        "🔋 摩尔定律失效了吗？",
        "🌡️ 温度对芯片有什么影响？"
    ],
    "设备构造 (EUV/PVD...)": [
        "🚜 光刻机内部长什么样？",
        "🌪️ 真空环境是怎么做到的？",
        "🦾 晶圆搬运机器人怎么工作？"
    ],
    "故障分析 (划痕/空洞...)": [
        "🔍 晶圆上有划痕怎么办？",
        "💥 为什么芯片会短路？",
        "🦠 灰尘是良率的最大杀手吗？"
    ],
    "行业职场 (薪资/前景...)": [
        "💰 IC 行业校招薪资大概多少？",
        "🏃‍♂️ 做工艺整合(PIE)累不累？",
        "📈 现在的行业风口在哪里？"
    ]
}

# ==================== 主界面 ====================
st.title("🤖 IC 芯手村 - 你的第一位 AI 导师")
st.caption(f"当前模式：{domain} | {difficulty}")

# 动态显示推荐问题
st.markdown("##### 💡 猜你想问：")
current_questions = question_bank.get(domain, [])
cols = st.columns(len(current_questions))
user_query = None

# 遍历生成按钮，如果点击了，就赋值给 user_query
for i, col in enumerate(cols):
    if col.button(current_questions[i], use_container_width=True):
        user_query = current_questions[i]

# 底部输入框 (如果有点击按钮，这里会被覆盖；如果没有，等待输入)
chat_input = st.chat_input("输入你想了解的 IC 知识...")
if chat_input:
    user_query = chat_input

# ==================== 核心处理逻辑 ====================
if user_query:
    if not api_key:
        st.warning("⚠️ 请先在左侧侧边栏填入 API Key 才能启动 AI 哦！")
        st.stop()

    # 1. 构建提示词 (Prompt Engineering)
    # 重点：命令 AI 用 Graphviz 语法画图
    visual_instruction = """
    【重要任务】
    在回答的最后，必须尝试根据刚才的内容生成一个简单的 Graphviz DOT 代码块来展示流程或逻辑关系。
    格式必须严格如下：
    ```graphviz
    digraph G {
        rankdir=LR;
        node [shape=box, style=filled, fillcolor=lightblue];
        A -> B -> C;
    }
    ```
    """
    
    if "小白" in difficulty:
        sys_prompt = f"你是一位幽默的科普作家。用户问的是【{domain}】领域。请用生活中的例子（做饭、盖楼、交通）来比喻。解释要通俗。{visual_instruction}"
    elif "专家" in difficulty:
        sys_prompt = f"你是一位20年经验的Fab厂技术总监。用户问的是【{domain}】领域。请用专业严谨的工程语言，包含参数、缺陷根因。{visual_instruction}"
    else:
        sys_prompt = f"你是大学微电子讲师。用户问的是【{domain}】领域。兼顾理论与通俗。{visual_instruction}"

    # 2. 显示用户提问
    with st.chat_message("user"):
        st.write(user_query)

    # 3. AI 回答
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_query}
                ],
                stream=True
            )
            
            # 流式输出文本
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)

            # 4. 自动提取并渲染图表 (Magic Happens Here)
            # 使用正则表达式寻找 ```graphviz ... ``` 代码块
            graphviz_match = re.search(r'```graphviz\n(.*?)\n```', full_response, re.DOTALL)
            
            if graphviz_match:
                dot_code = graphviz_match.group(1)
                st.markdown("### 🧩 逻辑可视化 (AI自动绘图)")
                try:
                    st.graphviz_chart(dot_code)
                except Exception as e:
                    st.error(f"图表渲染失败: {e}")
            else:
                # 如果AI没画出来，或者问题不需要画图
                pass

        except Exception as e:
            st.error(f"发生错误: {e}")
