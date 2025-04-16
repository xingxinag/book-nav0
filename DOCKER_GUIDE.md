# Docker 部署指南

## 1. 准备工作

确保您的服务器已安装 Docker 和 Docker Compose:

```bash
# 检查Docker是否安装
docker --version

# 检查Docker Compose是否安装
docker-compose --version
```

## 2. 项目结构

项目已为 Docker 部署做好准备，目录结构如下:

```
.
├── Dockerfile           # 容器构建配置
├── docker-compose.yml   # 容器编排配置
├── docker/              # Docker相关配置文件
│   ├── nginx.conf       # Nginx配置
│   └── supervisord.conf # Supervisor配置
├── config/              # 外部配置目录
│   └── nginx/           # Nginx配置（可修改）
├── data/                # 数据持久化目录
│   ├── backups/         # 数据库备份
│   └── uploads/         # 上传文件
└── app/                 # 应用程序代码
```

## 3. 启动服务

在项目根目录下运行:

```bash
# 首次构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 4. 持久化存储

本配置使用了以下卷挂载，确保数据持久性:

- `./data/app.db:/app/app.db` - 数据库文件
- `./data/backups:/app/app/backups` - 备份文件
- `./data/uploads:/app/app/uploads` - 上传的文件
- `./config/nginx:/etc/nginx/http.d` - Nginx 配置文件

## 5. 自定义配置

### 修改 Nginx 配置

编辑 `config/nginx/default.conf` 文件，然后重启容器:

```bash
# 编辑配置后重启Nginx
docker-compose exec nav nginx -s reload
```

### 修改环境变量

编辑 `docker-compose.yml` 文件中的 `environment` 部分:

```yaml
environment:
  - SECRET_KEY=your_secure_key_here
  - FLASK_ENV=production
  # 添加其他环境变量
```

## 6. 备份和恢复

### 备份数据

```bash
# 手动备份数据库
cp data/app.db data/backups/app_backup_$(date +%Y%m%d_%H%M%S).db
```

### 恢复数据

```bash
# 停止服务
docker-compose down

# 恢复数据库
cp data/backups/your_backup_file.db data/app.db

# 重启服务
docker-compose up -d
```

## 7. 故障排除

- **容器无法启动**: 检查 `docker-compose logs -f` 的输出
- **Nginx 错误**: 检查 `config/nginx/default.conf` 配置是否正确
- **应用错误**: 检查环境变量是否设置正确

祝您使用愉快！
