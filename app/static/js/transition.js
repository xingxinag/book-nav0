/**
 * 过渡页链接处理
 * 拦截所有外部链接点击事件，通过过渡页进行跳转
 */
document.addEventListener("DOMContentLoaded", function () {
  // 检查是否启用了过渡页
  if (!window.settings || !window.settings.enable_transition) {
    return;
  }

  // 检查是否已经选择了不再显示
  if (
    window.settings.transition_remember_choice &&
    localStorage.getItem("disableRedirect") === "true"
  ) {
    // 如果选择了不再显示，将所有外部链接直接跳转
    var links = document.querySelectorAll("a");
    links.forEach(function (link) {
      if (!link.href) return;

      // 检查是否是内部链接
      var isInternalLink =
        link.href.startsWith(window.location.origin) ||
        link.href.startsWith("#") ||
        link.href.startsWith("javascript:") ||
        link.getAttribute("href") === "#" ||
        link.classList.contains("no-transition");

      if (!isInternalLink) {
        // 保存原始链接
        link.setAttribute("data-original-url", link.href);
        // 直接跳转到目标URL
        link.setAttribute("href", link.href);
        // 确保链接在新窗口打开
        if (!link.getAttribute("target")) {
          link.setAttribute("target", "_blank");
        }
      }
    });
    return;
  }

  // 获取所有链接元素
  var links = document.querySelectorAll("a");

  links.forEach(function (link) {
    // 防止重复处理
    if (link.dataset.transitionHandled) return;

    handleLink(link);
  });

  // 处理单个链接的函数
  function handleLink(link) {
    // 检查链接是否包含href属性
    if (!link.href) return;

    // 防止重复处理
    if (link.dataset.transitionHandled) return;

    // 标记为已处理
    link.dataset.transitionHandled = "true";

    // 检查是否是内部链接或特殊链接
    var isInternalLink =
      link.href.startsWith(window.location.origin + "/goto/") || // 已经是过渡页链接
      (link.href.startsWith(window.location.origin) &&
        !link.href.match(/\/site\/\d+$/)) || // 不是/site/数字结尾的内部链接
      link.href.startsWith("#") ||
      link.href.startsWith("javascript:") ||
      link.getAttribute("href") === "#" ||
      link.classList.contains("no-transition");

    // 如果是内部链接且不需要处理，直接返回
    if (isInternalLink) {
      return;
    }

    // 获取链接对应的网站ID
    var websiteId = link.getAttribute("data-website-id");
    var websiteUrl = link.getAttribute("data-website-url");

    // 检查是否是网站详情页链接 (/site/123)
    var sitePageMatch = link.href.match(/\/site\/(\d+)$/);
    if (sitePageMatch && sitePageMatch[1]) {
      websiteId = sitePageMatch[1];
    }

    // 如果有网站ID，修改链接指向过渡页
    if (websiteId) {
      // 保存原始链接
      link.setAttribute("data-original-url", link.href);

      // 修改链接为过渡页路由
      link.setAttribute("href", "/goto/" + websiteId);

      // 确保链接在新窗口打开
      if (!link.getAttribute("target")) {
        link.setAttribute("target", "_blank");
      }
    }
  }

  // 对于后续动态添加的链接，使用MutationObserver监听
  const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      if (mutation.type === "childList") {
        mutation.addedNodes.forEach(function (node) {
          // 检查新添加的节点是否是链接或包含链接
          if (node.nodeType === 1) {
            // 元素节点
            if (node.nodeName === "A") {
              handleLink(node);
            } else {
              // 查找节点内的所有链接
              var childLinks = node.querySelectorAll("a");
              childLinks.forEach(handleLink);
            }
          }
        });
      }
    });
  });

  // 监听整个文档的变化
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
});
