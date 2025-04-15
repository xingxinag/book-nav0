document.addEventListener("DOMContentLoaded", function () {
  // 拖拽排序相关代码
  const cardContainers = document.querySelectorAll(".card-container.draggable");

  cardContainers.forEach((container) => {
    enableDragSort(container);
  });

  // 拖拽状态
  let dragStartTime = 0;
  let longPressTimer;
  let draggedCard = null;

  function enableDragSort(container) {
    const cards = container.querySelectorAll(".site-card.draggable");

    cards.forEach((card, index) => {
      // 长按开始拖拽
      card.addEventListener("mousedown", handleMouseDown);
      card.addEventListener("touchstart", handleTouchStart, { passive: false });

      function handleMouseDown(e) {
        // 只响应左键点击
        if (e.button !== 0) return;

        e.preventDefault();
        startLongPress(card, e.clientX, e.clientY);
      }

      function handleTouchStart(e) {
        e.preventDefault(); // 阻止触摸时的默认行为
        const touch = e.touches[0];
        startLongPress(card, touch.clientX, touch.clientY);
      }

      // 拖动句柄点击直接激活拖拽
      const dragHandle = card.querySelector(".drag-handle");
      if (dragHandle) {
        dragHandle.addEventListener("mousedown", function (e) {
          e.stopPropagation(); // 阻止冒泡
          e.preventDefault();
          startDragging(card, container, e.clientX, e.clientY);
        });

        dragHandle.addEventListener(
          "touchstart",
          function (e) {
            e.stopPropagation();
            e.preventDefault();
            const touch = e.touches[0];
            startDragging(card, container, touch.clientX, touch.clientY);
          },
          { passive: false }
        );
      }
    });
  }

  function startLongPress(card, x, y) {
    dragStartTime = Date.now();
    const initialX = x;
    const initialY = y;

    clearTimeout(longPressTimer);
    longPressTimer = setTimeout(() => {
      startDragging(card, card.parentNode, initialX, initialY);
    }, 300); // 长按300ms激活拖拽

    // 监听鼠标抬起和移出
    document.addEventListener("mouseup", cancelLongPress);
    document.addEventListener("mouseleave", cancelLongPress);
    document.addEventListener("touchend", cancelLongPress);
    document.addEventListener("touchcancel", cancelLongPress);

    function cancelLongPress() {
      clearTimeout(longPressTimer);
      document.removeEventListener("mouseup", cancelLongPress);
      document.removeEventListener("mouseleave", cancelLongPress);
      document.removeEventListener("touchend", cancelLongPress);
      document.removeEventListener("touchcancel", cancelLongPress);
    }
  }

  function startDragging(card, container, initialX, initialY) {
    if (draggedCard) {
      return;
    }

    draggedCard = card;
    draggedCard.classList.add("dragging");

    // 创建卡片克隆作为拖拽时的视觉提示
    const rect = card.getBoundingClientRect();

    // 设置卡片初始位置
    draggedCard.style.position = "fixed";
    draggedCard.style.zIndex = "1000";
    draggedCard.style.left = rect.left + "px";
    draggedCard.style.top = rect.top + "px";
    draggedCard.style.width = rect.width + "px";
    draggedCard.style.height = rect.height + "px";

    // 禁用卡片的点击链接功能
    draggedCard.originalHref = draggedCard.getAttribute("href");
    draggedCard.removeAttribute("href");

    // 移动到鼠标/触摸位置
    moveAt(initialX, initialY);

    // 监听移动事件
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("touchmove", onTouchMove, { passive: false });

    // 监听释放事件
    document.addEventListener("mouseup", onMouseUp);
    document.addEventListener("touchend", onMouseUp);

    function onMouseMove(e) {
      moveAt(e.clientX, e.clientY);
    }

    function onTouchMove(e) {
      e.preventDefault();
      const touch = e.touches[0];
      moveAt(touch.clientX, touch.clientY);
    }

    function moveAt(x, y) {
      if (!draggedCard) return;

      // 移动被拖拽的卡片
      draggedCard.style.left = x - draggedCard.offsetWidth / 2 + "px";
      draggedCard.style.top = y - draggedCard.offsetHeight / 2 + "px";

      const elemBelow = getElementBelow(x, y);

      if (elemBelow && elemBelow !== draggedCard) {
        // 执行卡片排序
        const rect = elemBelow.getBoundingClientRect();
        const middleY = rect.y + rect.height / 2;

        if (y < middleY && elemBelow.previousElementSibling !== draggedCard) {
          elemBelow.parentNode.insertBefore(draggedCard, elemBelow);
        } else if (
          y >= middleY &&
          elemBelow.nextElementSibling !== draggedCard
        ) {
          elemBelow.parentNode.insertBefore(
            draggedCard,
            elemBelow.nextElementSibling
          );
        }
      }
    }

    function onMouseUp() {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("touchmove", onTouchMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.removeEventListener("touchend", onMouseUp);

      if (!draggedCard) return;

      // 停止拖拽
      draggedCard.classList.remove("dragging");
      draggedCard.style.position = "";
      draggedCard.style.zIndex = "";
      draggedCard.style.left = "";
      draggedCard.style.top = "";
      draggedCard.style.width = "";
      draggedCard.style.height = "";

      // 恢复链接功能
      if (draggedCard.originalHref) {
        draggedCard.setAttribute("href", draggedCard.originalHref);
        draggedCard.originalHref = null;
      }

      // 更新排序并发送到服务器
      updateSortOrder(container);

      // 重置拖拽状态
      draggedCard = null;
    }
  }

  function getElementBelow(x, y) {
    if (!draggedCard) return null;

    // 临时隐藏当前拖拽的元素，以便获取下面的元素
    const originalDisplay = draggedCard.style.display;
    draggedCard.style.display = "none";

    // 获取指定位置的元素
    let elemBelow = document.elementFromPoint(x, y);

    // 恢复拖拽元素的显示
    draggedCard.style.display = originalDisplay;

    // 查找最近的.site-card元素
    if (elemBelow) {
      return elemBelow.closest(".site-card");
    }

    return null;
  }

  function updateSortOrder(container) {
    const cards = container.querySelectorAll(".site-card");
    if (!cards.length) {
      return;
    }

    const categoryId = container.dataset.categoryId;
    const items = [];
    const totalCards = cards.length; // 获取当前分类下的总链接数

    // 按新顺序分配权重，权重范围从1到totalCards
    cards.forEach((card, index) => {
      const websiteId = parseInt(card.dataset.id);
      if (isNaN(websiteId)) {
        return;
      }

      // 从前到后分配权重，靠前的权重大（totalCards），靠后的权重小（1）
      const newSortOrder = totalCards - index;

      // 修改data-sort属性
      card.dataset.sort = newSortOrder;

      // 同时更新DOM元素，方便右键菜单修改时显示正确的权重值
      card.setAttribute("data-sort-order", newSortOrder);

      items.push({
        id: websiteId,
        sort_order: newSortOrder,
      });
    });

    // 发送排序数据到服务器
    fetch("/api/website/update_order", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        category_id: categoryId,
        items: items,
      }),
      credentials: "same-origin",
    })
      .then((response) => response.json())
      .then((data) => {
        // 处理响应，但不输出日志
      })
      .catch((error) => {
        // 处理错误，但不输出日志
      });
  }
});
