// 将 currentCard 变量声明为全局变量
window.currentCard = null;

document.addEventListener("DOMContentLoaded", function () {
  const contextMenu = document.getElementById("contextMenu");
  const editLinkBtn = document.getElementById("editLink");
  const visitLinkBtn = document.getElementById("visitLink");
  const addLinkBtn = document.getElementById("addLink");
  const shareSiteBtn = document.getElementById("shareSite");
  const deleteLinkBtn = document.getElementById("deleteLink");

  // 添加卡片右键菜单功能
  document.addEventListener("contextmenu", function (e) {
    // 检查是否是卡片元素
    if (e.target.closest(".site-card")) {
      e.preventDefault();

      // 保存当前操作的卡片
      window.currentCard = e.target.closest(".site-card");

      // 显示自定义右键菜单
      contextMenu.style.display = "block";
      contextMenu.style.left = e.pageX + "px";
      contextMenu.style.top = e.pageY + "px";
    }
  });

  // 点击页面任意位置关闭右键菜单
  document.addEventListener("click", function () {
    contextMenu.style.display = "none";
  });

  // 访问链接按钮点击事件
  visitLinkBtn.addEventListener("click", function () {
    if (window.currentCard) {
      // 先隐藏上下文菜单
      contextMenu.style.display = "none";
      // 在新标签页中打开链接
      window.open(window.currentCard.href, "_blank");
    }
  });

  // 添加链接按钮点击事件
  if (addLinkBtn) {
    addLinkBtn.addEventListener("click", function () {
      // 隐藏上下文菜单
      contextMenu.style.display = "none";
      // 跳转到添加网站页面
      window.location.href = "/admin/website/add";
    });
  }

  // 分享按钮点击事件
  if (shareSiteBtn) {
    shareSiteBtn.addEventListener("click", function () {
      if (window.currentCard) {
        // 隐藏上下文菜单
        contextMenu.style.display = "none";

        const cardId = window.currentCard.href.split("/").pop();
        const cardTitle =
          window.currentCard.querySelector(".site-title").textContent;

        // 获取原始网站URL
        const getOriginalUrl = async (cardId) => {
          try {
            // 获取网站原始URL
            const response = await fetch(`/site/${cardId}/info`);
            const data = await response.json();

            if (data.success && data.website && data.website.url) {
              return {
                url: data.website.url, // 直接使用原始URL
                title: data.website.title || cardTitle,
              };
            }
            throw new Error("无法获取原始URL");
          } catch (error) {
            console.error("获取原始URL失败:", error);
            // 返回fallback URL (原来的格式)
            return {
              url: `${window.location.origin}/site/${cardId}`,
              title: cardTitle,
            };
          }
        };

        // 异步获取URL并复制
        (async () => {
          const copyData = await getOriginalUrl(cardId);

          // 复制链接到剪贴板
          const textArea = document.createElement("textarea");
          textArea.value = copyData.url;
          document.body.appendChild(textArea);
          textArea.select();
          document.execCommand("copy");
          document.body.removeChild(textArea);

          // 显示优雅的复制成功提示
          showCopyToast(`"${copyData.title}" 链接已复制`);
        })();
      }
    });
  }

  // 显示复制成功的提示
  function showCopyToast(message, type = "success") {
    // 检查是否已存在提示，如果有则移除
    const existingToast = document.querySelector(".copy-toast");
    if (existingToast) {
      document.body.removeChild(existingToast);
    }

    // 根据类型确定图标和颜色
    let icon, backgroundColor, borderColor;
    switch (type) {
      case "error":
        icon = "bi-exclamation-circle-fill";
        backgroundColor = "linear-gradient(145deg, #f44336, #e53935)";
        borderColor = "#c62828";
        break;
      case "warning":
        icon = "bi-exclamation-triangle-fill";
        backgroundColor = "linear-gradient(145deg, #ff9800, #f57c00)";
        borderColor = "#e65100";
        break;
      case "info":
        icon = "bi-info-circle-fill";
        backgroundColor = "linear-gradient(145deg, #2196f3, #1e88e5)";
        borderColor = "#0d47a1";
        break;
      case "success":
      default:
        icon = "bi-check-circle-fill";
        backgroundColor =
          "var(--primary-gradient, linear-gradient(135deg, #7049f0, #aa26ff))";
        borderColor = "rgba(112, 73, 240, 0.7)";
        break;
    }

    // 创建新的提示元素
    const toast = document.createElement("div");
    toast.className = "copy-toast";
    toast.style.background = backgroundColor;
    toast.style.borderLeft = `4px solid ${borderColor}`;
    toast.innerHTML = `
      <i class="bi ${icon}"></i>
      <span>${message}</span>
    `;

    // 添加到页面
    document.body.appendChild(toast);

    // 延迟一小段时间后显示，以便有渐入效果
    setTimeout(() => {
      toast.classList.add("show");
    }, 10);

    // 2.5秒后自动消失
    setTimeout(() => {
      toast.classList.remove("show");

      // 动画结束后从DOM中移除
      setTimeout(() => {
        if (toast.parentNode) {
          document.body.removeChild(toast);
        }
      }, 300); // 等待过渡动画完成
    }, 2500);
  }

  // 删除链接按钮点击事件
  if (deleteLinkBtn) {
    deleteLinkBtn.addEventListener("click", function () {
      if (window.currentCard) {
        // 隐藏上下文菜单
        contextMenu.style.display = "none";

        const cardId = window.currentCard.href.split("/").pop();
        const cardTitle =
          window.currentCard.querySelector(".site-title").textContent;

        // 弹出确认对话框
        if (confirm(`确定要删除"${cardTitle}"吗？此操作不可恢复。`)) {
          // 添加删除中状态
          window.currentCard.classList.add("deleting");

          // 半透明效果
          window.currentCard.style.opacity = "0.7";
          window.currentCard.style.pointerEvents = "none";

          // 发送删除请求
          fetch(`/api/website/${cardId}/delete`, {
            method: "DELETE",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
                .content,
            },
          })
            .then((response) => response.json())
            .then((data) => {
              // 移除删除中状态
              window.currentCard.classList.remove("deleting");

              if (data.success) {
                // 替换alert为showCopyToast
                showCopyToast(data.message);

                // 添加卡片淡出动画
                window.currentCard.style.transition =
                  "opacity 0.3s ease, transform 0.3s ease";
                window.currentCard.style.opacity = "0";
                window.currentCard.style.transform = "scale(0.95)";

                // 动画结束后从DOM中移除卡片
                setTimeout(() => {
                  window.currentCard.remove();
                  window.currentCard = null;
                }, 300);
              } else {
                // 恢复卡片状态
                window.currentCard.style.opacity = "1";
                window.currentCard.style.pointerEvents = "auto";

                // 保留alert用于错误提示，因为错误需要用户确认
                alert("删除失败: " + (data.message || "未知错误"));
              }
            })
            .catch((error) => {
              // 移除删除中状态
              window.currentCard.classList.remove("deleting");

              // 恢复卡片状态
              window.currentCard.style.opacity = "1";
              window.currentCard.style.pointerEvents = "auto";

              console.error("删除链接出错:", error);
              alert("删除链接时发生错误，请重试");
            });
        }
      }
    });
  }
});
