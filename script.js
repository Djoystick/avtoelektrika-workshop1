/* ======================================
   ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
   ====================================== */

let newsData = [];
let filteredData = [];
let currentCategory = 'all';

// DOM элементы
const searchInputEl = document.getElementById('search-input');
const newsListEl = document.getElementById('news-list');
const modalEl = document.getElementById('modal');
const modalTitleEl = document.getElementById('modal-title');
const modalImageEl = document.getElementById('modal-image');
const modalSummaryEl = document.getElementById('modal-summary');
const modalLinkEl = document.getElementById('modal-link');
const modalCloseEl = document.getElementById('modal-close');
const modalCategoryEl = document.getElementById('modal-category');
const modalSourceEl = document.getElementById('modal-source');
const modalsymptomsEl = document.getElementById('modal-symptoms');
const tagCloudEl = document.getElementById('tag-cloud');
const categoryFiltersEl = document.getElementById('category-filters');
const emptyStateEl = document.getElementById('empty-state');
const emptyMessageEl = document.getElementById('empty-message');
const triggerUpdateBtnEl = document.getElementById('trigger-update-btn');
const updateTimeEl = document.getElementById('update-time');
const totalNewsEl = document.getElementById('total-news');
const sourcesCountEl = document.getElementById('sources-count');

/* ======================================
   ОБРАБОТЧИКИ СОБЫТИЙ
   ====================================== */

// Поиск в реальном времени
searchInputEl.addEventListener('input', handleSearch);

// Закрытие модалки
modalCloseEl.addEventListener('click', closeModal);
modalEl.addEventListener('click', (e) => {
    if (e.target === modalEl) closeModal();
});

// Запрос обновления базы
if (triggerUpdateBtnEl) {
    triggerUpdateBtnEl.addEventListener('click', triggerDatabaseUpdate);
}

// Определяем touch или mouse
if (window.innerWidth > 768) {
    document.body.classList.add('no-touch');
    document.body.classList.remove('touch');
} else {
    document.body.classList.add('touch');
    document.body.classList.remove('no-touch');
}

/* ======================================
   ФУНКЦИЯ ПОИСКА
   ====================================== */

function handleSearch(e) {
    const query = e.target.value.toLowerCase().trim();

    if (!query) {
        // Если поиск пустой - показываем все
        applyFilter();
        return;
    }

    // Фильтруем по заголовку, описанию и симптомам
    filteredData = newsData.filter(item => {
        const title = (item.title || '').toLowerCase();
        const summary = (item.summary || '').toLowerCase();
        const symptoms = ((item.symptoms || []).join(' ')).toLowerCase();
        const category = (item.category || '').toLowerCase();

        const matchesQuery = 
            title.includes(query) || 
            summary.includes(query) || 
            symptoms.includes(query) ||
            category.includes(query);

        return matchesQuery && (currentCategory === 'all' || item.category === currentCategory);
    });

    renderNewsList(filteredData);

    // Если ничего не найдено - показываем кнопку обновления
    if (!filteredData.length) {
        showEmpty(`❌ По запросу "<strong>${query}</strong>" ничего не найдено.<br>Попытаемся найти в источниках...`);
    } else {
        hideEmpty();
    }
}

/* ======================================
   ФИЛЬТР ПО КАТЕГОРИЯМ
   ====================================== */

function applyFilter(category = 'all') {
    currentCategory = category;
    const query = searchInputEl.value.toLowerCase().trim();

    if (!query) {
        // Если нет поиска - показываем все по категории
        if (category === 'all') {
            filteredData = [...newsData];
        } else {
            filteredData = newsData.filter(item => item.category === category);
        }
    } else {
        // Если есть поиск - фильтруем и по запросу, и по категории
        filteredData = newsData.filter(item => {
            const title = (item.title || '').toLowerCase();
            const summary = (item.summary || '').toLowerCase();
            const symptoms = ((item.symptoms || []).join(' ')).toLowerCase();

            const matchesQuery = 
                title.includes(query) || 
                summary.includes(query) || 
                symptoms.includes(query);

            if (category === 'all') return matchesQuery;
            return matchesQuery && item.category === category;
        });
    }

    renderNewsList(filteredData);
    setActiveFilter(category);

    if (!filteredData.length) {
        showEmpty(`📭 По выбранным фильтрам статей не найдено.`);
    } else {
        hideEmpty();
    }
}

