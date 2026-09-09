/**
 * MBA EDITORIAL DAILY - EDITORIAL LOADER MODULE
 * Fetches index.json and renders exact 5-section MBA study guide format.
 */

const EditorialLoader = {
  async init(containerId = 'editorial-app', targetSlug = null) {
    const container = document.getElementById(containerId);
    if (!container) return;

    Utils.renderLoading(container);

    try {
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

      let targetMeta = indexData.editorials[0];

      if (targetSlug) {
        const found = indexData.editorials.find(item => item.slug === targetSlug);
        if (found) targetMeta = found;
      }

      const editorialJsonPath = Utils.getRelativePath(`data/editorials/${targetMeta.filePath}`);
      const editorialResponse = await fetch(editorialJsonPath);

      if (!editorialResponse.ok) {
        throw new Error(`Failed to load editorial details: ${editorialResponse.status}`);
      }

      const editorial = await editorialResponse.json();
      document.title = `Day ${editorial.dayNumber || 5}: ${editorial.mainTopic || editorial.title} | MBA Editorial Daily`;

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

  renderEditorial(container, data) {
    const dayNum = data.dayNumber || 5;
    const batchInfo = data.batchInfo || "For: MBA-I Batch (2026-28)";
    const mainTopic = data.mainTopic || data.title;
    const nextDayNum = dayNum + 1;

    // Build Section 1 Items
    let sec1Items = data.section1_simpleSummary || [];
    if (sec1Items.length === 0 && data.summary) {
      if (Array.isArray(data.summary.keyArguments)) {
        sec1Items = data.summary.keyArguments.map((arg, idx) => ({
          boldHeader: `Key Point ${idx + 1}`,
          text: arg
        }));
      }
    }

    // Build Section 2 Items
    let sec2Items = data.section2_mbaRelevance || [];
    if (sec2Items.length === 0 && data.keyTakeaways) {
      sec2Items = data.keyTakeaways.map((takeaway, idx) => ({
        boldHeader: `Management Takeaway ${idx + 1}`,
        text: takeaway
      }));
    }

    // Build Section 5 Keywords
    let keywords = data.section5_keywords || [];
    if (keywords.length === 0 && data.terminologies) {
      keywords = data.terminologies.map(t => ({
        word: t.term || t.word,
        simpleMeaning: t.simpleMeaning || t.simpleExplanation || t.definition
      }));
    }

    container.innerHTML = `
      <div class="editorial-analysis-wrapper">
        <div class="container">
          
          <!-- Top Day Header -->
          <header class="day-analysis-header">
            <div class="day-pill-badge">DAY ${dayNum}</div>
            <h1 class="header-main-title">The Indian Express Editorial Analysis</h1>
            
            <div class="meta-sub-bar">
              <span>Date: ${Utils.formatDate(data.date)}</span>
              <span class="meta-divider">|</span>
              <span>${Utils.escapeHTML(batchInfo)}</span>
            </div>

            <div class="main-topic-callout">
              Today's Main Topic: <em><strong>${Utils.escapeHTML(mainTopic)}</strong></em>
            </div>

            <div class="read-original-wrap">
              <a href="${Utils.escapeHTML(data.source.url)}" target="_blank" rel="noopener noreferrer" class="read-original-link">
                [Read the full editorial here (The Indian Express)] →
              </a>
            </div>
          </header>

          <!-- 1. What Does the Editorial Say? -->
          <section class="analysis-section-card">
            <h2 class="section-heading-numbered">1. What Does the Editorial Say? (Simple Summary)</h2>
            <p class="section-intro-lead">Today's paper looks at key national developments:</p>
            
            <ul class="analysis-bullets-list">
              ${sec1Items.map(item => `
                <li>
                  <strong>${Utils.escapeHTML(item.boldHeader)}:</strong> ${Utils.escapeHTML(item.text)}
                </li>
              `).join('')}
            </ul>
          </section>

          <!-- 2. What Is In It For You, As an MBA-I Student? -->
          <section class="analysis-section-card">
            <h2 class="section-heading-numbered">2. What Is In It For You, As an MBA-I Student?</h2>
            
            <ul class="analysis-bullets-list">
              ${sec2Items.map(item => `
                <li>
                  <strong>${Utils.escapeHTML(item.boldHeader)}:</strong> ${Utils.escapeHTML(item.text)}
                </li>
              `).join('')}
            </ul>
          </section>

          <!-- 3. How Daily News Reading Broadens Your Thinking -->
          <section class="analysis-section-card">
            <h2 class="section-heading-numbered">3. How Daily News Reading Broadens Your Thinking</h2>
            <p class="broadening-thinking-text">
              ${Utils.escapeHTML(data.section3_broadeningThinking || data.introduction)}
            </p>
          </section>

          <!-- 4. Question of the Day -->
          <section class="analysis-section-card question-box-card">
            <h2 class="section-heading-numbered" style="color: #78350f;">4. Question of the Day (Think About It - We Will Discuss)</h2>
            <p class="question-quote">
              "${Utils.escapeHTML(data.section4_questionOfTheDay || (data.discussionQuestion ? data.discussionQuestion.question : ''))}"
            </p>
          </section>

          <!-- 5. Keywords and Hard Words -->
          <section class="analysis-section-card">
            <h2 class="section-heading-numbered">5. Keywords and Hard Words (Simple Meanings)</h2>
            <p class="keywords-subtitle"><em>Learn these words today. They will come again and again in your MBA journey.</em></p>
            
            <div class="table-responsive-container">
              <table class="keywords-table">
                <thead>
                  <tr>
                    <th>Word</th>
                    <th>Simple Meaning</th>
                  </tr>
                </thead>
                <tbody>
                  ${keywords.map(kw => `
                    <tr>
                      <td class="word-col"><strong>${Utils.escapeHTML(kw.word || kw.term)}</strong></td>
                      <td class="meaning-col">${Utils.escapeHTML(kw.simpleMeaning || kw.simpleExplanation || kw.definition)}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </section>

          <!-- Bottom Streak Progress Bar -->
          <div class="streak-completion-footer">
            🔥 <strong>Day ${dayNum} complete.</strong> Ten minutes a day, every day. See you tomorrow for Day ${nextDayNum}.
          </div>

        </div>
      </div>
    `;
  }
};
