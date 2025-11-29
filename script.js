class DatabaseManager {
    constructor() {
        this.db = null;
        this.articles = [];
        this.errorCodes = null;
        this.vehicles = null;
    }
    
    async init() {
        try {
            const [dbRes, codesRes, vehiclesRes] = await Promise.all([
                fetch('db.json'),
                fetch('error-codes.json'),
                fetch('vehicles.json')
            ]);
            
            this.db = await dbRes.json();
            this.errorCodes = await codesRes.json();
            this.vehicles = await vehiclesRes.json();
            this.articles = this.db.articles || [];
            
            console.log('✅ База данных загружена');
        } catch (e) {
            console.error('❌ Ошибка загрузки БД:', e);
        }
    }
    
    getStats() {
        return this.db.stats || {};
    }
    
    searchByErrorCode(code) {
        const ids = this.db.indexes.errorCodes[code] || [];
        return this.articles.filter(a => ids.includes(a.id));
    }
    
    searchByBrand(brand) {
        const ids = this.db.indexes.brands[brand] || [];
        return this.articles.filter(a => ids.includes(a.id));
    }
    
    searchByProblem(problem) {
        const ids = this.db.indexes.problems[problem] || [];
        return this.articles.filter(a => ids.includes(a.id));
    }
    
    searchByText(query) {
        const q = query.toLowerCase();
        return this.articles.filter(a =>
            a.title.toLowerCase().includes(q) ||
            a.summary.toLowerCase().includes(q)
        );
    }
    
    getArticlesByBrand(brandKey) {
        return this.articles.filter(a => a.brands.includes(brandKey));
    }
    
    getRelated(article, limit = 5) {
        return this.articles
            .filter(a =>
                a.id !== article.id &&
                (
                    a.brands.some(b => article.brands.includes(b)) ||
                    a.errorCodes.some(c => article.errorCodes.includes(c)) ||
                    a.problemTags.some(t => article.problemTags.includes(t))
                )
            )
            .slice(0, limit);
    }
}

// Экспорт
window.DatabaseManager = DatabaseManager;
