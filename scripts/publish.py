#!/usr/bin/env python3
"""
AI Assistant 发布脚本

用法:
    python scripts/publish.py              # 构建并检查，不上传
    python scripts/publish.py --test       # 上传到 TestPyPI
    python scripts/publish.py --publish    # 上传到 PyPI
    python scripts/publish.py --clean      # 清理构建产物
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """运行命令并输出结果"""
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        print(f"命令失败，退出码: {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    return result


def clean():
    """清理构建产物"""
    print("清理构建产物...")
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
            print(f"  已删除: {d}")

    # 清理 egg-info 和 __pycache__
    for pattern in ["*.egg-info", "**/__pycache__"]:
        for p in PROJECT_ROOT.glob(pattern):
            if p.is_dir():
                shutil.rmtree(p)
                print(f"  已删除: {p}")

    print("清理完成。")


def check_version():
    """检查版本号一致性"""
    print("检查版本号一致性...")

    # 从 pyproject.toml 读取版本
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    pyproject_content = pyproject_path.read_text(encoding="utf-8")
    pyproject_version = None
    for line in pyproject_content.splitlines():
        if line.strip().startswith("version"):
            pyproject_version = line.split("=")[1].strip().strip('"')
            break

    # 从 ai_assistant/__init__.py 读取版本
    init_path = PROJECT_ROOT / "ai_assistant" / "__init__.py"
    init_content = init_path.read_text(encoding="utf-8")
    init_version = None
    for line in init_content.splitlines():
        if "__version__" in line:
            init_version = line.split("=")[1].strip().strip('"')
            break

    print(f"  pyproject.toml: {pyproject_version}")
    print(f"  ai_assistant/__init__.py: {init_version}")

    if pyproject_version != init_version:
        print("警告: 版本号不一致!", file=sys.stderr)
        sys.exit(1)

    print(f"版本号一致: {pyproject_version}")
    return pyproject_version


def build():
    """构建分发包"""
    print("构建分发包...")
    clean()
    run([sys.executable, "-m", "build"])

    # 列出生成的文件
    print("\n构建产物:")
    for f in DIST_DIR.iterdir():
        print(f"  {f.name}")


def check():
    """检查分发包"""
    print("检查分发包...")
    run([sys.executable, "-m", "twine", "check", str(DIST_DIR / "*")])


def upload_to_testpypi():
    """上传到 TestPyPI"""
    print("上传到 TestPyPI...")
    run([
        sys.executable, "-m", "twine", "upload",
        "--repository", "testpypi",
        str(DIST_DIR / "*"),
    ])
    print("\n上传成功! 安装命令:")
    print("  pip install --index-url https://test.pypi.org/simple/ ai-assistant")


def upload_to_pypi():
    """上传到 PyPI"""
    print("上传到 PyPI...")
    run([sys.executable, "-m", "twine", "upload", str(DIST_DIR / "*")])
    print("\n上传成功! 安装命令:")
    print("  pip install ai-assistant")


def main():
    parser = argparse.ArgumentParser(description="AI Assistant 发布脚本")
    parser.add_argument("--clean", action="store_true", help="清理构建产物")
    parser.add_argument("--build", action="store_true", help="仅构建")
    parser.add_argument("--test", action="store_true", help="上传到 TestPyPI")
    parser.add_argument("--publish", action="store_true", help="上传到 PyPI")
    args = parser.parse_args()

    if args.clean:
        clean()
        return

    # 检查版本号
    version = check_version()

    if args.build:
        build()
        check()
        return

    if args.test:
        build()
        check()
        upload_to_testpypi()
        return

    if args.publish:
        # 发布到正式 PyPI 前确认
        print(f"\n即将发布版本 {version} 到 PyPI")
        confirm = input("确认继续? (y/N): ").strip().lower()
        if confirm != "y":
            print("已取消。")
            return
        build()
        check()
        upload_to_pypi()
        return

    # 默认: 仅构建和检查
    build()
    check()
    print("\n构建和检查完成。如需上传:")
    print("  python scripts/publish.py --test      # 上传到 TestPyPI")
    print("  python scripts/publish.py --publish   # 上传到 PyPI")


if __name__ == "__main__":
    main()
