import streamlit as st
from openai import OpenAI
import os
import re
from pypdf import PdfReader # 新增：用于读取PDF

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="IC 芯手村 - 集成电路全能工坊", 
    page_icon="🚀", 
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
    .report-box {
        border: 2px dashed #4CAF50;
        padding: 20px;
        border-radius: 10px;
        background-color: #f9fff9;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 侧边栏配置 ====================
with st.sidebar:
    st.title("⚙️ 芯手村控制台")
    api_key = st.text_input("🔑 DeepSeek API Key", type="password", help="在此输入你的 sk- 开头的密钥")
    
    st.markdown("---")
    
    # 核心导航栏：在这里切换四大功能
    st.markdown("### 🛠️ 选择工具")
    app_mode = st.radio(
        "你想做什么？",
        ["🤖 AI 导师对话 (基础)", "🗺️ 学习路径生成 (Priority 1)", "📝 实验报告生成 (Priority 2)", "📄 论文速读助手 (Priority 3)"]
    )
    
    st.markdown("---")
    # 公用设置
    if app_mode == "🤖 AI 导师对话 (基础)" or app_mode == "🗺️ 学习路径生成 (Priority 1)":
        st.markdown("### 🎓 身份设定")
        difficulty = st.selectbox("当前段位", ["小白 (通俗)", "进阶 (原理)", "专家 (参数)"])

# ==================== 通用函数 ====================
def get_client():
    if not api_key:
        st.warning("⚠️ 请先在左侧填入 API Key")
        st.stop()
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

def extract_graphviz(text):
    """从回答中提取图表代码"""
    match = re.search(r'```graphviz\n(.*?)\n```', text, re.DOTALL)
    if match:
        return match.group(1)
    return None

# ==================== 功能模块 1: AI 导师对话 ====================
if app_mode == "🤖 AI 导师对话 (基础)":
    st.title("🤖 IC 知识问答")
    st.caption("支持自动绘图的智能导师")
    
    domain = st.selectbox("探索领域", ["工艺原理", "半导体物理", "设备构造", "故障分析", "行业职场"])
    
    # 推荐问题 (简化版)
    q_bank = {
        "工艺原理": "光刻工艺的核心步骤是什么？",
        "半导体物理": "PN结的工作原理？",
        "故障分析": "晶圆表面划痕的来源分析"
    }
    if st.button(f"🎲 试一试：{q_bank.get(domain, '芯片是怎么造的？')}"):
        user_query = q_bank.get(domain)
    else:
        user_query = st.chat_input("输入问题...")

    if user_query:
        client = get_client()
        with st.chat_message("user"):
            st.write(user_query)
        
        with st.chat_message("assistant"):
            prompt = f"你是一位IC专家。用户：{difficulty}。问题：{user_query}。请详细回答。最后必须用 ```graphviz 语法画一个流程图或逻辑图。"
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                stream=False # 简单起见，这里暂关流式
            )
            ans = response.choices[0].message.content
            st.markdown(ans)
            
            dot_code = extract_graphviz(ans)
            if dot_code:
                st.graphviz_chart(dot_code)

# ==================== 功能模块 2: 学习路径生成器 (Priority 1) ====================
elif app_mode == "🗺️ 学习路径生成 (Priority 1)":
    st.title("🗺️ 个性化 IC 学习路径生成器")
    st.markdown("输入你的现状和目标，AI 为你定制专属技能树。")
    
    col1, col2 = st.columns(2)
    with col1:
        current_role = st.selectbox("我现在是...", ["大一新生 (零基础)", "大三/大四 (考研/找工作)", "研究生 (科研)", "转行工程师"])
    with col2:
        target_goal = st.text_input("我的目标是...", placeholder="例如：成为数字后端工程师 / 搞懂模拟IC设计")
    
    time_span = st.slider("计划时长 (周)", 4, 24, 12)
    
    if st.button("🚀 生成学习图谱"):
        client = get_client()
        with st.spinner("AI 正在规划你的成神之路..."):
            prompt = f"""
            用户角色：{current_role}
            目标：{target_goal}
            时长：{time_span}周。
            
            任务：
            1. 请制定一个详细的周计划。
            2. 推荐必看的经典书籍（如拉扎维、西电教材等）和工具（Virtuoso, DC等）。
            3. 【关键】请生成一个 Graphviz DOT 代码，展示"前置知识 -> 进阶知识 -> 实战项目"的依赖关系图。
            代码格式要求：
            ```graphviz
            digraph G {{
                rankdir=LR;
                node [shape=box, style=filled, fillcolor="#e1f5fe"];
                基础电路 -> 模电 -> 运放设计;
            }}
            ```
            """
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )
            ans = response.choices[0].message.content
            
            # 分栏显示
            t1, t2 = st.tabs(["📅 详细计划", "🌳 知识图谱"])
            with t1:
                st.markdown(ans)
            with t2:
                dot_code = extract_graphviz(ans)
                if dot_code:
                    st.graphviz_chart(dot_code)
                else:
                    st.warning("图谱生成失败，请重试")

