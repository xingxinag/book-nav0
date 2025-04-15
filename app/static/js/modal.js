document.addEventListener("DOMContentLoaded", function () {
  const editLinkModal = document.getElementById("editLinkModal");
  const editLinkBtn = document.getElementById("editLink");
  const closeModalBtn = document.getElementById("closeModal");
  const cancelEditBtn = document.getElementById("cancelEdit");
  const editLinkForm = document.getElementById("editLinkForm");
  const fetchInfoBtn = document.getElementById("fetchInfo");
  const editIconPreview = document.getElementById("editIconPreview");

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
      alert("请选择分类");
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
        const confirmUpdate = confirm(
          `该链接已存在于分类"${checkResult.website.category_name}"中，标题为"${checkResult.website.title}"。\n\n是否仍要保存？`
        );
        if (!confirmUpdate) {
          return;
        }
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
            // 如果清除了图标，显示默认图标
            iconContainer.innerHTML =
              '<i class="bi bi-globe text-primary"></i>';
          }

          // 更新卡片的data-description属性
          window.currentCard.setAttribute(
            "data-description",
            description.trim()
          );
        }

        alert("网站信息修改成功!");

        // 关闭模态框而不刷新页面
        editLinkModal.style.display = "none";
      } else {
        alert("修改失败: " + data.message);
      }
    } catch (error) {
      console.error("修改链接出错:", error);
      alert("修改链接时发生错误，请重试");
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
      alert("请先输入网站链接地址");
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

          alert("网站信息获取成功！");
        } else {
          alert("获取网站信息失败: " + (data.message || "未知错误"));
        }
      })
      .catch((error) => {
        console.error("获取网站信息出错:", error);
        alert("获取网站信息失败，请手动填写");
      })
      .finally(() => {
        // 移除加载状态
        this.classList.remove("loading");
      });
  });
});