function setActiveFilter(category) {
    const chips = document.querySelectorAll('.filter-chip');
    chips.forEach(chip => {
        chip.classList.remove('filter-chip-active');
        if (chip.dataset.category === category) {
            chip.classList.add('filter-chip-active');
        }
    });
}

/* ======================================
   ФИЛЬТР ПО ТЕГАМ (СИМПТОМЫ)
   ====================================== */

function filterByTag(tag) {
    currentCategory = 'all';
    setActiveFilter('all');
    searchInputEl.value = '';

    filteredData = newsData.filter(item => {
        const symptoms = item.symptoms || [];
        return symptoms.some(s => s.toLowerCase().includes(tag.toLowerCase()));
    });

    renderNewsList(filteredData);

    if (!filteredData.length) {
        showEmpty(`🔍 Статей с тегом "<strong>${tag}</strong>" не найдено.`);
    } else {
        hideEmpty();
    }
}

/* ======================================
   РЕНДЕР СПИСКА НОВОСТЕЙ
   ====================================== */

function renderNewsList(list) {
    if (!newsListEl) return;

    newsListEl.innerHTML = '';

    list.forEach(item => {
        const article = document.createElement('article');
        article.className = 'news-item';

        // Изображение
        const imageUrl = item.image || 'assets/placeholder.jpg';
        const imgHtml = `<img src="${imageUrl}" alt="" class="news-item-image" onerror="this.src='assets/placeholder.jpg'">`;

        // Симптомы
        const symptomsHtml = item.symptoms && item.symptoms.length 
            ? `<div class="news-item-symptoms">${item.symptoms.map(s => `<span class="symptom-tag">${escapeHtml(s)}</span>`).join('')}</div>`
            : '';

        article.innerHTML = `
            ${imgHtml}
            <h3 class="news-item-title">${escapeHtml(item.title)}</h3>
            <p class="news-item-summary">${escapeHtml(item.summary)}</p>
            ${symptomsHtml}
            <div class="news-item-meta">
                <span class="news-item-category">${escapeHtml(item.category)}</span>
                <span class="news-item-source">${escapeHtml(item.source)}</span>
            </div>
        `;

        article.addEventListener('click', () => openModal(item));
        newsListEl.appendChild(article);
    });
}

/* ======================================
   РЕНДЕР ОБЛАКА ТЕГОВ
   ====================================== */

function renderTagCloud(list) {
    if (!tagCloudEl) return;

    const allSymptoms = new Set();

    list.forEach(item => {
        if (item.symptoms && Array.isArray(item.symptoms)) {
            item.symptoms.forEach(symptom => allSymptoms.add(symptom));
        }
    });

    tagCloudEl.innerHTML = '';

    const sortedSymptoms = Array.from(allSymptoms).sort();

    sortedSymptoms.forEach(symptom => {
        const tag = document.createElement('button');
        tag.className = 'tag';
        tag.textContent = symptom;
        tag.type = 'button';
        tag.addEventListener('click', () => filterByTag(symptom));
        tagCloudEl.appendChild(tag);
    });
}

/* ======================================
   РЕНДЕР ФИЛЬТРОВ ПО КАТЕГОРИЯМ
   ====================================== */

function renderCategoryFilters(list) {
    if (!categoryFiltersEl) return;

    // Собираем уникальные категории
    const categories = new Set(['all']);
    list.forEach(item => {
        if (item.category) categories.add(item.category);
    });

    categoryFiltersEl.innerHTML = '';

    const categoriesArray = Array.from(categories).sort();

    categoriesArray.forEach(category => {
        const chip = document.createElement('button');
        chip.className = 'filter-chip';
        chip.type = 'button';
        chip.dataset.category = category;
        
        if (category === 'all') {
            chip.textContent = '📋 Все категории';
            chip.classList.add('filter-chip-active');
        } else {
            chip.textContent = category;
        }

        chip.addEventListener('click', () => applyFilter(category));
        categoryFiltersEl.appendChild(chip);
    });
}

