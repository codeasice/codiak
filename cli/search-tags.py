#!/usr/bin/env python3
import argparse
import json
import sys
import os

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from tools.tag_search_util import find_notes_with_tags

def main():
    parser = argparse.ArgumentParser(description='Search Obsidian notes for tags')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--tags', nargs='+', required=True, help='Tags to search for (space or comma separated, with or without #)')
    parser.add_argument('--format', choices=['json', 'plain'], default='plain', help='Output format')
    args = parser.parse_args()

    tags = []
    for t in args.tags:
        if ',' in t:
            tags += [x.strip() for x in t.split(',') if x.strip()]
        else:
            tags.append(t.strip())
    results = find_notes_with_tags(args.vault, tags)
    if args.format == 'json':
        print(json.dumps({"results": results}, indent=2))
    else:
        for note in results:
            print(f"{note['title']}: {note['path']}")

if __name__ == '__main__':
    main()