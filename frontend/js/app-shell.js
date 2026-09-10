/* ==========================================================================
   MediDecode — App Shell
   Injects the sidebar + topbar into any page that includes:
     <div id="app-sidebar"></div>
     <div id="app-topbar" data-title-key="..." data-subtitle-key="..."></div>
   Keeps navigation, icons and badges identical across every page.
   ========================================================================== */

const NAV_ITEMS = [
  { id: "dashboard", labelKey: "dashboard", href: "dashboard.html", icon: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5"/>' },
  { id: "upload", labelKey: "upload_report", href: "upload.html", icon: '<path d="M12 15V4M12 4 8 8M12 4l4 4"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>' },
  { id: "reports", labelKey: "my_reports", href: "reports.html", icon: '<path d="M7 3h7l4 4v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z"/><path d="M9 12h6M9 16h6M9 8h2"/>' },
  { id: "history", labelKey: "report_history", href: "history.html", icon: '<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/><path d="M12 7v5l3 3"/>' },
  { id: "health", labelKey: "health_summary", href: "health.html", icon: '<path d="M20.5 5.5a5 5 0 0 0-8.5-3 5 5 0 0 0-8.5 3c0 6 8.5 12 8.5 12s8.5-6 8.5-12Z"/><path d="M8 12h2l1.5-3 2 5 1.2-2h1.8"/>' },
  { id: "hospitals", labelKey: "nearby_services", href: "hospitals.html", icon: '<path d="M12 21s-7-5.2-7-10.5A7 7 0 0 1 19 10.5C19 15.8 12 21 12 21Z"/><circle cx="12" cy="10.5" r="2.3"/>' },
  { id: "notifications", labelKey: "notifications", href: "notifications.html", icon: '<path d="M6 9a6 6 0 1 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z"/><path d="M10 20a2 2 0 0 0 4 0"/>', badge: true },
  { id: "profile", labelKey: "profile_settings", href: "profile.html", icon: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>' },
  { id: "settings", labelKey: "settings", href: "settings.html", icon: '<path d="M12 2.8v2.2M12 18.9v2.3M4.7 4.7l1.5 1.5M17.8 17.8l1.5 1.5M2.8 12h2.2M18.9 12h2.3M4.7 19.3l1.5-1.5M17.8 6.2l1.5-1.5"/><circle cx="12" cy="12" r="3.2"/>' },
  { id: "support", labelKey: "help_support", href: "support.html", icon: '<circle cx="12" cy="12" r="9"/><path d="M9.2 9a2.8 2.8 0 0 1 5.4 1c0 1.8-2.6 2-2.6 3.6"/><path d="M12 17h.01"/>' }
];

function svgIcon(pathData) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${pathData}</svg>`;
}

function renderSidebar(activeId) {
  const mount = document.getElementById("app-sidebar");
  if (!mount) return;

  const notifCount = localStorage.getItem("medidecode_notif_count") || "3";

  const items = NAV_ITEMS.map((item) => {
    const isActive = item.id === activeId;
    const badge = item.badge && Number(notifCount) > 0
      ? `<span class="nav-badge">${notifCount}</span>`
      : "";
    return `
      <a class="nav-item${isActive ? " active" : ""}" href="${item.href}">
        ${svgIcon(item.icon)}
        <span>${t(item.labelKey)}</span>
        ${badge}
      </a>`;
  }).join("");

  mount.innerHTML = `
    <div class="sidebar-logo">
      <div class="sidebar-logo-icon">${svgIcon('<path d="M12 2 4 5v6c0 5.2 3.4 9.9 8 11 4.6-1.1 8-5.8 8-11V5l-8-3Z"/><path d="M7.5 12.5h2.2l1.3-3 2 6 1.3-3h2.2"/>')}</div>
      <div class="sidebar-logo-text">
        <div class="brand">MediDecode</div>
        <div class="sub">${t("report_simplifier")}</div>
      </div>
    </div>
    <div class="nav-group">${items}</div>
    <a class="nav-item logout" href="#" id="logout-link">
      ${svgIcon('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>')}
      <span>${t("logout")}</span>
    </a>
    <div class="sidebar-promo">
      <div class="sidebar-promo-icon">🩺</div>
      <h4>${t("take_care_health")}</h4>
      <p>${t("simplify_reports")}</p>
    </div>`;

  document.getElementById("logout-link").addEventListener("click", (e) => {
    e.preventDefault();
    localStorage.removeItem("medidecode_token");
    window.location.href = "login.html";
  });
}

function renderTopbar() {
  const mount = document.getElementById("app-topbar");
  if (!mount) return;

  const name = localStorage.getItem("medidecode_name") || "Guest";
  const lang = getCurrentLanguage();
  const notifCount = localStorage.getItem("medidecode_notif_count") || "3";
  const initial = name.charAt(0).toUpperCase();

  const titleKey = mount.dataset.titleKey;
  const subtitleKey = mount.dataset.subtitleKey;

  const title = titleKey ? t(titleKey, { NAME: name }) : (mount.dataset.title || "Dashboard");
  const subtitle = subtitleKey ? t(subtitleKey) : (mount.dataset.subtitle || "");

  mount.innerHTML = `
    <div class="topbar-title">
      <h1>${title}</h1>
      ${subtitle ? `<p>${subtitle}</p>` : ""}
    </div>
    <div class="topbar-actions">
      <a class="pill-select" href="language.html" aria-label="Change language">
        ${svgIcon('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>')}
        <span>${getLanguageName(lang)}</span>
      </a>
      <a class="icon-btn" href="notifications.html">
        ${svgIcon('<path d="M6 9a6 6 0 1 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z"/><path d="M10 20a2 2 0 0 0 4 0"/>')}
        ${Number(notifCount) > 0 ? `<span class="dot">${notifCount}</span>` : ""}
      </a>
      <a class="avatar-chip" href="profile.html">
        <div class="avatar-circle">${initial}</div>
        <span style="font-weight:600;font-size:14px;">${name}</span>
        ${svgIcon('<path d="m6 9 6 6 6-6"/>')}
      </a>
    </div>`;
}

function requireAuth() {
  const publicPages = ["index.html", "language.html", "login.html", "signup.html", ""];
  const page = window.location.pathname.split("/").pop();
  if (publicPages.includes(page)) return;
  if (!localStorage.getItem("medidecode_token")) {
    window.location.href = "login.html";
  }
}

function showToast(message) {
  let toast = document.querySelector(".toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

function applyDarkModePreference() {
  const isDark = localStorage.getItem("medidecode_dark") === "true";
  document.body.classList.toggle("dark-theme", isDark);
  document.documentElement.style.colorScheme = isDark ? "dark" : "light";
}

document.addEventListener("DOMContentLoaded", () => {
  applyDarkModePreference();
  requireAuth();
  const sidebarMount = document.getElementById("app-sidebar");
  if (sidebarMount) renderSidebar(sidebarMount.dataset.active);
  renderTopbar();
});
