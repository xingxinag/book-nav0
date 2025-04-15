import os
import shutil
from pathlib import Path

def main():
    """修复vendor目录的嵌套结构问题"""
    print("开始修复vendor目录结构...")
    
    # 基础路径
    base_path = Path("app/static")
    nested_vendor = base_path / "vendor/app/static/vendor"
    target_vendor = base_path / "vendor"
    
    # 确认嵌套路径存在
    if not nested_vendor.exists():
        print(f"错误: 嵌套路径 {nested_vendor} 不存在!")
        return
    
    # 创建所需的目录
    dirs_to_create = [
        "bootstrap/css",
        "bootstrap/js",
        "bootstrap-icons",
        "bootstrap-icons/fonts",
        "font-awesome/css",
        "font-awesome/webfonts",
        "animate.css",
        "particles.js"
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(target_vendor / dir_path, exist_ok=True)
        print(f"已创建目录: {target_vendor / dir_path}")
    
    # 移动文件
    libraries = [
        "bootstrap",
        "bootstrap-icons",
        "font-awesome",
        "animate.css",
        "particles.js"
    ]
    
    for lib in libraries:
        nested_lib_path = nested_vendor / lib
        target_lib_path = target_vendor / lib
        
        if nested_lib_path.exists():
            # 移动文件
            for item in nested_lib_path.glob("**/*"):
                if item.is_file():
                    # 创建目标路径
                    rel_path = item.relative_to(nested_lib_path)
                    target_file = target_lib_path / rel_path
                    
                    # 确保目标目录存在
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    try:
                        shutil.copy2(item, target_file)
                        print(f"复制: {item} -> {target_file}")
                    except Exception as e:
                        print(f"复制文件 {item} 失败: {e}")
        else:
            print(f"警告: 路径 {nested_lib_path} 不存在，跳过")
    
    print("\n检查并修复CSS文件中的路径引用...")
    
    # 修复bootstrap-icons.css中的字体路径
    bi_css = target_vendor / "bootstrap-icons" / "bootstrap-icons.css"
    if bi_css.exists():
        fix_css_paths(bi_css, "../fonts/", "./fonts/")
    else:
        print(f"警告: {bi_css} 不存在，需要手动下载")
    
    # 修复Font Awesome CSS中的字体路径
    fa_css_files = [
        target_vendor / "font-awesome/css/fontawesome.min.css", 
        target_vendor / "font-awesome/css/solid.min.css"
    ]
    
    for fa_css in fa_css_files:
        if fa_css.exists():
            fix_css_paths(fa_css, "../webfonts/", "./webfonts/")
        else:
            print(f"警告: {fa_css} 不存在，需要手动下载")
    
    print("\n清理嵌套目录...")
    try:
        if (base_path / "vendor/app").exists():
            shutil.rmtree(base_path / "vendor/app")
            print("已删除嵌套目录")
    except Exception as e:
        print(f"清理嵌套目录失败: {e}")
    
    print("\n处理完成! 请检查以下文件是否存在，如果不存在需要手动下载:")
    files_to_check = [
        "bootstrap/css/bootstrap.min.css",
        "bootstrap/js/bootstrap.bundle.min.js",
        "bootstrap-icons/bootstrap-icons.css",
        "bootstrap-icons/fonts/bootstrap-icons.woff",
        "bootstrap-icons/fonts/bootstrap-icons.woff2",
        "font-awesome/css/fontawesome.min.css",
        "font-awesome/css/solid.min.css",
        "animate.css/animate.min.css",
        "particles.js/particles.min.js"
    ]
    
    for file_path in files_to_check:
        file_exists = (target_vendor / file_path).exists()
        status = "✓" if file_exists else "✗"
        print(f"[{status}] {target_vendor / file_path}")
    
    print("\n如果有标记为 ✗ 的文件，请参考 app/static/vendor/README.md 手动下载")

def fix_css_paths(css_file, old_path, new_path):
    """修复CSS文件中的路径引用"""
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_path in content:
            content = content.replace(old_path, new_path)
            with open(css_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已修复 {css_file} 中的路径: {old_path} -> {new_path}")
        else:
            print(f"{css_file} 中未找到需要替换的路径 {old_path}")
    except Exception as e:
        print(f"修复 {css_file} 中的路径失败: {e}")

if __name__ == "__main__":
    main() 