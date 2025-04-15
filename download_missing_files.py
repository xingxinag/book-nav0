import os
import urllib.request
from pathlib import Path

def main():
    """下载缺少的CSS和字体文件"""
    print("开始下载缺少的文件...")
    
    base_path = Path("app/static/vendor")
    
    files_to_download = [
        {
            "url": "https://cdn.bootcdn.net/ajax/libs/bootstrap-icons/1.8.0/font/bootstrap-icons.css",
            "path": base_path / "bootstrap-icons/bootstrap-icons.css"
        }
    ]
    
    for file_info in files_to_download:
        url = file_info["url"]
        path = file_info["path"]
        
        # 确保目录存在
        os.makedirs(path.parent, exist_ok=True)
        
        try:
            print(f"正在下载 {url} -> {path}")
            urllib.request.urlretrieve(url, path)
            print(f"✓ 下载成功: {path}")
        except Exception as e:
            print(f"✗ 下载失败: {path} - {e}")
    
    print("\n开始修复CSS文件中的路径引用...")
    
    # 修复bootstrap-icons.css中的字体路径
    bi_css = base_path / "bootstrap-icons/bootstrap-icons.css"
    if bi_css.exists():
        content = ""
        try:
            with open(bi_css, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换字体路径从相对路径到当前目录下的fonts/
            if "../fonts/" in content:
                content = content.replace("../fonts/", "./fonts/")
                with open(bi_css, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ 已修复 {bi_css} 中的字体路径")
            else:
                print(f"✓ {bi_css} 中未找到需要替换的字体路径")
        except Exception as e:
            print(f"✗ 修复 {bi_css} 时出错: {e}")
    
    # 修复Font Awesome CSS中的字体路径
    fa_css_files = [
        base_path / "font-awesome/css/fontawesome.min.css",
        base_path / "font-awesome/css/solid.min.css"
    ]
    
    for fa_css in fa_css_files:
        if fa_css.exists():
            content = ""
            try:
                with open(fa_css, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换字体路径从相对路径到当前目录下的webfonts/
                if "../webfonts/" in content:
                    content = content.replace("../webfonts/", "./webfonts/")
                    with open(fa_css, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✓ 已修复 {fa_css} 中的字体路径")
                else:
                    print(f"✓ {fa_css} 中未找到需要替换的字体路径")
            except Exception as e:
                print(f"✗ 修复 {fa_css} 时出错: {e}")
    
    print("\n处理完成。如果仍有缺少的文件，请参考 app/static/vendor/README.md 手动下载")

if __name__ == "__main__":
    main() 