/**
 * MBA EDITORIAL DAILY - MAIN APP ENTRY POINT
 * Initializes mobile navigation, active tab highlight, and page router.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile Navigation Drawer Toggle
  const navToggle = document.getElementById('mobile-nav-toggle');
  const mainNav = document.getElementById('main-nav');

  if (navToggle && mainNav) {
    navToggle.addEventListener('click', () => {
      mainNav.classList.toggle('is-open');
      const isOpen = mainNav.classList.contains('is-open');
      navToggle.setAttribute('aria-expanded', isOpen);
      navToggle.innerHTML = isOpen ? '✕' : '☰';
    });
  }

  // Active Navigation Link Highlight
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  const navLinks = document.querySelectorAll('.nav-link');
  
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (currentPath === '' && href === 'index.html')) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Page Initialization Dispatcher
  if (document.getElementById('homepage-editorial-app')) {
    EditorialLoader.init('homepage-editorial-app');
  } else if (document.getElementById('detail-editorial-app')) {
    const slug = Utils.getQueryParam('slug');
    EditorialLoader.init('detail-editorial-app', slug);
  } else if (document.getElementById('archive-list-container')) {
    ArchivePage.init('archive-list-container');
  } else if (document.getElementById('glossary-container')) {
    GlossaryPage.init('glossary-container');
  }
});
