// CSRF令牌处理脚本
(function () {
  "use strict";

  // 获取CSRF令牌
  function getCSRFToken() {
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    return tokenMeta ? tokenMeta.getAttribute("content") : "";
  }

  // 更新CSRF令牌
  function updateCSRFToken(newToken) {
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    if (tokenMeta) {
      tokenMeta.setAttribute("content", newToken);
    }
  }

  // 刷新CSRF令牌
  function refreshCSRFToken() {
    return fetch("/auth/refresh-csrf", {
      method: "GET",
      credentials: "same-origin",
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        }
        throw new Error("刷新CSRF令牌失败");
      })
      .then((data) => {
        if (data.success && data.csrf_token) {
          updateCSRFToken(data.csrf_token);
          console.log("CSRF令牌已刷新");
          return data.csrf_token;
        }
        throw new Error("无效的CSRF令牌响应");
      });
  }

  // 处理CSRF错误
  function handleCSRFError() {
    console.warn("检测到CSRF令牌可能过期，正在尝试刷新...");
    return refreshCSRFToken()
      .then(() => {
        // 令牌刷新成功，可以重试之前的请求
        return true;
      })
      .catch((error) => {
        console.error("CSRF令牌刷新失败:", error);
        // 如果刷新失败，建议用户刷新页面
        if (confirm("会话可能已过期，是否刷新页面？")) {
          window.location.reload();
        }
        return false;
      });
  }

  // 增强fetch函数，自动处理CSRF错误
  const originalFetch = window.fetch;
  window.fetch = function (url, options = {}) {
    // 如果是POST/PUT/DELETE请求且需要CSRF令牌
    if (["POST", "PUT", "DELETE", "PATCH"].includes(options.method)) {
      const token = getCSRFToken();
      if (token) {
        options.headers = options.headers || {};
        options.headers["X-CSRFToken"] = token;
      }
    }

    return originalFetch(url, options)
      .then((response) => {
        // 检查是否是CSRF错误
        if (response.status === 400) {
          return response.text().then((text) => {
            if (text.includes("CSRF") || text.includes("csrf")) {
              throw new Error("CSRF_TOKEN_ERROR");
            }
            // 如果不是CSRF错误，返回原始响应
            return new Response(text, {
              status: response.status,
              statusText: response.statusText,
              headers: response.headers,
            });
          });
        }
        return response;
      })
      .catch((error) => {
        if (error.message === "CSRF_TOKEN_ERROR") {
          return handleCSRFError().then((refreshed) => {
            if (refreshed) {
              // 重试原始请求
              const newToken = getCSRFToken();
              if (newToken && options.headers) {
                options.headers["X-CSRFToken"] = newToken;
              }
              return originalFetch(url, options);
            }
            throw error;
          });
        }
        throw error;
      });
  };

  // 定期检查CSRF令牌有效性（每小时检查一次）
  setInterval(() => {
    const token = getCSRFToken();
    if (token) {
      // 发送一个简单的请求来验证令牌是否有效
      fetch("/auth/check-csrf", {
        method: "GET",
        credentials: "same-origin",
      }).catch(() => {
        // 如果检查失败，尝试刷新令牌
        refreshCSRFToken().catch(() => {
          console.warn("CSRF令牌检查失败，可能需要刷新页面");
        });
      });
    }
  }, 60 * 60 * 1000); // 每小时检查一次

  // 页面可见性变化时检查令牌
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      // 页面重新变为可见时，检查令牌
      const token = getCSRFToken();
      if (token) {
        refreshCSRFToken().catch(() => {
          console.warn("页面重新可见时CSRF令牌刷新失败");
        });
      }
    }
  });

  // 导出函数供其他脚本使用
  window.CSRFHandler = {
    getToken: getCSRFToken,
    refreshToken: refreshCSRFToken,
    updateToken: updateCSRFToken,
  };
})();
