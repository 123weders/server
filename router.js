(function () {
  'use strict';

  // 1) Настоящие редиректы (старые адреса)
  var REDIRECTS = {
    '/donnats.html': '/donate'
  };

  // 2) Красивый путь -> реальный файл (для 404.html на GitHub Pages)
  var ROUTES = {
    '/':       '/index.html',
    '/info':   '/info.html',
    '/rules':  '/rules.html',
    '/donate': '/donate.html'
  };

  var path = window.location.pathname;

  // --- Шаг A: старые адреса -> новые (с перезагрузкой) ---
  if (REDIRECTS[path]) {
    window.location.replace(REDIRECTS[path]);
    return;
  }

  // --- Шаг B: *.html -> красивый URL без перезагрузки ---
  if (/\.html$/.test(path) && window.history && history.replaceState) {
    var pretty = path === '/index.html'
      ? '/'
      : path.replace(/\.html$/, '');
    history.replaceState(null, '', pretty + window.location.search + window.location.hash);
    path = pretty;
  }

  // --- Шаг C: 404.html + известный путь -> грузим файл ---
  var is404 = document.documentElement.getAttribute('data-404') === 'true';
  if (is404 && ROUTES[path]) {
    fetch(ROUTES[path])
      .then(function (r) { return r.text(); })
      .then(function (html) {
        document.open();
        document.write(html);
        document.close();
        if (window.history && history.replaceState) {
          history.replaceState(null, '', path);
        }
      })
      .catch(function () { window.location.href = '/'; });
    return;
  }

  // --- Шаг D: 404 и пути нет — заглушка ---
  if (is404 && !ROUTES[path]) {
    document.body.innerHTML =
      '<h1>404</h1><p>Страница не найдена. <a href="/">На главную</a></p>';
  }
})();
