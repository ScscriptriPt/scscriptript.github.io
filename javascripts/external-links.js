// 所有指向外部站点的链接一律在新标签页打开，站内链接不受影响
(function () {
  function externalize() {
    document.querySelectorAll('a[href^="http"]').forEach(function (a) {
      try {
        if (new URL(a.href).hostname !== window.location.hostname) {
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
        }
      } catch (e) {
        // 无效链接，忽略
      }
    });
  }

  // 兼容 Material 的 instant navigation：每次页面切换后重新应用
  if (window.document$ && window.document$.subscribe) {
    window.document$.subscribe(externalize);
  } else {
    document.addEventListener('DOMContentLoaded', externalize);
  }
})();
