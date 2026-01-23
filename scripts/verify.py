#!/usr/bin/env python3
"""Verify ScriptClub Scout installation and configuration."""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version is 3.10+."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need 3.10+")
        return False


def check_env_file():
    """Check if .env exists and has API key."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found - run: cp .env.example .env")
        return False

    with open(env_path) as f:
        content = f.read()

    if "your_api_key_here" in content or "ANTHROPIC_API_KEY=" not in content:
        print("⚠️  .env file exists but API key not configured")
        return False

    print("✅ .env file configured")
    return True


def check_dependencies():
    """Check if key dependencies are importable."""
    required = {
        "streamlit": "streamlit",
        "anthropic": "anthropic",
        "pydantic": "pydantic",
        "PyPDF2": "pypdf2",
        "httpx": "httpx",
        "dotenv": "python-dotenv",
    }

    all_good = True
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - run: uv sync")
            all_good = False

    return all_good


def check_project_structure():
    """Check if all required files exist."""
    required_files = [
        "src/app.py",
        "src/core/resume.py",
        "src/core/schemas.py",
        "src/core/prompts.py",
        "src/core/ranker.py",
        "src/integrations/llm.py",
        "src/integrations/mcp_client.py",
        "pyproject.toml",
        "README.md",
    ]

    all_good = True
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
            all_good = False

    return all_good


def main():
    """Run all checks."""
    print("🔍 Verifying ScriptClub Scout Installation\n")

    print("=" * 50)
    print("Python Version")
    print("=" * 50)
    python_ok = check_python_version()

    print("\n" + "=" * 50)
    print("Environment Configuration")
    print("=" * 50)
    env_ok = check_env_file()

    print("\n" + "=" * 50)
    print("Project Structure")
    print("=" * 50)
    structure_ok = check_project_structure()

    print("\n" + "=" * 50)
    print("Dependencies")
    print("=" * 50)
    deps_ok = check_dependencies()

    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)

    if python_ok and env_ok and structure_ok and deps_ok:
        print("✅ All checks passed! Ready to run:")
        print("   uv run streamlit run src/app.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        if not env_ok:
            print("\n📝 Next step: Configure your .env file")
        if not deps_ok:
            print("\n📦 Next step: Run 'uv sync' to install dependencies")

    print()


if __name__ == "__main__":
    main()
