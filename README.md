# AI Assistant / AI助手

[English](#english) | [中文](#中文)

---

## English

### Overview

A local AI assistant that solves three major pain points for ordinary users when using AI: inaccurate answers, expensive fees, and privacy concerns.

### Features

- **Multi-AI Aggregation**: Unified interface for OpenAI, Claude, and local models (Ollama)
- **18 Built-in Templates**: Code review, writing, analysis, translation, debugging, and more
- **Cost Tracking**: Monitor API spending with budget alerts and optimization tips
- **Privacy Protection**: Automatic detection and masking of sensitive information (ID cards, phone numbers, bank cards, etc.)
- **Local Storage**: All conversation history stored locally in SQLite
- **GUI Interface**: Modern PyQt6 desktop application
- **CLI Interface**: Full-featured command line tool

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-assistant.git
cd ai-assistant

# Install basic version
pip install -e .

# Install with GUI support
pip install -e ".[gui]"

# Install development dependencies
pip install -e ".[dev]"
```

### Quick Start

**CLI Usage:**
```bash
# Configure API keys
ai-assistant config set openai_api_key "your-key"
ai-assistant config set claude_api_key "your-key"

# Start chatting
ai-assistant chat

# Use a template
ai-assistant chat --template code-review

# View cost statistics
ai-assistant cost stats

# Launch GUI
ai-assistant gui
```

**GUI Usage:**
```bash
ai-assistant-gui
```

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

Three privacy levels:
- **Low**: Detects ID cards, bank cards, passwords
- **Medium**: Adds phone number detection
- **High**: Adds email and IP address detection

### Configuration

Config file location: `~/.ai-assistant/config.yaml`

### Development

```bash
# Run tests
pytest

# Code formatting
black src/ tests/
ruff check src/ tests/
```

### License

MIT License

---

## 中文

### 概述

本地化AI助手，解决普通用户使用AI的三大痛点：回答不准、收费贵、隐私顾虑。

### 功能特点

- **多AI聚合**：统一接口调用OpenAI、Claude、本地模型（Ollama）
- **18个内置模板**：代码审查、文档写作、数据分析、翻译、调试等
- **成本追踪**：监控API支出，提供预算警报和优化建议
- **隐私保护**：自动检测和脱敏敏感信息（身份证、手机号、银行卡等）
- **本地存储**：所有对话历史存储在本地SQLite数据库
- **GUI界面**：现代化PyQt6桌面应用
- **CLI界面**：功能完整的命令行工具

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/ai-assistant.git
cd ai-assistant

# 安装基础版本
pip install -e .

# 安装带GUI支持的版本
pip install -e ".[gui]"

# 安装开发依赖
pip install -e ".[dev]"
```

### 快速开始

**CLI使用：**
```bash
# 配置API密钥
ai-assistant config set openai_api_key "your-key"
ai-assistant config set claude_api_key "your-key"

# 开始对话
ai-assistant chat

# 使用模板
ai-assistant chat --template code-review

# 查看成本统计
ai-assistant cost stats

# 启动GUI
ai-assistant gui
```

**GUI使用：**
```bash
ai-assistant-gui
```

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

三个隐私级别：
- **低**：检测身份证号、银行卡号、密码
- **中**：增加手机号检测
- **高**：增加邮箱和IP地址检测

### 配置文件

配置文件位置：`~/.ai-assistant/config.yaml`

### 开发

```bash
# 运行测试
pytest

# 代码格式化
black src/ tests/
ruff check src/ tests/
```

### 许可证

MIT License
