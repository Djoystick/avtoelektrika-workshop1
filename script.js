/* =====================================================
   🔧 МАСТЕРСКАЯ АВТОЭЛЕКТРИКА v3.0
   Frontend Logic
   ===================================================== */

// ===== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
let allArticles = [];
let filteredArticles = [];
let currentFilters = {
    searchQuery: '',
    selectedCategory: 'all',
    contentType: 'all',
    problemTag: 'all'
};

// ===== DOM ЭЛЕМЕНТЫ =====
const searchInput = document.getElementById('search-input');
const categoryFilters = document.getElementById('category-filters');
const problemTagsCloud = document.getElementById('tag-cloud');
const articlesList = document.getElementById('news-list');
const emptyState = document.getElementById('empty-state');
const emptyMessage = document.getElementById('empty-message');
const updateTime = document.getElementById('update-time');
const totalArticles = document.getElementById('total-news');
const sourcesCount = document.getElementById('sources-count');

// ===== ИНИЦИАЛИЗАЦИЯ =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔧 Инициализация Мастерской Автоэлектрика v3.0...');
    loadData();
});

// ===== ЗАГРУЗКА ДАННЫХ =====
async function loadData() {
    try {
        const response = await fetch('news.json');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        // Поддержка старого и нового формата
        allArticles = data.articles || data.news || [];
        
        if (!allArticles.length) {
            showEmpty('📭 База еще пуста. Ожидаем первого обновления...');
            return;
        }
        
        // Рендер интерфейса
        renderCategoryFilters();
        renderProblemTags();
        updateStats(data);
        applyFilters();
        
        hideEmpty();
        
    } catch (error) {
        console.error('❌ Ошибка загрузки:', error);
        showEmpty(`⚠️ Ошибка загрузки: ${error.message}`);
    }
}

// ===== РЕНДЕР ФИЛЬТРОВ ПО КАТЕГОРИЯМ =====
function renderCategoryFilters() {
    if (!categoryFilters) return;
    
    const categories = ['all', ...new Set(allArticles.map(a => a.category))].sort();
    categoryFilters.innerHTML = '';
    
    categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = 'filter-chip';
        btn.type = 'button';
        btn.dataset.category = cat;
        btn.textContent = cat === 'all' ? '📋 Все разделы' : cat;
        
        if (cat === 'all') btn.classList.add('filter-chip-active');
        
        btn.addEventListener('click', () => {
            currentFilters.selectedCategory = cat;
            updateFilterButtons();
            applyFilters();
        });
        
        categoryFilters.appendChild(btn);
    });
}

// ===== РЕНДЕР ОБЛАКА ПРОБЛЕМ =====
function renderProblemTags() {
    if (!problemTagsCloud) return;
    
    // Собираем уникальные проблемы
    const allTags = new Set();
    allArticles.forEach(a => {
        (a.problemTags || []).forEach(t => allTags.add(t));
    });
    
    problemTagsCloud.innerHTML = '';
    
    Array.from(allTags).sort().forEach(tag => {
        const tagEl = document.createElement('button');
        tagEl.className = 'tag';
        tagEl.type = 'button';
        tagEl.textContent = tag;
        tagEl.addEventListener('click', () => {
            currentFilters.problemTag = currentFilters.problemTag === tag ? 'all' : tag;
            applyFilters();
        });
        problemTagsCloud.appendChild(tagEl);
    });
}

// ===== ПРИМЕНЕНИЕ ФИЛЬТРОВ =====
function applyFilters() {
    filteredArticles = allArticles.filter(article => {
        const matchesSearch = matchesSearchQuery(article);
        const matchesCategory = currentFilters.selectedCategory === 'all' 
            || article.category === currentFilters.selectedCategory;
        const matchesProblem = currentFilters.problemTag === 'all'
            || (article.problemTags || []).includes(currentFilters.problemTag);
        
        return matchesSearch && matchesCategory && matchesProblem;
    });
    
    renderArticles();
}

// ===== ПОИСК ПО ЗАПРОСУ =====
function matchesSearchQuery(article) {
    const query = currentFilters.searchQuery.toLowerCase();
    if (!query) return true;
    
    const title = (article.title || '').toLowerCase();
    const summary = (article.summary || '').toLowerCase();
    const tags = ((article.problemTags || []).join(' ')).toLowerCase();
    const codes = ((article.errorCodes || []).join(' ')).toLowerCase();
    
    return title.includes(query) 
        || summary.includes(query) 
        || tags.includes(query)
        || codes.includes(query);
}

// ===== РЕНДЕР СПИСКА СТАТЕЙ =====
function renderArticles() {
    if (!articlesList) return;
    
    articlesList.innerHTML = '';
    
    if (filteredArticles.length === 0) {
        showEmpty(`❌ По вашему запросу ничего не найдено`);
        return;
    }
    
    filteredArticles.forEach(article => {
        const card = createArticleCard(article);
        articlesList.appendChild(card);
    });
    
    hideEmpty();
}

