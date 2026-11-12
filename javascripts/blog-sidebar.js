// 博客侧栏的「Archive / 分类」默认展开，但保留折叠能力：
// 上面是原生 checkbox 折叠机制，只是替你点了一下，点击标题仍可正常收起/展开。
(function () {
  var TITLES = ['Archive', '分类'];

  function expand() {
    document
      .querySelectorAll('.md-sidebar--primary .md-nav__item--nested')
      .forEach(function (item) {
        var label = item.querySelector(':scope > label.md-nav__link');
        if (!label || TITLES.indexOf(label.textContent.trim()) === -1) return;
        var box = item.querySelector(':scope > input[type="checkbox"]');
        if (box && !box.checked) box.checked = true;
      });
  }

  // 兼容 Material 的 instant navigation：每次页面切换后重新应用
  if (window.document$ && window.document$.subscribe) {
    window.document$.subscribe(expand);
  } else {
    document.addEventListener('DOMContentLoaded', expand);
  }
})();
