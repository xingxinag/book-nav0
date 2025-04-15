/**
 * categorySorting.js
 * 用于实现前端分类侧边栏的拖拽排序功能
 * 仅在前端界面启用，后端管理界面不启用
 */

// 全局变量
let isBeingDragged = false;
let currentDraggedItem = null;

// 检查是否为管理员模式
function isAdminMode() {
  return document.body.classList.contains("user-admin");
}

// 检查是否在后端管理界面
function isAdminPage() {
  return window.location.pathname.includes("/admin/");
}

// 启用侧边栏分类的拖拽排序
function enableSidebarCategorySorting() {
  console.log("初始化侧边栏拖拽排序");

  // 获取分类菜单容器
  const container = document.querySelector(
    ".sidebar-content .sidebar-group:first-child .sidebar-menu"
  );
  if (!container) {
    console.error("未找到侧边栏分类菜单容器");
    return;
  }

  // 为容器添加唯一标识
  container.classList.add("sortable-categories");

  // 获取所有分类项
  const categoryItems = container.querySelectorAll(".sidebar-menu-item");
  if (categoryItems.length === 0) {
    console.error("未找到侧边栏分类项");
    return;
  }

  console.log(`找到 ${categoryItems.length} 个分类项`);

  // 为每个分类项设置ID和拖拽属性
  categoryItems.forEach((item, index) => {
    // 跳过"更多"分类中的项
    if (
      item.closest(".sidebar-group") &&
      item.closest(".sidebar-group").querySelector(".sidebar-group-title") &&
      item
        .closest(".sidebar-group")
        .querySelector(".sidebar-group-title")
        .textContent.trim() === "更多"
    ) {
      return;
    }

    // 获取分类的链接和ID
    const link = item.querySelector("a");
    if (!link) return;

    // 从链接的href属性中提取分类名
    const href = link.getAttribute("href");
    if (!href || !href.startsWith("#")) return;

    const categoryName = href.substring(1);

    // 在主内容区域中查找对应分类的ID
    const categorySection = document.getElementById(categoryName);
    if (!categorySection) return;

    const categoryContainer = categorySection.querySelector(".card-container");
    if (!categoryContainer) return;

    const categoryId = categoryContainer.dataset.categoryId;
    if (!categoryId) return;

    // 设置分类项的data-id属性
    item.setAttribute("data-id", categoryId);
    item.setAttribute("draggable", "true");

    // 添加拖拽手柄
    if (!item.querySelector(".drag-handle")) {
      const dragHandle = document.createElement("span");
      dragHandle.className = "drag-handle";
      dragHandle.innerHTML = '<i class="bi bi-grip-vertical"></i>';
      dragHandle.style.cssText =
        "cursor: grab; margin-right: 8px; opacity: 0.7; display: inline-block;";

      link.style.display = "flex";
      link.style.alignItems = "center";
      link.insertBefore(dragHandle, link.firstChild);
    }

    // 添加拖拽事件监听器
    item.addEventListener("dragstart", handleDragStart);
    item.addEventListener("dragend", handleDragEnd);
    item.addEventListener("dragover", handleDragOver);
    item.addEventListener("dragenter", handleDragEnter);
    item.addEventListener("dragleave", handleDragLeave);
    item.addEventListener("drop", handleDrop);

    console.log(`为分类 "${categoryName}" (ID: ${categoryId}) 启用拖拽`);
  });

  // 为容器添加类以支持拖拽样式
  container.classList.add("sortable");
}

// 拖拽开始事件处理
function handleDragStart(e) {
  isBeingDragged = true;
  currentDraggedItem = this;

  this.classList.add("dragging");

  // 设置拖拽数据
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", this.getAttribute("data-id"));

  // 在所有分类项上添加标记，以便样式
  document.querySelectorAll(".sidebar-menu-item").forEach((item) => {
    item.classList.add("during-drag");
  });

  // 记录初始位置
  const container = this.closest(".sidebar-menu");
  const items = Array.from(
    container.querySelectorAll(".sidebar-menu-item[data-id]")
  );
  items.forEach((item, index) => {
    item.dataset.position = index;
  });

  console.log(`开始拖拽分类: ${this.querySelector("a").textContent.trim()}`);
}

