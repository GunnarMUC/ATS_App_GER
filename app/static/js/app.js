function csrfToken() {
  const m = document.cookie.match(/(?:^|; )csrf_token=([^;]*)/);
  if (m) return decodeURIComponent(m[1]);
  return window.CSRF_TOKEN || "";
}

document.addEventListener("submit", (e) => {
  const form = e.target;
  if (!(form instanceof HTMLFormElement)) return;
  const method = (form.getAttribute("method") || "get").toLowerCase();
  if (!["post", "put", "patch", "delete"].includes(method) && !form.hasAttribute("hx-post")) {
    return;
  }
  let input = form.querySelector('input[name="csrf_token"]');
  if (!input) {
    input = document.createElement("input");
    input.type = "hidden";
    input.name = "csrf_token";
    form.appendChild(input);
  }
  input.value = csrfToken();
});

document.addEventListener("htmx:configRequest", (e) => {
  const t = csrfToken();
  if (t) e.detail.headers["X-CSRF-Token"] = t;
});

const _fetch = window.fetch.bind(window);
window.fetch = function (input, init) {
  init = init || {};
  const method = String(init.method || "GET").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS", "TRACE"].includes(method)) {
    const headers = new Headers(init.headers || {});
    if (!headers.has("X-CSRF-Token")) headers.set("X-CSRF-Token", csrfToken());
    init.headers = headers;
  }
  return _fetch(input, init);
};
