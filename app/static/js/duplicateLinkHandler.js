/**
 * 重复链接处理模块
 * 提供更友好的重复链接提示和处理功能
 */

// 存储当前正在处理的重复链接信息
let currentDuplicateData = null;
let resolvePromise = null;
let rejectPromise = null;

// 获取DOM元素
document.addEventListener("DOMContentLoaded", function () {
  const duplicateModal = document.getElementById("duplicateLinkModal");
  const closeDuplicateBtn = document.getElementById("closeDuplicateModal");
  const viewExistingBtn = document.getElementById("viewExistingLink");
  const addDuplicateBtn = document.getElementById("addDuplicateLink");
  const cancelDuplicateBtn = document.getElementById("cancelDuplicateAdd");

  // 关闭对话框
  function closeDuplicateModal() {
    duplicateModal.style.display = "none";
    // 如果存在Promise回调但尚未解决，则以"cancel"结果拒绝
    if (rejectPromise) {
      rejectPromise("cancel");
      resolvePromise = null;
      rejectPromise = null;
    }
  }

  // 关闭按钮事件
  if (closeDuplicateBtn) {
    closeDuplicateBtn.addEventListener("click", closeDuplicateModal);
  }

  // 点击模态框背景关闭
  if (duplicateModal) {
    duplicateModal.addEventListener("click", function (e) {
      if (e.target === duplicateModal) {
        closeDuplicateModal();
      }
    });
  }

  // 查看已有链接按钮事件
  if (viewExistingBtn) {
    viewExistingBtn.addEventListener("click", function () {
      if (currentDuplicateData && resolvePromise) {
        resolvePromise("view");
        duplicateModal.style.display = "none";
        currentDuplicateData = null;
        resolvePromise = null;
        rejectPromise = null;
      }
    });
  }

  // 仍然添加按钮事件
  if (addDuplicateBtn) {
    addDuplicateBtn.addEventListener("click", function () {
      if (currentDuplicateData && resolvePromise) {
        resolvePromise("add");
        duplicateModal.style.display = "none";
        currentDuplicateData = null;
        resolvePromise = null;
        rejectPromise = null;
      }
    });
  }

  // 取消按钮事件
  if (cancelDuplicateBtn) {
    cancelDuplicateBtn.addEventListener("click", function () {
      if (resolvePromise) {
        resolvePromise("cancel");
        duplicateModal.style.display = "none";
        currentDuplicateData = null;
        resolvePromise = null;
        rejectPromise = null;
      }
    });
  }
});

/**
 * 显示重复链接提示对话框
 * @param {Object} duplicateData - 重复链接的数据
 * @returns {Promise} - 用户操作的Promise，resolve的值为"view"(查看已有),"add"(仍然添加),"cancel"(取消)
 */
function showDuplicateLinkPrompt(duplicateData) {
  return new Promise((resolve, reject) => {
    const duplicateModal = document.getElementById("duplicateLinkModal");
    const categoryEl = document.getElementById("duplicateCategory");
    const titleEl = document.getElementById("duplicateTitle");
    const descEl = document.getElementById("duplicateDesc");

    if (!duplicateModal || !categoryEl || !titleEl || !descEl) {
      console.error("重复链接提示对话框元素不存在");
      reject("元素不存在");
      return;
    }

    // 存储当前数据和Promise解析函数
    currentDuplicateData = duplicateData;
    resolvePromise = resolve;
    rejectPromise = reject;

    // 设置对话框内容
    categoryEl.textContent = duplicateData.category_name || "未分类";
    titleEl.textContent = duplicateData.title || "未命名";
    descEl.textContent = duplicateData.description || "无描述";

    // 显示对话框
    duplicateModal.style.display = "flex";

    // ESC键关闭对话框
    const escHandler = function (e) {
      if (e.key === "Escape") {
        duplicateModal.style.display = "none";
        if (resolvePromise) resolvePromise("cancel");
        document.removeEventListener("keydown", escHandler);
      }
    };

    document.addEventListener("keydown", escHandler);
  });
}

/**
 * 导航到已有链接所在的页面
 * @param {Object} websiteData - 已存在的网站数据
 */
function navigateToExistingLink(websiteData) {
  if (!websiteData || !websiteData.category_id) {
    console.error("无法导航：缺少必要的网站数据");
    return;
  }

  // 构建分类页面URL
  const categoryUrl = `/category/${websiteData.category_id}`;

  // 导航到分类页面，并传递网站ID以便高亮显示
  window.location.href = `${categoryUrl}?highlight=${websiteData.id}`;
}
