// 侧边栏子菜单交互
document.addEventListener("DOMContentLoaded", function () {
  // 获取所有带有子菜单的菜单项
  const menuItemsWithSubmenu = document.querySelectorAll(
    ".sidebar-menu-item.has-submenu"
  );

  // 为每个菜单项添加点击事件
  menuItemsWithSubmenu.forEach((menuItem) => {
    const menuLink = menuItem.querySelector(".sidebar-menu-link");

    menuLink.addEventListener("click", function (e) {
      // 阻止默认行为，防止链接跳转
      e.preventDefault();

      // 切换当前菜单项的active类
      menuItem.classList.toggle("active");

      // 获取子菜单链接
      const submenuLinks = menuItem.querySelectorAll(".sidebar-submenu-link");

      // 为子菜单链接添加点击事件
      submenuLinks.forEach((link) => {
        link.addEventListener("click", function (e) {
          // 不阻止默认行为，允许链接跳转
          // 但是关闭侧边栏
          document.body.classList.remove("sidebar-active");
        });
      });
    });
  });
});
