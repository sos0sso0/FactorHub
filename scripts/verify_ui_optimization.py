#!/usr/bin/env python3
"""
FactorFlow UI 优化验证脚本
检查所有页面是否符合 UI/UX 设计规范
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# 颜色代码
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_header(msg: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{msg}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.END}\n")

class UIChecker:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.html_files = [
            'index.html',
            'factor-management.html',
            'factor-analysis.html',
            'factor-mining.html',
            'portfolio-analysis.html',
            'backtesting.html'
        ]
        self.results = {}

    def check_file(self, filename: str) -> Dict[str, any]:
        """检查单个文件"""
        filepath = self.base_dir / filename
        if not filepath.exists():
            return {'error': f'文件不存在: {filename}'}

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        results = {
            'filename': filename,
            'has_emoji': False,
            'emoji_count': 0,
            'has_cursor_pointer': False,
            'cursor_pointer_count': 0,
            'has_fira_sans': False,
            'has_fira_code': False,
            'has_primary_blue': False,
            'has_transition': False,
            'has_focus_visible': False,
            'issues': []
        }

        # 检查 emoji
        emojis = re.findall(r'[\U0001F300-\U0001F9FF]', content)
        if emojis:
            results['has_emoji'] = True
            results['emoji_count'] = len(emojis)
            results['issues'].append(f'发现 {len(emojis)} 个 emoji')

        # 检查 cursor-pointer
        cursor_pointers = content.count('cursor-pointer')
        if cursor_pointers > 0:
            results['has_cursor_pointer'] = True
            results['cursor_pointer_count'] = cursor_pointers

        # 检查字体
        if 'Fira Sans' in content:
            results['has_fira_sans'] = True
        if 'Fira Code' in content:
            results['has_fira_code'] = True

        # 检查蓝色主题
        if '#3B82F6' in content or 'primary-500' in content:
            results['has_primary_blue'] = True

        # 检查过渡动画
        if 'transition' in content:
            results['has_transition'] = True

        # 检查焦点状态
        if 'focus-visible' in content or 'focus:' in content:
            results['has_focus_visible'] = True

        return results

    def check_all(self):
        """检查所有文件"""
        print_header('FactorFlow UI 优化验证')

        total_issues = 0

        for filename in self.html_files:
            result = self.check_file(filename)
            self.results[filename] = result
            self.print_file_result(result)
            total_issues += len(result.get('issues', []))

        self.print_summary(total_issues)

    def print_file_result(self, result: Dict):
        """打印单个文件的检查结果"""
        filename = result['filename']

        if 'error' in result:
            print_error(f"{filename}: {result['error']}")
            return

        print(f"{Colors.BOLD}{filename}{Colors.END}")

        # Emoji 检查
        if result['has_emoji']:
            print_error(f"  发现 {result['emoji_count']} 个 emoji (应该移除)")
        else:
            print_success("  无 emoji 图标 ✓")

        # cursor-pointer 检查
        if result['cursor_pointer_count'] > 0:
            print_success(f"  包含 {result['cursor_pointer_count']} 处 cursor-pointer")
        else:
            print_warning("  缺少 cursor-pointer")

        # 字体检查
        if result['has_fira_sans']:
            print_success("  使用 Fira Sans 字体")
        else:
            print_warning("  未使用 Fira Sans 字体")

        if result['has_fira_code']:
            print_success("  使用 Fira Code 字体")
        else:
            print_warning("  未使用 Fira Code 字体")

        # 蓝色主题检查
        if result['has_primary_blue']:
            print_success("  使用蓝色主题 (#3B82F6)")
        else:
            print_warning("  未使用蓝色主题")

        # 过渡动画检查
        if result['has_transition']:
            print_success("  包含过渡动画")
        else:
            print_warning("  缺少过渡动画")

        # 焦点状态检查
        if result['has_focus_visible']:
            print_success("  包含焦点状态")
        else:
            print_warning("  缺少焦点状态")

        print()

    def print_summary(self, total_issues: int):
        """打印总结"""
        print_header('检查总结')

        if total_issues == 0:
            print_success("所有检查通过！✓")
            print("\n所有页面都符合 UI/UX 设计规范。")
        else:
            print_error(f"发现 {total_issues} 个问题需要修复")
            print("\n请查看上述详细结果并参考 UI_UX_DESIGN_GUIDELINES.md 进行修复。")

        # 统计信息
        total_cursor_pointer = sum(r.get('cursor_pointer_count', 0) for r in self.results.values() if 'error' not in r)
        total_emoji = sum(r.get('emoji_count', 0) for r in self.results.values() if 'error' not in r)

        print(f"\n{Colors.BOLD}统计信息:{Colors.END}")
        print(f"  总 cursor-pointer: {total_cursor_pointer}")
        print(f"  总 emoji: {total_emoji}")
        print(f"  总问题数: {total_issues}")

def main():
    # 获取前端目录
    base_dir = Path(__file__).parent.parent / 'frontend' / 'web'

    if not base_dir.exists():
        print_error(f"前端目录不存在: {base_dir}")
        return 1

    checker = UIChecker(base_dir)
    checker.check_all()

    return 0

if __name__ == '__main__':
    exit(main())
