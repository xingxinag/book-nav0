/**
 * 图标选择器JS
 * 提供常用Bootstrap图标选择功能
 */
class IconPicker {
  constructor(options) {
    this.targetInput = document.getElementById(options.inputId);
    if (!this.targetInput) return;

    this.container = document.createElement("div");
    this.container.className = "icon-picker-container";
    this.targetInput.parentNode.insertBefore(this.container, this.targetInput);
    this.container.appendChild(this.targetInput);

    // 隐藏原始输入框
    this.targetInput.style.display = "none";

    // 当前选中的图标
    this.selectedIcon = this.targetInput.value || "";

    // 创建预览
    this.createPreview();

    // 创建下拉选择器
    this.createDropdown();

    // 初始化图标数据
    this.initIconsData();

    // 绑定事件
    this.bindEvents();

    // 更新预览
    this.updatePreview();
  }

  createPreview() {
    this.preview = document.createElement("div");
    this.preview.className = "icon-picker-preview";
    this.preview.innerHTML = `
      <i class="bi"></i>
      <span class="icon-picker-preview-text">选择图标</span>
      <i class="bi bi-chevron-down"></i>
    `;
    this.container.appendChild(this.preview);
  }

  createDropdown() {
    this.dropdown = document.createElement("div");
    this.dropdown.className = "icon-picker-dropdown";
    this.dropdown.innerHTML = `
      <div class="icon-picker-categories">
        <button type="button" class="icon-category-btn active" data-category="recommended">推荐</button>
        <button type="button" class="icon-category-btn" data-category="general">常规</button>
        <button type="button" class="icon-category-btn" data-category="media">媒体</button>
        <button type="button" class="icon-category-btn" data-category="communications">通讯</button>
        <button type="button" class="icon-category-btn" data-category="devices">设备</button>
        <button type="button" class="icon-category-btn" data-category="shapes">形状</button>
        <button type="button" class="icon-category-btn" data-category="arrows">箭头</button>
        <button type="button" class="icon-category-btn" data-category="all">全部</button>
      </div>
      <div class="icon-picker-search">
        <input type="text" placeholder="搜索图标...">
        <i class="bi bi-search"></i>
      </div>
      <div class="icon-picker-body"></div>
      <div class="icon-picker-footer">
        <div class="icon-preview-box">
          <i class="bi"></i>
        </div>
      </div>
    `;
    this.container.appendChild(this.dropdown);

    // 设置引用
    this.iconBody = this.dropdown.querySelector(".icon-picker-body");
    this.searchInput = this.dropdown.querySelector(".icon-picker-search input");
    this.previewIcon = this.dropdown.querySelector(".icon-preview-box i");
    this.categoryBtns = this.dropdown.querySelectorAll(".icon-category-btn");
  }

  initIconsData() {
    // 推荐图标
    this.recommendedIcons = [
      "folder",
      "collection",
      "bookmark",
      "globe",
      "star",
      "tags",
      "lightning",
      "database",
      "cloud",
      "palette",
      "award",
      "book",
      "music-note",
      "film",
      "chat",
      "people",
      "image",
      "camera",
      "gear",
      "tools",
      "code",
      "terminal",
      "file-code",
      "puzzle",
    ];

    // 分类图标
    this.categories = {
      general: [
        "folder",
        "file",
        "document",
        "card-list",
        "collection",
        "bookmark",
        "tag",
        "tags",
        "star",
        "heart",
        "award",
        "trophy",
        "flag",
        "pin",
        "geo",
        "dice",
        "puzzle",
        "tools",
        "gear",
        "sliders",
        "wrench",
        "screwdriver",
      ],
      media: [
        "image",
        "camera",
        "film",
        "video",
        "music-note",
        "speaker",
        "mic",
        "volume-up",
        "headphones",
        "play",
        "pause",
        "stop",
        "skip-forward",
        "record",
        "palette",
        "brush",
        "pen",
        "eyedropper",
        "fonts",
      ],
      communications: [
        "chat",
        "envelope",
        "telephone",
        "megaphone",
        "broadcast",
        "rss",
        "share",
        "send",
        "at",
        "chat-dots",
        "chat-quote",
        "reply",
        "globe",
        "translate",
        "link",
        "bell",
        "wifi",
      ],
      devices: [
        "laptop",
        "pc-display",
        "tv",
        "phone",
        "tablet",
        "printer",
        "usb",
        "mouse",
        "keyboard",
        "hdd",
        "cpu",
        "battery",
        "bluetooth",
        "watch",
        "router",
        "server",
        "thermometer",
        "speedometer",
        "water",
      ],
      shapes: [
        "square",
        "circle",
        "triangle",
        "pentagon",
        "hexagon",
        "octagon",
        "diamond",
        "heart",
        "suit-club",
        "suit-spade",
        "suit-heart",
        "suit-diamond",
        "lightning",
        "cloud",
        "layers",
        "grid",
        "calendar",
      ],
      arrows: [
        "arrow-up",
        "arrow-down",
        "arrow-left",
        "arrow-right",
        "arrow-up-right",
        "arrow-up-left",
        "arrow-down-right",
        "arrow-down-left",
        "chevron-up",
        "chevron-down",
        "chevron-left",
        "chevron-right",
        "caret-up",
        "caret-down",
        "caret-left",
        "caret-right",
        "arrow-repeat",
        "arrow-clockwise",
      ],
    };

    // 所有图标
    this.allIcons = [];
    for (const category in this.categories) {
      this.categories[category].forEach((icon) => {
        if (!this.allIcons.includes(icon)) {
          this.allIcons.push(icon);
        }
      });
    }

    // 添加更多通用图标
    const moreIcons = [
      "house",
      "person",
      "people",
      "building",
      "signpost",
      "tree",
      "lamp",
      "shop",
      "box",
      "basket",
      "bag",
      "cart",
      "cash",
      "credit-card",
      "bank",
      "coin",
      "currency-dollar",
      "currency-euro",
      "currency-bitcoin",
      "receipt",
      "graph-up",
      "table",
      "clipboard",
      "list",
      "check",
      "x",
      "exclamation",
      "question",
      "info",
      "shield",
      "lock",
      "unlock",
      "key",
      "door-open",
      "eye",
      "eye-slash",
      "eyeglasses",
      "emoji-smile",
      "emoji-neutral",
      "emoji-frown",
      "cup",
      "gift",
      "briefcase",
      "alarm",
      "clock",
    ];

    moreIcons.forEach((icon) => {
      if (!this.allIcons.includes(icon)) {
        this.allIcons.push(icon);
      }
    });

    // 初始化推荐类别
    this.renderIcons("recommended");
  }

