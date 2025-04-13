/**
 * 颜色选择器JS
 * 提供便捷的颜色选择功能，包括预设颜色和自定义颜色
 */
class ColorPicker {
  constructor(options) {
    this.targetInput = document.getElementById(options.inputId);
    if (!this.targetInput) return;

    this.container = document.createElement("div");
    this.container.className = "color-picker-container";
    this.targetInput.parentNode.insertBefore(this.container, this.targetInput);
    this.container.appendChild(this.targetInput);

    // 隐藏原始输入框
    this.targetInput.style.display = "none";

    // 当前选中的颜色
    this.selectedColor = this.targetInput.value || "#7049f0";

    // 创建预览
    this.createPreview();

    // 创建下拉选择器
    this.createDropdown();

    // 初始化颜色数据
    this.initColorsData();

    // 绑定事件
    this.bindEvents();

    // 更新预览
    this.updatePreview();
  }

  createPreview() {
    this.preview = document.createElement("div");
    this.preview.className = "color-picker-preview";
    this.preview.innerHTML = `
      <div class="color-preview-swatch"></div>
      <span class="color-picker-preview-text"></span>
      <i class="bi bi-chevron-down"></i>
    `;
    this.container.appendChild(this.preview);
  }

  createDropdown() {
    this.dropdown = document.createElement("div");
    this.dropdown.className = "color-picker-dropdown";
    this.dropdown.innerHTML = `
      <div class="theme-colors-grid">
        <div class="theme-color-item" data-color="#7049f0">
          <div class="theme-color-swatch" style="background-color: #7049f0"></div>
          <span>主题色</span>
        </div>
        <div class="theme-color-item" data-color="#4a88fc">
          <div class="theme-color-swatch" style="background-color: #4a88fc"></div>
          <span>辅助蓝</span>
        </div>
        <div class="theme-color-item" data-color="#ff6b6b">
          <div class="theme-color-swatch" style="background-color: #ff6b6b"></div>
          <span>亮红色</span>
        </div>
      </div>
      
      <div class="color-input-group">
        <div class="color-input-visual">
          <input type="color" id="colorInputVisual" value="${this.selectedColor}">
        </div>
        <div class="color-input-text">
          <input type="text" id="colorInputText" value="${this.selectedColor}" placeholder="#000000">
        </div>
      </div>
      
      <div class="color-picker-presets">
        <div class="color-picker-presets-title">预设颜色</div>
        <div class="color-preset-grid" id="colorPresets"></div>
      </div>
      
      <div class="color-picker-footer">
        <div class="color-preview-box">
          <i class="bi bi-folder"></i>
        </div>
        <div>
          <button type="button" class="btn btn-sm btn-outline-secondary" id="colorPickerCancel">取消</button>
          <button type="button" class="btn btn-sm btn-primary" id="colorPickerConfirm">确认选择</button>
        </div>
      </div>
    `;
    this.container.appendChild(this.dropdown);

    // 设置引用
    this.colorInputVisual = this.dropdown.querySelector("#colorInputVisual");
    this.colorInputText = this.dropdown.querySelector("#colorInputText");
    this.colorPresets = this.dropdown.querySelector("#colorPresets");
    this.previewBox = this.dropdown.querySelector(".color-preview-box");
    this.cancelBtn = this.dropdown.querySelector("#colorPickerCancel");
    this.confirmBtn = this.dropdown.querySelector("#colorPickerConfirm");
    this.themeColors = this.dropdown.querySelectorAll(".theme-color-item");
  }

  initColorsData() {
    // 预设颜色
    this.presetColors = [
      "#3498db",
      "#2ecc71",
      "#9b59b6",
      "#e74c3c",
      "#f39c12",
      "#1abc9c",
      "#34495e",
      "#16a085",
      "#27ae60",
      "#2980b9",
      "#8e44ad",
      "#2c3e50",
      "#f1c40f",
      "#e67e22",
      "#d35400",
      "#c0392b",
      "#7f8c8d",
      "#95a5a6",
    ];

    // 渲染预设颜色
    this.renderPresetColors();

    // 更新预览框颜色
    this.updatePreviewBox();
  }

