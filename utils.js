// VIN Decoder (NHTSA API)
async function decodeVIN(vin) {
    if (!vin || vin.length !== 17) {
        throw new Error("VIN должен состоять из 17 символов");
    }

    try {
        // Реальный запрос к API
        const response = await fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/${vin}?format=json`);
        const data = await response.json();
        
        const results = data.Results;
        const getVal = (id) => results.find(r => r.VariableId === id)?.Value || "Не найдено";

        // ID переменных в API NHTSA:
        // 26: Make, 28: Model, 29: Model Year, 27: Manufacturer Name
        // 14: Body Class, 15: Engine Cylinders, 24: Fuel Type
        // 9: Engine HP

        return {
            manufacturer: getVal(27),
            brand: getVal(26),
            model: getVal(28),
            year: getVal(29),
            body: getVal(14),
            engine: `${getVal(15)} cyl, ${getVal(24)}`,
            fuel: getVal(24),
            hp: getVal(9)
        };
    } catch (e) {
        console.error("VIN Error:", e);
        // Фолбек на локальный декодер, если API недоступен
        return decodeVINLocal(vin);
    }
}

// Локальный декодер (запасной)
function decodeVINLocal(vin) {
    const yearCode = vin[9];
    const years = {
        'A': 2010, 'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014,
        'F': 2015, 'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019,
        'L': 2020, 'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024, 'S': 2025
    };
    return {
        manufacturer: "Unknown (Offline Mode)",
        brand: "Unknown",
        model: "Check Internet",
        year: years[yearCode] || "Unknown",
        body: "-",
        engine: "-"
    };
}

// Остальные утилиты
function formatDate(isoString) {
    return new Date(isoString).toLocaleDateString('ru-RU');
}

window.decodeVIN = decodeVIN;
window.formatDate = formatDate;