// ===== СОЗДАНИЕ КАРТОЧКИ СТАТЬИ =====
function createArticleCard(article) {
    const card = document.createElement('article');
    card.className = 'news-item';
    
    // Изображение
    const imageHtml = article.image 
        ? `<img src="${article.image}" alt="" class="news-item-image" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE2MCIgZmlsbD0iIzIwMjQyOCIvPjwvc3ZnPg=='"/>`
        : '';
    
    // Теги проблем
    const problemsHtml = (article.problemTags || []).length
        ? `<div class="news-item-problems">${article.problemTags.map(t => `<span class="problem-tag">${escapeHtml(t)}</span>`).join('')}</div>`
        : '';
    
    // Коды ошибок (если есть)
    const codesHtml = (article.errorCodes || []).length
        ? `<div class="news-item-codes">${article.errorCodes.slice(0, 3).map(c => `<span class="error-code">${c}</span>`).join('')}</div>`
        : '';
    
    card.innerHTML = `
        ${imageHtml}
        <div class="news-item-header">
            <span class="content-type-badge">${article.contentType || '📚'}</span>
            <span class="category-badge">${escapeHtml(article.category)}</span>
        </div>
        <h3 class="news-item-title">${escapeHtml(article.title)}</h3>
        <p class="news-item-summary">${escapeHtml(article.summary.substring(0, 150))}...</p>
        ${problemsHtml}
        ${codesHtml}
        <div class="news-item-footer">
            <span class="source">${escapeHtml(article.source)}</span>
        </div>
    `;
    
    card.addEventListener('click', () => openModal(article));
    return card;
}

// ===== МОДАЛЬНОЕ ОКНО =====
function openModal(article) {
    const modal = document.getElementById('modal');
    
    document.getElementById('modal-title').textContent = article.title;
    document.getElementById('modal-category').textContent = `📂 ${article.category}`;
    document.getElementById('modal-source').textContent = `📌 ${article.source}`;
    
    const img = document.getElementById('modal-image');
    if (article.image) {
        img.src = article.image;
        img.style.display = 'block';
    } else {
        img.style.display = 'none';
    }
    
    const modalProblems = document.getElementById('modal-symptoms');
    if (article.problemTags && article.problemTags.length) {
        modalProblems.innerHTML = article.problemTags
            .map(t => `<span class="modal-symptom-badge">${escapeHtml(t)}</span>`)
            .join('');
    } else {
        modalProblems.innerHTML = '';
    }
    
    document.getElementById('modal-summary').textContent = article.summary;
    document.getElementById('modal-link').href = article.link;
    
    modal.classList.remove('modal-hidden');
}

// ===== ЗАКРЫТИЕ МОДАЛКИ =====
function closeModal() {
    document.getElementById('modal').classList.add('modal-hidden');
}

// ===== ОБНОВЛЕНИЕ КНОПОК ФИЛЬТРОВ =====
function updateFilterButtons() {
    document.querySelectorAll('.filter-chip').forEach(btn => {
        btn.classList.remove('filter-chip-active');
        if (btn.dataset.category === currentFilters.selectedCategory) {
            btn.classList.add('filter-chip-active');
        }
    });
}

// ===== ОБНОВЛЕНИЕ СТАТИСТИКИ =====
function updateStats(data) {
    if (totalArticles) totalArticles.textContent = data.stats?.totalArticles || allArticles.length;
    if (sourcesCount) sourcesCount.textContent = data.stats?.totalSources || 'много';
    if (updateTime && data.lastUpdated) {
        updateTime.textContent = new Date(data.lastUpdated).toLocaleString('ru-RU');
    }
}

// ===== ПУСТОЕ СОСТОЯНИЕ =====
function showEmpty(message) {
    if (emptyState) {
        emptyState.classList.remove('hidden');
        emptyMessage.innerHTML = message;
    }
}

function hideEmpty() {
    if (emptyState) emptyState.classList.add('hidden');
}

// ===== УТИЛИТЫ =====
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ===== ОБРАБОТЧИКИ ПОИСКА =====
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        currentFilters.searchQuery = e.target.value;
        applyFilters();
    });
}

// ===== ЗАКРЫТИЕ МОДАЛКИ =====
document.getElementById('modal-close')?.addEventListener('click', closeModal);
document.getElementById('modal')?.addEventListener('click', (e) => {
    if (e.target === document.getElementById('modal')) closeModal();
});

// ===== ПЕРЕЗАГРУЗКА ДАННЫХ КАЖДЫЕ 10 МИНУТ =====
setInterval(() => {
    console.log('🔄 Проверка обновлений...');
    loadData();
}, 10 * 60 * 1000);
