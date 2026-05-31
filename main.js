const fs = require('fs');
const readline = require('readline');
const catalog = require('./materials_catalog.json');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function displayRegions() {
    console.log('\n=== Выберите регион ===');
    catalog.regions.forEach((region, idx) => {
        console.log(`  ${idx + 1}. ${region}`);
    });
}

function getUserChoice(prompt, maxValue) {
    return new Promise((resolve) => {
        rl.question(prompt, (answer) => {
            const choice = parseInt(answer);
            if (choice >= 1 && choice <= maxValue) {
                resolve(choice);
            } else {
                console.log(`Ошибка: Введите число от 1 до ${maxValue}`);
                resolve(getUserChoice(prompt, maxValue));
            }
        });
    });
}

function askConfirmation(prompt) {
    return new Promise((resolve) => {
        rl.question(prompt, (answer) => {
            const response = answer.trim().toLowerCase();
            if (['y', 'yes', 'д', 'да'].includes(response)) {
                resolve(true);
            } else if (['n', 'no', 'н', 'нет'].includes(response)) {
                resolve(false);
            } else {
                console.log("Ошибка: Введите 'y' или 'n'");
                resolve(askConfirmation(prompt));
            }
        });
    });
}

function displayProducts(region) {
    console.log(`\n=== Список материалов (регион: ${region}) ===`);
    console.log('-'.repeat(80));
    console.log('№   | Товар                                     | Категория        | Цена');
    console.log('-'.repeat(80));
    
    catalog.products.forEach((product, idx) => {
        const price = product.prices[region];
        const name = product.name.length > 40 ? product.name.slice(0, 40) : product.name;
        console.log(`${(idx + 1).toString().padEnd(3)} | ${name.padEnd(40)} | ${product.category.padEnd(15)} | ${price} руб.`);
    });
    
    console.log('-'.repeat(80));
}

function findCheapestInCategory(category, region) {
    const productsInCategory = catalog.products.filter(p => p.category === category);
    return productsInCategory.reduce((min, p) => 
        p.prices[region] < min.prices[region] ? p : min
    );
}

function calculateDiscountedPrice(price, discountPercent = 5) {
    return price * (1 - discountPercent / 100);
}

function createOrderFile(product, region, finalPrice, discountApplied = false) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const filename = `order_${timestamp}.json`;
    
    const orderData = {
        order_date: new Date().toISOString().slice(0, 19).replace('T', ' '),
        region: region,
        product: {
            id: product.id,
            name: product.name,
            category: product.category
        },
        original_price: product.prices[region],
        final_price: finalPrice,
        discount_applied: discountApplied,
        discount_percent: discountApplied ? 5 : 0
    };
    
    fs.writeFileSync(filename, JSON.stringify(orderData, null, 2), 'utf8');
    return filename;
}

async function main() {
    console.log('='.repeat(80));
    console.log('    ФОРМИРОВАНИЕ ЗАЯВКИ');
    console.log('='.repeat(80));
    
    // 1. Выбор региона
    displayRegions();
    const regionIdx = await getUserChoice('Введите номер региона: ', catalog.regions.length);
    const region = catalog.regions[regionIdx - 1];
    console.log(`\nВыбран регион: ${region}`);
    
    // 2. Вывод списка товаров
    displayProducts(region);
    
    // 3. Выбор товара
    const productIdx = await getUserChoice('Введите номер товара: ', catalog.products.length);
    const product = catalog.products[productIdx - 1];
    const price = product.prices[region];
    
    // 4. Показ заказа
    console.log('\n' + '='.repeat(80));
    console.log('    ВАШ ЗАКАЗ');
    console.log('='.repeat(80));
    console.log(`  Регион:           ${region}`);
    console.log(`  Товар:            ${product.name}`);
    console.log(`  Категория:        ${product.category}`);
    console.log(`  Цена:             ${price} руб.`);
    console.log('='.repeat(80));
    
    // 5. Вопрос о подтверждении
    const confirmed = await askConfirmation('\nОформляем заявку? (y/n): ');
    
    if (confirmed) {
        const filename = createOrderFile(product, region, price);
        console.log(`\n✓ Заявка успешно оформлена!`);
        console.log(`✓ Файл заявки: ${filename}`);
        rl.close();
        return;
    }
    
    // Логика при отказе - удержание клиента
    console.log('\n' + '='.repeat(80));
    console.log('    СПЕЦИАЛЬНОЕ ПРЕДЛОЖЕНИЕ ДЛЯ ВАС!');
    console.log('='.repeat(80));
    
    const cheapest = findCheapestInCategory(product.category, region);
    const cheapestPrice = cheapest.prices[region];
    
    if (cheapest.id === product.id) {
        // Товар самый дешевый - предлагаем скидку
        const discountedPrice = calculateDiscountedPrice(price, 5);
        console.log(`\n  Для вас специальная скидка 5% на выбранный товар!`);
        console.log(`\n  Товар:            ${product.name}`);
        console.log(`  Цена без скидки:  ${price} руб.`);
        console.log(`  Цена со скидкой:  ${discountedPrice.toFixed(2)} руб.`);
        console.log(`  Экономия:         ${(price - discountedPrice).toFixed(2)} руб.`);
        console.log('='.repeat(80));
        
        const finalConfirm = await askConfirmation('\nОформляем заявку по специальному предложению? (y/n): ');
        if (finalConfirm) {
            const filename = createOrderFile(product, region, discountedPrice, true);
            console.log(`\n✓ Заявка успешно оформлена!`);
            console.log(`✓ Файл заявки: ${filename}`);
        } else {
            console.log('\nЖаль, что вы отказались. Будем рады видеть вас снова!');
        }
    } else {
        // Есть более дешевый аналог
        console.log(`\n  Мы можем предложить вам более выгодный вариант в этой категории:`);
        console.log(`\n  Товар:            ${cheapest.name}`);
        console.log(`  Категория:        ${cheapest.category}`);
        console.log(`  Цена:             ${cheapestPrice} руб.`);
        console.log(`  Экономия:         ${price - cheapestPrice} руб.`);
        console.log('\n  Этот товар имеет аналогичные характеристики!');
        console.log('='.repeat(80));
        
        const finalConfirm = await askConfirmation('\nОформляем заявку по специальному предложению? (y/n): ');
        if (finalConfirm) {
            const filename = createOrderFile(cheapest, region, cheapestPrice, false);
            console.log(`\n✓ Заявка успешно оформлена!`);
            console.log(`✓ Файл заявки: ${filename}`);
        } else {
            console.log('\nЖаль, что вы отказались. Будем рады видеть вас снова!');
        }
    }
    
    rl.close();
}

main().catch(err => {
    console.error(`\nПроизошла ошибка: ${err.message}`);
    rl.close();
});
