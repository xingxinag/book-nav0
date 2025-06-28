/**
 * 移动端Tooltip处理
 * 解决移动端点击链接后返回时tooltip仍然显示的问题
 */
document.addEventListener("DOMContentLoaded", function () {
  // 检测是否为移动设备
  const isMobile =
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    );

  if (!isMobile) {
    return; // 只在移动端处理
  }

  // 隐藏所有tooltip的函数
  function hideAllTooltips() {
    // 查找所有显示的tooltip元素
    const tooltips = document.querySelectorAll(".tooltip.show");
    tooltips.forEach((tooltip) => {
      tooltip.classList.remove("show");
    });

    // 如果使用Bootstrap tooltip，也隐藏它们
    if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
      const tooltipElements = document.querySelectorAll(
        '[data-bs-toggle="tooltip"]'
      );
      tooltipElements.forEach((element) => {
        const tooltipInstance = bootstrap.Tooltip.getInstance(element);
        if (tooltipInstance) {
          tooltipInstance.hide();
        }
      });
    }
  }

  // 监听页面可见性变化（用户从其他页面返回时）
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) {
      hideAllTooltips();
    }
  });

  // 监听页面焦点变化
  window.addEventListener("focus", function () {
    hideAllTooltips();
  });

  // 监听页面显示事件（从缓存恢复时）
  window.addEventListener("pageshow", function (event) {
    // 如果页面是从缓存恢复的，隐藏所有tooltip
    if (event.persisted) {
      hideAllTooltips();
    }
  });

  // 监听网站卡片点击事件
  const siteCards = document.querySelectorAll(
    '.site-card[data-bs-toggle="tooltip"]'
  );
  siteCards.forEach((card) => {
    card.addEventListener("click", function () {
      // 点击时立即隐藏tooltip
      hideAllTooltips();
    });
  });

  // 监听触摸开始事件，在移动端触摸时隐藏其他tooltip
  document.addEventListener("touchstart", function () {
    hideAllTooltips();
  });

  // 页面加载完成后也隐藏一次，确保没有残留的tooltip
  setTimeout(hideAllTooltips, 100);
});
