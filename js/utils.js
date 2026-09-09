/**
 * MBA EDITORIAL DAILY - UTILITY MODULE
 * Helper functions for UI rendering, URL formatting, date parsing & security
 */

const Utils = {
  /**
   * Safe HTML Escaping to prevent XSS vulnerabilities
   * @param {string} str - Raw string input
   * @returns {string} Safe HTML string
   */
  escapeHTML(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  /**
   * Formats ISO date string into human-readable date
   * Example: "2026-09-09" -> "September 9, 2026"
   * @param {string} dateStr 
   * @returns {string} Formatted date
   */
  formatDate(dateStr) {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return dateStr;
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch (e) {
      return dateStr;
    }
  },

  /**
   * Extract query parameters from window location
   * @param {string} param 
   * @returns {string|null}
   */
  getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
  },

  /**
   * Resolves relative path to support both local dev and GitHub Pages base paths
   * @param {string} relativePath 
   * @returns {string} Normalized fetchable URL
   */
  getRelativePath(relativePath) {
    // Strip leading slashes to prevent root domain resolution issues on GitHub Pages project sites
    const cleanPath = relativePath.startsWith('/') ? relativePath.substring(1) : relativePath;
    return cleanPath;
  },

  /**
   * Renders standardized skeleton loading placeholder into container
   * @param {HTMLElement} container 
   */
  renderLoading(container) {
    if (!container) return;
    container.innerHTML = `
      <div class="skeleton-container" aria-busy="true" aria-live="polite">
        <div class="skeleton-box" style="height: 3rem; width: 75%;"></div>
        <div class="skeleton-box" style="height: 1.5rem; width: 40%;"></div>
        <div class="skeleton-box" style="height: 12rem; width: 100%; margin-top: 1rem;"></div>
        <div class="skeleton-box" style="height: 16rem; width: 100%;"></div>
      </div>
    `;
  },

  /**
   * Renders error UI state with retry capability
   * @param {HTMLElement} container 
   * @param {string} title 
   * @param {string} message 
   * @param {Function} retryCallback 
   */
  renderError(container, title = 'Unable to load content', message = 'Please check your internet connection or try again later.', retryCallback = null) {
    if (!container) return;
    const retryId = 'retry-btn-' + Math.random().toString(36).substring(2, 7);
    container.innerHTML = `
      <div class="error-state" role="alert">
        <div class="error-icon">⚠️</div>
        <h3 class="error-title">${this.escapeHTML(title)}</h3>
        <p class="error-desc">${this.escapeHTML(message)}</p>
        ${retryCallback ? `<button id="${retryId}" class="btn btn-outline btn-sm">🔄 Try Again</button>` : ''}
      </div>
    `;
    if (retryCallback) {
      const btn = document.getElementById(retryId);
      if (btn) btn.addEventListener('click', retryCallback);
    }
  },

  /**
   * Renders empty database state
   * @param {HTMLElement} container 
   * @param {string} title 
   * @param {string} message 
   */
  renderEmpty(container, title = 'No Editorials Available Yet', message = 'The daily automation pipeline runs every morning at 8:00 AM IST. Check back soon!') {
    if (!container) return;
    container.innerHTML = `
      <div class="error-state">
        <div class="error-icon" style="color: var(--brand-accent);">📚</div>
        <h3 class="error-title">${this.escapeHTML(title)}</h3>
        <p class="error-desc">${this.escapeHTML(message)}</p>
      </div>
    `;
  }
};
