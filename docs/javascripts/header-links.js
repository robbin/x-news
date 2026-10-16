(function () {
  var links = [
    ["主站", "https://fankai.me/"],
    ["教程", "https://fankaishuo.ai/"],
    ["YouTube", "https://www.youtube.com/@fankaishuoai"],
    ["X", "https://x.com/fankaishuoai"]
  ];
  function add() {
    var inner = document.querySelector(".md-header__inner");
    if (!inner || inner.querySelector(".fk-links")) return;
    var box = document.createElement("nav");
    box.className = "fk-links";
    links.forEach(function (l) {
      var a = document.createElement("a");
      a.href = l[1]; a.textContent = l[0]; a.target = "_blank"; a.rel = "noopener";
      box.appendChild(a);
    });
    var search = inner.querySelector(".md-search");
    inner.insertBefore(box, search ? search.nextSibling : null);
  }
  if (window.document$) document$.subscribe(add); else document.addEventListener("DOMContentLoaded", add);
})();
