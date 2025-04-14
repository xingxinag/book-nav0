/**
 * 回到顶部功能
 * 滚动超过一定距离显示按钮，点击平滑滚动到顶部
 */
document.addEventListener("DOMContentLoaded", function () {
  // 创建回到顶部按钮元素
  const backToTopButton = document.createElement("button");
  backToTopButton.className = "back-to-top";
  backToTopButton.setAttribute("aria-label", "回到顶部");
  backToTopButton.setAttribute("title", "回到顶部");
  backToTopButton.innerHTML = '<i class="bi bi-arrow-up"></i>';

  // 添加到页面
  document.body.appendChild(backToTopButton);

  // 滚动显示阈值（像素）
  const scrollThreshold = 300;

  // 节流函数 - 限制滚动事件触发频率
  let isScrolling = false;

  // 监听滚动事件
  window.addEventListener("scroll", function () {
    if (!isScrolling) {
      isScrolling = true;

      // 使用requestAnimationFrame优化性能
      requestAnimationFrame(function () {
        if (window.pageYOffset > scrollThreshold) {
          backToTopButton.classList.add("visible");
        } else {
          backToTopButton.classList.remove("visible");
        }
        isScrolling = false;
      });
    }
  });

  // 点击事件
  backToTopButton.addEventListener("click", function (e) {
    e.preventDefault();

    // 添加点击动画效果
    backToTopButton.classList.add("clicked");

    // 平滑滚动到顶部
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });

    // 移除点击效果
    setTimeout(function () {
      backToTopButton.classList.remove("clicked");
    }, 300);
  });

  // 初始检查滚动位置
  if (window.pageYOffset > scrollThreshold) {
    backToTopButton.classList.add("visible");
  }
});
