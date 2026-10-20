(function () {
  var en = (document.documentElement.lang || "").toLowerCase().indexOf("en") === 0;
  var links = [
    [en ? "Home" : "主站", "https://fankai.me/"],
    [en ? "Subscribe" : "免费订阅", "https://fankai.me/subscribe?utm_source=news.fankai.me&utm_medium=website&utm_campaign=personal_articles&utm_content=header"],
    [en ? "Tutorials" : "教程", "https://fankaishuo.ai/"],
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
    // One-click 中/EN toggle at the far right; reuses the i18n alternate link
    // so it lands on the same article in the other language.
    var alt = document.querySelector('.md-select__link[hreflang="' + (en ? "zh" : "en") + '"]');
    if (alt && !inner.querySelector(".fk-lang")) {
      var t = document.createElement("a");
      t.className = "fk-lang"; t.href = alt.getAttribute("href");
      t.textContent = en ? "中文" : "EN";
      t.title = en ? "切换到中文" : "Switch to English";
      inner.appendChild(t);
    }
  }
  if (window.document$) document$.subscribe(add); else document.addEventListener("DOMContentLoaded", add);
})();
