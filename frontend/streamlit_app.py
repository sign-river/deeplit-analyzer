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


def load_conversation_list(document_id: str):
    """加载文档的对话列表"""
    try:
        result = make_api_request(f"/qa/conversations/{document_id}")
        if result:
            return result.get("conversations", [])
        return []
    except Exception as e:
        st.error(f"加载对话列表失败: {str(e)}")
        return []


def load_conversation_detail(conversation_id: str):
    """加载对话详细内容"""
    try:
        result = make_api_request(f"/qa/conversation/{conversation_id}/detail")
        return result
    except Exception as e:
        st.error(f"加载对话详情失败: {str(e)}")
        return None


def export_conversation(conversation_id: str, format_type: str = "json"):
    """导出对话记录"""
    try:
        result = make_api_request(f"/qa/conversation/{conversation_id}/export?format={format_type}")
        return result
    except Exception as e:
        st.error(f"导出对话记录失败: {str(e)}")
        return None


def delete_conversation(conversation_id: str):
    """删除对话记录"""
    try:
        result = make_api_request(f"/qa/conversation/{conversation_id}", method="DELETE")
        return result is not None
    except Exception as e:
        st.error(f"删除对话记录失败: {str(e)}")
        return False


def show_conversation_history_sidebar(document_id: str):
    """显示对话历史侧边栏 - 已弃用，现在在主页面显示"""
    pass  # 不再使用此函数，避免重复渲染


