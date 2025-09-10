# deeplit-analyzer - 学术文献处理AI系统

## 📚 项目简介

deeplit-analyzer 是一款专注于学术文献领域的智能处理系统，旨在为科研人员、学生和学术工作者提供高效的文献处理工具。系统通过AI技术自动化完成文献信息的深度加工与智能交互，解决文献阅读耗时久、信息提取效率低、知识整合难、疑问解答不及时等痛点。

## ✨ 核心功能

### 🔍 文献导入与解析
- **多格式支持**: PDF（扫描件+可编辑版）、Word、LaTeX、HTML、文本等
- **多来源导入**: 本地文件上传、在线链接导入、批量导入
- **智能解析**: 自动提取元数据、章节结构、图表、参考文献
- **OCR识别**: 支持扫描版PDF的OCR文字识别

### 🧠 知识点提取
- **核心观点提取**: 从摘要、讨论、结论章节提取核心论点
- **研究方法分析**: 识别研究设计类型、关键步骤、参数、工具
- **实验结果总结**: 提取关键数据、统计学意义、图表关联
- **局限与展望**: 识别研究不足和未来研究方向
- **关键词扩展**: 构建层级化关键词树

### 📝 智能总结
- **全文献概括**: 按"目的→方法→结果→结论"逻辑生成总结
- **章节聚焦**: 针对特定章节的详细总结
- **定制化总结**: 支持关键词筛选和结构模板选择
- **多语言支持**: 中英文文献总结

### 💬 智能问答
- **事实类问答**: 基于文献内容的精准回答
- **逻辑类问答**: 分析因果关系和逻辑推导
- **深度分析**: 提供研究局限影响和泛化性分析
- **多轮对话**: 支持上下文关联的连续问答
- **DeepSeek集成**: 使用DeepSeek API提供高质量回答

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 8GB+ RAM（推荐）
- 网络连接（用于DeepSeek API）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ScholarMind-AI
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

**启动后端服务**:
```bash
python start_backend.py
```

**启动前端服务**:
```bash
python start_frontend.py
```

5. **访问系统**
- 前端界面: http://localhost:8501
- API文档: http://localhost:8000/docs
- 后端服务: http://localhost:8000

## 📖 使用指南

### 1. 文档上传
- 支持拖拽上传多个文件
- 支持从URL导入文献
- 自动检测文件格式和完整性

### 2. 文档处理
- 系统自动解析文档内容
- 提取元数据和章节结构
- 生成知识点和向量索引

### 3. 文献总结
- 选择总结类型（全文献/章节/定制）
- 选择总结模板或关键词
- 生成高质量总结

### 4. 智能问答
- 选择目标文档
- 输入问题或选择建议问题
- 获得基于文献的准确回答

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

# 性能配置
MAX_FILE_SIZE=50MB
MAX_BATCH_SIZE=100
```

### DeepSeek API配置
1. 访问 [DeepSeek官网](https://www.deepseek.com/) 注册账号
2. 获取API密钥
3. 在`.env`文件中配置`DEEPSEEK_API_KEY`

## 📊 性能指标

### 解析准确率
- 可编辑PDF/Word: ≥98%
- 扫描件PDF OCR: ≥95%
- 元数据提取: ≥95%
- 章节识别: ≥90%
- 参考文献解析: ≥92%

### 知识点提取
- 核心观点准确率: ≥90%
- 实验结果准确率: ≥90%
- 研究方法准确率: ≥85%
- 关键词扩展准确率: ≥85%
- 冗余信息占比: ≤5%

### 响应时间
- 单篇文献解析: ≤30秒
- 在线链接导入: ≤10秒
- 事实类问答: ≤2秒
- 逻辑/分析类问答: ≤5秒

## 🏗️ 系统架构

```
deeplit-analyzer
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   └── services/       # 业务服务
│   │       ├── parser/     # 文档解析
│   │       ├── extractor/  # 知识点提取
│   │       ├── summarizer/ # 总结生成
│   │       ├── qa/         # 智能问答
│   │       └── storage/    # 数据存储
├── frontend/               # 前端界面
│   └── streamlit_app.py   # Streamlit应用
├── data/                   # 数据目录
│   ├── uploads/           # 上传文件
│   ├── processed/         # 处理结果
│   └── index/             # 向量索引
└── docs/                  # 文档
```

## 🔌 API接口

### 文档管理
- `POST /documents/upload` - 上传文档
- `POST /documents/upload/url` - 从URL导入
- `GET /documents/` - 获取文档列表
- `GET /documents/{id}` - 获取文档详情
- `DELETE /documents/{id}` - 删除文档

### 文献总结
- `POST /summaries/generate` - 生成总结
- `GET /summaries/full/{id}` - 全文献总结
- `GET /summaries/section/{id}` - 章节总结
- `POST /summaries/custom/{id}` - 定制总结

### 智能问答
- `POST /qa/ask` - 提问
- `GET /qa/suggestions/{id}` - 获取问题建议
- `POST /qa/conversation/{id}` - 开始对话
- `POST /qa/conversation/{id}/continue` - 继续对话

## 🛠️ 开发指南

### 添加新的文档格式支持
1. 在`backend/app/services/parser/`中创建新的解析器
2. 实现`parse_document`方法
3. 在`DocumentParser`中注册新格式

### 扩展知识点提取规则
1. 在`backend/app/services/extractor/`中修改提取逻辑
2. 添加学科特定的提取规则
3. 更新置信度计算算法

### 自定义总结模板
1. 在`SummarizerService`中添加新模板
2. 定义模板结构和提示词
3. 在前端界面中添加模板选项

## 📝 更新日志

### v1.0.0 (2024-01-01)
- ✨ 初始版本发布
- 🔍 支持多格式文档解析
- 🧠 实现知识点提取
- 📝 提供智能总结功能
- 💬 集成DeepSeek API问答
- 🎨 构建Streamlit前端界面

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系我们

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 邮箱: [your-email@example.com]

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供强大的AI API服务
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Streamlit](https://streamlit.io/) - 快速构建数据应用
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF处理库
- [Sentence Transformers](https://www.sbert.net/) - 文本向量化

---

**deeplit-analyzer** - 让学术研究更智能 🚀
