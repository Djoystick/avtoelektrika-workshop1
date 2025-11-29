/**
 * 🗄️ Database Manager v1.0
 * Загружает и управляет данными из db.json
 */

class DatabaseManager {
    constructor() {
        this.db = null;
        this.articles = [];
    }

    /**
     * Инициализация - загрузить БД
     */
    async init() {
        try {
            // Пытаемся загрузить db.json
            const response = await fetch('./db.json');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.db = await response.json();
            this.articles = this.db.articles || [];
            
            console.log(`✅ Database loaded: ${this.articles.length} articles`);
            
        } catch (error) {
            console.error('❌ Failed to load database:', error);
            // Fallback - пустая БД
            this.db = {
                articles: [],
                stats: {
                    totalArticles: 0,
                    totalCategories: 0,
                    totalSources: 0,
                    youtube: 0,
                    habr: 0,
                    forums: 0,
                    community: 0
                },
                lastUpdated: new Date().toISOString()
            };
            this.articles = [];
        }
    }

    /**
     * Получить статистику
     */
    getStats() {
        return {
            totalArticles: this.articles.length,
            totalBrands: this._getUniqueBrands().length,
            totalErrorCodes: this._getUniqueErrorCodes().length,
            totalCategories: Object.keys(this.db.indexes?.categories || {}).length,
            totalSources: Object.keys(this.db.indexes?.sources || {}).length
        };
    }

    /**
     * Получить уникальные марки авто
     */
    _getUniqueBrands() {
        const brands = new Set();
        this.articles.forEach(article => {
            if (article.brands && Array.isArray(article.brands)) {
                article.brands.forEach(b => brands.add(b));
            }
        });
        return Array.from(brands);
    }

    /**
     * Получить уникальные коды ошибок
     */
    _getUniqueErrorCodes() {
        const codes = new Set();
        this.articles.forEach(article => {
            // Ищем коды типа P0300, C0040 и т.д.
            const matches = article.title.match(/[PBC]\d{4}/g);
            if (matches) {
                matches.forEach(code => codes.add(code));
            }
            // Также проверяем в summary
            const summaryMatches = article.summary.match(/[PBC]\d{4}/g);
            if (summaryMatches) {
                summaryMatches.forEach(code => codes.add(code));
            }
        });
        return Array.from(codes);
    }

    /**
     * Поиск по коду ошибки
     */
    searchByErrorCode(code) {
        const upperCode = code.toUpperCase();
        return this.articles.filter(article => 
            article.title.includes(upperCode) || 
            article.summary.includes(upperCode)
        );
    }

    /**
     * Поиск по симптому
     */
    searchBySymptom(symptom) {
        const lowerSymptom = symptom.toLowerCase();
        return this.articles.filter(article =>
            article.title.toLowerCase().includes(lowerSymptom) ||
            article.summary.toLowerCase().includes(lowerSymptom) ||
            article.category.toLowerCase().includes(lowerSymptom)
        );
    }

    /**
     * Поиск по марке авто
     */
    searchByBrand(brand) {
        return this.articles.filter(article =>
            article.brands && article.brands.some(b => 
                b.toLowerCase().includes(brand.toLowerCase())
            )
        );
    }

    /**
     * Поиск по категории
     */
    searchByCategory(category) {
        return this.articles.filter(article =>
            article.category.toLowerCase().includes(category.toLowerCase())
        );
    }

    /**
     * Поиск по источнику
     */
    searchBySource(source) {
        return this.articles.filter(article =>
            article.source.toLowerCase().includes(source.toLowerCase())
        );
    }

    /**
     * Общий поиск по любому полю
     */
    search(query) {
        const lowerQuery = query.toLowerCase();
        return this.articles.filter(article =>
            article.title.toLowerCase().includes(lowerQuery) ||
            article.summary.toLowerCase().includes(lowerQuery) ||
            article.source.toLowerCase().includes(lowerQuery) ||
            article.category.toLowerCase().includes(lowerQuery)
        );
    }

    /**
     * Получить статьи по категориям
     */
    getByCategory(category) {
        return this.articles.filter(a => a.category === category);
    }

    /**
     * Получить статьи по типу (youtube, habr, forums, community)
     */
    getByType(type) {
        return this.articles.filter(a => a.type === type);
    }

    /**
     * Получить топ статей по популярности/времени
     */
    getTopArticles(limit = 10) {
        return this.articles.slice(0, limit);
    }

    /**
     * Получить видео
     */
    getVideos() {
        return this.articles.filter(a => a.contentType === '🎬 Видео');
    }

    /**
     * Получить статьи
     */
    getArticles() {
        return this.articles.filter(a => a.contentType === '📚 Статья' || a.contentType === '📖 Статья');
    }

    /**
     * Получить форум посты
     */
    getForumPosts() {
        return this.articles.filter(a => a.contentType === '💬 Форум');
    }

    /**
     * Получить community решения
     */
    getCommunitySolutions() {
        return this.articles.filter(a => a.type === 'community');
    }

    /**
     * Получить все категории
     */
    getAllCategories() {
        const categories = new Set();
        this.articles.forEach(article => {
            categories.add(article.category);
        });
        return Array.from(categories).sort();
    }

    /**
     * Получить все источники
     */
    getAllSources() {
        const sources = new Set();
        this.articles.forEach(article => {
            sources.add(article.source);
        });
        return Array.from(sources).sort();
    }

    /**
     * Получить статьи за последний день
     */
    getRecentArticles(days = 1) {
        const now = new Date();
        const cutoff = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
        
        return this.articles.filter(article => {
            try {
                const publishDate = new Date(article.published);
                return publishDate > cutoff;
            } catch (e) {
                return false;
            }
        });
    }

    /**
     * Получить индексы
     */
    getIndexes() {
        return this.db.indexes || {
            categories: {},
            sources: {},
            types: {},
            brands: {}
        };
    }

    /**
     * Получить URL для статьи
     */
    getArticleUrl(article) {
        if (article.link.startsWith('http')) {
            return article.link;
        }
        if (article.link.startsWith('#')) {
            // Это локальное решение в db/solutions/
            return '#' + article.link;
        }
        return article.link;
    }
}

// Экспортируем для использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DatabaseManager;
}