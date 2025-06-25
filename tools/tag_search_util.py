import os
import re
def parse_yaml_tags(yaml_block):
    tags = []
    in_tags = False
    for line in yaml_block.splitlines():
        line = line.strip()
        if line.startswith('tags:'):
            if '[' in line and ']' in line:
                tag_list = line.split('[',1)[1].split(']',1)[0]
                tags += [t.strip().strip('"\'') for t in tag_list.split(',')]
                in_tags = False
            elif line.endswith(':'):
                in_tags = True
            else:
                tag_val = line.split(':',1)[1].strip()
                if tag_val:
                    tags.append(tag_val.strip('"\''))
                in_tags = False
        elif in_tags:
            if line.startswith('- '):
                tags.append(line[2:].strip('"\''))
            else:
                in_tags = False
    return tags

def remove_code_blocks(text):
    result = []
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith('```'):
            in_code = not in_code
            continue
        if not in_code:
            result.append(line)
    return '\n'.join(result)

def find_notes_with_tags(vault_path, tags):
    """
    Search all .md files in vault_path for notes containing any of the tags (YAML or body).
    tags: list of tags, with or without leading #
    Returns: list of dicts {"title": ..., "path": ...}
    """
    tag_set = set(t.lstrip('#') for t in tags)
    results = []
    for root, _, files in os.walk(vault_path):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                has_tag = False
                yaml_end = -1
                if content.startswith('---'):
                    yaml_end = content.find('---', 3)
                    if yaml_end != -1:
                        yaml_block = content[3:yaml_end].strip()
                        tags_found = parse_yaml_tags(yaml_block)
                        if tag_set.intersection(t.lstrip('#') for t in tags_found):
                            has_tag = True
                if not has_tag:
                    body = content[yaml_end+3:] if yaml_end != -1 else content
                    body_no_code = remove_code_blocks(body)
                    for tag in tags:
                        tag_pattern = r'(?<!\w)#' + re.escape(tag.lstrip('#')) + r'(?![\w/])'
                        if re.search(tag_pattern, body_no_code):
                            has_tag = True
                            break
                if has_tag:
                    rel_path = os.path.relpath(file_path, vault_path)
                    title = os.path.splitext(os.path.basename(file))[0]
                    results.append({"title": title, "path": rel_path})
    return results