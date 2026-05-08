(function () {
  const printButton = document.querySelector("[data-print]");
  if (printButton) printButton.addEventListener("click", () => window.print());

  const navLinks = Array.from(document.querySelectorAll(".card-nav a"));
  const sections = Array.from(document.querySelectorAll(".card"));

  document.querySelectorAll("[data-detail]").forEach((button) => {
    button.addEventListener("click", () => {
      const section = button.closest(".card");
      const drawer = section && section.querySelector(".detail-drawer");
      if (!drawer) return;

      drawer.textContent = button.getAttribute("data-detail") || "";
      drawer.classList.add("is-filled");
      drawer.setAttribute("tabindex", "-1");
      drawer.focus({ preventScroll: true });
    });
  });

  if (!("IntersectionObserver" in window)) {
    sections.forEach((section) => section.classList.add("is-visible"));
    return;
  }

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  sections.forEach((section) => revealObserver.observe(section));

  const activeObserver = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

    if (!visible) return;
    navLinks.forEach((link) => {
      link.classList.toggle("active", link.getAttribute("href") === "#" + visible.target.id);
    });
  }, { threshold: [0.35, 0.55, 0.75] });
  sections.forEach((section) => activeObserver.observe(section));
})();
