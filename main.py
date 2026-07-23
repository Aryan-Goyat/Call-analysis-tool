import re

with open('c:/Users/Admin/OneDrive/Desktop/Call Analysis tool/Call-Analysis-Tool/Frontend/Notifications.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'PAGE_CSS\s*=\s*\"\"\"[\s\S]*?\"\"\"', '', content)
content = content.replace('            html.Style(PAGE_CSS),\n', '')

with open('c:/Users/Admin/OneDrive/Desktop/Call Analysis tool/Call-Analysis-Tool/Frontend/Notifications.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
