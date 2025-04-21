document.addEventListener("paste", async function (e) {
  // 只有管理员才能使用快速添加功能
  if (!document.body.classList.contains("user-admin")) {
    return;
  }

  // 如果编辑链接窗口打开中，不触发快速添加
  const editLinkModal = document.getElementById("editLinkModal");
  if (editLinkModal && editLinkModal.style.display === "flex") {
    return;
  }

  // 获取剪贴板内容
  const clipboardData = e.clipboardData || window.clipboardData;
  const pastedData = clipboardData.getData("text");

  // 验证是否是有效的URL
  if (!isValidUrl(pastedData)) {
    return;
  }

  // 显示加载中状态
  showQuickAddModal();
  setQuickAddLoading(true);

  try {
    // 检查URL是否已存在
    const checkResponse = await fetch(
      `/api/check_url_exists?url=${encodeURIComponent(pastedData)}`
    );
    const checkResult = await checkResponse.json();

    if (checkResult.exists) {
      // 使用自定义对话框替代confirm
      closeQuickAddModal();

      // 显示重复链接提示对话框
      const action = await showDuplicateLinkPrompt(checkResult.website);

      if (action === "view") {
        // 导航到已有链接
        navigateToExistingLink(checkResult.website);
        return;
      } else if (action === "cancel") {
        // 用户选择取消添加
        return;
      }
      // 用户选择继续添加，重新打开快速添加对话框
      showQuickAddModal();
    }

    // 获取网站信息和图标
    const requestOptions = {
      method: "GET",
      redirect: "follow",
    };

    const websiteInfo = await fetch(
      `/api/fetch_website_info?url=${encodeURIComponent(pastedData)}`,
      requestOptions
    ).then((r) => r.json());

    // 填充表单
    document.getElementById("quickAddTitle").value = websiteInfo.title || "";
    document.getElementById("quickAddUrl").value = pastedData;
    document.getElementById("quickAddDescription").value =
      websiteInfo.description || "";

    // 设置图标
    if (websiteInfo.success && websiteInfo.icon_url) {
      const iconInput = document.getElementById("quickAddIcon");
      const iconPreview = document.getElementById("quickAddIconPreview");
      iconInput.value = websiteInfo.icon_url;
      iconPreview.src = websiteInfo.icon_url;
      iconPreview.style.display = "block";
    }
  } catch (error) {
    console.error("获取网站信息失败:", error);
    // 如果获取失败，至少填充URL
    document.getElementById("quickAddUrl").value = pastedData;
  } finally {
    setQuickAddLoading(false);
  }
});

// 验证URL是否合法
function isValidUrl(url) {
  try {
    const urlObj = new URL(url);
    return urlObj.protocol === "http:" || urlObj.protocol === "https:";
  } catch (error) {
    return false;
  }
}

function showQuickAddModal() {
  const modal = document.getElementById("quickAddModal");
  modal.style.display = "flex";
}

function closeQuickAddModal() {
  const modal = document.getElementById("quickAddModal");
  modal.style.display = "none";
  // 清空表单
  document.getElementById("quickAddTitle").value = "";
  document.getElementById("quickAddUrl").value = "";
  document.getElementById("quickAddDescription").value = "";
  document.getElementById("quickAddIcon").value = "";
  document.getElementById("quickAddIconPreview").style.display = "none";
  document.getElementById("quickAddCategory").value = "";
  document.getElementById("quickAddWeight").value = "0"; // 重置权重为默认值
}

function setQuickAddLoading(isLoading) {
  const submitBtn = document.querySelector("#quickAddModal .btn-primary");
  if (isLoading) {
    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm me-1"></span>加载中...';
  } else {
    submitBtn.disabled = false;
    submitBtn.innerHTML = "添加";
  }
}

async function submitQuickAdd() {
  const categoryId = document.getElementById("quickAddCategory").value;
  if (!categoryId) {
    alert("请选择分类");
    return;
  }

  const url = document.getElementById("quickAddUrl").value.trim();

  try {
    // 检查URL是否已存在（这里是新增，不需要排除ID）
    const checkResponse = await fetch(
      `/api/check_url_exists?url=${encodeURIComponent(url)}`
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

    const submitBtn = document.querySelector("#quickAddModal .btn-primary");
    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm me-1"></span>提交中...';

    const data = {
      title: document.getElementById("quickAddTitle").value.trim(),
      url: url,
      description: document.getElementById("quickAddDescription").value.trim(),
      icon: document.getElementById("quickAddIcon").value.trim(),
      category_id: parseInt(categoryId),
      is_private: document.getElementById("quickAddPrivate").checked ? 1 : 0,
      sort_order:
        parseInt(document.getElementById("quickAddWeight").value) || 0,
    };

    const response = await fetch("/api/website/quick-add", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
          .content,
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();
    if (result.success) {
      closeQuickAddModal();
      // 刷新页面以显示新添加的链接
      window.location.reload();
    } else {
      alert(result.message || "添加失败");
    }
  } catch (error) {
    console.error("提交失败:", error);
    alert("提交失败，请重试");
  } finally {
    const submitBtn = document.querySelector("#quickAddModal .btn-primary");
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="bi bi-plus-lg me-1"></i>添加';
  }
}
