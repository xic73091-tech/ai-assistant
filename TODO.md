# AI Assistant - 待办事项 / TODO List

## 项目状态 / Project Status
- **当前版本**: v0.2.0
- **GitHub**: https://github.com/xic73091-tech/ai-assistant
- **最后更新**: 2026-05-19

---

## 明天要做的事 / Tomorrow's Tasks

### 1. 注册PyPI账号并发布 / Register PyPI and Publish
- [ ] 访问 https://pypi.org/account/register/ 注册账号
- [ ] 访问 https://pypi.org/manage/account/token/ 创建API Token
- [ ] 运行 `python scripts/publish.py --test` 先发布到TestPyPI测试
- [ ] 运行 `python scripts/publish.py --publish` 正式发布到PyPI
- [ ] 验证 `pip install ai-assistant` 可以正常安装

### 2. 修复已知问题 / Fix Known Issues
- [ ] CLI流式输出在Windows下仍有编码问题（第一次调用正常，后续失败）
- [ ] 测试所有4个AI提供商（OpenAI、Claude、Ollama、MiMo）
- [ ] 确保GUI在不同分辨率下正常显示

### 3. 完善文档 / Improve Documentation
- [ ] 添加使用示例和截图到README
- [ ] 创建详细的安装指南
- [ ] 添加API配置教程

### 4. 功能增强 / Feature Enhancements
- [ ] 添加更多AI提供商支持
- [ ] 优化本地模型（Ollama）的使用体验
- [ ] 添加对话导出为PDF功能
- [ ] 添加多语言界面切换

---

## 已完成的工作 / Completed Work

### v0.2.0 (2026-05-19)
- [x] 多AI聚合（OpenAI、Claude、Ollama、MiMo）
- [x] 18个内置提示词模板
- [x] 成本追踪和预算警报
- [x] 隐私保护和敏感信息检测
- [x] 本地SQLite存储
- [x] PyQt6 GUI界面（深色/浅色主题）
- [x] CLI命令行工具
- [x] 联网搜索功能
- [x] 文件处理功能
- [x] 对话导出功能
- [x] 国际化支持（i18n）
- [x] Windows中文编码修复
- [x] 完整测试套件

### v0.1.0 (2026-05-19)
- [x] 项目初始化
- [x] 基本CLI功能
- [x] 配置管理
- [x] 本地存储

---

## 技术栈 / Tech Stack
- **语言**: Python 3.10+
- **CLI**: Click + Rich
- **GUI**: PyQt6
- **数据库**: SQLite
- **AI接口**: OpenAI SDK, Anthropic SDK, httpx
- **测试**: pytest
- **构建**: hatchling

---

## 项目结构 / Project Structure
```
ai-assistant/
├── src/
│   ├── cli.py              # CLI主程序
│   ├── config.py           # 配置管理
│   ├── storage.py          # 本地存储
│   ├── cost_tracker.py     # 成本追踪
│   ├── privacy.py          # 隐私保护
│   ├── i18n.py             # 国际化
│   ├── web_search.py       # 联网搜索
│   ├── file_handler.py     # 文件处理
│   ├── export.py           # 导出功能
│   ├── providers/          # AI提供商
│   ├── templates/          # 提示词模板
│   └── gui/                # GUI界面
├── tests/                  # 测试
├── scripts/                # 脚本
└── pyproject.toml          # 项目配置
```

---

## 联系方式 / Contact
- **GitHub**: https://github.com/xic73091-tech
- **项目地址**: https://github.com/xic73091-tech/ai-assistant

---

## 备注 / Notes
- MiMo API使用小写模型名称：`mimo-v2.5-pro`, `mimo-v2.5`
- MiMo Base URL: `https://token-plan-cn.xiaomimimo.com/v1`
- 代理地址：配置在本地环境变量中，勿公开
- Windows编码修复：使用 `chcp 65001` 和 UTF-8 包装

---

*最后更新: 2026-05-19 22:00*