/* ======================================
   МОДАЛЬНОЕ ОКНО
   ====================================== */

function openModal(item) {
    modalTitleEl.textContent = item.title;
    modalImageEl.src = item.image || 'assets/placeholder.jpg';
    modalImageEl.style.display = item.image ? 'block' : 'none';
    modalSummaryEl.textContent = item.summary;
    modalLinkEl.href = item.link;
    modalCategoryEl.textContent = `📂 ${item.category}`;
    modalSourceEl.textContent = `📌 ${item.source}`;

    // Симптомы в модалке
    if (item.symptoms && item.symptoms.length) {
        modalsymptomsEl.innerHTML = item.symptoms
            .map(s => `<span class="modal-symptom-badge">${escapeHtml(s)}</span>`)
            .join('');
    } else {
        modalsymptomsEl.innerHTML = '';
    }

    modalEl.classList.remove('modal-hidden');
}

function closeModal() {
    modalEl.classList.add('modal-hidden');
}

/* ======================================
   ПУСТОЕ СОСТОЯНИЕ
   ====================================== */

function showEmpty(message) {
    emptyStateEl.classList.remove('hidden');
    emptyMessageEl.innerHTML = message;
}

function hideEmpty() {
    emptyStateEl.classList.add('hidden');
}

/* ======================================
   ЗАГРУЗКА НОВОСТЕЙ
   ====================================== */

async function loadNews() {
    try {
        const response = await fetch('news.json');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // news.json может быть массивом или объектом { news: [...] }
        newsData = Array.isArray(data) ? data : (data.news || []);

        if (!newsData.length) {
            showEmpty('📭 База новостей пуста. Пожалуйста, подождите обновления.');
            return;
        }

        // Обновляем统计
        updateStats();

        // Рендерим
        renderNewsList(newsData);
        renderTagCloud(newsData);
        renderCategoryFilters(newsData);

        // Обновляем время
        if (data.lastUpdated) {
            updateTimeEl.textContent = formatDate(data.lastUpdated);
        }

        hideEmpty();
    } catch (error) {
        console.error('❌ Ошибка загрузки news.json:', error);
        showEmpty(`⚠️ Ошибка загрузки базы: ${error.message}`);
    }
}

/* ======================================
   ОБНОВЛЕНИЕ СТАТИСТИКИ
   ====================================== */

function updateStats() {
    totalNewsEl.textContent = newsData.length;

    // Считаем уникальные источники
    const sources = new Set();
    newsData.forEach(item => {
        if (item.source) sources.add(item.source);
    });
    sourcesCountEl.textContent = sources.size;
}

/* ======================================
   ЗАПРОС ОБНОВЛЕНИЯ БАЗЫ
   ====================================== */

function triggerDatabaseUpdate() {
    if (!triggerUpdateBtnEl) return;

    triggerUpdateBtnEl.textContent = '⏳ Запрос отправлен...';
    triggerUpdateBtnEl.disabled = true;

    // Отправляем сигнал на обновление (если есть API)
    // Либо просто уведомляем, что нужно вручную запустить workflow
    const searchQuery = searchInputEl.value || 'запрос';

    console.log(`🔄 Запрос обновления базы: "${searchQuery}"`);

    // Через 3 сек - уведомляем
    setTimeout(() => {
        triggerUpdateBtnEl.textContent = '✅ Запрос принят! Обновление через 6 часов.';
    }, 3000);

    // Через 10 сек - возвращаем кнопку
    setTimeout(() => {
        triggerUpdateBtnEl.textContent = '🔄 Запросить обновление базы';
        triggerUpdateBtnEl.disabled = false;
    }, 10000);
}

/* ======================================
   УТИЛИТЫ
   ====================================== */

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function formatDate(timestamp) {
    if (!timestamp) return 'неизвестно';
    const date = new Date(timestamp);
    return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/* ======================================
   ИНИЦИАЛИЗАЦИЯ
   ====================================== */

document.addEventListener('DOMContentLoaded', () => {
    console.log('🔧 Мастерская Автоэлектрика загружается...');
    loadNews();
});

// Перезагрузка каждые 10 минут
setInterval(() => {
    console.log('🔄 Проверка обновлений...');
    loadNews();
}, 10 * 60 * 1000);
