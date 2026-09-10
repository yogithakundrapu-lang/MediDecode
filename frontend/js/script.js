/* ==========================================================================
   MediDecode — Shared JavaScript
   Vanilla JS only. Each page includes this file; page-specific logic is
   guarded by checking for the relevant element so it's safe to share.
   ========================================================================== */

/* ---------- Splash screen: redirect to language selection ---------- */
(function initSplash() {
  const splash = document.querySelector("[data-splash]");
  if (!splash) return;

  const SPLASH_DURATION_MS = 2400;

  setTimeout(() => {
    window.location.href = "language.html";
  }, SPLASH_DURATION_MS);

  // Allow skipping the splash screen with a tap/click
  splash.addEventListener("click", () => {
    window.location.href = "language.html";
  });
})();
