"""提示词模板管理器"""

import json
from pathlib import Path
from typing import Any, Optional


class Template:
    """提示词模板"""

    def __init__(self, name: str, data: dict[str, Any]):
        self.name = name
        self.description = data.get("description", "")
        self.system_prompt = data.get("system_prompt", "")
        self.user_prompt_template = data.get("user_prompt_template", "")
        self.variables = data.get("variables", [])
        self.category = data.get("category", "general")
        self.tags = data.get("tags", [])

    def render(self, **kwargs) -> str:
        """渲染模板"""
        prompt = self.user_prompt_template
        for key, value in kwargs.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        return prompt

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.system_prompt

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "variables": self.variables,
            "category": self.category,
            "tags": self.tags,
        }


class TemplateManager:
    """模板管理器"""

    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path(__file__).parent
        self.templates: dict[str, Template] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """加载内置模板"""
        builtin_templates = {
            # ===== 原有8个模板 =====
            "code-review": {
                "description": "代码审查助手",
                "system_prompt": "你是一位资深的代码审查专家。请从代码质量、安全性、性能、可维护性等方面进行审查，给出具体的改进建议。审查时请逐条列出问题，按严重程度排序，并提供修复示例代码。",
                "user_prompt_template": "请审查以下代码：\n\n```{language}\n{code}\n```\n\n请重点关注：{focus}",
                "variables": ["language", "code", "focus"],
                "category": "code",
                "tags": ["review", "quality", "security"],
            },
            "writing": {
                "description": "文档写作助手",
                "system_prompt": "你是一位专业的技术文档写作者。请用清晰、简洁、准确的语言撰写文档，注重结构和可读性。使用恰当的标题层级、列表和代码块来组织内容。",
                "user_prompt_template": "请帮我写一份{document_type}，主题是：{topic}\n\n目标读者：{audience}\n\n要求：{requirements}",
                "variables": ["document_type", "topic", "audience", "requirements"],
                "category": "writing",
                "tags": ["documentation", "technical-writing"],
            },
            "analysis": {
                "description": "数据分析助手",
                "system_prompt": "你是一位数据分析专家，擅长从数据中提取有价值的洞察。请用结构化的方式呈现分析结果，包含数据概览、关键发现、趋势分析和可操作建议。",
                "user_prompt_template": "请分析以下数据：\n\n{data}\n\n分析目标：{goal}\n\n请提供：{output_format}",
                "variables": ["data", "goal", "output_format"],
                "category": "analysis",
                "tags": ["data", "insights", "statistics"],
            },
            "translate": {
                "description": "翻译优化助手",
                "system_prompt": "你是一位专业的翻译专家，精通多种语言。请提供准确、自然、符合目标语言习惯的翻译。对于专业术语，请在括号中保留原文。如有多种译法，请简要说明选择理由。",
                "user_prompt_template": "请将以下内容翻译成{target_language}：\n\n{text}\n\n风格要求：{style}",
                "variables": ["target_language", "text", "style"],
                "category": "language",
                "tags": ["translation", "localization"],
            },
            "debug": {
                "description": "调试助手",
                "system_prompt": "你是一位调试专家。请帮助分析代码问题，按照以下步骤进行：1) 理解错误信息；2) 定位问题根源；3) 分析触发条件；4) 提供修复方案并解释原因。优先考虑最常见的原因。",
                "user_prompt_template": "遇到以下问题：\n\n错误信息：{error}\n\n相关代码：\n```{language}\n{code}\n```\n\n已尝试的解决方案：{tried}",
                "variables": ["error", "language", "code", "tried"],
                "category": "code",
                "tags": ["debugging", "troubleshooting"],
            },
            "explain": {
                "description": "概念解释助手",
                "system_prompt": "你是一位善于解释复杂概念的老师。请用简单易懂的语言解释技术概念，多用类比和例子。先给出一句话定义，再逐步展开，最后用实际场景举例说明。",
                "user_prompt_template": "请解释{concept}这个概念。\n\n我的背景：{background}\n\n希望了解的深度：{depth}",
                "variables": ["concept", "background", "depth"],
                "category": "learning",
                "tags": ["explanation", "teaching"],
            },
            "summarize": {
                "description": "内容总结助手",
                "system_prompt": "你是一位信息提炼专家。请从大量内容中提取关键信息，生成简洁准确的总结。总结应包含核心观点、关键数据和主要结论，避免遗漏重要信息。",
                "user_prompt_template": "请总结以下内容：\n\n{content}\n\n总结长度：{length}\n\n重点突出：{focus}",
                "variables": ["content", "length", "focus"],
                "category": "writing",
                "tags": ["summary", "extraction"],
            },
            "brainstorm": {
                "description": "头脑风暴助手",
                "system_prompt": "你是一位创意激发专家。请提供多样化的创意想法，鼓励发散思维。每个方案应包含：方案名称、核心思路、预期效果和实施难度评估。优先提供创新性方案，同时也不忽视务实的解决方案。",
                "user_prompt_template": "我需要关于{topic}的创意想法。\n\n背景：{context}\n\n约束条件：{constraints}\n\n请提供{count}个不同的方案。",
                "variables": ["topic", "context", "constraints", "count"],
                "category": "creative",
                "tags": ["ideas", "innovation"],
            },

            # ===== 新增10个模板 =====
            "code-generation": {
                "description": "代码生成助手",
                "system_prompt": "你是一位资深的全栈开发工程师。根据需求生成高质量、可直接运行的代码。代码应遵循最佳实践，包含必要的注释、错误处理和类型提示。优先考虑可读性和可维护性，不写过度工程化的代码。",
                "user_prompt_template": "请根据以下需求生成代码：\n\n需求描述：{requirement}\n\n编程语言：{language}\n\n技术栈/框架：{framework}\n\n特殊要求：{constraints}",
                "variables": ["requirement", "language", "framework", "constraints"],
                "category": "code",
                "tags": ["generation", "code", "programming"],
            },
            "test-case": {
                "description": "测试用例生成助手",
                "system_prompt": "你是一位测试架构师，擅长编写全面的测试用例。请生成覆盖正常流程、边界条件和异常场景的测试用例。每个测试用例应包含：测试名称、前置条件、测试步骤、预期结果。代码测试请使用对应语言的主流测试框架。",
                "user_prompt_template": "请为以下内容生成测试用例：\n\n测试对象：{target}\n\n编程语言/框架：{language}\n\n测试类型：{test_type}\n\n重点关注：{focus}",
                "variables": ["target", "language", "test_type", "focus"],
                "category": "code",
                "tags": ["testing", "unit-test", "quality"],
            },
            "api-doc": {
                "description": "API文档生成助手",
                "system_prompt": "你是一位API文档专家。请生成清晰、完整的API文档，遵循RESTful规范。文档应包含：接口描述、请求方法、URL路径、请求参数（含类型和是否必填）、响应格式、状态码说明和调用示例。使用Markdown格式输出。",
                "user_prompt_template": "请为以下API生成文档：\n\nAPI描述：{description}\n\n接口信息：{endpoints}\n\n数据模型：{models}\n\n文档风格：{style}",
                "variables": ["description", "endpoints", "models", "style"],
                "category": "code",
                "tags": ["api", "documentation", "technical-writing"],
            },
            "data-report": {
                "description": "数据分析报告助手",
                "system_prompt": "你是一位高级数据分析师。请生成专业的数据分析报告，结构包括：执行摘要、数据概览、关键指标分析、趋势洞察、异常发现、结论与建议。使用具体数据支撑观点，避免主观臆断。报告语言应专业但不晦涩，适合向非技术人员汇报。",
                "user_prompt_template": "请生成数据分析报告：\n\n数据描述：{data_description}\n\n分析维度：{dimensions}\n\n业务背景：{business_context}\n\n报告受众：{audience}",
                "variables": ["data_description", "dimensions", "business_context", "audience"],
                "category": "analysis",
                "tags": ["data", "report", "analytics"],
            },
            "product-requirements": {
                "description": "产品需求文档助手",
                "system_prompt": "你是一位经验丰富的产品经理。请帮助整理产品需求文档（PRD），结构包括：需求背景与目标、用户画像、功能需求（含优先级）、非功能需求、用户故事、验收标准、风险评估。需求描述应清晰无歧义，便于开发团队理解和执行。",
                "user_prompt_template": "请整理以下产品需求：\n\n产品/功能名称：{product}\n\n需求背景：{background}\n\n目标用户：{users}\n\n核心诉求：{requirements}",
                "variables": ["product", "background", "users", "requirements"],
                "category": "business",
                "tags": ["product", "requirements", "prd"],
            },
            "meeting-notes": {
                "description": "会议纪要助手",
                "system_prompt": "你是一位专业的会议记录员。请将会议内容整理为结构化的会议纪要，包含：会议基本信息（时间、参会人、主题）、议题讨论摘要、决议事项、待办事项（含负责人和截止日期）、下次会议安排。语言简洁准确，重点突出行动项。",
                "user_prompt_template": "请整理以下会议内容为会议纪要：\n\n会议主题：{topic}\n\n参会人员：{participants}\n\n会议内容：{content}\n\n格式要求：{format}",
                "variables": ["topic", "participants", "content", "format"],
                "category": "business",
                "tags": ["meeting", "notes", "minutes"],
            },
            "email": {
                "description": "邮件撰写助手",
                "system_prompt": "你是一位商务沟通专家。请撰写专业得体的邮件。邮件应有清晰的主题行、恰当的称呼、结构化的正文（目的、详情、行动项）和礼貌的结尾。语气根据场景调整：正式商务、友好协作或紧急催办。中文邮件使用标准商务格式。",
                "user_prompt_template": "请帮我撰写一封邮件：\n\n邮件目的：{purpose}\n\n收件人：{recipient}\n\n关键内容：{content}\n\n语气风格：{tone}",
                "variables": ["purpose", "recipient", "content", "tone"],
                "category": "writing",
                "tags": ["email", "professional", "communication"],
            },
            "learning-plan": {
                "description": "学习计划制定助手",
                "system_prompt": "你是一位学习规划顾问。请制定切实可行的学习计划，包含：学习目标与里程碑、分阶段学习内容、推荐学习资源、每日/每周时间安排、自我评估方式。计划应考虑学习者的现有水平和可用时间，循序渐进，避免过于激进。",
                "user_prompt_template": "请帮我制定学习计划：\n\n学习主题：{topic}\n\n当前水平：{current_level}\n\n目标水平：{target_level}\n\n可用时间：{time_available}\n\n学习偏好：{preferences}",
                "variables": ["topic", "current_level", "target_level", "time_available", "preferences"],
                "category": "learning",
                "tags": ["learning", "plan", "study"],
            },
            "interview-prep": {
                "description": "面试准备助手",
                "system_prompt": "你是一位资深的面试辅导专家。请根据目标岗位准备面试问题和参考答案。问题应覆盖技术能力、项目经验、行为面试和系统设计等维度。参考答案应结构清晰，突出候选人的思考过程和解决问题的能力，而非死记硬背的标准答案。",
                "user_prompt_template": "请帮我准备面试：\n\n目标岗位：{position}\n\n公司/行业：{company}\n\n经验年限：{experience}\n\n需要重点准备：{focus_areas}",
                "variables": ["position", "company", "experience", "focus_areas"],
                "category": "learning",
                "tags": ["interview", "preparation", "career"],
            },
            "project-plan": {
                "description": "项目计划制定助手",
                "system_prompt": "你是一位PMP认证的项目管理专家。请制定专业的项目计划，包含：项目目标与范围、关键交付物、工作分解结构（WBS）、时间线与里程碑、资源分配、风险识别与应对策略、沟通计划。计划应务实可执行，预留合理的缓冲时间。",
                "user_prompt_template": "请帮我制定项目计划：\n\n项目名称：{project}\n\n项目目标：{objective}\n\n约束条件：{constraints}\n\n团队规模：{team_size}\n\n预计周期：{timeline}",
                "variables": ["project", "objective", "constraints", "team_size", "timeline"],
                "category": "business",
                "tags": ["project", "planning", "management"],
            },
        }

        for name, data in builtin_templates.items():
            self.templates[name] = Template(name, data)

    def get_template(self, name: str) -> Optional[Template]:
        """获取模板"""
        return self.templates.get(name)

    def list_templates(self, category: Optional[str] = None) -> list[dict[str, str]]:
        """列出模板，可按分类过滤"""
        templates = []
        for name, template in self.templates.items():
            if category and template.category != category:
                continue
            templates.append({
                "name": name,
                "description": template.description,
                "category": template.category,
                "tags": ", ".join(template.tags),
            })
        return templates

    def get_categories(self) -> list[str]:
        """获取所有分类"""
        categories = set()
        for template in self.templates.values():
            categories.add(template.category)
        return sorted(categories)

    def get_all_tags(self) -> list[str]:
        """获取所有标签（去重排序）"""
        tags = set()
        for template in self.templates.values():
            tags.update(template.tags)
        return sorted(tags)

    def list_templates_by_tag(self, tag: str) -> list[dict[str, str]]:
        """按标签筛选模板"""
        results = []
        tag_lower = tag.lower()
        for name, template in self.templates.items():
            if tag_lower in [t.lower() for t in template.tags]:
                results.append({
                    "name": name,
                    "description": template.description,
                    "category": template.category,
                    "tags": ", ".join(template.tags),
                })
        return results

    def search_templates(self, keyword: str) -> list[dict[str, str]]:
        """搜索模板（搜索名称、描述、标签、系统提示词和用户提示词模板）"""
        results = []
        keyword = keyword.lower()
        for name, template in self.templates.items():
            if (keyword in name.lower() or
                keyword in template.description.lower() or
                keyword in " ".join(template.tags).lower() or
                keyword in template.system_prompt.lower() or
                keyword in template.user_prompt_template.lower()):
                results.append({
                    "name": name,
                    "description": template.description,
                    "category": template.category,
                    "tags": ", ".join(template.tags),
                })
        return results

    def load_custom_template(self, file_path: Path) -> Template:
        """从JSON文件加载单个自定义模板"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        name = data.get("name", file_path.stem)
        template = Template(name, data)
        self.templates[name] = template
        return template

    def load_custom_templates(self, directory: Optional[Path] = None) -> list[Template]:
        """从目录批量加载自定义模板（加载所有.json文件）"""
        target_dir = directory or self.template_dir
        loaded = []
        if not target_dir.exists() or not target_dir.is_dir():
            return loaded
        for json_file in sorted(target_dir.glob("*.json")):
            try:
                template = self.load_custom_template(json_file)
                loaded.append(template)
            except (json.JSONDecodeError, KeyError, OSError):
                # 跳过无法解析的文件，不中断批量加载
                continue
        return loaded

    def save_template(self, template: Template, file_path: Path) -> None:
        """保存模板到JSON文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
