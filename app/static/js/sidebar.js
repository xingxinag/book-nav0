document.addEventListener("DOMContentLoaded", function () {
  // 获取DOM元素
  const menuToggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebarOverlay");
  const bodyElement = document.body;

  // 默认显示侧边栏（桌面设备）
  if (window.innerWidth >= 768) {
    bodyElement.classList.add("sidebar-active");
  }

  // 菜单切换功能
  menuToggle.addEventListener("click", function () {
    bodyElement.classList.toggle("sidebar-active");
  });

  // 点击遮罩层关闭侧边栏
  sidebarOverlay.addEventListener("click", function () {
    bodyElement.classList.remove("sidebar-active");
  });

  // 点击链接平滑滚动并关闭侧边栏
  document.querySelectorAll(".sidebar-menu-link").forEach((link) => {
    link.addEventListener("click", function (e) {
      const href = this.getAttribute("href");

      if (href.startsWith("#")) {
        e.preventDefault();
        const targetElement = document.getElementById(href.substring(1));

        if (targetElement) {
          window.scrollTo({
            top: targetElement.offsetTop - 80,
            behavior: "smooth",
          });

          // 在移动设备上关闭侧边栏
          if (window.innerWidth < 768) {
            bodyElement.classList.remove("sidebar-active");
          }

          // 如果在搜索结果页面，先清除搜索
          const searchResults = document.getElementById("searchResults");
          if (searchResults.style.display !== "none") {
            window.dispatchEvent(new Event("clearSearch"));
          }
        }
      }
    });
  });

  // 监听窗口大小变化
  window.addEventListener("resize", function () {
    const isMobile = window.innerWidth < 768;

    if (isMobile) {
      // 移动设备上默认隐藏侧边栏
      bodyElement.classList.remove("sidebar-active");
    } else {
      // 桌面设备上默认显示侧边栏
      bodyElement.classList.add("sidebar-active");
    }
  });
});
