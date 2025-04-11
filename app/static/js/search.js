document.addEventListener("DOMContentLoaded", function () {
  const searchForm = document.getElementById("searchForm");
  const searchInput = document.getElementById("searchInput");
  const clearSearchBtn = document.getElementById("clearSearch");
  const searchResults = document.getElementById("searchResults");
  const searchKeyword = document.getElementById("searchKeyword");
  const resultsContent = document.getElementById("resultsContent");
  const noResults = document.getElementById("noResults");
  const categoriesContainer = document.getElementById("categoriesContainer");

  // 搜索功能
  searchForm.addEventListener("submit", function (e) {
    e.preventDefault();
    const query = searchInput.value.trim().toLowerCase();

    if (query) {
      // 使用Ajax获取搜索结果
      fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then((response) => response.json())
        .then((data) => {
          // 清空之前的搜索结果
          resultsContent.innerHTML = "";

          if (data.websites && data.websites.length > 0) {
            // 显示搜索关键词
            searchKeyword.textContent = `"${query}"`;

            // 创建卡片容器
            const cardContainer = document.createElement("div");
            cardContainer.className = "card-container";

            // 根据结果数量添加额外的CSS类
            if (data.websites.length <= 4) {
              cardContainer.classList.add(`results-${data.websites.length}`);
            }

            resultsContent.appendChild(cardContainer);

            // 循环添加搜索结果
            data.websites.forEach((site) => {
              // 使用DOM API创建元素，避免innerHTML注入问题
              const siteCard = document.createElement("a");
              siteCard.href = `/site/${site.id}`;
              siteCard.className = "site-card";

              const siteHeader = document.createElement("div");
              siteHeader.className = "site-header";
              siteCard.appendChild(siteHeader);

              // 创建图标容器
              const iconContainer = document.createElement("div");
              iconContainer.className = "site-icon";

              if (site.icon) {
                const img = document.createElement("img");
                img.src = site.icon;
                img.alt = site.title;
                iconContainer.appendChild(img);
              } else {
                const icon = document.createElement("i");
                icon.className = "bi bi-globe text-primary";
                iconContainer.appendChild(icon);
              }

              siteHeader.appendChild(iconContainer);

              // 创建文本容器
              const textContainer = document.createElement("div");
              textContainer.className = "site-text";

              const titleEl = document.createElement("h5");
              titleEl.className = "site-title";
              titleEl.textContent = site.title;
              textContainer.appendChild(titleEl);

              const descEl = document.createElement("p");
              descEl.className = "site-description";
              descEl.textContent = site.description || "";
              textContainer.appendChild(descEl);

              siteHeader.appendChild(textContainer);

              // 将卡片添加到结果容器
              cardContainer.appendChild(siteCard);
            });

            // 显示搜索结果或无结果提示
            if (data.websites.length > 0) {
              noResults.style.display = "none";
            } else {
              noResults.style.display = "block";
            }

            // 隐藏分类容器，显示搜索结果
            categoriesContainer.style.display = "none";
            searchResults.style.display = "block";
          } else {
            // 无结果时显示提示
            noResults.style.display = "block";
          }
        })
        .catch((error) => {
          console.error("搜索出错:", error);
        });
    } else {
      clearSearch();
    }
  });

  // 监听搜索框输入
  searchInput.addEventListener("input", function () {
    if (this.value.trim()) {
      clearSearchBtn.style.display = "flex";
    } else {
      clearSearchBtn.style.display = "none";
      // 如果输入框被清空，自动恢复显示原始内容
      if (searchResults.style.display !== "none") {
        clearSearch();
      }
    }
  });

  // 清除搜索按钮
  clearSearchBtn.addEventListener("click", clearSearch);

  // 清除搜索
  function clearSearch() {
    searchInput.value = "";
    clearSearchBtn.style.display = "none";
    searchResults.style.display = "none";
    categoriesContainer.style.display = "block";
  }

  // 监听清除搜索事件
  window.addEventListener("clearSearch", clearSearch);
});
