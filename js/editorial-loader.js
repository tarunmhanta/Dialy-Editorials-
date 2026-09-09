/**
 * MBA EDITORIAL DAILY - EDITORIAL LOADER MODULE
 * Fetches JSON index, loads target editorial, and renders dynamic HTML content.
 */

const EditorialLoader = {
  /**
   * Initializes homepage or detail page loading
   * @param {string} containerId - Target HTML element ID for rendering
   * @param {string|null} targetSlug - Optional slug filter for specific editorial detail view
   */
  async init(containerId = 'editorial-app', targetSlug = null) {
    const container = document.getElementById(containerId);
    if (!container) return;

    Utils.renderLoading(container);

    try {
      // Step 1: Fetch index.json
      const indexPath = Utils.getRelativePath('data/editorials/index.json');
      const indexResponse = await fetch(indexPath, { cache: 'no-cache' });
      
      if (!indexResponse.ok) {
        throw new Error(`HTTP error! status: ${indexResponse.status}`);
      }

      const indexData = await indexResponse.json();

      if (!indexData || !Array.isArray(indexData.editorials) || indexData.editorials.length === 0) {
        Utils.renderEmpty(container);
        return;
      }

      // Step 2: Determine which editorial to load
      let targetMeta = indexData.editorials[0]; // Default to latest

      if (targetSlug) {
        const found = indexData.editorials.find(item => item.slug === targetSlug);
        if (found) targetMeta = found;
      }

      // Step 3: Fetch detailed editorial JSON file
      const editorialJsonPath = Utils.getRelativePath(`data/editorials/${targetMeta.filePath}`);
      const editorialResponse = await fetch(editorialJsonPath);

      if (!editorialResponse.ok) {
        throw new Error(`Failed to load editorial details: ${editorialResponse.status}`);
      }

      const editorial = await editorialResponse.json();

      // Step 4: Update document page title for SEO
      document.title = `${editorial.title} | MBA Editorial Daily`;

      // Step 5: Render full editorial UI
      this.renderEditorial(container, editorial);

    } catch (error) {
      console.error('Error loading editorial:', error);
      Utils.renderError(
        container,
        'Unable to Load Editorial',
        'We encountered an issue fetching today\'s editorial data. Please check back shortly.',
        () => this.init(containerId, targetSlug)
      );
    }
  },

  /**
   * Renders complete editorial layout
   * @param {HTMLElement} container 
   * @param {Object} data - Editorial JSON object
   */
  renderEditorial(container, data) {
    const tagsHtml = (data.tags || []).map(tag => 
      `<span class="badge badge-blue">${Utils.escapeHTML(tag)}</span>`
    ).join(' ');

    const difficultyBadge = data.difficulty ? 
      `<span class="badge badge-slate">Level: ${Utils.escapeHTML(data.difficulty)}</span>` : '';

    const readingTimeBadge = data.readingTimeMinutes ?
      `<span class="badge badge-amber">⏱️ ${data.readingTimeMinutes} min read</span>` : '';

    // Render HTML structure
    container.innerHTML = `
      <!-- Hero Header Section -->
      <header class="hero-section">
        <div class="container">
          <div class="hero-meta-bar">
            <span class="today-tag">
              <span style="display:inline-block; width:8px; height:8px; background-color:var(--brand-emerald); border-radius:50%;"></span>
              Editorial Analysis
            </span>
            <div style="display:flex; gap:0.5rem; flex-wrap:wrap; align-items:center;">
              <span style="font-size:0.875rem; color:var(--text-muted); font-weight:500;">
                📅 ${Utils.formatDate(data.date)}
              </span>
              ${difficultyBadge}
              ${readingTimeBadge}
            </div>
          </div>

          <h1 class="editorial-header-title">${Utils.escapeHTML(data.title)}</h1>
          
          <div style="margin-top: 0.75rem;">
            ${tagsHtml}
          </div>

          <!-- Source Attribution Card -->
          <div class="source-attribution-card">
            <div class="source-info">
              <span class="source-name">Source: ${Utils.escapeHTML(data.source.name || 'Indian Express')}</span>
              ${data.source.author ? `<span class="source-author">By ${Utils.escapeHTML(data.source.author)}</span>` : ''}
            </div>
            <a href="${Utils.escapeHTML(data.source.url)}" target="_blank" rel="noopener noreferrer" class="source-link-btn">
              Read Original Editorial on Indian Express →
            </a>
          </div>
        </div>
      </header>

      <!-- Main Editorial Content Body -->
      <div class="container">
        <div class="editorial-container">

          <!-- Section 1: Introduction -->
          ${data.introduction ? `
          <section class="section-block">
            <div class="section-title-wrap">
              <div class="section-icon">💡</div>
              <h2 class="section-heading">Why This Editorial?</h2>
            </div>
            <div class="editorial-intro-p">
              ${Utils.escapeHTML(data.introduction)}
            </div>
          </section>
          ` : ''}

          <!-- Section 2: Simplified Summary -->
          <section class="section-block">
            <div class="section-title-wrap">
              <div class="section-icon">📖</div>
              <h2 class="section-heading">Editorial in Simple Words</h2>
            </div>

            <div class="summary-grid">
              ${data.summary.overview ? `
              <div class="summary-card-sub">
                <h4>📌 Overview</h4>
                <p style="color:var(--text-secondary); font-size:0.975rem; line-height:1.7;">
                  ${Utils.escapeHTML(data.summary.overview)}
                </p>
              </div>
              ` : ''}

              ${data.summary.howItIntroducesTheTopic ? `
              <div class="summary-card-sub">
                <h4>🎯 Context & Issue Framing</h4>
                <p style="color:var(--text-secondary); font-size:0.95rem; line-height:1.6;">
                  ${Utils.escapeHTML(data.summary.howItIntroducesTheTopic)}
                </p>
              </div>
              ` : ''}

              ${Array.isArray(data.summary.keyArguments) && data.summary.keyArguments.length > 0 ? `
              <div class="summary-card-sub">
                <h4>⚖️ Major Arguments</h4>
                <ul class="summary-list">
                  ${data.summary.keyArguments.map(arg => `<li>${Utils.escapeHTML(arg)}</li>`).join('')}
                </ul>
              </div>
              ` : ''}

              ${Array.isArray(data.summary.importantFacts) && data.summary.importantFacts.length > 0 ? `
              <div class="summary-card-sub">
                <h4>📊 Key Facts & Policy Context</h4>
                <ul class="summary-list">
                  ${data.summary.importantFacts.map(fact => `<li>${Utils.escapeHTML(fact)}</li>`).join('')}
                </ul>
              </div>
              ` : ''}

              ${data.summary.conclusion ? `
              <div class="summary-card-sub" style="border-left: 3px solid var(--brand-emerald);">
                <h4>🏁 Editorial Conclusion</h4>
                <p style="color:var(--text-primary); font-weight:500; font-size:0.95rem; line-height:1.6;">
                  ${Utils.escapeHTML(data.summary.conclusion)}
                </p>
              </div>
              ` : ''}
            </div>
          </section>

          <!-- Section 3: MBA Relevance Section -->
          <section class="mba-relevance-box">
            <h3>🎓 Why Should an MBA Student Care?</h3>
            <p class="mba-relevance-desc">${Utils.escapeHTML(data.mbaRelevance.importance)}</p>

            <div style="margin-bottom: 1.5rem;">
              <h4 style="color:#94a3b8; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.75rem;">
                Related MBA 1st-Year Subjects
              </h4>
              <div class="mba-tags-row">
                ${(data.mbaRelevance.subjects || []).map(sub => 
                  `<span class="mba-subject-pill">📘 ${Utils.escapeHTML(sub)}</span>`
                ).join('')}
              </div>
            </div>

            <div style="margin-bottom: 1.5rem;">
              <h4 style="color:#94a3b8; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.75rem;">
                Core Management Concepts
              </h4>
              <div class="mba-tags-row">
                ${(data.mbaRelevance.managementConcepts || []).map(concept => 
                  `<span class="mba-concept-pill">🧩 ${Utils.escapeHTML(concept)}</span>`
                ).join('')}
              </div>
            </div>

            ${data.mbaRelevance.practicalBusinessConnection ? `
            <div class="practical-connection-card">
              <h4>🏢 Practical Business & Managerial Impact</h4>
              <p>${Utils.escapeHTML(data.mbaRelevance.practicalBusinessConnection)}</p>
            </div>
            ` : ''}
          </section>

          <!-- Section 4: Key Takeaways -->
          ${Array.isArray(data.keyTakeaways) && data.keyTakeaways.length > 0 ? `
          <section class="section-block">
            <div class="section-title-wrap">
              <div class="section-icon">🚀</div>
              <h2 class="section-heading">Key Learning Takeaways</h2>
            </div>
            <div class="takeaways-grid">
              ${data.keyTakeaways.map((item, idx) => `
                <div class="takeaway-card">
                  <div class="takeaway-num">${idx + 1}</div>
                  <div class="takeaway-text">${Utils.escapeHTML(item)}</div>
                </div>
              `).join('')}
            </div>
          </section>
          ` : ''}

          <!-- Section 5: Important Terminologies -->
          ${Array.isArray(data.terminologies) && data.terminologies.length > 0 ? `
          <section class="section-block">
            <div class="section-title-wrap">
              <div class="section-icon">📚</div>
              <h2 class="section-heading">Important Terms You Should Know</h2>
            </div>
            <div class="terms-grid">
              ${data.terminologies.map(term => `
                <div class="term-card">
                  <div class="term-header">
                    <span class="term-title">${Utils.escapeHTML(term.term)}</span>
                  </div>
                  <div class="term-def">" ${Utils.escapeHTML(term.definition)} "</div>
                  <div class="term-simple">
                    <strong>Simple Explanation:</strong> ${Utils.escapeHTML(term.simpleExplanation)}
                  </div>
                  ${term.example ? `
                  <div class="term-example">
                    💡 <strong>Example:</strong> ${Utils.escapeHTML(term.example)}
                  </div>
                  ` : ''}
                </div>
              `).join('')}
            </div>
          </section>
          ` : ''}

          <!-- Section 6: Think Like a Manager Discussion Question -->
          ${data.discussionQuestion ? `
          <section class="discussion-box">
            <div class="section-title-wrap" style="border-bottom-color: #fde68a;">
              <div class="section-icon" style="background-color:#fef3c7; color:#b45309;">🧠</div>
              <h2 class="section-heading" style="color:#78350f;">Think Like a Manager</h2>
            </div>
            <p class="discussion-question-text">
              "${Utils.escapeHTML(data.discussionQuestion.question)}"
            </p>
            ${data.discussionQuestion.whyThinkAboutIt ? `
            <div class="discussion-why">
              💡 <strong>Why Consider This?</strong> ${Utils.escapeHTML(data.discussionQuestion.whyThinkAboutIt)}
            </div>
            ` : ''}
          </section>
          ` : ''}

        </div>
      </div>
    `;
  }
};
