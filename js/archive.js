/**
 * MBA EDITORIAL DAILY - ARCHIVE PAGE MODULE
 * Multi-faceted filtering, searching, and pagination of editorial records.
 */

const ArchivePage = {
  allEditorials: [],
  filteredEditorials: [],

  async init(containerId = 'archive-list-container') {
    const container = document.getElementById(containerId);
    if (!container) return;

    Utils.renderLoading(container);

    try {
      const indexPath = Utils.getRelativePath('data/editorials/index.json') + '?t=' + Date.now();
      const response = await fetch(indexPath, { cache: 'no-cache' });
      
      if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
      
      const indexData = await response.json();
      this.allEditorials = indexData.editorials || [];
      this.filteredEditorials = [...this.allEditorials];

      // Populate filter dropdown choices dynamically
      this.populateFilterDropdowns();

      // Bind search & filter input events
      this.bindEvents();

      // Render initial cards list
      this.render();

    } catch (error) {
      console.error('Error fetching archive index:', error);
      Utils.renderError(
        container,
        'Unable to Load Archive',
        'Could not load the editorial archive repository. Please try again later.',
        () => this.init(containerId)
      );
    }
  },

  populateFilterDropdowns() {
    const yearSelect = document.getElementById('filter-year');
    const tagSelect = document.getElementById('filter-tag');

    if (yearSelect) {
      const years = Array.from(new Set(this.allEditorials.map(e => e.date ? e.date.substring(0, 4) : null))).filter(Boolean);
      years.sort((a, b) => b - a);
      years.forEach(yr => {
        const opt = document.createElement('option');
        opt.value = yr;
        opt.textContent = yr;
        yearSelect.appendChild(opt);
      });
    }

    if (tagSelect) {
      const allTags = new Set();
      this.allEditorials.forEach(e => {
        if (Array.isArray(e.tags)) e.tags.forEach(t => allTags.add(t));
      });
      Array.from(allTags).sort().forEach(tag => {
        const opt = document.createElement('option');
        opt.value = tag;
        opt.textContent = tag;
        tagSelect.appendChild(opt);
      });
    }
  },

  bindEvents() {
    const searchInput = document.getElementById('archive-search');
    const yearSelect = document.getElementById('filter-year');
    const monthSelect = document.getElementById('filter-month');
    const tagSelect = document.getElementById('filter-tag');
    const difficultySelect = document.getElementById('filter-difficulty');

    const handleFilterChange = () => {
      const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
      const year = yearSelect ? yearSelect.value : '';
      const month = monthSelect ? monthSelect.value : '';
      const tag = tagSelect ? tagSelect.value : '';
      const difficulty = difficultySelect ? difficultySelect.value : '';

      this.filteredEditorials = this.allEditorials.filter(item => {
        // Search title query
        const matchesQuery = !query || item.title.toLowerCase().includes(query) || (item.tags && item.tags.some(t => t.toLowerCase().includes(query)));
        
        // Date year & month filtering
        const itemYear = item.date ? item.date.substring(0, 4) : '';
        const itemMonth = item.date ? item.date.substring(5, 7) : '';
        
        const matchesYear = !year || itemYear === year;
        const matchesMonth = !month || itemMonth === month;
        const matchesTag = !tag || (item.tags && item.tags.includes(tag));
        const matchesDifficulty = !difficulty || item.difficulty === difficulty;

        return matchesQuery && matchesYear && matchesMonth && matchesTag && matchesDifficulty;
      });

      this.render();
    };

    if (searchInput) searchInput.addEventListener('input', handleFilterChange);
    if (yearSelect) yearSelect.addEventListener('change', handleFilterChange);
    if (monthSelect) monthSelect.addEventListener('change', handleFilterChange);
    if (tagSelect) tagSelect.addEventListener('change', handleFilterChange);
    if (difficultySelect) difficultySelect.addEventListener('change', handleFilterChange);
  },

  render() {
    const container = document.getElementById('archive-list-container');
    const countEl = document.getElementById('archive-count');

    if (countEl) {
      countEl.textContent = `Showing ${this.filteredEditorials.length} of ${this.allEditorials.length} Editorials`;
    }

    if (!container) return;

    if (this.filteredEditorials.length === 0) {
      container.innerHTML = `
        <div class="error-state" style="grid-column: 1 / -1;">
          <div class="error-icon">🔍</div>
          <h3 class="error-title">No Matching Editorials Found</h3>
          <p class="error-desc">Try resetting your filters or search keywords to view available summaries.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = this.filteredEditorials.map(item => {
      const tags = (item.tags || []).map(t => `<span class="badge badge-blue">${Utils.escapeHTML(t)}</span>`).join(' ');
      const difficulty = item.difficulty ? `<span class="badge badge-slate">${Utils.escapeHTML(item.difficulty)}</span>` : '';

      return `
        <article class="card" style="display:flex; flex-direction:column; justify-between; gap:1rem;">
          <div>
            <div style="display:flex; justify-between; align-items:center; margin-bottom:0.75rem; font-size:0.85rem; color:var(--text-muted);">
              <span>📅 ${Utils.formatDate(item.date)}</span>
              ${difficulty}
            </div>
            <h3 style="font-size:1.2rem; line-height:1.35; margin-bottom:0.75rem; color:var(--text-primary);">
              <a href="editorial.html?slug=${encodeURIComponent(item.slug)}" style="color:inherit;">
                ${Utils.escapeHTML(item.title)}
              </a>
            </h3>
            <div style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-bottom:1rem;">
              ${tags}
            </div>
          </div>
          <div style="margin-top:auto; padding-top:0.75rem; border-top:1px solid var(--border-light); display:flex; justify-between; align-items:center;">
            <a href="editorial.html?slug=${encodeURIComponent(item.slug)}" class="btn btn-outline btn-sm">
              Read Educational Summary →
            </a>
          </div>
        </article>
      `;
    }).join('');
  }
};
