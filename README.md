# deeplit-analyzer - 学术文献处理AI系统

## 📚 项目简介

deeplit-analyzer 是一款专注于学术文献领域的智能处理系统，旨在为科研人员、学生和学术工作者提供高效的文献处理工具。系统通过集成 DeepSeek API 实现文献信息的深度加工与智能交互，解决文献阅读耗时久、信息提取效率低、知识整合难、疑问解答不及时等痛点。

## ✨ 核心功能

### 🔍 文献导入与解析
- **多格式支持**: PDF、Word文档等主流格式
- **本地文件上传**: 支持批量文件上传处理
- **智能解析**: 自动提取文档内容、章节结构、元数据
- **OCR支持**: 处理扫描版PDF的文字识别

### 📝 智能总结
- **多种总结模式**: 
  - 全文献概括：整体内容总结
  - 章节总结：针对特定章节的详细分析
  - 定制化总结：基于关键词和模板的个性化总结
- **结构化模板**: 
  - 问题-方法-结论
  - 背景-方法-结果
  - 目标-方法-发现
  - 局限-展望
  - 贡献-影响
- **关键词提取**: 智能识别文档核心关键词

### 💬 智能问答
- **基于文档的精准问答**: 针对文档内容的智能回答
- **多轮对话支持**: 保持上下文的连续问答
- **对话历史管理**: 完整的对话记录和管理功能
- **问题建议**: 智能生成相关问题建议
- **DeepSeek API集成**: 利用先进AI模型提供高质量回答

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 8GB+ RAM（推荐）
- 网络连接（用于DeepSeek API）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/sign-river/deeplit-analyzer.git
cd deeplit-analyzer
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制环境变量模板
cp env.example .env

# 编辑.env文件，配置DeepSeek API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

4. **启动服务**

**一键启动（推荐）**:
```bash
python run.py
```

**分别启动**:
```bash
# 启动后端服务
python start_backend.py

# 启动前端服务  
python start_frontend.py
```

5. **访问系统**
- 前端界面: http://localhost:8501
- API文档: http://localhost:8000/docs
- 后端服务: http://localhost:8000

## 📖 使用指南

### 1. 文档上传
- 支持拖拽上传多个文件
- 自动检测文件格式和完整性

### 2. 文档处理
- 系统自动解析文档内容
- 提取元数据和章节结构
- 生成文档索引

### 3. 文献总结
- 选择总结类型（全文献/章节/定制）
- 选择总结模板或关键词
- 生成高质量结构化总结

### 4. 智能问答
- 选择目标文档
- 输入问题或选择建议问题
- 获得基于文献的准确回答
- 支持多轮对话和历史记录

## 🔧 配置说明

### 环境变量配置
```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 文件存储配置
UPLOAD_DIR=./data/uploads
PROCESSED_DIR=./data/processed
INDEX_DIR=./data/index

# OCR配置（可选）
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# 应用配置
APP_NAME=deeplit-analyzer
APP_VERSION=1.0.0
DEBUG=True

# 性能配置
MAX_FILE_SIZE=50MB
MAX_BATCH_SIZE=100
```

### DeepSeek API配置
1. 访问 [DeepSeek官网](https://www.deepseek.com/) 注册账号
2. 获取API密钥
3. 在`.env`文件中配置`DEEPSEEK_API_KEY`


## 🏗️ 系统架构

```
deeplit-analyzer
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   │   ├── documents.py    # 文档管理API
│   │   │   ├── summaries.py    # 总结API  
│   │   │   └── qa.py          # 问答API
│   │   ├── core/           # 核心配置
│   │   │   └── config.py      # 应用配置
│   │   ├── models/         # 数据模型
│   │   │   ├── document.py    # 文档模型
│   │   │   ├── qa.py          # 问答模型
│   │   │   └── conversation.py # 对话模型
│   │   └── services/       # 业务服务
│   │       ├── parser/     # 文档解析
│   │       ├── summarizer/ # 总结生成
│   │       ├── qa/         # 智能问答
│   │       ├── search/     # 搜索服务
│   │       └── storage/    # 数据存储
├── frontend/               # 前端界面
│   └── streamlit_app.py   # Streamlit应用
├── data/                   # 数据目录
│   ├── uploads/           # 上传文件
│   ├── processed/         # 处理结果
│   ├── conversations/     # 对话记录
│   └── index/             # 索引文件
├── run.py                  # 一键启动脚本
├── start_backend.py        # 后端启动脚本
├── start_frontend.py       # 前端启动脚本
├── requirements.txt        # 依赖包列表
├── env.example            # 环境变量模板
└── README.md              # 项目说明文档
```

## 🔌 API接口

### 文档管理
- `POST /documents/upload` - 上传文档
- `GET /documents/` - 获取文档列表
- `GET /documents/{id}` - 获取文档详情
- `DELETE /documents/{id}` - 删除文档
- `POST /documents/{id}/reprocess` - 重新处理文档

### 文献总结
- `POST /summaries/generate` - 生成总结
- `GET /summaries/full/{id}` - 全文献总结
- `POST /summaries/section/{id}` - 章节总结
- `GET /summaries/section/{id}` - 获取章节总结
- `POST /summaries/custom/{id}` - 定制总结
- `GET /summaries/templates` - 获取总结模板
- `GET /summaries/keywords/{id}` - 获取关键词

### 智能问答
- `POST /qa/ask` - 提问
- `GET /qa/suggestions/{id}` - 获取问题建议
- `POST /qa/conversation/{id}` - 开始对话
- `POST /qa/conversation/{id}/continue` - 继续对话
- `GET /qa/conversations/{document_id}` - 获取对话列表
- `GET /qa/conversation/{conversation_id}/detail` - 获取对话详情
- `DELETE /qa/conversation/{conversation_id}` - 删除对话
- `POST /qa/conversation/{conversation_id}/archive` - 归档对话
- `GET /qa/conversation/{conversation_id}/export` - 导出对话

## 🛠️ 开发指南

### 添加新的文档格式支持
1. 在`backend/app/services/parser/`中创建新的解析器
2. 实现`parse_document`方法
3. 在`DocumentParser`中注册新格式

### 扩展总结模板
1. 在`SummarizerService`中添加新模板
2. 定义模板结构和提示词
3. 在前端界面中添加模板选项

### 自定义问答逻辑
1. 在`QAService`中修改问答逻辑
2. 调整问题分析和回答生成
3. 优化上下文检索算法

## 📝 更新日志

### v1.0.0 (2025-09-12)
- ✨ 初始版本发布
- 🔍 支持PDF、Word文档解析
- 📝 实现多模板智能总结功能
- 💬 集成DeepSeek API智能问答
- 🎨 构建Streamlit前端界面
- 📋 支持对话历史管理
- 🔄 优化依赖包配置

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 👥 贡献者

感谢所有为项目做出贡献的开发者！

<a href="https://github.com/sign-river/deeplit-analyzer/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=sign-river/deeplit-analyzer" />
</a>

*由 [contrib.rocks](https://contrib.rocks) 生成*

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系我们

- 项目主页: [GitHub - deeplit-analyzer](https://github.com/sign-river/deeplit-analyzer)
- 问题反馈: [GitHub Issues](https://github.com/sign-river/deeplit-analyzer/issues)
- 邮箱: 
  - 3217344726@qq.com
  - 2584628465@qq.com

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供强大的AI API服务
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Streamlit](https://streamlit.io/) - 快速构建数据应用
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF处理库
- [Sentence Transformers](https://www.sbert.net/) - 文本向量化

---

**deeplit-analyzer** - 让学术研究更智能 🚀
