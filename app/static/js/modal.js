document.addEventListener("DOMContentLoaded", function () {
  const editLinkModal = document.getElementById("editLinkModal");
  const editLinkBtn = document.getElementById("editLink");
  const closeModalBtn = document.getElementById("closeModal");
  const cancelEditBtn = document.getElementById("cancelEdit");
  const editLinkForm = document.getElementById("editLinkForm");
  const fetchInfoBtn = document.getElementById("fetchInfo");
  const editIconPreview = document.getElementById("editIconPreview");

  /**
   * 显示toast通知
   * @param {string} message - 显示的消息
   * @param {string} type - 通知类型：success, error, warning, info
   */
  function showToast(message, type = "success") {
    // 检查是否已存在提示，如果有则移除
    const existingToast = document.querySelector(".copy-toast");
    if (existingToast) {
      document.body.removeChild(existingToast);
    }

    // 根据类型确定图标和颜色
    let icon, backgroundColor, borderColor;
    switch (type) {
      case "error":
        icon = "bi-exclamation-circle-fill";
        backgroundColor = "linear-gradient(145deg, #f44336, #e53935)";
        borderColor = "#c62828";
        break;
      case "warning":
        icon = "bi-exclamation-triangle-fill";
        backgroundColor = "linear-gradient(145deg, #ff9800, #f57c00)";
        borderColor = "#e65100";
        break;
      case "info":
        icon = "bi-info-circle-fill";
        backgroundColor = "linear-gradient(145deg, #2196f3, #1e88e5)";
        borderColor = "#0d47a1";
        break;
      case "success":
      default:
        icon = "bi-check-circle-fill";
        backgroundColor =
          "var(--primary-gradient, linear-gradient(135deg, #7049f0, #aa26ff))";
        borderColor = "rgba(112, 73, 240, 0.7)";
        break;
    }

    // 创建新的提示元素
    const toast = document.createElement("div");
    toast.className = "copy-toast";
    toast.style.background = backgroundColor;
    toast.style.borderLeft = `4px solid ${borderColor}`;
    toast.innerHTML = `
      <i class="bi ${icon}"></i>
      <span>${message}</span>
    `;

    // 添加到页面
    document.body.appendChild(toast);

    // 延迟一小段时间后显示，以便有渐入效果
    setTimeout(() => {
      toast.classList.add("show");
    }, 10);

    // 2.5秒后自动消失
    setTimeout(() => {
      toast.classList.remove("show");

      // 动画结束后从DOM中移除
      setTimeout(() => {
        if (toast.parentNode) {
          document.body.removeChild(toast);
        }
      }, 300); // 等待过渡动画完成
    }, 2500);
  }

  // 修改链接按钮点击事件
  editLinkBtn.addEventListener("click", function () {
    if (window.currentCard) {
      const cardId = window.currentCard.href.split("/").pop();
      const cardTitle = window.currentCard
        .querySelector(".site-title")
        .textContent.trim();
      const cardDesc = window.currentCard
        .querySelector(".site-description")
        .textContent.trim();
      const cardIcon = window.currentCard.querySelector(".site-icon img");

      // 获取排序权重值 - 优先使用data-sort-order，不存在则使用data-sort
      let sortOrder = window.currentCard.getAttribute("data-sort-order");
      if (!sortOrder) {
        sortOrder = window.currentCard.getAttribute("data-sort");
      }

      // 填充表单
      document.getElementById("editLinkId").value = cardId;
      document.getElementById("editTitle").value = cardTitle;
      document.getElementById("editUrl").value = ""; // 获取URL需要额外请求
      document.getElementById("editDescription").value = cardDesc;

      // 如果能从DOM中获取权重值，则直接设置
      if (sortOrder) {
        document.getElementById("editWeight").value = sortOrder;
      }

      if (cardIcon) {
        document.getElementById("editIcon").value = cardIcon.src;
        // 更新图标预览
        editIconPreview.src = cardIcon.src;
        editIconPreview.style.display = "block";
      } else {
        document.getElementById("editIcon").value = "";
        editIconPreview.style.display = "none";
      }

      // 从服务器获取完整信息
      fetch(`/site/${cardId}/info`)
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            document.getElementById("editUrl").value = data.website.url;
            // 更新描述，使用服务器返回的完整描述
            if (data.website.description) {
              document.getElementById("editDescription").value =
                data.website.description;
            }
            // 设置私有/公开状态
            if (data.website.is_private) {
              document.getElementById("editPrivate").checked = true;
            } else {
              document.getElementById("editPublic").checked = true;
            }

            // 只有在DOM中没有获取到权重值时，才从服务器数据中设置
            if (!sortOrder && data.website.sort_order !== undefined) {
              document.getElementById("editWeight").value =
                data.website.sort_order;
            }

            // 设置当前分类
            if (data.website.category && data.website.category.id) {
              const categorySelect = document.getElementById("editCategory");
              if (categorySelect) {
                categorySelect.value = data.website.category.id;
              }
            }
          }
        })
        .catch((error) => {
          console.error("获取网站信息出错:", error);
        });

      // 显示对话框
      editLinkModal.style.display = "flex";
    }
  });

  // 监听图标输入框变化，更新预览
  document.getElementById("editIcon").addEventListener("input", function () {
    const iconUrl = this.value.trim();
    if (iconUrl) {
      editIconPreview.src = iconUrl;
      editIconPreview.style.display = "block";

      // 处理加载错误
      editIconPreview.onerror = function () {
        this.style.display = "none";
      };
    } else {
      editIconPreview.style.display = "none";
    }
  });

  // 关闭对话框
  closeModalBtn.addEventListener("click", function () {
    editLinkModal.style.display = "none";
  });

  cancelEditBtn.addEventListener("click", function () {
    editLinkModal.style.display = "none";
  });

  // 点击遮罩层关闭对话框
  editLinkModal.addEventListener("click", function (e) {
    if (e.target === this) {
      this.style.display = "none";
    }
  });

  // 处理表单提交
  editLinkForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    const siteId = document.getElementById("editLinkId").value;
    const title = document.getElementById("editTitle").value;
    const url = document.getElementById("editUrl").value;
    const icon = document.getElementById("editIcon").value;
    const description = document.getElementById("editDescription").value;
    const categoryId = document.getElementById("editCategory").value;
    const sortOrder =
      parseInt(document.getElementById("editWeight").value) || 0;

    // 验证分类选择
    if (!categoryId) {
      showToast("请选择分类", "info");
      return;
    }

    try {
      // 检查URL是否已存在（排除当前编辑的链接）
      const checkResponse = await fetch(
        `/api/check_url_exists?url=${encodeURIComponent(
          url
        )}&exclude_id=${siteId}`
      );
      const checkResult = await checkResponse.json();

      if (checkResult.exists) {
        // 使用自定义对话框替代confirm
        const action = await showDuplicateLinkPrompt(checkResult.website);

        if (action === "view") {
          // 导航到已有链接
          navigateToExistingLink(checkResult.website);
          return;
        } else if (action === "cancel") {
          // 用户选择取消添加
          return;
        }
        // 用户选择继续添加
      }

      // 发送修改请求到服务器
      const response = await fetch(`/api/website/update/${siteId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
            .content,
        },
        body: JSON.stringify({
          title: title,
          url: url,
          icon: icon,
          description: description,
          is_private: document.getElementById("editPrivate").checked ? 1 : 0,
          category_id: parseInt(categoryId),
          sort_order: sortOrder,
        }),
      });

      const data = await response.json();
      if (data.success) {
        // 判断分类是否改变，如果改变则刷新页面
        const originalCategoryId =
          window.currentCard.closest(".card-container")?.dataset.categoryId;
        if (originalCategoryId && originalCategoryId !== categoryId) {
          // 分类已更改，刷新页面
          alert("链接分类已更改，页面将重新加载");
          window.location.reload();
          return;
        }

        // 分类未改变，更新卡片显示
        if (window.currentCard) {
          const titleEl = window.currentCard.querySelector(".site-title");
          const descEl = window.currentCard.querySelector(".site-description");
          const iconImg = window.currentCard.querySelector(".site-icon img");
          const iconContainer = window.currentCard.querySelector(".site-icon");

          if (titleEl) titleEl.textContent = title.trim();
          if (descEl) descEl.textContent = description.trim();

          // 更新图标
          if (icon) {
            if (iconImg) {
              iconImg.src = icon;
            } else {
              // 如果之前没有图标，创建一个
              iconContainer.innerHTML = `<img src="${icon}" alt="${title}">`;
            }
          } else if (iconImg) {
            // 如果清除了图标，显示默认图标（使用网站标题首字母）
            const firstLetter = title.trim().charAt(0).toUpperCase();
            iconContainer.innerHTML = `<div class="default-site-icon">${firstLetter}</div>`;
          }

          // 更新卡片的data-description属性
          window.currentCard.setAttribute(
            "data-description",
            description.trim()
          );
        }

        showToast("网站信息修改成功!");

        // 关闭模态框而不刷新页面
        editLinkModal.style.display = "none";
      } else {
        showToast("修改失败: " + data.message, "error");
      }
    } catch (error) {
      console.error("修改链接出错:", error);
      showToast("修改链接时发生错误，请重试", "error");
    }
  });

  // 自动获取网站信息
  fetchInfoBtn.addEventListener("click", function () {
    const urlInput = document.getElementById("editUrl");
    const titleInput = document.getElementById("editTitle");
    const descInput = document.getElementById("editDescription");
    const iconInput = document.getElementById("editIcon");
    const url = urlInput.value.trim();

    if (!url) {
      showToast("请先输入网站链接地址", "info");
      return;
    }

    // 显示加载状态
    this.classList.add("loading");

    // 请求网站信息
    fetch(`/api/fetch_website_info?url=${encodeURIComponent(url)}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // 直接更新标题和描述，无论是否为空
          if (data.title) {
            titleInput.value = data.title;
          }

          if (data.description) {
            descInput.value = data.description;
          }

          // 解析域名获取图标
          try {
            let domain = url;
            if (url.startsWith("http")) {
              const urlObj = new URL(url);
              domain = urlObj.hostname;
            } else if (url.includes("/")) {
              domain = url.split("/")[0];
            }

            // 使用API获取图标
            const requestOptions = {
              method: "GET",
              redirect: "follow",
            };

            fetch(
              `/api/get_website_icon?url=${encodeURIComponent(url)}`,
              requestOptions
            )
              .then((response) => response.json())
              .then((iconData) => {
                if (iconData.success && iconData.icon_url) {
                  iconInput.value = iconData.icon_url;
                } else if (iconData.fallback_url) {
                  // 如果API获取失败但有备用服务
                  iconInput.value = iconData.fallback_url;
                } else {
                  // 如果API获取失败，使用备用服务
                  iconInput.value = `https://favicon.cccyun.cc/${domain}`;
                }
              })
              .catch(() => {
                // 如果请求出错，使用备用服务
                iconInput.value = `https://favicon.cccyun.cc/${domain}`;
              });
          } catch (error) {
            console.error("解析域名出错:", error);
          }

          showToast("网站信息获取成功!");
        } else {
          showToast(
            "获取网站信息失败: " + (data.message || "未知错误"),
            "error"
          );
        }
      })
      .catch((error) => {
        console.error("获取网站信息出错:", error);
        showToast("获取网站信息失败，请手动填写", "warning");
      })
      .finally(() => {
        // 移除加载状态
        this.classList.remove("loading");
      });
  });
});
