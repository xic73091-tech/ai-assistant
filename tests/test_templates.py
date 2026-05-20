"""提示词模板系统测试"""

import json
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_assistant.templates.manager import Template, TemplateManager


def test_builtin_templates_count():
    """测试内置模板数量"""
    manager = TemplateManager()
    templates = manager.list_templates()
    assert len(templates) == 18, f"期望18个模板，实际{len(templates)}个"
    print(f"[OK] 内置模板数量: {len(templates)}")


def test_original_templates():
    """测试原有8个模板仍然存在"""
    manager = TemplateManager()
    original_names = [
        "code-review", "writing", "analysis", "translate",
        "debug", "explain", "summarize", "brainstorm",
    ]
    for name in original_names:
        template = manager.get_template(name)
        assert template is not None, f"原有模板 '{name}' 不存在"
        assert template.description, f"模板 '{name}' 缺少描述"
        assert template.system_prompt, f"模板 '{name}' 缺少系统提示词"
        assert template.user_prompt_template, f"模板 '{name}' 缺少用户提示词模板"
    print("[OK] 原有8个模板完整性验证通过")


def test_new_templates():
    """测试新增10个模板"""
    manager = TemplateManager()
    new_names = [
        "code-generation", "test-case", "api-doc", "data-report",
        "product-requirements", "meeting-notes", "email",
        "learning-plan", "interview-prep", "project-plan",
    ]
    for name in new_names:
        template = manager.get_template(name)
        assert template is not None, f"新增模板 '{name}' 不存在"
        assert template.description, f"模板 '{name}' 缺少描述"
        assert template.system_prompt, f"模板 '{name}' 缺少系统提示词"
        assert template.user_prompt_template, f"模板 '{name}' 缺少用户提示词模板"
        assert template.variables, f"模板 '{name}' 缺少变量定义"
        assert template.category, f"模板 '{name}' 缺少分类"
        assert template.tags, f"模板 '{name}' 缺少标签"
    print("[OK] 新增10个模板完整性验证通过")


def test_template_render():
    """测试模板渲染"""
    manager = TemplateManager()

    # 测试代码生成模板渲染
    template = manager.get_template("code-generation")
    rendered = template.render(
        requirement="实现一个快速排序算法",
        language="Python",
        framework="标准库",
        constraints="需要支持自定义比较函数",
    )
    assert "快速排序" in rendered
    assert "Python" in rendered
    assert "自定义比较函数" in rendered

    # 测试邮件模板渲染
    template = manager.get_template("email")
    rendered = template.render(
        purpose="项目进度汇报",
        recipient="项目经理",
        content="本周完成了API开发",
        tone="正式",
    )
    assert "项目进度汇报" in rendered
    assert "项目经理" in rendered

    # 测试会议纪要模板渲染
    template = manager.get_template("meeting-notes")
    rendered = template.render(
        topic="周会",
        participants="张三、李四",
        content="讨论了Q2计划",
        format="标准格式",
    )
    assert "周会" in rendered
    assert "张三、李四" in rendered

    print("[OK] 模板渲染测试通过")


def test_categories():
    """测试分类系统"""
    manager = TemplateManager()
    categories = manager.get_categories()

    # 验证预期分类存在
    expected_categories = {"code", "writing", "analysis", "language", "learning", "creative", "business"}
    assert expected_categories.issubset(set(categories)), \
        f"缺少分类: {expected_categories - set(categories)}"

    # 验证按分类过滤
    code_templates = manager.list_templates(category="code")
    code_names = [t["name"] for t in code_templates]
    assert "code-review" in code_names
    assert "code-generation" in code_names
    assert "test-case" in code_names
    assert "api-doc" in code_names
    assert "debug" in code_names

    business_templates = manager.list_templates(category="business")
    business_names = [t["name"] for t in business_templates]
    assert "product-requirements" in business_names
    assert "meeting-notes" in business_names
    assert "project-plan" in business_names

    print(f"[OK] 分类系统测试通过，共{len(categories)}个分类: {categories}")


def test_tags():
    """测试标签系统"""
    manager = TemplateManager()

    # 测试获取所有标签
    all_tags = manager.get_all_tags()
    assert len(all_tags) > 0
    assert "review" in all_tags
    assert "testing" in all_tags
    assert "api" in all_tags
    assert "email" in all_tags

    # 测试按标签筛选
    testing_templates = manager.list_templates_by_tag("testing")
    assert len(testing_templates) >= 1
    assert any(t["name"] == "test-case" for t in testing_templates)

    doc_templates = manager.list_templates_by_tag("documentation")
    assert len(doc_templates) >= 1

    print(f"[OK] 标签系统测试通过，共{len(all_tags)}个标签")


