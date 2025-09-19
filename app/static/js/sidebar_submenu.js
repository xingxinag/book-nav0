// 侧边栏子菜单交互
// 只在点击下拉箭头时展开/收起子菜单，点击文字正常跳转

document.addEventListener("DOMContentLoaded", function () {
  // 获取所有带有子菜单的菜单项
  const menuItemsWithSubmenu = document.querySelectorAll(
    ".sidebar-menu-item.has-submenu"
  );

  // 从预渲染状态恢复子菜单状态
  const submenuStates = document.documentElement.getAttribute(
    "data-submenu-states"
  );
  if (submenuStates) {
    try {
      const states = JSON.parse(submenuStates);
      menuItemsWithSubmenu.forEach((menuItem) => {
        const categoryId = menuItem
          .querySelector(".sidebar-menu-link")
          .getAttribute("href")
          .substring(1);
        const key = `submenu_${categoryId}`;
        if (states[key] === "true") {
          menuItem.classList.add("active");
        }
      });
    } catch (e) {
      console.error("Failed to parse submenu states:", e);
    }
  }

  // 记录点击的子分类ID和侧边栏滚动位置
  document.querySelectorAll(".sidebar-submenu-link").forEach((link) => {
    link.addEventListener("click", function () {
      const href = this.getAttribute("href");
      if (href) {
        localStorage.setItem("last_visited_subcategory", href);
        // 记录滚动位置
        const sidebarContent = document.querySelector(".sidebar-content");
        if (sidebarContent) {
          localStorage.setItem("sidebar_scroll_top", sidebarContent.scrollTop);
        }
      }
    });
  });

  // 恢复侧边栏滚动位置
  function restoreSidebarScroll() {
    if (document.documentElement.getAttribute("data-page-type") === "index") {
      const scrollTop = localStorage.getItem("sidebar_scroll_top");
      if (scrollTop !== null) {
        const sidebarContent = document.querySelector(".sidebar-content");
        if (sidebarContent) {
          sidebarContent.scrollTop = parseInt(scrollTop, 10);
        }
        localStorage.removeItem("sidebar_scroll_top");
      }
    }
  }

  restoreSidebarScroll();
  window.addEventListener("pageshow", restoreSidebarScroll);

  menuItemsWithSubmenu.forEach((menuItem) => {
    const menuLink = menuItem.querySelector(".sidebar-menu-link");
    const submenuToggle = menuItem.querySelector(".submenu-toggle");

    // 只给下拉箭头绑定展开/收起事件
    if (submenuToggle) {
      submenuToggle.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        menuItem.classList.toggle("active");

        // 保存子菜单状态到localStorage
        const categoryId = menuLink.getAttribute("href").substring(1);
        localStorage.setItem(
          `submenu_${categoryId}`,
          menuItem.classList.contains("active")
        );
      });
    }
    // 点击父分类文字正常跳转，无需特殊处理
  });
});
