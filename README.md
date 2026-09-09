# MBA Editorial Daily 🎓

An automated, lightweight, static educational platform and daily pipeline that collects editorials from **The Indian Express**, processes them using **Google Gemini AI**, and publishes MBA-focused educational summaries for first-year business students.

---

## 🏗️ System Architecture

```text
                                AUTOMATION PIPELINE


          The Indian Express Editorial Section
                        │
                        ▼
              Python Editorial Discovery
                        │
                        ▼
              Article URL Identification
                        │
                        ▼
              Duplicate Detection
                        │
                        ▼
               Article Content Extraction
                        │
                        ▼
                  Content Cleaning
                        │
                        ▼
                    Gemini API
                        │
                        ▼
             MBA-focused AI Analysis
                        │
                        ▼
              Structured JSON Output
                        │
                        ▼
            JSON Validation and Cleaning
                        │
                        ▼
          Save Editorial JSON in Repository
                        │
                        ▼
                Update index.json
                        │
                        ▼
                Git Commit and Push
                        │
                        ▼
                 GitHub Pages Deploy
                        │
                        ▼
                    LIVE WEBSITE
```

---

## 🚀 Key Features

* **MBA 1st-Year Subject Connections:** Maps daily public policy and economic news directly to core subjects (*Managerial Economics, Business Environment, Strategic Management, Financial Systems*).
* **Simplified Jargon Explanations:** Extracts key business, economic, and political terms into student-friendly cards with examples.
* **100% Static & Lightweight:** Built using standard HTML5, CSS3, Vanilla JS, and static JSON databases hosted directly on GitHub Pages. No Node.js server, React overhead, or database servers required.
* **Zero Maintenance Daily Automation:** Scheduled GitHub Actions runner handles discovery, AI generation, JSON indexing, git commits, and live site deployment every morning at 8:00 AM IST (02:30 UTC).
* **Strict API Key Security:** Gemini API keys are maintained exclusively inside GitHub Secrets (`GEMINI_API_KEY`) and are never exposed to browser code or public commits.

---

## 🛠️ Technology Stack

* **Frontend:** HTML5, CSS3 (Vanilla design system with CSS Variables, Flexbox, Grid), Vanilla JavaScript (Fetch API, ES6 modules).
* **Automation Backend:** Python 3.11+, `requests`, `beautifulsoup4`, official Google Gemini SDK (`google-genai`), `python-dotenv` (local dev).
* **Database:** Git Repository JSON Database (`data/editorials/index.json`, `data/glossary.json`, year/month partitioned JSON files).
* **Hosting & CI/CD:** GitHub Actions & GitHub Pages.

---


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
