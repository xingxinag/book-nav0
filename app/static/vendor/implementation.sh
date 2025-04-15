#!/bin/bash
# CDN资源本地化实施脚本

# 创建目录结构
mkdir -p app/static/vendor/bootstrap/css
mkdir -p app/static/vendor/bootstrap/js
mkdir -p app/static/vendor/bootstrap-icons/fonts
mkdir -p app/static/vendor/font-awesome/css
mkdir -p app/static/vendor/font-awesome/webfonts
mkdir -p app/static/vendor/animate.css
mkdir -p app/static/vendor/particles.js

# 下载Bootstrap资源
echo "正在下载Bootstrap资源..."
curl -o app/static/vendor/bootstrap/css/bootstrap.min.css https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css
curl -o app/static/vendor/bootstrap/js/bootstrap.bundle.min.js https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/js/bootstrap.bundle.min.js

# 下载Bootstrap Icons
echo "正在下载Bootstrap Icons资源..."
curl -o app/static/vendor/bootstrap-icons/bootstrap-icons.css https://cdn.bootcdn.net/ajax/libs/bootstrap-icons/1.8.0/font/bootstrap-icons.css

# 如果需要下载字体文件，请手动从GitHub下载完整包
echo "请手动下载Bootstrap Icons字体文件: https://github.com/twbs/icons/releases/tag/v1.8.0"
echo "并将fonts目录复制到 app/static/vendor/bootstrap-icons/ 下"

# 下载Font Awesome资源
echo "正在下载Font Awesome资源..."
curl -o app/static/vendor/font-awesome/css/fontawesome.min.css https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/css/fontawesome.min.css
curl -o app/static/vendor/font-awesome/css/solid.min.css https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/css/solid.min.css

# 如果需要字体文件，请手动下载完整包
echo "请手动下载Font Awesome字体文件: https://fontawesome.com/download"
echo "并将webfonts目录复制到 app/static/vendor/font-awesome/ 下"

# 下载Animate.css
echo "正在下载Animate.css资源..."
curl -o app/static/vendor/animate.css/animate.min.css https://cdn.bootcdn.net/ajax/libs/animate.css/4.1.1/animate.min.css

# 下载particles.js
echo "正在下载particles.js资源..."
curl -o app/static/vendor/particles.js/particles.min.js https://cdn.bootcdn.net/ajax/libs/particles.js/2.0.0/particles.min.js

echo "所有资源下载完成！"
echo "请确保Bootstrap Icons和Font Awesome的字体文件已正确放置"
echo "然后修改app/templates/base.html文件，将CDN引用修改为本地资源引用" 