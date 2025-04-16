# 第一阶段：构建依赖
FROM python:3.9-alpine AS builder

# 设置工作目录
WORKDIR /app

# 切换Alpine镜像源为国内源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories

# 安装构建依赖
RUN apk add --no-cache gcc musl-dev libffi-dev

# 配置pip使用国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制依赖文件，安装到轮子目录
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels gunicorn

# 第二阶段：运行环境
FROM python:3.9-alpine

# 设置工作目录
WORKDIR /app

# 切换Alpine镜像源为国内源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories

# 安装运行时依赖
RUN apk add --no-cache nginx supervisor libffi && \
    mkdir -p /run/nginx

# 设置Python环境
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 从构建阶段复制wheel并安装
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# 配置Nginx
COPY docker/nginx.conf /etc/nginx/http.d/default.conf

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/app/data /app/app/backups /app/app/uploads /data

# 配置Supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 添加启动脚本并设置执行权限
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 设置持久化卷
VOLUME ["/data", "/app/app/backups", "/app/app/uploads", "/etc/nginx/http.d"]

# 暴露端口
EXPOSE 80

# 使用启动脚本作为容器入口点
ENTRYPOINT ["/entrypoint.sh"] 