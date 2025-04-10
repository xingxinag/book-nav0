# 炫酷导航站

一个为小团体设计的炫酷导航站，支持管理员登录和邀请码注册。

## 功能特点

- 美观炫酷的用户界面，包含粒子动画等特效
- 分类管理网站链接
- 用户注册需要邀请码
- 管理员可以生成邀请码
- 管理员可以管理分类和网站
- 响应式设计，适配各种设备

## 安装步骤

1. 克隆代码库

   ```
   git clone <repository-url>
   cd nav
   ```

2. 创建虚拟环境并激活

   ```
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. 安装依赖

   ```
   pip install -r requirements.txt
   ```

4. 初始化数据库

   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. 运行应用

   ```
   python run.py
   ```

6. 访问应用
   浏览器打开 http://127.0.0.1:5000

## 默认管理员账户

- 用户名: admin
- 密码: admin123

_首次登录后请立即修改默认密码_

## 配置

可以通过创建`.env`文件或设置环境变量来配置应用：

```
SECRET_KEY=your-secret-key
ADMIN_USERNAME=your-admin-username
ADMIN_EMAIL=your-admin-email
ADMIN_PASSWORD=your-admin-password
```

## 技术栈

- 后端: Python + Flask
- 数据库: SQLite (可扩展到其他数据库)
- 前端: Bootstrap 5 + Particles.js + Animate.css

## 许可证

MIT
