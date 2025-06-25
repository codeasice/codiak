#!/usr/bin/env python3
"""Command-line interface for listing UI tools."""
import argparse
import json
import sys
import os

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from tools.ui_tools_manager import UIToolsManager

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description='List UI tools from AI Procurement Manager')
    parser.add_argument('--category', '-c', help='Filter by category')
    parser.add_argument('--tag', '-t', help='Filter by tag')
    parser.add_argument('--no-descriptions', action='store_true',
                       help='Exclude descriptions from output')
    parser.add_argument('--format', '-f', choices=['json', 'table', 'simple'],
                       default='table', help='Output format')

    args = parser.parse_args()

    try:
        manager = UIToolsManager(use_fast_mode=True)  # CLI always uses fast mode
        tools = manager.get_tools()

        # Apply filters
        if args.category or args.tag:
            tools = manager.filter_tools(tools, category=args.category, tag=args.tag)

        # Get summary
        summary = manager.get_tools_summary(tools)

        result = {
            'tools': tools,
            'metadata': summary
        }

        if args.format == 'json':
            print(json.dumps(result, indent=2))
        elif args.format == 'simple':
            for tool in result['tools']:
                print(f"{tool['id']}: {tool['short_title']} ({tool['category']})")
        else:  # table format
            total_tools = result['metadata']['total_tools']
            print(f"Found {total_tools} tools:")
            print("-" * 80)
            for tool in result['tools']:
                print(f"• {tool['short_title']}")
                print(f"  ID: {tool['id']}")
                print(f"  Category: {tool['category']}")
                if tool.get('tags') and tool['tags']:
                    print(f"  Tags: {', '.join(tool['tags'])}")
                if not args.no_descriptions and tool.get('description'):
                    description = tool['description']
                    if len(description) > 100:
                        description = description[:100] + "..."
                    print(f"  Description: {description}")
                print()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()