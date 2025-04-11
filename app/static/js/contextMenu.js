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

        // 创建分享链接
        const shareUrl = `${window.location.origin}/site/${cardId}`;

        // 如果支持原生分享API
        if (navigator.share) {
          navigator
            .share({
              title: cardTitle,
              url: shareUrl,
            })
            .catch((error) => console.error("分享失败:", error));
        } else {
          // 否则复制链接到剪贴板
          const textArea = document.createElement("textarea");
          textArea.value = shareUrl;
          document.body.appendChild(textArea);
          textArea.select();
          document.execCommand("copy");
          document.body.removeChild(textArea);

          alert("链接已复制到剪贴板");
        }
      }
    });
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
              if (data.success) {
                alert(data.message);

                // 从DOM中移除已删除的卡片
                window.currentCard.remove();
                window.currentCard = null;
              } else {
                alert("删除失败: " + (data.message || "未知错误"));
              }
            })
            .catch((error) => {
              console.error("删除链接出错:", error);
              alert("删除链接时发生错误，请重试");
            });
        }
      }
    });
  }
});