  renderPresetColors() {
    this.colorPresets.innerHTML = "";

    this.presetColors.forEach((color) => {
      const colorItem = document.createElement("div");
      colorItem.className = `color-preset-item ${
        this.selectedColor.toLowerCase() === color.toLowerCase()
          ? "selected"
          : ""
      }`;
      colorItem.style.backgroundColor = color;
      colorItem.dataset.color = color;

      // 点击选择颜色
      colorItem.addEventListener("click", () => {
        this.selectColor(color);
      });

      this.colorPresets.appendChild(colorItem);
    });
  }

  bindEvents() {
    // 切换下拉显示
    this.preview.addEventListener("click", () => {
      this.toggleDropdown();
    });

    // 取消按钮
    this.cancelBtn.addEventListener("click", () => {
      this.closeDropdown();
    });

    // 确认按钮
    this.confirmBtn.addEventListener("click", () => {
      this.confirmSelection();
    });

    // 颜色输入 - 可视化
    this.colorInputVisual.addEventListener("input", () => {
      const color = this.colorInputVisual.value;
      this.colorInputText.value = color;
      this.selectColor(color);
    });

    // 颜色输入 - 文本
    this.colorInputText.addEventListener("input", () => {
      let color = this.colorInputText.value;
      if (color.match(/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/)) {
        this.colorInputVisual.value = color;
        this.selectColor(color);
      }
    });

    // 主题颜色
    this.themeColors.forEach((item) => {
      item.addEventListener("click", () => {
        const color = item.dataset.color;
        this.selectColor(color);
      });
    });

    // 点击外部关闭
    document.addEventListener("click", (e) => {
      if (!this.container.contains(e.target)) {
        this.closeDropdown();
      }
    });
  }

  selectColor(color) {
    this.selectedColor = color;

    // 更新输入框
    this.colorInputVisual.value = color;
    this.colorInputText.value = color;

    // 更新预设颜色选中状态
    const presetItems =
      this.colorPresets.querySelectorAll(".color-preset-item");
    presetItems.forEach((item) => {
      item.classList.remove("selected");
      if (item.dataset.color.toLowerCase() === color.toLowerCase()) {
        item.classList.add("selected");
      }
    });

    // 更新主题颜色选中状态
    this.themeColors.forEach((item) => {
      item.classList.remove("selected");
      if (item.dataset.color.toLowerCase() === color.toLowerCase()) {
        item.classList.add("selected");
      }
    });

    // 更新预览框
    this.updatePreviewBox();
  }

  updatePreviewBox() {
    this.previewBox.style.backgroundColor = this.selectedColor;

    // 计算文字颜色
    const rgb = this.hexToRgb(this.selectedColor);
    if (rgb) {
      const brightness = Math.round(
        (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000
      );
      this.previewBox.style.color = brightness > 125 ? "black" : "white";
    }
  }

  hexToRgb(hex) {
    const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    hex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);

    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16),
        }
      : null;
  }

  confirmSelection() {
    // 设置输入框的值
    this.targetInput.value = this.selectedColor;

    // 更新预览
    this.updatePreview();

    // 关闭下拉
    this.closeDropdown();

    // 触发change事件
    const event = new Event("change", { bubbles: true });
    this.targetInput.dispatchEvent(event);
  }

  updatePreview() {
    const colorSwatch = this.preview.querySelector(".color-preview-swatch");
    const textPreview = this.preview.querySelector(
      ".color-picker-preview-text"
    );

    colorSwatch.style.backgroundColor = this.selectedColor;
    textPreview.textContent = this.selectedColor;
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
  }

  closeDropdown() {
    this.dropdown.classList.remove("show");
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // 初始化颜色选择器，检查页面上是否有相应元素
  if (document.getElementById("color")) {
    new ColorPicker({
      inputId: "color",
    });
  }
});
