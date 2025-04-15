# CDN 资源本地化指南

## 介绍

本目录用于存储本地化的第三方库资源，替代 CDN 服务，以提高网站加载速度和稳定性。

## 资源清单

以下是需要本地化的 CDN 资源：

1. **Bootstrap 5.1.3**

   - CSS: `app/static/vendor/bootstrap/css/bootstrap.min.css`
   - JS: `app/static/vendor/bootstrap/js/bootstrap.bundle.min.js`
   - 下载地址: https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css
   - 下载地址: https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/js/bootstrap.bundle.min.js

2. **Bootstrap Icons 1.8.0**

   - CSS: `app/static/vendor/bootstrap-icons/bootstrap-icons.css`
   - Fonts: `app/static/vendor/bootstrap-icons/fonts/` (所有字体文件)
   - 下载地址: https://cdn.bootcdn.net/ajax/libs/bootstrap-icons/1.8.0/font/bootstrap-icons.css
   - 字体文件还需要单独下载完整的库: https://github.com/twbs/icons/releases/tag/v1.8.0

3. **Font Awesome 5.15.4**

   - CSS: `app/static/vendor/font-awesome/css/fontawesome.min.css`
   - CSS: `app/static/vendor/font-awesome/css/solid.min.css`
   - Fonts: `app/static/vendor/font-awesome/webfonts/` (所有字体文件)
   - 下载地址: https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/css/fontawesome.min.css
   - 下载地址: https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/css/solid.min.css
   - 字体文件需要从完整包中获取: https://fontawesome.com/download (免费版)

4. **Animate.css 4.1.1**

   - CSS: `app/static/vendor/animate.css/animate.min.css`
   - 下载地址: https://cdn.bootcdn.net/ajax/libs/animate.css/4.1.1/animate.min.css

5. **particles.js 2.0.0**
   - JS: `app/static/vendor/particles.js/particles.min.js`
   - 下载地址: https://cdn.bootcdn.net/ajax/libs/particles.js/2.0.0/particles.min.js

## 实施步骤

1. 下载所有以上文件到各自目录
2. 修改`app/templates/base.html`中的引用路径
3. 确认所有前端功能正常工作
4. 测试网站加载速度，与使用 CDN 的版本进行对比

## CSS 路径修复

对于 CSS 文件中引用的相对路径资源（如字体文件），需要确保路径正确。例如，Bootstrap Icons 和 Font Awesome 的 CSS 文件中会引用字体文件，应当确保这些路径指向正确的本地文件。

## 完整模板示例

```html
<!-- 替换前 -->
<link
  rel="stylesheet"
  href="https://cdn.bootcdn.net/ajax/libs/bootstrap-icons/1.8.0/font/bootstrap-icons.css"
/>

<!-- 替换后 -->
<link
  rel="stylesheet"
  href="{{ url_for('static', filename='vendor/bootstrap-icons/bootstrap-icons.css') }}"
/>
```

## 资源大小参考

资源总大小约为 1.4MB，具体如下：

- Bootstrap CSS+JS: 约 240KB
- Bootstrap Icons: 约 180KB (含字体文件)
- Font Awesome: 约 500KB (含字体文件)
- Animate.css: 约 75KB
- particles.js: 约 50KB
