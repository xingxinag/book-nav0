// 在显示搜索结果时，设置数量
function displaySearchResults(data) {
  // 更新搜索状态提示
  const searchKeyword = document.getElementById("searchKeyword");
  if (searchKeyword) {
    searchKeyword.textContent = data.keyword;
  }
  const searchCount = document.getElementById("searchCount");
  if (searchCount) {
    searchCount.textContent = data.count;
  }
  searchStatus.style.display = "flex";
  // ... existing code ...
}