// 拖拽结束事件处理
function handleDragEnd(e) {
  isBeingDragged = false;
  this.classList.remove("dragging");

  // 移除所有项的拖拽标记
  document.querySelectorAll(".sidebar-menu-item").forEach((item) => {
    item.classList.remove("during-drag");
    item.classList.remove("drag-over");
  });

  // 更新排序
  const container = this.closest(".sidebar-menu");
  saveNewOrder(container);

  currentDraggedItem = null;
  console.log("拖拽结束");
}

// 拖拽经过事件处理
function handleDragOver(e) {
  if (e.preventDefault) {
    e.preventDefault(); // 允许放置
  }
  e.dataTransfer.dropEffect = "move";
  return false;
}

// 拖拽进入事件处理
function handleDragEnter(e) {
  if (this !== currentDraggedItem) {
    this.classList.add("drag-over");
  }
}

// 拖拽离开事件处理
function handleDragLeave(e) {
  this.classList.remove("drag-over");
}

// 放置事件处理
function handleDrop(e) {
  e.stopPropagation(); // 阻止冒泡
  e.preventDefault();

  if (this === currentDraggedItem) return;

  // 清除拖放目标样式
  this.classList.remove("drag-over");

  // 获取拖拽项的ID
  const draggedId = e.dataTransfer.getData("text/plain");
  if (!draggedId) return;

  const draggedItem = document.querySelector(
    `.sidebar-menu-item[data-id="${draggedId}"]`
  );
  if (!draggedItem) return;

  // 获取容器和所有分类项
  const container = this.closest(".sidebar-menu");
  const items = Array.from(
    container.querySelectorAll(".sidebar-menu-item[data-id]")
  );

  // 确定拖拽方向
  const draggedIndex = items.indexOf(draggedItem);
  const targetIndex = items.indexOf(this);

  // 如果目标位置有效，移动元素
  if (targetIndex !== -1) {
    if (draggedIndex < targetIndex) {
      // 向下拖动
      this.parentNode.insertBefore(draggedItem, this.nextSibling);
    } else {
      // 向上拖动
      this.parentNode.insertBefore(draggedItem, this);
    }

    console.log(`移动分类从位置 ${draggedIndex} 到 ${targetIndex}`);
  }

  return false;
}

// 保存新的排序顺序
function saveNewOrder(container) {
  if (!container) return;

  const items = [];
  const categoryItems = container.querySelectorAll(
    ".sidebar-menu-item[data-id]"
  );

  categoryItems.forEach((item, index) => {
    const id = parseInt(item.dataset.id, 10);
    if (!isNaN(id)) {
      items.push({
        id: id,
        order: (index + 1) * 10, // 使用10的倍数作为排序值
      });
    }
  });

  if (items.length === 0) {
    console.warn("没有找到要排序的分类项");
    return;
  }

  console.log(`准备保存新排序: ${JSON.stringify(items)}`);

  // 发送排序数据到服务器
  fetch("/api/category/update_order", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({ items: items }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        console.log(`排序更新成功: ${data.message}`);
        // 可以添加视觉反馈，如提示消息
        if (typeof showToast === "function") {
          showToast("success", "分类排序已更新");
        }
      } else {
        console.error(`排序更新失败: ${data.message}`);
        if (typeof showToast === "function") {
          showToast("error", "分类排序更新失败");
        }
      }
    })
    .catch((error) => {
      console.error(`排序请求失败: ${error}`);
      if (typeof showToast === "function") {
        showToast("error", "网络错误，排序更新失败");
      }
    });
}

// 获取CSRF令牌
function getCsrfToken() {
  const tokenMeta = document.querySelector('meta[name="csrf-token"]');
  return tokenMeta ? tokenMeta.getAttribute("content") : "";
}

// 初始化函数
function initCategorySorting() {
  // 检查是否在后端管理界面
  if (isAdminPage()) {
    console.log("后端管理界面不启用分类排序");
    return;
  }

  // 检查是否为管理员
  if (!isAdminMode()) {
    console.log("非管理员模式，不启用分类排序");
    return;
  }

  console.log("初始化分类排序");

  // 启用侧边栏分类排序
  enableSidebarCategorySorting();
}

// 当DOM加载完成后初始化
document.addEventListener("DOMContentLoaded", function () {
  setTimeout(() => {
    initCategorySorting();
  }, 500); // 延迟500毫秒确保DOM完全加载
});