def test_search():
    """测试搜索功能"""
    manager = TemplateManager()

    # 按名称搜索
    results = manager.search_templates("code")
    names = [r["name"] for r in results]
    assert "code-review" in names
    assert "code-generation" in names

    # 按描述搜索
    results = manager.search_templates("邮件")
    names = [r["name"] for r in results]
    assert "email" in names

    # 按标签搜索
    results = manager.search_templates("testing")
    names = [r["name"] for r in results]
    assert "test-case" in names

    # 按系统提示词内容搜索（增强的搜索功能）
    results = manager.search_templates("RESTful")
    names = [r["name"] for r in results]
    assert "api-doc" in names

    # 按用户提示词模板内容搜索
    results = manager.search_templates("会议主题")
    names = [r["name"] for r in results]
    assert "meeting-notes" in names

    # 无结果搜索
    results = manager.search_templates("xyznonexistent")
    assert len(results) == 0

    print("[OK] 搜索功能测试通过")


def test_custom_template_load():
    """测试加载单个自定义模板"""
    manager = TemplateManager()

    custom_data = {
        "name": "my-custom",
        "description": "我的自定义模板",
        "system_prompt": "你是一个自定义助手。",
        "user_prompt_template": "请帮我{task}，上下文：{context}",
        "variables": ["task", "context"],
        "category": "custom",
        "tags": ["custom", "personal"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(custom_data, f, ensure_ascii=False)
        temp_path = Path(f.name)

    try:
        template = manager.load_custom_template(temp_path)
        assert template.name == "my-custom"
        assert template.description == "我的自定义模板"

        # 验证已注册到管理器
        loaded = manager.get_template("my-custom")
        assert loaded is not None
        assert loaded.render(task="写代码", context="Python项目") == "请帮我写代码，上下文：Python项目"

        print("[OK] 单个自定义模板加载测试通过")
    finally:
        temp_path.unlink(missing_ok=True)


def test_custom_templates_batch_load():
    """测试批量加载自定义模板"""
    manager = TemplateManager()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # 创建多个自定义模板文件
        for i in range(3):
            data = {
                "name": f"batch-{i}",
                "description": f"批量模板{i}",
                "system_prompt": f"你是批量助手{i}。",
                "user_prompt_template": f"任务{i}: {{task}}",
                "variables": ["task"],
                "category": "batch",
                "tags": ["batch"],
            }
            with open(tmpdir_path / f"template-{i}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

        # 创建一个无效JSON文件（应被跳过）
        with open(tmpdir_path / "invalid.json", "w", encoding="utf-8") as f:
            f.write("not valid json {{{")

        # 创建一个非JSON文件（应被忽略）
        with open(tmpdir_path / "readme.txt", "w", encoding="utf-8") as f:
            f.write("this is not a template")

        loaded = manager.load_custom_templates(tmpdir_path)
        assert len(loaded) == 3, f"期望加载3个模板，实际{len(loaded)}个"

        # 验证模板已注册
        for i in range(3):
            t = manager.get_template(f"batch-{i}")
            assert t is not None
            assert t.description == f"批量模板{i}"

        print("[OK] 批量自定义模板加载测试通过")


def test_save_and_load_template():
    """测试保存和重新加载模板"""
    manager = TemplateManager()
    template = manager.get_template("code-review")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        temp_path = Path(f.name)

    try:
        manager.save_template(template, temp_path)

        # 重新加载验证
        with open(temp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["name"] == "code-review"
        assert data["description"] == "代码审查助手"
        assert "system_prompt" in data
        assert "user_prompt_template" in data
        assert "variables" in data
        assert "category" in data
        assert "tags" in data

        print("[OK] 模板保存和重载测试通过")
    finally:
        temp_path.unlink(missing_ok=True)


def test_template_to_dict():
    """测试模板序列化"""
    manager = TemplateManager()
    template = manager.get_template("project-plan")
    d = template.to_dict()

    assert d["name"] == "project-plan"
    assert d["category"] == "business"
    assert "planning" in d["tags"]
    assert "WBS" in d["system_prompt"]

    print("[OK] 模板序列化测试通过")


def test_empty_directory_batch_load():
    """测试加载空目录"""
    manager = TemplateManager()
    with tempfile.TemporaryDirectory() as tmpdir:
        loaded = manager.load_custom_templates(Path(tmpdir))
        assert len(loaded) == 0
    print("[OK] 空目录批量加载测试通过")


def test_nonexistent_directory_batch_load():
    """测试加载不存在的目录"""
    manager = TemplateManager()
    loaded = manager.load_custom_templates(Path("/nonexistent/path"))
    assert len(loaded) == 0
    print("[OK] 不存在目录批量加载测试通过")


def main():
    """运行所有测试"""
    print("开始模板系统测试...\n")

    tests = [
        test_builtin_templates_count,
        test_original_templates,
        test_new_templates,
        test_template_render,
        test_categories,
        test_tags,
        test_search,
        test_custom_template_load,
        test_custom_templates_batch_load,
        test_save_and_load_template,
        test_template_to_dict,
        test_empty_directory_batch_load,
        test_nonexistent_directory_batch_load,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n测试结果: {passed} 通过, {failed} 失败, 共 {len(tests)} 个")
    if failed > 0:
        sys.exit(1)
    else:
        print("所有测试通过!")


if __name__ == "__main__":
    main()