def show_conversation_detail_modal(conversation_detail):
    """显示对话详情"""
    st.markdown(f"## 💬 {conversation_detail['title']}")
    st.write(f"**文档**: {conversation_detail['document_title']}")
    st.write(f"**问题总数**: {conversation_detail['total_questions']}")
    
    st.markdown("### 对话内容")
    
    for i, entry in enumerate(conversation_detail['entries'], 1):
        with st.expander(f"问题 {i}: {entry['question'][:50]}{'...' if len(entry['question']) > 50 else ''}", expanded=False):
            st.markdown(f"**时间**: {entry['timestamp'][:19].replace('T', ' ')}")
            st.markdown(f"**问题**: {entry['question']}")
            st.markdown(f"**回答**: {entry['answer']}")
            if entry.get('confidence', 0) > 0:
                st.markdown(f"**置信度**: {entry['confidence']:.2f}")
            if entry.get('processing_time', 0) > 0:
                st.markdown(f"**处理时间**: {entry['processing_time']:.2f}秒")

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
        st.toast("列表已刷新", icon="🔄")
        st.rerun()  # 这个rerun是必要的，但添加了用户友好的提示
    
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
            
            # 获取关键词建议（带加载提示）
            st.markdown("#### 📝 关键词选择")
            
            # 使用缓存来避免重复加载
            cache_key = f"keywords_cache_{doc_id}"
            if cache_key not in st.session_state:
                # 显示加载状态
                with st.spinner("🔍 正在智能分析文档，提取关键词..."):
                    st.info("💡 AI正在分析文档内容，识别重要的学术术语和概念，请稍候...")
                    keywords_result = make_api_request(f"/summaries/keywords/{doc_id}")
                    suggested_keywords = keywords_result.get('keywords', []) if keywords_result else []
                    # 缓存结果
                    st.session_state[cache_key] = suggested_keywords
            else:
                # 使用缓存的结果
                suggested_keywords = st.session_state[cache_key]
            
            if suggested_keywords:
                # 关键词选择
                selected_keywords = st.multiselect(
                    "选择关键词（可选）",
                    options=suggested_keywords,
                    help="AI已为您提取了文档中的重要学术术语，请选择您感兴趣的关键词"
                )
                
                # 显示提取到的关键词数量
                st.success(f"✅ 成功提取 {len(suggested_keywords)} 个关键词")
                
                # 添加刷新按钮
                if st.button("🔄 重新提取关键词", help="重新分析文档并提取关键词"):
                    # 清除缓存并重新加载
                    if cache_key in st.session_state:
                        del st.session_state[cache_key]
                    st.rerun()
                    
            else:
                st.warning("⚠️ 关键词提取失败或未找到合适的关键词")
                st.info("💡 您仍可以选择总结模板来生成定制总结")
                selected_keywords = []
            
            # 生成按钮和条件检查
            st.markdown("#### 🚀 生成总结")
            
            # 检查是否有选择
            has_template = selected_template is not None
            has_keywords = 'selected_keywords' in locals() and selected_keywords
            
            # 初始化生成状态
            if 'custom_summary_generated' not in st.session_state:
                st.session_state.custom_summary_generated = False
            if 'custom_summary_result' not in st.session_state:
                st.session_state.custom_summary_result = None
                
            if has_template or has_keywords:
                generation_info = []
                if has_template:
                    generation_info.append(f"📋 模板: {selected_template}")
                if has_keywords:
                    generation_info.append(f"🔑 关键词: {len(selected_keywords)}个")
                
                st.info("将基于以下设置生成总结:\n" + "\n".join(generation_info))
                
                # 只有在没有生成结果时才显示生成按钮
                if not st.session_state.custom_summary_generated:
                    if st.button("🚀 生成定制总结", type="primary", key="generate_custom_summary"):
                        with st.spinner("正在生成定制总结..."):
                            data = {}
                            selected_template_name = None
                            if selected_template:
                                data['template'] = template_options[selected_template]
                                selected_template_name = selected_template  # 保存模板名称用于显示
                            if has_keywords:
                                data['keywords'] = selected_keywords
                            
                            result = make_api_request(f"/summaries/custom/{doc_id}", "POST", data=data)
                            
                            if result:
                                # 保存结果到session state
                                st.session_state.custom_summary_result = {
                                    'result': result,
                                    'template_name': selected_template_name,
                                    'keywords': selected_keywords if has_keywords else []
                                }
                                st.session_state.custom_summary_generated = True
                                st.rerun()
                else:
                    # 显示重新生成按钮
                    col_a, col_b = st.columns([1, 1])
                    with col_a:
                        if st.button("🔄 重新生成", type="secondary", key="regenerate_custom_summary"):
                            st.session_state.custom_summary_generated = False
                            st.session_state.custom_summary_result = None
                            st.rerun()
                    with col_b:
                        if st.button("✨ 生成新总结", type="primary", key="new_custom_summary"):
                            # 清除当前结果，允许重新选择参数
                            st.session_state.custom_summary_generated = False
                            st.session_state.custom_summary_result = None
                            st.rerun()
            else:
                st.warning("⚠️ 请至少选择一个总结模板或关键词")
                st.button("🚀 生成定制总结", type="primary", disabled=True)
                
            # 显示生成的结果（如果有）
            if st.session_state.custom_summary_result:
                saved_result = st.session_state.custom_summary_result
                result = saved_result['result']
                
                st.success("✅ 定制总结生成成功")
                
                # 显示总结
                st.markdown("### 📄 定制总结")
                st.markdown(result['summary'])
                
                # 显示定制信息
                st.markdown("#### 📊 定制信息")
                col1, col2 = st.columns(2)
                
                with col1:
                    if saved_result['template_name']:
                        st.write(f"**模板**: {saved_result['template_name']}")
                    if saved_result['keywords']:
                        st.write(f"**关键词**: {', '.join(saved_result['keywords'])}")
                
                with col2:
                    metadata = result.get('metadata', {})
                    st.write(f"**生成时间**: {metadata.get('generated_at', '未知')}")
                    if metadata.get('document_id'):
                        st.write(f"**文档ID**: {metadata['document_id'][:8]}...")

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
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None  # 当前对话ID
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []  # 对话历史记录
    if "show_history_sidebar" not in st.session_state:
        st.session_state.show_history_sidebar = False  # 是否显示历史记录侧边栏
    if "view_conversation_id" not in st.session_state:
        st.session_state.view_conversation_id = None  # 要查看详情的对话ID
    if "last_loaded_doc_id" not in st.session_state:
        st.session_state.last_loaded_doc_id = None  # 上次加载的文档ID，用于缓存控制
    if "hide_qa_interface" not in st.session_state:
        st.session_state.hide_qa_interface = False  # 是否隐藏问答界面

    # --- 获取文档列表（使用缓存） ---
    if "documents_cache" not in st.session_state or "documents_cache_time" not in st.session_state:
        result = make_api_request("/documents/")
        if result is None:
            st.error("❌ 获取文档列表失败：服务无响应")
            return
        st.session_state.documents_cache = result
        st.session_state.documents_cache_time = time.time()
    else:
        # 如果缓存超过5秒，重新加载
        if time.time() - st.session_state.documents_cache_time > 5:
            result = make_api_request("/documents/")
            if result:
                st.session_state.documents_cache = result
                st.session_state.documents_cache_time = time.time()
    
    documents = st.session_state.documents_cache or []
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
    
    # 检测文档是否发生变化，如果变化则强制刷新
    previous_doc_id = st.session_state.get("qa_selected_doc_id")
    if previous_doc_id != doc_id:
        st.session_state.qa_selected_doc_id = doc_id
        # 清空之前的QA结果，避免显示其他文档的结果
        st.session_state.qa_result = None
        st.session_state.qa_question = ""
        # 清空对话状态
        st.session_state.current_conversation_id = None
        st.session_state.show_history_sidebar = False
        st.session_state.view_conversation_id = None  # 清空查看详情状态
        
        # 清理所有缓存
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith(('conversations_', 'conversation_detail_'))]
        for key in keys_to_remove:
            del st.session_state[key]
        
        st.rerun()
    
    st.session_state.qa_selected_doc_id = doc_id

    # 获取文档详细信息（使用缓存，实时更新）
    doc_detail_cache_key = f"doc_detail_{doc_id}"
    if (doc_detail_cache_key not in st.session_state or 
        st.session_state.get("last_loaded_doc_id") != doc_id):
        doc_detail = make_api_request(f"/documents/{doc_id}")
        if doc_detail:
            st.session_state[doc_detail_cache_key] = doc_detail
            st.session_state.last_loaded_doc_id = doc_id
    else:
        doc_detail = st.session_state.get(doc_detail_cache_key)
    
    if doc_detail:
        # 合并基本信息和详细信息
        display_doc = {**selected_doc, **doc_detail}
    else:
        # 如果获取详细信息失败，使用基本信息
        display_doc = selected_doc

    # 文档 Meta（按需显示你后端实际字段）
    with st.expander("📄 文档信息", expanded=False):
        cols = st.columns(2)
        cols[0].metric("状态", display_doc.get("status", "-"))
        cols[1].metric("上传时间", display_doc.get("created_at", "-"))
        
        # 额外信息
        if display_doc.get("word_count"):
            st.info(f"📊 字数统计：{display_doc['word_count']:,} 字")
        if display_doc.get("filename"):
            st.caption(f"📁 文件名：{display_doc['filename']}")
        if display_doc.get("notes"):
            st.caption(f"📝 备注：{display_doc['notes']}")

    # 对话管理区域
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # 显示成功消息
        if st.session_state.get('conversation_continued'):
            st.success("✅ 已切换到该对话，可以继续提问")
            st.session_state['conversation_continued'] = False  # 显示后清除
        
        if st.session_state.current_conversation_id:
            st.info(f"💬 当前对话ID: {st.session_state.current_conversation_id[:8]}...")
        else:
            st.info("💬 新对话（首次提问将创建对话记录）")
    
    with col2:
        if st.button("📖 查看历史", key="show_history"):
            st.session_state.show_history_sidebar = not st.session_state.show_history_sidebar
            # 当打开历史记录时，隐藏问题建议和提出问题部分
            if st.session_state.show_history_sidebar:
                st.session_state.hide_qa_interface = True
            else:
                st.session_state.hide_qa_interface = False
    
    with col3:
        if st.button("🆕 新建对话", key="new_conversation"):
            st.session_state.current_conversation_id = None
            st.session_state.qa_result = None
            st.session_state.qa_question = ""
            # 关闭历史记录并显示问答界面
            st.session_state.show_history_sidebar = False
            st.session_state.hide_qa_interface = False
            st.toast("已开始新对话", icon="🆕")
    
    # 显示对话历史记录
    if st.session_state.show_history_sidebar:
        st.markdown("---")
        st.markdown("### 📚 对话历史记录")
        
        # 使用缓存来避免重复加载
        cache_key = f"conversations_{doc_id}"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = load_conversation_list(doc_id)
        
        conversations = st.session_state[cache_key]
        
        # 添加刷新按钮
        if st.button("🔄 刷新历史记录", key="refresh_conversations"):
            st.session_state[cache_key] = load_conversation_list(doc_id)
            conversations = st.session_state[cache_key]
        
        if not conversations:
            st.info("暂无对话记录")
        else:
            # 选择要查看的对话
            conv_options = {f"{conv['title'][:40]}{'...' if len(conv['title']) > 40 else ''} ({conv['total_questions']}个问题)": conv['id'] 
                           for conv in conversations}
            
            selected_conv_display = st.selectbox(
                "选择要查看的对话：",
                options=list(conv_options.keys()),
                key="selected_conversation"
            )
            
            if selected_conv_display:
                selected_conv_id = conv_options[selected_conv_display]
                
                # 操作按钮
                col_a, col_b, col_c, col_d = st.columns(4)
                
                with col_a:
                    if st.button("📖 查看详情", key="view_conv_detail"):
                        detail = load_conversation_detail(selected_conv_id)
                        if detail:
                            st.session_state['showing_conv_detail'] = detail
                            st.session_state['detail_loaded'] = True
                            st.markdown("""
                            <script>
                                window.scrollTo(0, window.scrollY);
                            </script>
                            """, unsafe_allow_html=True)
                            st.rerun()  # 需要立即显示详情，但不滚动
                
                with col_b:
                    if st.button("🔄 继续对话", key="continue_conv"):
                        st.session_state.current_conversation_id = selected_conv_id
                        st.session_state.qa_result = None
                        st.session_state.qa_question = ""
                        st.session_state['conversation_continued'] = True
                        st.session_state.qa_clear_counter += 1  # 触发文本框刷新
                        # 关闭历史记录并显示问答界面
                        st.session_state.show_history_sidebar = False
                        st.session_state.hide_qa_interface = False
                        st.markdown("""
                        <script>
                            window.scrollTo(0, window.scrollY);
                        </script>
                        """, unsafe_allow_html=True)
                        st.rerun()  # 需要立即切换对话状态，但不自动滚动
                
                with col_c:
                    if st.button("📥 导出", key="export_conv"):
                        export_data = export_conversation(selected_conv_id, "markdown")
                        if export_data:
                            st.download_button(
                                label="💾 下载MD文件",
                                data=export_data['content'],
                                file_name=export_data['filename'],
                                mime="text/markdown",
                                key="download_conv_md"
                            )
                
                with col_d:
                    # 删除确认机制
                    delete_confirm_key = f"delete_confirm_{selected_conv_id}"
                    if delete_confirm_key not in st.session_state:
                        st.session_state[delete_confirm_key] = False
                    
                    if st.session_state[delete_confirm_key]:
                        if st.button("⚠️ 确认删除", key="confirm_delete_conv", type="primary"):
                            if delete_conversation(selected_conv_id):
                                st.success("删除成功")
                                if st.session_state.current_conversation_id == selected_conv_id:
                                    st.session_state.current_conversation_id = None
                                del st.session_state[delete_confirm_key]
                    else:
                        if st.button("🗑️ 删除", key="delete_conv", type="secondary"):
                            st.session_state[delete_confirm_key] = True
        
        # 显示对话详情
        if 'showing_conv_detail' in st.session_state and st.session_state['showing_conv_detail']:
            st.markdown("---")
            detail = st.session_state['showing_conv_detail']
            show_conversation_detail_modal(detail)
            
            if st.button("❌ 关闭详情", key="close_detail"):
                del st.session_state['showing_conv_detail']
                st.markdown("""
                <script>
                    window.scrollTo(0, window.scrollY);
                </script>
                """, unsafe_allow_html=True)
                st.rerun()  # 需要立即隐藏详情窗口，但不自动滚动
    
    # 显示对话历史侧边栏
    if st.session_state.show_history_sidebar:
        show_conversation_history_sidebar(doc_id)

    # --- 文档状态检查 ---
    doc_status = display_doc.get("status", "").lower()
    if doc_status not in ["parsed", "extracted", "completed"]:
        st.warning(f"⚠️ 文档状态为 '{doc_status}'，请等待处理完成后再进行问答")
        st.info("💡 提示：文档需要处理完成（状态为 parsed/extracted/completed）才能进行智能问答")
        return

    # --- 获取问题建议（与文档选择同风格：selectbox）---
    # 只有在不隐藏问答界面时才显示问题建议
    if not st.session_state.get('hide_qa_interface', False):
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
                st.session_state['suggestion_applied'] = True  # 标记已应用建议
                st.session_state.qa_clear_counter += 1  # 触发文本框刷新

            st.selectbox(
                "选择一个建议问题：",
                options=suggestion_options,
                index=default_idx,
                key="qa_suggestion_select",
                on_change=_apply_suggestion,
            )
            
            # 显示应用建议的成功消息
            if st.session_state.get('suggestion_applied'):
                st.success("✅ 建议问题已填入输入框")
                st.session_state['suggestion_applied'] = False  # 显示后清除
                
            st.caption("提示：选择后会自动填入下方输入框。")
            st.divider()

    # 初始化清空计数器
    if 'qa_clear_counter' not in st.session_state:
        st.session_state.qa_clear_counter = 0
    
    # 只有在不隐藏问答界面时才显示提出问题部分
    if not st.session_state.get('hide_qa_interface', False):
        st.markdown("### ❓ 提出问题")
        with st.form("qa_ask_form", clear_on_submit=False):
            question = st.text_area(
                "输入您的问题",
                value=st.session_state.qa_question,
                height=120,
                placeholder="例如：这篇文献的主要研究方法是什么？",
                key=f"qa_question_input_{st.session_state.qa_clear_counter}",  # 使用计数器强制刷新
            )
            c1, c2, _ = st.columns([1, 1, 4])
            submit = c1.form_submit_button("🚀 提问", use_container_width=True)
            clear = c2.form_submit_button("🧹 清空", use_container_width=True)

        if clear:
            st.session_state.qa_question = ""
            st.session_state.qa_result = None  # 同时清空QA结果
            st.session_state.qa_clear_counter += 1  # 增加计数器强制刷新文本框
            st.toast("已清空问题", icon="🧹")
            st.markdown("""
            <script>
                window.scrollTo(0, window.scrollY);
            </script>
            """, unsafe_allow_html=True)
            st.rerun()  # 必要：需要立即清空文本框显示

        if submit:
            if not question.strip():
                st.warning("请输入问题")
                st.stop()

            with st.spinner("正在思考中..."):
                payload = {
                    "document_id": doc_id, 
                    "question": question.strip()
                }
                # 如果有当前对话ID，则传递以延续对话
                if st.session_state.current_conversation_id:
                    payload["conversation_id"] = st.session_state.current_conversation_id
                
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
            
            # 保存或更新对话ID
            if qa_result.get("conversation_id"):
                st.session_state.current_conversation_id = qa_result["conversation_id"]

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

    # 显示对话详情（如果有选中的对话）
    if st.session_state.view_conversation_id:
        st.markdown("---")
        st.markdown("### 📋 对话详情")
        
        # 添加关闭按钮
        col1, col2 = st.columns([1, 6])
        with col1:
            if st.button("❌ 关闭", key="close_conversation_detail"):
                st.session_state.view_conversation_id = None
                # 清理缓存
                detail_cache_key = f"conversation_detail_{st.session_state.view_conversation_id}"
                if detail_cache_key in st.session_state:
                    del st.session_state[detail_cache_key]
                st.rerun()
        
        # 使用缓存加载对话详情
        detail_cache_key = f"conversation_detail_{st.session_state.view_conversation_id}"
        if detail_cache_key not in st.session_state:
            st.session_state[detail_cache_key] = load_conversation_detail(st.session_state.view_conversation_id)
        
        detail = st.session_state[detail_cache_key]
        if detail:
            show_conversation_detail_modal(detail)
        else:
            st.error("无法加载对话详情")
            st.session_state.view_conversation_id = None


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