# ==================== 功能模块 3: 实验报告生成器 (Priority 2) ====================
elif app_mode == "📝 实验报告生成 (Priority 2)":
    st.title("📝 实验报告自动生成助手")
    st.markdown("输入杂乱的数据，秒变标准 IEEE/高校 格式报告。")
    
    exp_name = st.text_input("实验名称", placeholder="例如：MOSFET 输出特性曲线测试")
    
    c1, c2 = st.columns(2)
    with c1:
        raw_data = st.text_area("在此粘贴实验数据/现象描述", height=200, placeholder="Vgs=1V时，Id=0.1mA...\n观察到饱和区电流基本不变...")
    with c2:
        requirements = st.text_area("报告要求", height=200, placeholder="需要包含：实验原理、数据表格、误差分析、结论。")
    
    if st.button("✨ 一键生成报告"):
        if not raw_data:
            st.error("请先输入数据！")
        else:
            client = get_client()
            with st.spinner("AI 正在撰写分析报告..."):
                prompt = f"""
                你是一个严谨的助教。请根据以下信息撰写一份完整的实验报告。
                实验名称：{exp_name}
                原始数据/现象：{raw_data}
                要求：{requirements}
                
                输出格式：Markdown。包含：
                1. 实验目的
                2. 实验原理 (简述)
                3. 数据处理与分析 (重点)
                4. 误差分析
                5. 结论
                """
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("### 📄 报告预览")
                st.markdown('<div class="report-box">', unsafe_allow_html=True)
                st.markdown(response.choices[0].message.content)
                st.markdown('</div>', unsafe_allow_html=True)
                st.download_button("📥 下载 Markdown", response.choices[0].message.content, "lab_report.md")

# ==================== 功能模块 4: 论文阅读助手 (Priority 3) ====================
elif app_mode == "📄 论文速读助手 (Priority 3)":
    st.title("📄 IC 论文速读助手")
    st.markdown("上传 PDF，自动提取工艺参数和创新点。")
    
    uploaded_file = st.file_uploader("上传论文 PDF", type=["pdf"])
    
    if uploaded_file is not None:
        try:
            # 读取 PDF 文本
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            st.success(f"成功读取 PDF，共 {len(reader.pages)} 页，字数：{len(text)}")
            
            if st.button("🔍 开始深度分析"):
                client = get_client()
                with st.spinner("正在解析关键工艺参数..."):
                    # 截取前 8000 字以防 token 溢出 (对于长论文)
                    prompt = f"""
                    这是集成电路领域的论文内容：
                    {text[:8000]}... (后略)
                    
                    请帮我提取以下核心信息，并用表格展示：
                    1. **关键工艺参数** (Process Parameters)：如栅长、氧化层厚度、掺杂浓度、供电电压等。
                    2. **性能指标** (Performance)：如增益、带宽、功耗、FOM。
                    3. **核心创新点** (Innovations)：这就到底改了什么？
                    4. **可复现性评估**：这篇论文是否给出了足够的步骤让人复现？缺什么数据？
                    """
                    
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.markdown(response.choices[0].message.content)
                    
        except Exception as e:
            st.error(f"解析 PDF 失败: {e}")
