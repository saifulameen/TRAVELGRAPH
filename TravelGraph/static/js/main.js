/*
  main.js
  Global site behaviour: mobile nav toggle, dark mode toggle.
*/

document.addEventListener('DOMContentLoaded', () => {
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
    });
  }

  const themeToggle = document.getElementById('themeToggle');
  const body = document.body;

  // Restore saved theme preference.
  const savedTheme = window.__tgTheme || null;
  if (savedTheme === 'dark') {
    body.setAttribute('data-theme', 'dark');
    if (themeToggle) themeToggle.textContent = '☀️';
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const isDark = body.getAttribute('data-theme') === 'dark';
      if (isDark) {
        body.setAttribute('data-theme', 'light');
        themeToggle.textContent = '🌙';
        window.__tgTheme = 'light';
      } else {
        body.setAttribute('data-theme', 'dark');
        themeToggle.textContent = '☀️';
        window.__tgTheme = 'dark';
      }
    });
  }
});
