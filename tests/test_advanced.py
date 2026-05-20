"""高级功能测试"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_assistant.i18n import I18n, i18n, TRANSLATIONS
from ai_assistant.web_search import WebSearcher, DuckDuckGoSearch, SearchResult, SearchResponse
from ai_assistant.file_handler import FileHandler, FileContent
from ai_assistant.export import Exporter
from ai_assistant.storage import Storage


def test_i18n():
    """测试多语言模块"""
    t = I18n()

    # 测试默认语言
    assert t.lang == "zh"

    # 测试中文翻译
    text = t.t("app_name")
    assert text == "AI Assistant"

    # 测试带参数的翻译
    text = t.t("searching", query="test")
    assert "test" in text

    # 测试切换语言
    t.lang = "en"
    assert t.lang == "en"
    text = t.t("goodbye")
    assert text == "Goodbye!"

    # 测试不支持的语言
    try:
        t.lang = "fr"
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # 测试回退到中文
    t.lang = "zh"

    # 测试列出语言
    langs = t.list_languages()
    assert len(langs) == 2
    assert langs[0]["code"] == "zh"
    assert langs[1]["code"] == "en"

    # 测试所有翻译键都存在
    zh_keys = set(TRANSLATIONS["zh"].keys())
    en_keys = set(TRANSLATIONS["en"].keys())
    assert zh_keys == en_keys, f"Translation keys mismatch: {zh_keys.symmetric_difference(en_keys)}"

    print("[OK] i18n模块测试通过")


def test_web_search():
    """测试联网搜索模块"""
    searcher = WebSearcher()

    # 测试默认提供商
    assert searcher.default_provider == "duckduckgo"

    # 测试设置提供商
    searcher.default_provider = "bing"
    assert searcher.default_provider == "bing"
    searcher.default_provider = "duckduckgo"

    # 测试不支持的提供商
    try:
        searcher.default_provider = "google"
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # 测试格式化结果
    response = SearchResponse(
        query="test",
        results=[
            SearchResult(title="Test 1", url="https://example.com/1", snippet="Snippet 1", source="DDG"),
            SearchResult(title="Test 2", url="https://example.com/2", snippet="Snippet 2", source="DDG"),
        ],
        provider="duckduckgo",
    )
    formatted = searcher.format_results(response)
    assert "Test 1" in formatted
    assert "Snippet 1" in formatted
    assert "https://example.com/1" in formatted

    # 测试空结果格式化
    empty_response = SearchResponse(query="test", provider="duckduckgo")
    formatted = searcher.format_results(empty_response)
    assert len(formatted) > 0  # 应该显示"未找到结果"

    # 测试错误结果格式化
    error_response = SearchResponse(query="test", provider="duckduckgo", error="Network error")
    formatted = searcher.format_results(error_response)
    assert "Network error" in formatted

    # 测试上下文提示
    context = searcher.get_context_prompt(response)
    assert "test" in context
    assert "Test 1" in context

    # 测试空结果的上下文提示
    context = searcher.get_context_prompt(empty_response)
    assert context == ""

    print("[OK] 联网搜索模块测试通过")


def test_file_handler():
    """测试文件处理模块"""
    handler = FileHandler()

    # 测试支持格式检查
    assert handler.is_supported("test.txt")
    assert handler.is_supported("test.md")
    assert handler.is_supported("test.py")
    assert handler.is_supported("test.csv")
    assert not handler.is_supported("test.xyz")

    # 测试列出支持格式
    formats = handler.list_supported_formats()
    assert "text" in formats
    assert "markdown" in formats
    assert "csv" in formats
    assert "code" in formats

    # 测试读取txt文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Hello, World!")
        txt_path = f.name

    try:
        result = handler.load_file(txt_path)
        assert result.error is None
        assert result.content == "Hello, World!"
        assert result.format == "text"
        assert result.size == 13
    finally:
        Path(txt_path).unlink(missing_ok=True)

    # 测试读取md文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Title\n\nSome content")
        md_path = f.name

    try:
        result = handler.load_file(md_path)
        assert result.error is None
        assert "# Title" in result.content
        assert result.format == "markdown"
    finally:
        Path(md_path).unlink(missing_ok=True)

    # 测试读取csv文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="") as f:
        f.write("name,age,city\nAlice,30,Beijing\nBob,25,Shanghai")
        csv_path = f.name

    try:
        result = handler.load_file(csv_path)
        assert result.error is None
        assert "name" in result.content
        assert "Alice" in result.content
        assert result.format == "csv"
    finally:
        Path(csv_path).unlink(missing_ok=True)

    # 测试读取json文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write('{"key": "value", "number": 42}')
        json_path = f.name

    try:
        result = handler.load_file(json_path)
        assert result.error is None
        assert '"key"' in result.content
        assert result.format == "json"
    finally:
        Path(json_path).unlink(missing_ok=True)

    # 测试读取yaml文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write("key: value\nlist:\n  - item1\n  - item2")
        yaml_path = f.name

    try:
        result = handler.load_file(yaml_path)
        assert result.error is None
        assert "key" in result.content
        assert result.format == "yaml"
    finally:
        Path(yaml_path).unlink(missing_ok=True)

    # 测试读取代码文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write("def hello():\n    print('hello')")
        py_path = f.name

    try:
        result = handler.load_file(py_path)
        assert result.error is None
        assert "def hello" in result.content
        assert result.format == "code"
    finally:
        Path(py_path).unlink(missing_ok=True)

    # 测试文件不存在
    result = handler.load_file("/nonexistent/file.txt")
    assert result.error is not None
    assert "不存在" in result.error or "not found" in result.error

    # 测试不支持的格式
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        xyz_path = f.name

    try:
        result = handler.load_file(xyz_path)
        assert result.error is not None
    finally:
        Path(xyz_path).unlink(missing_ok=True)

    # 测试上下文提示
    file_content = FileContent(
        path="/test/file.txt",
        name="file.txt",
        format="text",
        content="Test content",
        size=12,
    )
    context = handler.get_context_prompt(file_content)
    assert "file.txt" in context
    assert "Test content" in context

    # 测试错误文件的上下文提示
    error_content = FileContent(
        path="/test/file.txt",
        name="file.txt",
        format="text",
        content="",
        size=0,
        error="File not found",
    )
    context = handler.get_context_prompt(error_content)
    assert "File Error" in context

    print("[OK] 文件处理模块测试通过")


def test_export():
    """测试导出模块"""
    exporter = Exporter()

    # 使用临时数据库
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        test_storage = Storage(db_path)

        # 创建测试数据
        conv_id = test_storage.create_conversation("Test Chat", "openai", "gpt-4o")
        test_storage.add_message(conv_id, "user", "Hello", 10, 0.001)
        test_storage.add_message(conv_id, "assistant", "Hi there! How can I help?", 20, 0.002)
        test_storage.add_message(conv_id, "user", "What's the weather?", 15, 0.0015)

        # 用patch将exporter内部的storage替换为测试的storage
        with patch("ai_assistant.export.storage", test_storage):
            # 测试Markdown导出
            with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
                md_path = f.name

            try:
                result_path = exporter.export_conversation(conv_id, "md", md_path)
                assert result_path == md_path
                content = Path(md_path).read_text(encoding="utf-8")
                assert "Test Chat" in content
                assert "Hello" in content
                assert "Hi there" in content
            finally:
                Path(md_path).unlink(missing_ok=True)

            # 测试HTML导出
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
                html_path = f.name

            try:
                result_path = exporter.export_conversation(conv_id, "html", html_path)
                content = Path(html_path).read_text(encoding="utf-8")
                assert "<!DOCTYPE html>" in content
                assert "Test Chat" in content
                assert "Hello" in content
            finally:
                Path(html_path).unlink(missing_ok=True)

            # 测试TXT导出
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
                txt_path = f.name

            try:
                result_path = exporter.export_conversation(conv_id, "txt", txt_path)
                content = Path(txt_path).read_text(encoding="utf-8")
                assert "Test Chat" in content
                assert "Hello" in content
            finally:
                Path(txt_path).unlink(missing_ok=True)

            # 测试不存在的对话
            try:
                exporter.export_conversation(99999, "md", "/tmp/test.md")
                assert False, "Should raise ValueError"
            except ValueError:
                pass

        print("[OK] 导出模块测试通过")

    finally:
        try:
            db_path.unlink(missing_ok=True)
        except:
            pass


def test_export_cost_report():
    """测试成本报告导出"""
    exporter = Exporter()

    # 测试Markdown格式
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        md_path = f.name

    try:
        # export_cost_report 会调用 cost_tracker.get_stats()，
        # 这里我们直接测试格式化方法
        stats = {
            "total_cost": 1.2345,
            "total_tokens": 10000,
            "record_count": 5,
            "by_provider": {"openai": 0.8, "claude": 0.4345},
            "by_model": {"gpt-4o": 0.8, "claude-sonnet-4-20250514": 0.4345},
        }

        content = exporter._cost_to_markdown(stats)
        assert "1.2345" in content
        assert "10,000" in content
        assert "openai" in content

        content = exporter._cost_to_html(stats)
        assert "<!DOCTYPE html>" in content
        assert "1.2345" in content

        content = exporter._cost_to_text(stats)
        assert "1.2345" in content
        assert "openai" in content

        print("[OK] 成本报告导出测试通过")

    finally:
        Path(md_path).unlink(missing_ok=True)


def test_search_duckduckgo_parsing():
    """测试DuckDuckGo HTML解析"""
    ddg = DuckDuckGoSearch()

    # 测试HTML实体解码
    assert ddg._decode_entities("&amp;") == "&"
    assert ddg._decode_entities("&lt;") == "<"
    assert ddg._decode_entities("&gt;") == ">"
    assert ddg._decode_entities("&#39;") == "'"

    print("[OK] DuckDuckGo解析测试通过")


def main():
    """运行所有测试"""
    print("开始高级功能测试...\n")

    tests = [
        test_i18n,
        test_web_search,
        test_file_handler,
        test_export,
        test_export_cost_report,
        test_search_duckduckgo_parsing,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"[FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n测试结果: {passed} 通过, {failed} 失败")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