  bindEvents() {
    // 切换下拉显示
    this.preview.addEventListener("click", () => {
      this.toggleDropdown();
    });

    // 搜索图标
    this.searchInput.addEventListener("input", () => {
      this.searchIcons();
    });

    // 切换分类
    this.categoryBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const category = btn.dataset.category;

        // 更新选中状态
        this.categoryBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        // 渲染图标
        this.renderIcons(category);
      });
    });

    // 点击外部关闭
    document.addEventListener("click", (e) => {
      if (!this.container.contains(e.target)) {
        this.closeDropdown();
      }
    });
  }

  renderIcons(category) {
    let icons = [];

    if (category === "recommended") {
      icons = this.recommendedIcons;
    } else if (category === "all") {
      icons = this.allIcons;
    } else {
      icons = this.categories[category] || [];
    }

    this.iconBody.innerHTML = "";

    icons.forEach((icon) => {
      const iconItem = document.createElement("div");
      iconItem.className = `icon-item ${
        this.selectedIcon === icon ? "selected" : ""
      }`;
      iconItem.dataset.icon = icon;
      iconItem.innerHTML = `
        <i class="bi bi-${icon}"></i>
        <span>${icon}</span>
      `;

      // 点击选择图标
      iconItem.addEventListener("click", () => {
        this.selectIcon(icon);
      });

      this.iconBody.appendChild(iconItem);
    });
  }

  searchIcons() {
    const searchTerm = this.searchInput.value.trim().toLowerCase();

    if (!searchTerm) {
      // 恢复当前分类
      const activeCategory = this.dropdown.querySelector(
        ".icon-category-btn.active"
      ).dataset.category;
      this.renderIcons(activeCategory);
      return;
    }

    // 在所有图标中搜索
    const results = this.allIcons.filter((icon) => icon.includes(searchTerm));

    this.iconBody.innerHTML = "";

    if (results.length === 0) {
      this.iconBody.innerHTML =
        '<div class="text-center text-muted py-4">没有找到匹配的图标</div>';
      return;
    }

    results.forEach((icon) => {
      const iconItem = document.createElement("div");
      iconItem.className = `icon-item ${
        this.selectedIcon === icon ? "selected" : ""
      }`;
      iconItem.dataset.icon = icon;
      iconItem.innerHTML = `
        <i class="bi bi-${icon}"></i>
        <span>${icon}</span>
      `;

      // 点击选择图标
      iconItem.addEventListener("click", () => {
        this.selectIcon(icon);
      });

      this.iconBody.appendChild(iconItem);
    });
  }

  selectIcon(icon) {
    this.selectedIcon = icon;

    // 更新选中状态
    const iconItems = this.iconBody.querySelectorAll(".icon-item");
    iconItems.forEach((item) => {
      item.classList.remove("selected");
      if (item.dataset.icon === icon) {
        item.classList.add("selected");
      }
    });

    // 更新预览图标
    this.previewIcon.className = `bi bi-${icon}`;

    // 立即应用选择
    this.confirmSelection();
  }

  confirmSelection() {
    // 设置输入框的值
    this.targetInput.value = this.selectedIcon;

    // 更新预览
    this.updatePreview();

    // 关闭下拉
    this.closeDropdown();

    // 触发change事件
    const event = new Event("change", { bubbles: true });
    this.targetInput.dispatchEvent(event);
  }

  updatePreview() {
    const iconPreview = this.preview.querySelector("i:first-child");
    const textPreview = this.preview.querySelector(".icon-picker-preview-text");

    if (this.selectedIcon) {
      iconPreview.className = `bi bi-${this.selectedIcon}`;
      textPreview.textContent = this.selectedIcon;
    } else {
      iconPreview.className = "bi";
      textPreview.textContent = "选择图标";
    }
  }

  toggleDropdown() {
    if (this.dropdown.classList.contains("show")) {
      this.closeDropdown();
    } else {
      this.openDropdown();
    }
  }

  openDropdown() {
    this.dropdown.classList.add("show");
    this.searchInput.focus();
  }

  closeDropdown() {
    this.dropdown.classList.remove("show");
    this.searchInput.value = "";
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // 初始化图标选择器，检查页面上是否有相应元素
  if (document.getElementById("icon")) {
    new IconPicker({
      inputId: "icon",
    });
  }
});
