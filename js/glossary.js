/**
 * MBA EDITORIAL DAILY - GLOSSARY PAGE MODULE
 * Dynamically aggregates, sorts, and renders business/economics terms.
 */

const GlossaryPage = {
  allTerms: [],
  filteredTerms: [],

  async init(containerId = 'glossary-container') {
    const container = document.getElementById(containerId);
    if (!container) return;

    Utils.renderLoading(container);

    try {
      const glossaryPath = Utils.getRelativePath('data/glossary.json');
      const response = await fetch(glossaryPath, { cache: 'no-cache' });

      if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

      const data = await response.json();
      this.allTerms = data.terms || [];
      
      // Sort alphabetically by term name
      this.allTerms.sort((a, b) => a.term.localeCompare(b.term));
      this.filteredTerms = [...this.allTerms];

      this.renderAlphabetBar();
      this.bindEvents();
      this.render();

    } catch (error) {
      console.error('Error loading glossary data:', error);
      Utils.renderError(
        container,
        'Unable to Load Glossary',
        'Could not fetch terminology dictionary. Please try again later.',
        () => this.init(containerId)
      );
    }
  },

  renderAlphabetBar() {
    const bar = document.getElementById('alphabet-bar');
    if (!bar) return;

    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
    const availableLetters = new Set(this.allTerms.map(t => t.term.charAt(0).toUpperCase()));

    let html = `<button class="btn btn-sm btn-primary filter-letter-btn active" data-letter="ALL">ALL</button>`;
    
    alphabet.forEach(letter => {
      const isAvailable = availableLetters.has(letter);
      html += `
        <button class="btn btn-sm ${isAvailable ? 'btn-outline' : 'btn-outline disabled'}" 
                data-letter="${letter}" 
                ${!isAvailable ? 'disabled style="opacity:0.4; cursor:default;"' : ''}>
          ${letter}
        </button>
      `;
    });

    bar.innerHTML = html;

    bar.addEventListener('click', (e) => {
      if (e.target.tagName === 'BUTTON' && !e.target.disabled) {
        const letter = e.target.getAttribute('data-letter');
        
        bar.querySelectorAll('.filter-letter-btn').forEach(btn => btn.classList.remove('active', 'btn-primary'));
        e.target.classList.add('active', 'btn-primary');

        if (letter === 'ALL') {
          this.filteredTerms = [...this.allTerms];
        } else {
          this.filteredTerms = this.allTerms.filter(t => t.term.charAt(0).toUpperCase() === letter);
        }

        this.render();
      }
    });
  },

  bindEvents() {
    const searchInput = document.getElementById('glossary-search');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      this.filteredTerms = this.allTerms.filter(t => 
        t.term.toLowerCase().includes(query) || 
        (t.definition && t.definition.toLowerCase().includes(query)) ||
        (t.simpleExplanation && t.simpleExplanation.toLowerCase().includes(query))
      );
      this.render();
    });
  },

  render() {
    const container = document.getElementById('glossary-container');
    const countEl = document.getElementById('glossary-count');

    if (countEl) {
      countEl.textContent = `Showing ${this.filteredTerms.length} of ${this.allTerms.length} Terms`;
    }

    if (!container) return;

    if (this.filteredTerms.length === 0) {
      container.innerHTML = `
        <div class="error-state" style="grid-column:1 / -1;">
          <div class="error-icon">📖</div>
          <h3 class="error-title">No Terms Found</h3>
          <p class="error-desc">No glossary terminology matches your current filter or search criteria.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = this.filteredTerms.map(term => {
      const editorialsHtml = Array.isArray(term.editorials) && term.editorials.length > 0 ? `
        <div style="margin-top:0.75rem; font-size:0.85rem; color:var(--text-muted);">
          📍 <strong>Featured in:</strong> 
          ${term.editorials.map(ed => 
            `<a href="editorial.html?slug=${encodeURIComponent(ed.slug)}">${Utils.escapeHTML(ed.title || ed.slug)}</a>`
          ).join(', ')}
        </div>
      ` : '';

      return `
        <article class="term-card">
          <div class="term-header">
            <h3 class="term-title">${Utils.escapeHTML(term.term)}</h3>
          </div>
          ${term.definition ? `<div class="term-def">" ${Utils.escapeHTML(term.definition)} "</div>` : ''}
          ${term.simpleExplanation ? `
            <div class="term-simple">
              <strong>Simple Explanation:</strong> ${Utils.escapeHTML(term.simpleExplanation)}
            </div>
          ` : ''}
          ${editorialsHtml}
        </article>
      `;
    }).join('');
  }
};
