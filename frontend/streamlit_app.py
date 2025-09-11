"""
deeplit-analyzer 前端界面
使用Streamlit构建用户界面
"""
import streamlit as st
import requests
import json
from typing import List, Dict, Optional
import time
from hashlib import md5

# 页面配置
st.set_page_config(
    page_title="deeplit-analyzer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #e7f3ff;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# API配置
API_BASE_URL = "http://127.0.0.1:8000"

def make_api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None, files: Optional[Dict] = None):
    """发送API请求"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, params=data)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"API请求失败: {str(e)}")
        return None
    except Exception as e:
        st.error(f"请求处理失败: {str(e)}")
        return None

def main():
    """主函数"""
    # 标题
    st.markdown('<h1 class="main-header">📚 deeplit-analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">deeplit-analyzer 学术文献智能处理系统</p>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.markdown("## 🔧 系统设置")
        
        # API地址配置
        api_url = st.text_input("API地址", value=API_BASE_URL, help="后端API服务地址")
        if api_url != API_BASE_URL:
            st.warning("请重启应用以应用新的API地址")
        
        # 健康检查
        if st.button("检查服务状态"):
            with st.spinner("检查服务状态..."):
                result = make_api_request("/health")
                if result:
                    st.success("✅ 服务运行正常")
                else:
                    st.error("❌ 服务连接失败")
        
        st.markdown("---")
        st.markdown("## 📖 使用说明")
        st.markdown("""
        1. **上传文档**: 支持PDF、Word等格式
        2. **等待处理**: 系统自动解析文档内容
        3. **查看总结**: 生成文献总结
        4. **智能问答**: 与文档进行对话
        """)
    
    # 主内容区域
    tab1, tab2, tab3, tab4 = st.tabs(["📄 文档管理", "📝 文献总结", "💬 智能问答", "🔍 文档检索"])
    
    with tab1:
        document_management_tab()
    
    with tab2:
        summarization_tab()
    
    with tab3:
        qa_tab()
    
    with tab4:
        search_tab()

def document_management_tab():
    """文档管理标签页"""
    st.markdown('<h2 class="section-header">📄 文档管理</h2>', unsafe_allow_html=True)
    
    # 文档上传
    st.markdown("### 📤 上传文档")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "选择文档文件",
            type=['pdf', 'doc', 'docx', 'txt'],
            accept_multiple_files=True,
            help="支持PDF、Word、文本文件"
        )
    
    with col2:
        batch_name = st.text_input("批次名称", placeholder="可选")
    
    if st.button("🚀 开始上传", type="primary"):
        if uploaded_files:
            with st.spinner("正在上传文档..."):
                files_data = []
                for file in uploaded_files:
                    files_data.append(("files", (file.name, file, file.type)))
                
                if batch_name:
                    files_data.append(("batch_name", batch_name))
                
                result = make_api_request("/documents/upload", "POST", files=files_data)
                
                if result:
                    st.success(f"✅ 成功上传 {len(uploaded_files)} 个文件")
                    
                    # 显示上传结果
                    for doc in result.get("documents", []):
                        st.info(f"📄 {doc['filename']} - ID: {doc['id']}")
                    
                    # 刷新文档列表
                    st.rerun()
        else:
            st.warning("请先选择要上传的文件")
    
    st.markdown("---")
    
    # 从URL导入
    st.markdown("### 🌐 从URL导入")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        url = st.text_input("文献URL", placeholder="https://example.com/paper.pdf")
    
    with col2:
        filename = st.text_input("文件名", placeholder="可选")
    
    if st.button("📥 从URL导入"):
        if url:
            with st.spinner("正在从URL导入..."):
                data = {"url": url}
                if filename:
                    data["filename"] = filename
                
                result = make_api_request("/documents/upload/url", "POST", data=data)
                
                if result:
                    st.success("✅ 成功从URL导入文档")
                    doc = result.get("document", {})
                    st.info(f"📄 {doc.get('filename', '未知')} - ID: {doc.get('id', '未知')}")
        else:
            st.warning("请输入有效的URL")
    
    st.markdown("---")
    
    # 文档列表
    st.markdown("### 📋 文档列表")
    
    if st.button("🔄 刷新列表"):
        st.rerun()
    
    # 获取文档列表
    result = make_api_request("/documents/")
    
    if result is None:
        st.error("❌ 获取文档列表失败")
        return
    
    documents = result if isinstance(result, list) else []
    if not documents:
        st.info("📭 文件列表为空")
        return
    
    st.markdown(f"共找到 {len(documents)} 个文档")
    
    for doc in documents:
        with st.expander(f"📄 {doc['filename']} - {doc['status']}"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**ID**: {doc['id']}")
                st.write(f"**状态**: {doc['status']}")
                st.write(f"**上传时间**: {doc['created_at']}")
                if doc.get('page_count'):
                    st.write(f"**页数**: {doc['page_count']}")
                if doc.get('word_count'):
                    st.write(f"**字数**: {doc['word_count']}")
            
            with col2:
                if st.button(f"📊 查看详情", key=f"detail_{doc['id']}"):
                    st.session_state['detail_doc_id'] = doc['id']
                    st.session_state['detail_open'] = True
                    st.rerun()  # 修复：使用新版API
            
            with col3:
                if st.button(f"🗑️ 删除", key=f"delete_{doc['id']}"):
                    delete_document(doc['id'])

    # 在列表下方以全宽区域展示详情，避免被放入窄列
    if st.session_state.get('detail_open') and st.session_state.get('detail_doc_id'):
        st.markdown("---")
        view_document_details(st.session_state['detail_doc_id'])

def view_document_details(doc_id: str):
    """查看文档详情"""
    result = make_api_request(f"/documents/{doc_id}")
    
    if result:
        st.markdown("### 📊 文档详情")
        
        # 基本信息
        st.markdown("#### 基本信息")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**文件名**: {result['filename']}")
            st.write(f"**状态**: {result['status']}")
            st.write(f"**创建时间**: {result['created_at']}")
        
        with col2:
            st.write(f"**更新时间**: {result['updated_at']}")
            if result.get('page_count'):
                st.write(f"**页数**: {result['page_count']}")
            if result.get('word_count'):
                st.write(f"**字数**: {result['word_count']}")
        
        # 元数据（仅展示标题）
        if result.get('metadata'):
            st.markdown("#### 元数据")
            metadata = result['metadata']
            if metadata.get('title'):
                st.write(f"**标题**: {metadata['title']}")
        
        # 章节信息（仅展示内容前150字的预览，不显示全文）
        if result.get('sections'):
            st.markdown("#### 章节信息")
            sections = result['sections']
            max_sections = min(5, len(sections))
            for section in sections[:max_sections]:
                title = section.get('title', '未命名章节')
                content = section.get('content', '')
                preview = content[:150] + ("..." if len(content) > 150 else "")
                st.markdown(f"**📑 {title}**")
                st.write(preview)
        
        # 处理错误
        if result.get('processing_errors'):
            st.markdown("#### 处理错误")
            for error in result['processing_errors']:
                st.error(f"❌ {error}")

def delete_document(doc_id: str):
    """删除文档"""
    result = make_api_request(f"/documents/{doc_id}", "DELETE")
    
    if result:
        st.success("✅ 文档删除成功")
        st.rerun()
    else:
        st.error("❌ 文档删除失败")

def summarization_tab():
    """文献总结标签页"""
    st.markdown('<h2 class="section-header">📝 文献总结</h2>', unsafe_allow_html=True)
    
    # 获取文档列表
    result = make_api_request("/documents/")
    
    if not result:
        st.error("❌ 获取文档列表失败")
        return
    
    documents = result
    if not documents:
        st.info("📭 请先上传文档")
        return
    
    # 选择文档
    doc_options = {f"{doc['filename']} ({doc['status']})": doc['id'] for doc in documents}
    selected_doc = st.selectbox("选择文档", options=list(doc_options.keys()))
    
    if not selected_doc:
        return
    
    doc_id = doc_options[selected_doc]
    
    # 总结类型选择
    st.markdown("### 📋 总结类型")
    
    summary_type = st.radio(
        "选择总结类型",
        ["全文献概括总结", "章节聚焦总结", "定制化总结"],
        horizontal=True
    )
    
    if summary_type == "全文献概括总结":
        if st.button("🚀 生成全文献总结", type="primary"):
            with st.spinner("正在生成总结..."):
                result = make_api_request(f"/summaries/full/{doc_id}")
                
                if result:
                    st.success("✅ 总结生成成功")
                    
                    # 显示总结
                    st.markdown("### 📄 文献总结")
                    st.markdown(result['summary'])
                    
                    # 显示元数据
                    if result.get('metadata'):
                        metadata = result['metadata']
                        st.markdown("#### 📊 总结信息")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**字数**: {metadata.get('word_count', 0)}")
                        with col2:
                            st.write(f"**生成时间**: {metadata.get('generated_at', '未知')}")
                        with col3:
                            st.write(f"**文档ID**: {metadata.get('document_id', '未知')}")
    
    elif summary_type == "章节聚焦总结":
        # 获取章节列表
        doc_result = make_api_request(f"/documents/{doc_id}")
        
        if doc_result and doc_result.get('sections'):
            sections = [section['title'] for section in doc_result['sections']]
            selected_section = st.selectbox("选择章节", sections)
            
            if st.button("🚀 生成章节总结", type="primary"):
                with st.spinner("正在生成章节总结..."):
                    result = make_api_request(f"/summaries/section/{doc_id}", data={"section_name": selected_section})
                    
                    if result:
                        st.success("✅ 章节总结生成成功")
                        
                        # 显示总结
                        st.markdown(f"### 📑 {selected_section} 总结")
                        st.markdown(result['summary'])
        else:
            st.warning("该文档没有可用的章节信息")
    
    elif summary_type == "定制化总结":
        st.markdown("### 🎯 定制选项")
        
        # 获取总结模板
        templates_result = make_api_request("/summaries/templates")
        
        if templates_result:
            templates = templates_result['templates']
            template_options = {template['name']: template['id'] for template in templates}
            selected_template = st.selectbox("选择总结模板", options=list(template_options.keys()))
            
            # 获取关键词建议
            keywords_result = make_api_request(f"/summaries/keywords/{doc_id}")
            suggested_keywords = keywords_result.get('keywords', []) if keywords_result else []
            
            # 关键词选择
            selected_keywords = st.multiselect(
                "选择关键词（可选）",
                options=suggested_keywords,
                help="选择要重点总结的关键词"
            )
            
            if st.button("🚀 生成定制总结", type="primary"):
                with st.spinner("正在生成定制总结..."):
                    data = {}
                    if selected_template:
                        data['template'] = template_options[selected_template]
                    if selected_keywords:
                        data['keywords'] = selected_keywords
                    
                    result = make_api_request(f"/summaries/custom/{doc_id}", "POST", data=data)
                    
                    if result:
                        st.success("✅ 定制总结生成成功")
                        
                        # 显示总结
                        st.markdown("### 📄 定制总结")
                        st.markdown(result['summary'])
                        
                        # 显示定制信息
                        if result.get('metadata'):
                            metadata = result['metadata']
                            st.markdown("#### 📊 定制信息")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if metadata.get('template'):
                                    st.write(f"**模板**: {metadata['template']}")
                                if metadata.get('keywords'):
                                    st.write(f"**关键词**: {', '.join(metadata['keywords'])}")
                            
                            with col2:
                                st.write(f"**生成时间**: {metadata.get('generated_at', '未知')}")

import streamlit as st
from hashlib import md5

def qa_tab():
    """智能问答标签页"""
    st.markdown('<h2 class="section-header">💬 智能问答</h2>', unsafe_allow_html=True)

    # --- SessionState 初始化 ---
    if "qa_question" not in st.session_state:
        st.session_state.qa_question = ""
    if "qa_selected_doc_id" not in st.session_state:
        st.session_state.qa_selected_doc_id = None
    if "qa_suggestion_selected" not in st.session_state:
        st.session_state.qa_suggestion_selected = None  # 记住上次选择的建议
    if "qa_result" not in st.session_state:
        st.session_state.qa_result = None  # 保存最新的QA结果

    # --- 获取文档列表 ---
    result = make_api_request("/documents/")
    if result is None:
        st.error("❌ 获取文档列表失败：服务无响应")
        return
    documents = result or []
    if not documents:
        st.info("📭 暂无可用文档，请先上传并完成处理")
        return

    # 用 index + format_func 避免同名覆盖
    doc_labels = [f"{doc.get('filename','未知文件')}（{doc.get('status','未知状态')}）" for doc in documents]

    # 恢复选中
    idx_default = 0
    if st.session_state.qa_selected_doc_id:
        for i, d in enumerate(documents):
            if d.get("id") == st.session_state.qa_selected_doc_id:
                idx_default = i
                break

    selected_index = st.selectbox(
        "选择文档",
        options=list(range(len(documents))),
        index=idx_default,
        format_func=lambda i: doc_labels[i],
        key="qa_doc_selectbox",
    )
    selected_doc = documents[selected_index]
    doc_id = selected_doc.get("id")
    st.session_state.qa_selected_doc_id = doc_id

    # 文档 Meta（按需显示你后端实际字段）
    with st.expander("📄 文档信息", expanded=False):
        cols = st.columns(3)
        cols[0].metric("状态", selected_doc.get("status", "-"))
        cols[1].metric("页数", selected_doc.get("pages", "-"))
        cols[2].metric("最后更新", selected_doc.get("updated_at", "-"))
        if selected_doc.get("notes"):
            st.caption(f"备注：{selected_doc['notes']}")

    # --- 获取问题建议（与文档选择同风格：selectbox）---
    suggestions = []
    suggestions_result = make_api_request(f"/qa/suggestions/{doc_id}")
    if suggestions_result:
        suggestions = suggestions_result.get("suggestions", []) or []

    if suggestions:
        st.markdown("### 💡 问题建议")
        
        # 添加占位选项，避免预选中任何建议问题
        suggestion_options = ["请选择一个建议问题..."] + suggestions
        
        # 默认选择：优先用当前文本域内容（若在建议列表里），否则用上次选择，最后回退到占位项
        if st.session_state.qa_question in suggestions:
            default_idx = suggestions.index(st.session_state.qa_question) + 1  # +1 因为有占位项
        elif st.session_state.qa_suggestion_selected in suggestions:
            default_idx = suggestions.index(st.session_state.qa_suggestion_selected) + 1
        else:
            default_idx = 0  # 选中占位项

        def _apply_suggestion():
            sel = st.session_state.qa_suggestion_select
            # 如果选择的是占位项，不执行任何操作
            if sel == "请选择一个建议问题...":
                return
            st.session_state.qa_suggestion_selected = sel
            st.session_state.qa_question = sel  # 自动填充到文本域

        st.selectbox(
            "选择一个建议问题：",
            options=suggestion_options,
            index=default_idx,
            key="qa_suggestion_select",
            on_change=_apply_suggestion,
        )
        st.caption("提示：选择后会自动填入下方输入框。")
        st.divider()

    # --- 提问（form 保证原子提交）---
    st.markdown("### ❓ 提出问题")
    with st.form("qa_ask_form", clear_on_submit=False):
        question = st.text_area(
            "输入您的问题",
            value=st.session_state.qa_question,
            height=120,
            placeholder="例如：这篇文献的主要研究方法是什么？",
            key="qa_question_input",
        )
        c1, c2, _ = st.columns([1, 1, 4])
        submit = c1.form_submit_button("🚀 提问", use_container_width=True)
        clear = c2.form_submit_button("🧹 清空", use_container_width=True)

    if clear:
        st.session_state.qa_question = ""
        st.toast("已清空问题", icon="🧹")
        st.rerun()  # 强制页面重新运行以刷新text_area显示

    if submit:
        if not question.strip():
            st.warning("请输入问题")
            st.stop()

        with st.spinner("正在思考中..."):
            payload = {"document_id": doc_id, "question": question.strip()}
            qa_result = make_api_request("/qa/ask", method="POST", data=payload)

        # 统一错误处理并中断
        if not qa_result:
            st.error("❌ 回答问题失败：服务无响应或网络异常")
            st.stop()
        if isinstance(qa_result, dict) and qa_result.get("error"):
            msg = qa_result.get("message") or qa_result.get("detail") or "未知错误"
            st.error(f"❌ 回答问题失败：{msg}")
            st.stop()

        # 成功渲染
        st.success("✅ 回答生成成功")
        st.session_state.qa_question = question  # 记录当前问题
        st.session_state.qa_result = qa_result  # 保存结果到session_state以便持久显示

    # 显示之前的QA结果（如果有的话）
    if 'qa_result' in st.session_state and st.session_state.qa_result:
        qa_result = st.session_state.qa_result
        
        st.markdown("### 🤖 AI 回答")
        st.markdown(qa_result.get("answer", "_（无内容）_"))

        # 置信度
        try:
            confidence = float(qa_result.get("confidence", 0.0) or 0.0)
        except Exception:
            confidence = 0.0
        st.markdown("**置信度**")
        st.progress(min(max(confidence, 0.0), 1.0))
        st.caption(f":blue[{confidence:.2f}]")

        # 来源
        sources = qa_result.get("sources") or []
        if sources:
            st.markdown("### 📚 答案来源")
            for i, src in enumerate(sources, start=1):
                title = (src.get("title") or f"来源 {i}").strip()
                try:
                    sconf = float(src.get("confidence", 0.0) or 0.0)
                except Exception:
                    sconf = 0.0
                with st.expander(f"{title}（参考置信度：{sconf:.2f}）", expanded=False):
                    if src.get("url"):
                        st.markdown(f"- 🔗 [打开原文]({src['url']})")
                    if src.get("page"):
                        st.markdown(f"- 📄 页码：{src['page']}")
                    if src.get("chunk_id"):
                        st.markdown(f"- 🧩 片段：{src['chunk_id']}")
                    st.write((src.get("source_text") or "").strip() or "_（无可显示的片段）_")

        # 后续可追问（改为一行一个按钮，竖排且铺满宽度）
        followups = qa_result.get("follow_up_suggestions") or []
        if followups:
            st.markdown("### 💡 后续可追问")
            st.markdown("点击下方按钮将问题自动填入上方文本框：")
            
            # 添加调试信息
            st.caption(f"当前问题内容：{st.session_state.qa_question[:50]}{'...' if len(st.session_state.qa_question) > 50 else ''}")
            
            for i, s in enumerate(followups):
                # 使用更简单的key生成方式
                key = f"followup_btn_{doc_id}_{i}_persistent"
                button_clicked = st.button(s, key=key, use_container_width=True)
                
                if button_clicked:
                    # 添加更多调试信息
                    st.info(f"🔄 按钮被点击！正在设置问题为：{s}")
                    st.session_state.qa_question = s
                    st.toast(f"✅ 已选择追问：{s[:50]}{'...' if len(s) > 50 else ''}", icon="💭")
                    st.rerun()


def search_tab():
    """文档检索标签页"""
    st.markdown('<h2 class="section-header">🔍 文档检索</h2>', unsafe_allow_html=True)
    
    # 获取文档列表
    result = make_api_request("/documents/")
    
    if not result:
        st.error("❌ 获取文档列表失败")
        return
    
    documents = result
    if not documents:
        st.info("📭 请先上传文档")
        return
    
    # 选择文档
    doc_options = {f"{doc['filename']} ({doc['status']})": doc['id'] for doc in documents}
    selected_doc = st.selectbox("选择文档", options=list(doc_options.keys()), key="search_doc_select")
    
    if not selected_doc:
        return
    
    doc_id = doc_options[selected_doc]
    
    # 搜索查询
    st.markdown("### 🔍 搜索查询")
    
    query = st.text_input("输入搜索关键词", placeholder="例如：研究方法、实验结果、结论")
    
    if st.button("🚀 搜索", type="primary"):
        if query:
            with st.spinner("正在搜索..."):
                result = make_api_request(f"/qa/search", data={"document_id": doc_id, "q": query})
                
                if result:
                    st.success("✅ 搜索完成")
                    
                    # 显示搜索结果
                    st.markdown("### 📋 搜索结果")
                    
                    results = result.get('results', [])
                    if results:
                        for i, search_result in enumerate(results):
                            with st.expander(f"结果 {i+1} (相似度: {search_result.get('score', 0):.3f})"):
                                st.write(search_result.get('text', ''))
                    else:
                        st.info("未找到相关结果")
                else:
                    st.error("❌ 搜索失败")
        else:
            st.warning("请输入搜索关键词")

if __name__ == "__main__":
    main()
