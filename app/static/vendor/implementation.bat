@echo off
REM CDN资源本地化实施脚本 (Windows版)

echo 创建目录结构...
mkdir app\static\vendor\bootstrap\css
mkdir app\static\vendor\bootstrap\js
mkdir app\static\vendor\bootstrap-icons\fonts
mkdir app\static\vendor\font-awesome\css
mkdir app\static\vendor\font-awesome\webfonts
mkdir app\static\vendor\animate.css
mkdir app\static\vendor\particles.js

echo 正在下载Bootstrap资源...
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css' -OutFile 'app\static\vendor\bootstrap\css\bootstrap.min.css'"
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/js/bootstrap.bundle.min.js' -OutFile 'app\static\vendor\bootstrap\js\bootstrap.bundle.min.js'"

echo 正在下载Bootstrap Icons资源...
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.bootcdn.net/ajax/libs/bootstrap-icons/1.8.0/font/bootstrap-icons.css' -OutFile 'app\static\vendor\bootstrap-icons\bootstrap-icons.css'"

echo 请手动下载Bootstrap Icons字体文件: https://github.com/twbs/icons/releases/tag/v1.8.0
echo 并将fonts目录复制到 app\static\vendor\bootstrap-icons\ 下

echo 正在下载Font Awesome资源...
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/css/fontawesome.min.css' -OutFile 'app\static\vendor\font-awesome\css\fontawesome.min.css'"
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/css/solid.min.css' -OutFile 'app\static\vendor\font-awesome\css\solid.min.css'"

echo 请手动下载Font Awesome字体文件: https://fontawesome.com/download
echo 并将webfonts目录复制到 app\static\vendor\font-awesome\ 下

echo 正在下载Animate.css资源...
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.bootcdn.net/ajax/libs/animate.css/4.1.1/animate.min.css' -OutFile 'app\static\vendor\animate.css\animate.min.css'"

echo 正在下载particles.js资源...
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.bootcdn.net/ajax/libs/particles.js/2.0.0/particles.min.js' -OutFile 'app\static\vendor\particles.js\particles.min.js'"

echo 所有资源下载完成！
echo 请确保Bootstrap Icons和Font Awesome的字体文件已正确放置
echo 然后修改app\templates\base.html文件，将CDN引用修改为本地资源引用

pause 