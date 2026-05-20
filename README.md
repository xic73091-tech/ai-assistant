# AI Assistant / AI助手

[![PyPI version](https://img.shields.io/pypi/v/ai-assistant.svg)](https://pypi.org/project/ai-assistant/)
[![Python versions](https://img.shields.io/pypi/pyversions/ai-assistant.svg)](https://pypi.org/project/ai-assistant/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/ai-assistant.svg)](https://pypi.org/project/ai-assistant/)

[English](#english) | [中文](#中文)

---

## English

### Overview

A local AI assistant that solves three major pain points for ordinary users when using AI: inaccurate answers, expensive fees, and privacy concerns.

### Features

- **Multi-AI Aggregation**: Unified interface for OpenAI, Claude, Ollama, and MiMo (Xiaomi)
- **18 Built-in Templates**: Code review, writing, analysis, translation, debugging, and more
- **Cost Tracking**: Monitor API spending with budget alerts and optimization tips
- **Privacy Protection**: Automatic detection and masking of sensitive information (ID cards, phone numbers, bank cards, etc.)
- **Local Storage**: All conversation history stored locally in SQLite
- **Web Search**: Search the web and inject results into AI context
- **File Processing**: Load and analyze 20+ file formats (TXT, MD, CSV, PDF, DOCX, JSON, YAML, code files)
- **GUI Interface**: Modern PyQt6 desktop application with dark/light theme
- **CLI Interface**: Full-featured command line tool

### Installation

**From PyPI (recommended):**

```bash
# Install basic version
pip install ai-assistant

# Install with GUI support
pip install ai-assistant[gui]

# Install with file processing support (PDF/DOCX)
pip install ai-assistant[files]

# Install with PDF export support
pip install ai-assistant[pdf]

# Install all features
pip install ai-assistant[gui,files,pdf]
```

**From source:**

```bash
git clone https://github.com/xic73091-tech/ai-assistant.git
cd ai-assistant

# Install basic version
pip install -e .

# Install with all optional dependencies
pip install -e ".[gui,files,pdf,dev]"
```

**Optional Dependencies:**

| Package | Install Command | Features |
|---------|-----------------|----------|
| gui | `pip install ai-assistant[gui]` | PyQt6 desktop application |
| files | `pip install ai-assistant[files]` | PDF/DOCX file reading |
| pdf | `pip install ai-assistant[pdf]` | Export conversations to PDF |
| dev | `pip install ai-assistant[dev]` | Development tools (pytest, black, ruff) |

### Quick Start

**1. Configure API Keys:**

```bash
# Option 1: CLI commands
ai-assistant config set openai_api_key "sk-..."
ai-assistant config set claude_api_key "sk-ant-..."
ai-assistant config set mimo_api_key "your-mimo-key"

# Option 2: Environment variables (.env file)
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-ant-...
MIMO_API_KEY=your-mimo-key
OLLAMA_BASE_URL=http://localhost:11434
AI_DEFAULT_PROVIDER=openai

# Option 3: GUI settings dialog
ai-assistant gui
```

**2. Start Using:**

```bash
# CLI chat
ai-assistant chat

# Use a template
ai-assistant chat --template code-review

# Switch provider
ai-assistant chat --provider claude

# Launch GUI
ai-assistant gui
```

### AI Providers

| Provider | SDK | Default Model | Authentication |
|----------|-----|---------------|----------------|
| OpenAI | openai | gpt-4o | API Key (`sk-...`) |
| Claude | anthropic | claude-sonnet-4-20250514 | API Key (`sk-ant-...`) |
| Ollama | httpx | llama3 | None (local service) |
| MiMo | openai (compatible) | mimo-v2.5-pro | API Key + custom base_url |

**MiMo Configuration:**
```bash
ai-assistant config set mimo_api_key "your-key"
ai-assistant config set mimo_base_url "https://token-plan-cn.xiaomimimo.com/v1"
ai-assistant config set mimo_model "mimo-v2.5-pro"
```

### CLI Commands

**Main Commands:**
| Command | Description |
|---------|-------------|
| `ai-assistant chat` | Start a conversation |
| `ai-assistant gui` | Launch GUI application |
| `ai-assistant language` | Switch language (zh/en) |

**Configuration:**
| Command | Description |
|---------|-------------|
| `ai-assistant config set <key> <value>` | Set configuration value |
| `ai-assistant config show` | Show all configuration |

**Cost Management:**
| Command | Description |
|---------|-------------|
| `ai-assistant cost stats` | View cost statistics |
| `ai-assistant cost tips` | Get optimization tips |
| `ai-assistant cost export` | Export cost report |

**Templates:**
| Command | Description |
|---------|-------------|
| `ai-assistant template list` | List all templates |
| `ai-assistant template show <name>` | Show template details |

**Privacy:**
| Command | Description |
|---------|-------------|
| `ai-assistant privacy level` | Show/set privacy level |
| `ai-assistant privacy test` | Test privacy detection |

**Export:**
| Command | Description |
|---------|-------------|
| `ai-assistant export chat` | Export conversation history |
| `ai-assistant export cost` | Export cost report |

**In-Chat Commands:**
| Command | Description |
|---------|-------------|
| `/search <query>` | Search the web |
| `/file <path>` | Load a file |
| `/export` | Export current conversation |
| `help` | Show available commands |
| `cost` | Show cost statistics |
| `tips` | Get optimization tips |
| `quit` | Exit chat |

### Templates

| Template | Description | Category |
|----------|-------------|----------|
| code-review | Code review assistant | code |
| code-generation | Code generation assistant | code |
| test-case | Test case generation | code |
| api-doc | API documentation generation | code |
| debug | Debugging assistant | code |
| writing | Document writing assistant | writing |
| summarize | Content summarization | writing |
| email | Professional email drafting | writing |
| analysis | Data analysis assistant | analysis |
| data-report | Data analysis report | analysis |
| translate | Translation optimization | language |
| explain | Concept explanation | learning |
| learning-plan | Learning plan creation | learning |
| interview-prep | Interview preparation | learning |
| brainstorm | Brainstorming assistant | creative |
| product-requirements | Product requirements document | business |
| meeting-notes | Meeting notes整理 | business |
| project-plan | Project planning | business |

### Privacy Protection

Three privacy levels with automatic detection and masking:

| Level | Detection Scope |
|-------|-----------------|
| Low | ID card numbers, bank card numbers, passwords |
| Medium | + Phone numbers |
| High | + Email addresses, IP addresses |

When sensitive information is detected, it is automatically masked before sending to AI providers.

### Configuration

**Config file location:** `~/.ai-assistant/config.yaml`

**Complete configuration example:**

```yaml
# Default AI provider
default_provider: openai

# Provider configurations
providers:
  openai:
    api_key: sk-...
    model: gpt-4o
    base_url: https://api.openai.com/v1
  claude:
    api_key: sk-ant-...
    model: claude-sonnet-4-20250514
  ollama:
    base_url: http://localhost:11434
    model: llama3
  mimo:
    api_key: your-mimo-key
    base_url: https://token-plan-cn.xiaomimimo.com/v1
    model: mimo-v2.5-pro

# Privacy settings
privacy:
  level: medium  # low, medium, high
  auto_detect: true

# Storage settings
storage:
  path: ~/.ai-assistant/data
  max_conversations: 1000

# Cost tracking
cost:
  monthly_budget: 10.0  # USD
  alert_threshold: 0.8  # 80% of budget
```

**Environment variables (higher priority than config file):**

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `CLAUDE_API_KEY` | Claude API key |
| `OLLAMA_BASE_URL` | Ollama service URL |
| `AI_DEFAULT_PROVIDER` | Default provider name |

### Architecture

```
ai-assistant/
├── src/
│   ├── cli.py              # CLI main program (Click + Rich)
│   ├── config.py           # YAML configuration management
│   ├── storage.py          # SQLite local storage
│   ├── cost_tracker.py     # Cost tracking and budget alerts
│   ├── privacy.py          # Privacy protection (3 levels)
│   ├── i18n.py             # Internationalization (zh/en)
│   ├── web_search.py       # Web search (DuckDuckGo + Bing)
│   ├── file_handler.py     # File loading (20+ formats)
│   ├── export.py           # Export (MD/HTML/PDF/TXT)
│   ├── providers/          # AI provider implementations
│   │   ├── base.py         # Abstract base class
│   │   ├── openai.py       # OpenAI provider
│   │   ├── claude.py       # Claude provider
│   │   ├── ollama.py       # Ollama provider
│   │   └── mimo.py         # MiMo provider
│   ├── templates/          # Prompt template system
│   │   └── manager.py      # 18 built-in templates
│   └── gui/                # PyQt6 GUI
│       ├── main_window.py  # Main window
│       ├── chat_widget.py  # Chat interface
│       ├── cost_widget.py  # Cost statistics
│       └── styles.py       # Dark/light theme
├── tests/                  # Test suite
├── scripts/                # Build scripts
└── pyproject.toml          # Project configuration
```

### Development

```bash
# Run tests
pytest

# Code formatting
black src/ tests/
ruff check src/ tests/

# Type checking
mypy src/
```

### License

MIT License

---

## 中文

### 概述

本地化AI助手，解决普通用户使用AI的三大痛点：回答不准、收费贵、隐私顾虑。

### 功能特点

- **多AI聚合**：统一接口调用OpenAI、Claude、Ollama、MiMo（小米）
- **18个内置模板**：代码审查、文档写作、数据分析、翻译、调试等
- **成本追踪**：监控API支出，提供预算警报和优化建议
- **隐私保护**：自动检测和脱敏敏感信息（身份证、手机号、银行卡等）
- **本地存储**：所有对话历史存储在本地SQLite数据库
- **联网搜索**：搜索网络并注入AI上下文
- **文件处理**：加载和分析20+种文件格式（TXT、MD、CSV、PDF、DOCX、JSON、YAML、代码文件）
- **GUI界面**：现代化PyQt6桌面应用，支持深色/浅色主题
- **CLI界面**：功能完整的命令行工具

### 安装

**从 PyPI 安装（推荐）：**

```bash
# 安装基础版本
pip install ai-assistant

# 安装带GUI支持的版本
pip install ai-assistant[gui]

# 安装带文件处理支持的版本（PDF/DOCX读取）
pip install ai-assistant[files]

# 安装带PDF导出支持的版本
pip install ai-assistant[pdf]

# 安装所有功能
pip install ai-assistant[gui,files,pdf]
```

**从源码安装：**

```bash
git clone https://github.com/xic73091-tech/ai-assistant.git
cd ai-assistant

# 安装基础版本
pip install -e .

# 安装所有可选依赖
pip install -e ".[gui,files,pdf,dev]"
```

**可选依赖：**

| 包名 | 安装命令 | 功能 |
|------|----------|------|
| gui | `pip install ai-assistant[gui]` | PyQt6桌面应用 |
| files | `pip install ai-assistant[files]` | PDF/DOCX文件读取 |
| pdf | `pip install ai-assistant[pdf]` | 导出对话为PDF |
| dev | `pip install ai-assistant[dev]` | 开发工具（pytest、black、ruff） |

### 快速开始

**1. 配置API密钥：**

```bash
# 方式1：CLI命令
ai-assistant config set openai_api_key "sk-..."
ai-assistant config set claude_api_key "sk-ant-..."
ai-assistant config set mimo_api_key "your-mimo-key"

# 方式2：环境变量（.env文件）
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-ant-...
MIMO_API_KEY=your-mimo-key
OLLAMA_BASE_URL=http://localhost:11434
AI_DEFAULT_PROVIDER=openai

# 方式3：GUI设置对话框
ai-assistant gui
```

**2. 开始使用：**

```bash
# CLI对话
ai-assistant chat

# 使用模板
ai-assistant chat --template code-review

# 切换提供商
ai-assistant chat --provider claude

# 启动GUI
ai-assistant gui
```

### AI提供商

| 提供商 | SDK | 默认模型 | 认证方式 |
|--------|-----|----------|----------|
| OpenAI | openai | gpt-4o | API Key (`sk-...`) |
| Claude | anthropic | claude-sonnet-4-20250514 | API Key (`sk-ant-...`) |
| Ollama | httpx | llama3 | 无需认证（本地服务） |
| MiMo | openai（兼容） | mimo-v2.5-pro | API Key + 自定义 base_url |

**MiMo配置：**
```bash
ai-assistant config set mimo_api_key "your-key"
ai-assistant config set mimo_base_url "https://token-plan-cn.xiaomimimo.com/v1"
ai-assistant config set mimo_model "mimo-v2.5-pro"
```

### CLI命令

**主命令：**
| 命令 | 说明 |
|------|------|
| `ai-assistant chat` | 开始对话 |
| `ai-assistant gui` | 启动GUI应用 |
| `ai-assistant language` | 切换语言（zh/en） |

**配置：**
| 命令 | 说明 |
|------|------|
| `ai-assistant config set <key> <value>` | 设置配置值 |
| `ai-assistant config show` | 显示所有配置 |

**成本管理：**
| 命令 | 说明 |
|------|------|
| `ai-assistant cost stats` | 查看成本统计 |
| `ai-assistant cost tips` | 获取优化建议 |
| `ai-assistant cost export` | 导出成本报告 |

**模板：**
| 命令 | 说明 |
|------|------|
| `ai-assistant template list` | 列出所有模板 |
| `ai-assistant template show <name>` | 显示模板详情 |

**隐私：**
| 命令 | 说明 |
|------|------|
| `ai-assistant privacy level` | 查看/设置隐私级别 |
| `ai-assistant privacy test` | 测试隐私检测 |

**导出：**
| 命令 | 说明 |
|------|------|
| `ai-assistant export chat` | 导出对话历史 |
| `ai-assistant export cost` | 导出成本报告 |

**对话内命令：**
| 命令 | 说明 |
|------|------|
| `/search <query>` | 搜索网络 |
| `/file <path>` | 加载文件 |
| `/export` | 导出当前对话 |
| `help` | 显示可用命令 |
| `cost` | 显示成本统计 |
| `tips` | 获取优化建议 |
| `quit` | 退出对话 |

### 模板列表

| 模板名称 | 说明 | 分类 |
|----------|------|------|
| code-review | 代码审查助手 | 代码 |
| code-generation | 代码生成助手 | 代码 |
| test-case | 测试用例生成 | 代码 |
| api-doc | API文档生成 | 代码 |
| debug | 调试助手 | 代码 |
| writing | 文档写作助手 | 写作 |
| summarize | 内容总结 | 写作 |
| email | 专业邮件撰写 | 写作 |
| analysis | 数据分析助手 | 分析 |
| data-report | 数据分析报告 | 分析 |
| translate | 翻译优化 | 语言 |
| explain | 概念解释 | 学习 |
| learning-plan | 学习计划制定 | 学习 |
| interview-prep | 面试准备 | 学习 |
| brainstorm | 头脑风暴助手 | 创意 |
| product-requirements | 产品需求文档 | 商业 |
| meeting-notes | 会议纪要整理 | 商业 |
| project-plan | 项目计划制定 | 商业 |

### 隐私保护

三个隐私级别，自动检测和脱敏：

| 级别 | 检测范围 |
|------|----------|
| 低 | 身份证号、银行卡号、密码 |
| 中 | + 手机号 |
| 高 | + 邮箱地址、IP地址 |

检测到敏感信息后，自动脱敏再发送给AI提供商。

### 配置文件

**配置文件位置：** `~/.ai-assistant/config.yaml`

**完整配置示例：**

```yaml
# 默认AI提供商
default_provider: openai

# 提供商配置
providers:
  openai:
    api_key: sk-...
    model: gpt-4o
    base_url: https://api.openai.com/v1
  claude:
    api_key: sk-ant-...
    model: claude-sonnet-4-20250514
  ollama:
    base_url: http://localhost:11434
    model: llama3
  mimo:
    api_key: your-mimo-key
    base_url: https://token-plan-cn.xiaomimimo.com/v1
    model: mimo-v2.5-pro

# 隐私设置
privacy:
  level: medium  # low, medium, high
  auto_detect: true

# 存储设置
storage:
  path: ~/.ai-assistant/data
  max_conversations: 1000

# 成本追踪
cost:
  monthly_budget: 10.0  # 美元
  alert_threshold: 0.8  # 预算的80%
```

**环境变量（优先级高于配置文件）：**

| 变量名 | 说明 |
|--------|------|
| `OPENAI_API_KEY` | OpenAI API密钥 |
| `CLAUDE_API_KEY` | Claude API密钥 |
| `OLLAMA_BASE_URL` | Ollama服务地址 |
| `AI_DEFAULT_PROVIDER` | 默认提供商名称 |

### 架构说明

```
ai-assistant/
├── src/
│   ├── cli.py              # CLI主程序（Click + Rich）
│   ├── config.py           # YAML配置管理
│   ├── storage.py          # SQLite本地存储
│   ├── cost_tracker.py     # 成本追踪和预算警报
│   ├── privacy.py          # 隐私保护（3级）
│   ├── i18n.py             # 国际化（zh/en）
│   ├── web_search.py       # 联网搜索（DuckDuckGo + Bing）
│   ├── file_handler.py     # 文件加载（20+格式）
│   ├── export.py           # 导出（MD/HTML/PDF/TXT）
│   ├── providers/          # AI提供商实现
│   │   ├── base.py         # 抽象基类
│   │   ├── openai.py       # OpenAI提供商
│   │   ├── claude.py       # Claude提供商
│   │   ├── ollama.py       # Ollama提供商
│   │   └── mimo.py         # MiMo提供商
│   ├── templates/          # 提示词模板系统
│   │   └── manager.py      # 18个内置模板
│   └── gui/                # PyQt6 GUI
│       ├── main_window.py  # 主窗口
│       ├── chat_widget.py  # 聊天界面
│       ├── cost_widget.py  # 成本统计
│       └── styles.py       # 深色/浅色主题
├── tests/                  # 测试套件
├── scripts/                # 构建脚本
└── pyproject.toml          # 项目配置
```

### 开发

```bash
# 运行测试
pytest

# 代码格式化
black src/ tests/
ruff check src/ tests/

# 类型检查
mypy src/
```

### 许可证

MIT License
