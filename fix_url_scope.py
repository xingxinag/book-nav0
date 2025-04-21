import os
import re

# 文件路径
routes_file = 'app/main/routes.py'

# 读取文件内容
with open(routes_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并修改问题代码
pattern = r"""(def generate\(\):
        try:.*?# 确保URL有协议前缀
            )if not url\.startswith\(\('http://', 'https://'\)\):
                url = 'https://' \+ url"""

replacement = r"""\1request_url = url
            if not request_url.startswith(('http://', 'https://')):
                request_url = 'https://' + request_url"""

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# 继续修改后续使用 url 的地方，改为使用 request_url
new_content = new_content.replace(
    "response = requests.get(url, headers=headers, timeout=10)",
    "response = requests.get(request_url, headers=headers, timeout=10)"
)
new_content = new_content.replace(
    "parsed_url = urlparse(url)",
    "parsed_url = urlparse(request_url)"
)
new_content = new_content.replace(
    "icon_result = get_website_icon(url)",
    "icon_result = get_website_icon(request_url)"
)

# 写回文件
with open(routes_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("成功修复 fetch_website_info_with_progress 函数中的变量作用域问题！")
print("现在 url 变量在内部函数中被正确地复制到 request_url 局部变量中使用。") 