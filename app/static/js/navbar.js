document.addEventListener("DOMContentLoaded", function () {
  // 移动端设备检测
  const isMobile = window.matchMedia("(max-width: 768px)").matches;

  // 处理用户下拉菜单在移动设备上的点击事件
  if (isMobile) {
    const userDropdownToggle = document.querySelector(".user-dropdown-toggle");
    const userDropdownMenu = document.querySelector(".user-dropdown-menu");

    if (userDropdownToggle && userDropdownMenu) {
      userDropdownToggle.addEventListener("click", function (e) {
        e.preventDefault();
        userDropdownMenu.classList.toggle("show");

        // 点击其他区域关闭菜单
        document.addEventListener("click", function closeMenu(event) {
          if (
            !userDropdownToggle.contains(event.target) &&
            !userDropdownMenu.contains(event.target)
          ) {
            userDropdownMenu.classList.remove("show");
            document.removeEventListener("click", closeMenu);
          }
        });
      });
    }
  }

  // 为菜单切换按钮添加点击涟漪效果
  const menuButtons = document.querySelectorAll(".menu-toggle, .navbar-action");

  menuButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      const ripple = document.createElement("span");
      ripple.classList.add("ripple-effect");

      this.appendChild(ripple);

      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);

      ripple.style.width = ripple.style.height = `${size}px`;
      ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
      ripple.style.top = `${e.clientY - rect.top - size / 2}px`;

      ripple.classList.add("active");

      setTimeout(() => {
        ripple.remove();
      }, 600);
    });
  });
});
