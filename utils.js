// VIN Decoder
function decodeVIN(vin) {
    const makers = {
        'W': 'Germany',
        'V': 'France',
        'X': 'Soviet Union',
        'Y': 'Sweden',
        'Z': 'Italy',
        'J': 'Japan',
        'K': 'Korea',
        'L': 'Belgium',
        'M': 'Hungary',
        'N': 'Netherlands',
        'P': 'Spain',
        'R': 'Brazil',
        'S': 'Britain',
        'T': 'Switzerland',
        'U': 'Romania',
        'A': 'Japan',
        'B': 'Britain',
        'C': 'Japan',
        'D': 'Germany',
        'E': 'Germany',
        'F': 'Germany',
        'G': 'Germany',
        'H': 'Hungary',
    };
    
    const years = {
        'Y': 2000, 'Z': 2001, 'A': 2010, 'B': 2011, 'C': 2012,
        'D': 2013, 'E': 2014, 'F': 2015, 'G': 2016, 'H': 2017,
        'J': 2018, 'K': 2019, 'L': 2020, 'M': 2021, 'N': 2022,
        'P': 2023, 'R': 2024
    };
    
    return {
        manufacturer: makers[vin[0]] || 'Unknown',
        brand: vin.substring(0, 3),
        year: years[vin[9]] || 'Unknown',
        serialNumber: vin.substring(11)
    };
}

// DTC Search
function searchDTC(code) {
    const patterns = {
        'P': 'Powertrain',
        'B': 'Body',
        'C': 'Chassis',
        'U': 'Network'
    };
    return patterns[code[0]] || 'Unknown';
}

// Форматирование даты
function formatDate(isoString) {
    return new Date(isoString).toLocaleDateString('ru-RU');
}

// Сохранение в избранное
function saveToFavorites(articleId) {
    let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    if (!favorites.includes(articleId)) {
        favorites.push(articleId);
        localStorage.setItem('favorites', JSON.stringify(favorites));
    }
}

// Получение избранного
function getFavorites() {
    return JSON.parse(localStorage.getItem('favorites') || '[]');
}

// Экспорт
window.decodeVIN = decodeVIN;
window.searchDTC = searchDTC;
window.formatDate = formatDate;
window.saveToFavorites = saveToFavorites;
window.getFavorites = getFavorites;
