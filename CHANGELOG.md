# 更新日志 / Changelog

本文件记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/)，
项目遵循 [语义化版本](https://semver.org/)。

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [0.2.0] - 2026-05-19

### 新增 / Added
- MiMo 提供商支持，可集成本地模型 / MiMo provider support for local model integration
- PyQt6 现代桌面图形界面 / PyQt6 GUI with modern desktop interface
- 聊天组件及消息历史记录 / Chat widget with message history
- 成本追踪组件及可视化统计 / Cost tracking widget with visual statistics
- 设置对话框管理 API 密钥 / Settings dialog for API key management
- 导出功能（PDF、Markdown、HTML）/ Export functionality (PDF, Markdown, HTML)
- 文件处理器（PDF、DOCX）/ File handler for document processing (PDF, DOCX)
- 国际化（i18n）支持 / Internationalization (i18n) support
- 网页搜索集成 / Web search integration
- 18 个内置提示词模板 / 18 built-in prompt templates for various use cases
- 隐私保护：自动检测和脱敏个人信息 / Privacy protection with automatic PII detection and masking
- 三级隐私保护（低、中、高）/ Three privacy levels (low, medium, high)

### 变更 / Changed
- 优化项目结构为 src 布局 / Improved project structure with src layout
- 增强 CLI 命令 / Enhanced CLI with more subcommands
- 更新依赖版本 / Updated dependency versions

### 修复 / Fixed
- Windows 中文编码问题 / Windows Chinese encoding issues
- 测试套件稳定性 / Test suite stability

---

## [0.1.0] - 2026-05-01

### 新增 / Added
- 初始版本发布 / Initial release
- 多提供商支持：OpenAI、Claude、Ollama / Multi-provider support: OpenAI, Claude, Ollama
- 统一聊天界面 / Unified chat interface for all providers
- CLI 交互模式 / CLI tool with interactive mode
- 本地 SQLite 存储对话历史 / Local SQLite storage for conversation history
- 每次 API 调用的基础成本追踪 / Basic cost tracking per API call
- YAML 配置系统 / YAML-based configuration system
- 流式响应支持 / Streaming response support
- 环境变量支持（.env 文件）/ Environment variable support via .env files
