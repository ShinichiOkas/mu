import os
import re

def md_to_html(text):
    # Headings
    for i in range(6, 0, -1):
        text = re.sub(rf'^{"#" * i}\s+(.*)$', rf'<h{i}>\1</h{i}>', text, flags=re.MULTILINE)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Unordered Lists
    # This is a simple implementation. It looks for lines starting with '-' and wraps them.
    lines = text.splitlines()
    new_lines = []
    in_list = False
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            new_lines.append(f'<li>{line.strip()[2:]}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)
    if in_list:
        new_lines.append('</ul>')
    
    return '\n'.join(new_lines)

def main():
    src_dir = 'md_src'
    out_dir = 'site'
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    md_files = [f for f in os.listdir(src_dir) if f.endswith('.md')]
    md_files.sort()
    
    html_files = []
    for md_file in md_files:
        with open(os.path.join(src_dir, md_file), 'r', encoding='utf-8') as f:
            content = f.read()
        
        html_content = md_to_html(content)
        
        html_file = md_file.replace('.md', '.html')
        with open(os.path.join(out_dir, html_file), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        html_files.append(html_file)
    
    # Generate index.html
    index_content = '<html><body><h1>Index</h1><ul>'
    for html_file in html_files:
        index_content += f'<li><a href="{html_file}">{html_file}</a></li>'
    index_content += '</ul></body></html>'
    
    with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_content)
        
    print(f'SITEGEN OK {len(md_files)}')

if __name__ == '__main__':
    main()
