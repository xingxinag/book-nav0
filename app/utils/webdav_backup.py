"""
WebDAV备份工具模块
支持HTTP和HTTPS协议的WebDAV备份功能
"""

import os
import requests
from urllib.parse import urljoin, urlparse
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime
from flask import current_app


class WebDAVBackup:
    """WebDAV备份客户端"""

    def __init__(self, url, username, password, remote_path='/backups/'):
        """
        初始化WebDAV客户端

        Args:
            url: WebDAV服务器地址 (支持HTTP和HTTPS)
            username: 用户名
            password: 密码
            remote_path: 远程备份路径
        """
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.remote_path = remote_path.strip('/')
        if self.remote_path and not self.remote_path.endswith('/'):
            self.remote_path += '/'

        # 配置请求会话
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)

        # 支持HTTP和HTTPS
        parsed_url = urlparse(self.url)
        if parsed_url.scheme not in ['http', 'https']:
            raise ValueError("WebDAV URL must use HTTP or HTTPS protocol")

        # 对于HTTPS，可以选择性验证SSL证书
        if parsed_url.scheme == 'https':
            # 在生产环境中应该验证证书，这里为了兼容性设为False
            # 可以根据需要添加配置选项
            self.session.verify = True

    def test_connection(self):
        """
        测试WebDAV连接

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # 尝试访问根目录
            response = self.session.request('PROPFIND', self.url, timeout=10)

            if response.status_code in [200, 207, 301, 302]:
                return True, "连接成功"
            elif response.status_code == 401:
                return False, "认证失败：用户名或密码错误"
            elif response.status_code == 403:
                return False, "访问被拒绝：权限不足"
            elif response.status_code == 404:
                return False, "WebDAV服务器不存在或路径错误"
            else:
                return False, f"连接失败：HTTP {response.status_code}"

        except requests.exceptions.SSLError as e:
            return False, f"SSL证书错误：{str(e)}"
        except requests.exceptions.ConnectionError as e:
            return False, f"连接错误：无法连接到服务器"
        except requests.exceptions.Timeout as e:
            return False, "连接超时"
        except Exception as e:
            return False, f"未知错误：{str(e)}"

    def create_directory(self, path):
        """
        创建远程目录

        Args:
            path: 目录路径

        Returns:
            bool: 是否成功
        """
        try:
            full_url = urljoin(self.url + '/', path.lstrip('/'))
            response = self.session.request('MKCOL', full_url, timeout=30)

            # 201: 创建成功, 405: 目录已存在
            return response.status_code in [201, 405]
        except Exception as e:
            current_app.logger.error(f"创建WebDAV目录失败: {str(e)}")
            return False

    def upload_file(self, local_path, remote_filename):
        """
        上传文件到WebDAV服务器

        Args:
            local_path: 本地文件路径
            remote_filename: 远程文件名

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not os.path.exists(local_path):
                return False, f"本地文件不存在: {local_path}"

            # 确保远程目录存在
            if self.remote_path:
                self.create_directory(self.remote_path)

            # 构建完整的远程文件URL
            if self.remote_path:
                remote_file_path = f"{self.remote_path}{remote_filename}"
            else:
                remote_file_path = remote_filename

            full_url = urljoin(self.url + '/', remote_file_path)

            # 上传文件
            with open(local_path, 'rb') as f:
                response = self.session.put(full_url, data=f, timeout=300)

            if response.status_code in [200, 201, 204]:
                file_size = os.path.getsize(local_path)
                return True, f"上传成功 ({self._format_size(file_size)})"
            else:
                return False, f"上传失败: HTTP {response.status_code}"

        except Exception as e:
            current_app.logger.error(f"WebDAV上传失败: {str(e)}")
            return False, f"上传失败: {str(e)}"

    def list_files(self):
        """
        列出远程备份目录的文件

        Returns:
            tuple: (success: bool, files: list or error_message: str)
        """
        try:
            if self.remote_path:
                list_url = urljoin(self.url + '/', self.remote_path)
            else:
                list_url = self.url

            response = self.session.request('PROPFIND', list_url, timeout=30)

            if response.status_code in [200, 207]:
                # 简单解析响应（实际实现可能需要更复杂的XML解析）
                files = []
                # 这里可以解析WebDAV的XML响应来获取文件列表
                # 为了简化，返回成功状态
                return True, files
            else:
                return False, f"列表获取失败: HTTP {response.status_code}"

        except Exception as e:
            current_app.logger.error(f"WebDAV文件列表获取失败: {str(e)}")
            return False, f"获取文件列表失败: {str(e)}"

    def delete_file(self, remote_filename):
        """
        删除远程文件

        Args:
            remote_filename: 远程文件名

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if self.remote_path:
                remote_file_path = f"{self.remote_path}{remote_filename}"
            else:
                remote_file_path = remote_filename

            full_url = urljoin(self.url + '/', remote_file_path)
            response = self.session.delete(full_url, timeout=30)

            if response.status_code in [200, 204, 404]:
                return True, "删除成功"
            else:
                return False, f"删除失败: HTTP {response.status_code}"

        except Exception as e:
            current_app.logger.error(f"WebDAV删除失败: {str(e)}")
            return False, f"删除失败: {str(e)}"

    @staticmethod
    def _format_size(size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f}KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f}MB"
        else:
            return f"{size_bytes/(1024**3):.1f}GB"


def encrypt_password(password):
    """编码密码用于数据库存储（简单Base64编码）"""
    if not password:
        return None
    return base64.b64encode(password.encode('utf-8')).decode('utf-8')


def decrypt_password(encoded_password):
    """解码密码"""
    if not encoded_password:
        return None
    try:
        return base64.b64decode(encoded_password.encode('utf-8')).decode('utf-8')
    except Exception:
        return None


def create_webdav_client(settings):
    """
    根据设置创建WebDAV客户端

    Args:
        settings: SiteSettings对象

    Returns:
        WebDAVBackup: WebDAV客户端实例，如果配置无效则返回None
    """
    if not settings.webdav_enabled or not all([
        settings.webdav_url,
        settings.webdav_username,
        settings.webdav_password
    ]):
        return None

    try:
        # 解码密码
        decoded_password = decrypt_password(settings.webdav_password)
        if not decoded_password:
            return None

        return WebDAVBackup(
            url=settings.webdav_url,
            username=settings.webdav_username,
            password=decoded_password,
            remote_path=settings.webdav_path or '/backups/'
        )
    except Exception as e:
        current_app.logger.error(f"创建WebDAV客户端失败: {str(e)}")
        return None


def backup_to_webdav(backup_file_path, settings):
    """
    执行WebDAV备份

    Args:
        backup_file_path: 本地备份文件路径
        settings: SiteSettings对象

    Returns:
        tuple: (success: bool, message: str)
    """
    webdav_client = create_webdav_client(settings)
    if not webdav_client:
        return False, "WebDAV未配置或配置无效"

    if not os.path.exists(backup_file_path):
        return False, f"备份文件不存在: {backup_file_path}"

    # 生成远程文件名
    filename = os.path.basename(backup_file_path)

    # 上传文件
    success, message = webdav_client.upload_file(backup_file_path, filename)

    if success:
        current_app.logger.info(f"WebDAV备份成功: {filename}")
    else:
        current_app.logger.error(f"WebDAV备份失败: {message}")

    return success, message