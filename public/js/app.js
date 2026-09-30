/**
 * FinNews AI – Client-Side Application Logic
 * Handles asynchronous news retrieval, AI summary rendering, state management, and UI transitions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const fetchBtn = document.getElementById('fetch-btn');
    const articleCountSelect = document.getElementById('article-count');
    const categoryPills = document.querySelectorAll('.cat-pill');
    const loadingState = document.getElementById('loading-state');
    const skeletonGrid = document.getElementById('skeleton-grid');
    const resultsSection = document.getElementById('results-section');
    const resultsHeader = document.getElementById('results-header');
    const articlesContainer = document.getElementById('articles-container');
    const resultsCountBadge = document.getElementById('results-count-badge');
    const resultsModeBadge = document.getElementById('results-mode-badge');
    const modeText = document.getElementById('mode-text');
    const errorBanner = document.getElementById('error-banner');
    const errorMessage = document.getElementById('error-message');
    const errorRetryBtn = document.getElementById('error-retry-btn');
    const systemStatus = document.getElementById('system-status');
    const statusText = document.getElementById('status-text');
    const toastContainer = document.getElementById('toast-container');

    // State Variables
    let selectedCategory = '';
    let isFetching = false;

    // -------------------------------------------------------------------------
    // 1. Initial Health Check
    // -------------------------------------------------------------------------
    async function checkSystemHealth() {
        try {
            let response = await fetch('/health');
            if (!response.ok) {
                response = await fetch('/api/health');
            }
            if (!response.ok) throw new Error('Health check response not OK');
            const data = await response.json();

            systemStatus.classList.remove('offline');
            systemStatus.classList.add('online');

            if (data.groq_configured && data.newsapi_configured) {
                statusText.textContent = 'Groq 70B & NewsAPI Live';
                systemStatus.title = `Connected to Groq (${data.model}) and NewsAPI`;
            } else if (data.groq_configured) {
                statusText.textContent = 'Groq 70B Live';
                systemStatus.title = `Connected to Groq (${data.model}) | Curated Financial Feeds`;
            } else {
                statusText.textContent = 'System Ready (Demo Mode)';
                systemStatus.title = 'Running in intelligent fallback mode with curated real-time financial articles';
            }
        } catch (err) {
            console.warn('System status check failed:', err);
            systemStatus.classList.remove('online');
            systemStatus.classList.add('offline');
            statusText.textContent = 'Backend Offline';
            systemStatus.title = 'Unable to connect to FastAPI backend at /health or /api/health';
        }
    }

    // -------------------------------------------------------------------------
    // 2. Category Filter Interaction
    // -------------------------------------------------------------------------
    categoryPills.forEach(pill => {
        pill.addEventListener('click', () => {
            if (isFetching) return;
            categoryPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            selectedCategory = pill.getAttribute('data-category') || '';
            // Trigger fetch on category change if articles already exist
            if (articlesContainer.querySelectorAll('.article-card').length > 0) {
                fetchAndRenderNews();
            }
        });
    });

    // -------------------------------------------------------------------------
    // 3. News Retrieval & AI Simplification Handler
    // -------------------------------------------------------------------------
    async function fetchAndRenderNews() {
        if (isFetching) return;

        const count = parseInt(articleCountSelect.value, 10) || 5;

        // UI State: Enter loading
        setLoadingState(true);
        hideError();

        try {
            // Build query params
            const params = new URLSearchParams({ count: count });
            if (selectedCategory) {
                params.append('category', selectedCategory);
            }

            let response = await fetch(`/news?${params.toString()}`);
            if (!response.ok) {
                response = await fetch(`/api/news?${params.toString()}`);
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Server returned status ${response.status}`);
            }

            const data = await response.json();

            if (!data.success || !Array.isArray(data.articles)) {
                throw new Error('Malformed response from backend server');
            }

            renderArticles(data.articles, data.mode, data.model);
            showToast(`Successfully simplified ${data.articles.length} financial articles!`, 'success');

            // Smooth scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            console.error('Error fetching simplified news:', error);
            showError(error.message || 'Unable to connect to the server. Please check that Uvicorn is running.');
            showToast('Failed to fetch financial news', 'error');
        } finally {
            setLoadingState(false);
        }
    }

    // -------------------------------------------------------------------------
    // 4. Dynamic DOM Rendering
    // -------------------------------------------------------------------------
    function renderArticles(articles, mode, model) {
        articlesContainer.innerHTML = '';

        if (articles.length === 0) {
            articlesContainer.innerHTML = `
                <div class="empty-state-card">
                    <div class="empty-icon">🔍</div>
                    <h3>No Articles Found</h3>
                    <p>No financial news matched your selected category. Try selecting "All Finance" or a different topic.</p>
                </div>
            `;
            resultsHeader.classList.remove('hidden');
            resultsCountBadge.textContent = '0 Articles';
            return;
        }

        // Update header metadata
        resultsHeader.classList.remove('hidden');
        resultsCountBadge.textContent = `${articles.length} ${articles.length === 1 ? 'Article' : 'Articles'}`;
        
        if (mode === 'live') {
            modeText.textContent = `Groq Cloud (${model})`;
            resultsModeBadge.style.borderColor = 'var(--accent-emerald)';
        } else if (mode === 'hybrid') {
            modeText.textContent = `Hybrid Mode (${model})`;
        } else {
            modeText.textContent = `Groq Llama 3.3 70B (Curated Feed)`;
        }

        // Inject article cards
        articles.forEach((article, index) => {
            const card = createArticleCard(article, index);
            articlesContainer.appendChild(card);
        });
    }

    function createArticleCard(article, index) {
        const card = document.createElement('article');
        card.className = 'article-card';
        card.style.animation = `fadeIn 400ms ease forwards ${index * 80}ms`;

        // Format publication date
        const timeAgo = formatTimeAgo(article.published_at);
        const sourceName = escapeHtml(article.source || 'Financial Wire');
        const title = escapeHtml(article.title || 'Untitled Financial Update');
        const category = escapeHtml(article.category || 'Markets');
        const originalSnippet = escapeHtml(article.original_description || 'No original snippet available.');
        const summary = escapeHtml(article.summary || '');
        const author = escapeHtml(article.author || 'Financial Reporter');
        const articleUrl = article.url || '#';

        // Build Key Takeaways HTML
        let takeawaysHtml = '';
        if (Array.isArray(article.key_takeaways) && article.key_takeaways.length > 0) {
            const listItems = article.key_takeaways
                .map(item => `
                    <li class="takeaway-item">
                        <span class="takeaway-bullet">✦</span>
                        <span>${escapeHtml(item)}</span>
                    </li>
                `)
                .join('');

            takeawaysHtml = `
                <div class="takeaways-section">
                    <span class="takeaway-heading">Key Market Takeaways</span>
                    <ul class="takeaways-list">
                        ${listItems}
                    </ul>
                </div>
            `;
        }

        // Build Jargon Terms Glossary HTML
        let termsHtml = '';
        if (article.simplified_terms && Object.keys(article.simplified_terms).length > 0) {
            const chips = Object.entries(article.simplified_terms)
                .map(([term, def]) => `
                    <div class="term-chip" title="${escapeHtml(def)}">
                        <strong>${escapeHtml(term)}:</strong>
                        <span>${escapeHtml(def)}</span>
                    </div>
                `)
                .join('');

            termsHtml = `
                <div class="terms-section">
                    <span class="terms-heading">Jargon Simplified</span>
                    <div class="terms-chips">
                        ${chips}
                    </div>
                </div>
            `;
        }

        card.innerHTML = `
            <div class="card-header-bar">
                <div class="card-tags">
                    <span class="source-badge">${sourceName}</span>
                    <span class="category-tag">${category}</span>
                </div>
                <span class="pub-time">${timeAgo}</span>
            </div>

            <div class="card-content">
                <a href="${articleUrl}" target="_blank" rel="noopener noreferrer" class="article-headline">
                    ${title}
                </a>

                <!-- Collapsible Original Snippet -->
                <details class="snippet-accordion">
                    <summary class="snippet-summary-toggle">
                        <span>Original Raw Technical Snippet</span>
                    </summary>
                    <p class="snippet-text">"${originalSnippet}"</p>
                </details>

                <!-- AI Simplified Summary Panel -->
                <div class="ai-summary-box">
                    <div class="ai-summary-header">
                        <div class="ai-summary-label">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                            </svg>
                            Simplified Explanation
                        </div>
                        <button class="copy-btn" title="Copy summary to clipboard" data-summary="${escapeHtml(summary)}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                        </button>
                    </div>

                    <p class="simplified-text">${summary}</p>

                    ${takeawaysHtml}
                    ${termsHtml}
                </div>
            </div>

            <div class="card-footer">
                <span class="article-author" title="${author}">By ${author}</span>
                <a href="${articleUrl}" target="_blank" rel="noopener noreferrer" class="read-original-link">
                    Read Full Story
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                        <line x1="7" y1="17" x2="17" y2="7"></line>
                        <polyline points="7 7 17 7 17 17"></polyline>
                    </svg>
                </a>
            </div>
        `;

        // Attach copy button action
        const copyBtn = card.querySelector('.copy-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const textToCopy = article.summary;
                navigator.clipboard.writeText(textToCopy).then(() => {
                    showToast('Summary copied to clipboard!', 'info');
                }).catch(() => {
                    showToast('Unable to copy to clipboard', 'error');
                });
            });
        }

        return card;
    }

    // -------------------------------------------------------------------------
    // 5. UI State Management
    // -------------------------------------------------------------------------
    function setLoadingState(loading) {
        isFetching = loading;

        if (loading) {
            fetchBtn.disabled = true;
            fetchBtn.querySelector('.btn-text').textContent = 'Analyzing & Simplifying...';
            loadingState.classList.remove('hidden');
            skeletonGrid.classList.remove('hidden');
            articlesContainer.classList.add('hidden');
        } else {
            fetchBtn.disabled = false;
            fetchBtn.querySelector('.btn-text').textContent = 'Fetch & Simplify';
            loadingState.classList.add('hidden');
            skeletonGrid.classList.add('hidden');
            articlesContainer.classList.remove('hidden');
        }
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorBanner.classList.remove('hidden');
    }

    function hideError() {
        errorBanner.classList.add('hidden');
    }

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // -------------------------------------------------------------------------
    // 6. Utility Functions
    // -------------------------------------------------------------------------
    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatTimeAgo(isoString) {
        if (!isoString) return 'Recent';
        try {
            const pubDate = new Date(isoString);
            const now = new Date();
            const diffMs = now - pubDate;
            const diffSec = Math.floor(diffMs / 1000);
            const diffMin = Math.floor(diffSec / 60);
            const diffHr = Math.floor(diffMin / 60);
            const diffDays = Math.floor(diffHr / 24);

            if (diffDays > 0) return `${diffDays}d ago`;
            if (diffHr > 0) return `${diffHr}h ago`;
            if (diffMin > 0) return `${diffMin}m ago`;
            return 'Just now';
        } catch {
            return 'Recent';
        }
    }

    // -------------------------------------------------------------------------
    // 7. Event Listeners
    // -------------------------------------------------------------------------
    fetchBtn.addEventListener('click', fetchAndRenderNews);
    errorRetryBtn.addEventListener('click', fetchAndRenderNews);

    // Keyboard shortcut: Press Enter when count dropdown is focused
    articleCountSelect.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            fetchAndRenderNews();
        }
    });

    // Check system status immediately
    checkSystemHealth();
});
