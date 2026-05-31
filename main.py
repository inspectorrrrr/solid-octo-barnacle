import json
import os
from datetime import datetime


def load_catalog(filepath: str = "materials_catalog.json") -> dict:
    """Загружает каталог материалов из JSON-файла"""
    if not os.path.exists(filepath):
        print(f"Ошибка: Файл каталога '{filepath}' не найден!")
        exit(1)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def display_regions(catalog: dict) -> None:
    """Выводит список доступных регионов"""
    print("\n=== Выберите регион ===")
    for idx, region in enumerate(catalog['regions'], 1):
        print(f"  {idx}. {region}")


def get_user_choice(prompt: str, max_value: int) -> int:
    """Получает выбор пользователя с валидацией"""
    while True:
        try:
            choice = int(input(prompt))
            if 1 <= choice <= max_value:
                return choice
            print(f"Ошибка: Введите число от 1 до {max_value}")
        except ValueError:
            print("Ошибка: Введите корректное число")


def display_products_by_region(catalog: dict, region: str) -> None:
    """Выводит список товаров с ценами для выбранного региона"""
    print(f"\n=== Список материалов (регион: {region}) ===")
    print("-" * 80)
    print(f"{'№':<3} | {'Товар':<40} | {'Категория':<15} | {'Цена'}")
    print("-" * 80)
    
    for idx, product in enumerate(catalog['products'], 1):
        price = product['prices'][region]
        name = product['name'][:40] if len(product['name']) > 40 else product['name']
        category = product['category']
        print(f"{idx:<3} | {name:<40} | {category:<15} | {price} руб.")
    
    print("-" * 80)


def get_product_by_index(catalog: dict, index: int) -> dict:
    """Возвращает продукт по индексу (1-based)"""
    return catalog['products'][index - 1]


def find_cheapest_in_category(catalog: dict, category: str, region: str) -> dict:
    """Находит самый дешевый товар в категории для региона"""
    products_in_category = [
        p for p in catalog['products'] 
        if p['category'] == category
    ]
    
    cheapest = min(products_in_category, key=lambda p: p['prices'][region])
    return cheapest


def calculate_discounted_price(price: float, discount_percent: float = 5) -> float:
    """Возвращает цену со скидкой"""
    return price * (1 - discount_percent / 100)


def create_order_file(product: dict, region: str, final_price: float, discount_applied: bool = False) -> str:
    """Создает JSON-файл заявки и возвращает путь к файлу"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"order_{timestamp}.json"
    
    order_data = {
        "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "region": region,
        "product": {
            "id": product['id'],
            "name": product['name'],
            "category": product['category']
        },
        "original_price": product['prices'][region],
        "final_price": final_price,
        "discount_applied": discount_applied,
        "discount_percent": 5 if discount_applied else 0
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(order_data, f, ensure_ascii=False, indent=2)
    
    return filename


def ask_confirmation(prompt: str) -> bool:
    """Запрашивает подтверждение у пользователя (y/n)"""
    while True:
        response = input(prompt).strip().lower()
        if response in ['y', 'yes', 'д', 'да']:
            return True
        elif response in ['n', 'no', 'н', 'нет']:
            return False
        print("Ошибка: Введите 'y' или 'n'")


def run_retention_logic(catalog: dict, product: dict, region: str) -> tuple:
    """
    Логика удержания клиента:
    1. Находит самый дешевый товар в категории
    2. Если текущий товар самый дешевый - предлагает скидку 5%
    3. Иначе предлагает более дешевый аналог
    Возвращает (продукт, финальная_цена, применена_скидка, это_аналог)
    """
    category = product['category']
    current_price = product['prices'][region]
    
    cheapest = find_cheapest_in_category(catalog, category, region)
    cheapest_price = cheapest['prices'][region]
    
    # Если текущий товар - самый дешевый
    if cheapest['id'] == product['id']:
        # Предлагаем скидку 5%
        discounted_price = calculate_discounted_price(current_price, 5)
        return product, discounted_price, True, False
    else:
        # Предлагаем более дешевый аналог
        return cheapest, cheapest_price, False, True


def main():
    """Основная функция приложения"""
    print("=" * 70)
    print("    ФОРМИРОВАНИЕ ЗАЯВКИ")
    print("=" * 70)
    
    # Загружаем каталог
    catalog = load_catalog()
    
    # 1. Выбор региона
    display_regions(catalog)
    region_idx = get_user_choice("Введите номер региона: ", len(catalog['regions']))
    region = catalog['regions'][region_idx - 1]
    print(f"\nВыбран регион: {region}")
    
    # 2. Вывод списка товаров
    display_products_by_region(catalog, region)
    
    # 3. Выбор товара
    product_idx = get_user_choice(
        "Введите номер товара: ", 
        len(catalog['products'])
    )
    product = get_product_by_index(catalog, product_idx)
    price = product['prices'][region]
    
    # 4. Показ заказа
    print("\n" + "=" * 70)
    print("    ВАШ ЗАКАЗ")
    print("=" * 70)
    print(f"  Регион:           {region}")
    print(f"  Товар:            {product['name']}")
    print(f"  Категория:        {product['category']}")
    print(f"  Цена:             {price} руб.")
    print("=" * 70)
    
    # 5. Вопрос о подтверждении
    confirmed = ask_confirmation("\nОформляем заявку? (y/n): ")
    
    if confirmed:
        # Создаем файл заявки
        filename = create_order_file(product, region, price)
        print(f"\n✓ Заявка успешно оформлена!")
        print(f"✓ Файл заявки: {filename}")
        return
    
    # Логика при отказе - удержание клиента
    print("\n" + "=" * 70)
    print("    СПЕЦИАЛЬНОЕ ПРЕДЛОЖЕНИЕ ДЛЯ ВАС!")
    print("=" * 70)
    
    final_product, final_price, discount_applied, is_analogue = run_retention_logic(
        catalog, product, region
    )
    
    if is_analogue:
        # Предлагаем более дешевый аналог
        print(f"\n  Мы можем предложить вам более выгодный вариант в этой категории:")
        print(f"\n  Товар:            {final_product['name']}")
        print(f"  Категория:        {final_product['category']}")
        print(f"  Цена:             {final_price} руб.")
        print(f"  Экономия:         {price - final_price} руб.")
        print("\n  Этот товар имеет аналогичные характеристики!")
    elif discount_applied:
        # Предлагаем скидку (товар уже самый дешевый)
        print(f"\n  Для вас специальная скидка 5% на выбранный товар!")
        print(f"\n  Товар:            {final_product['name']}")
        print(f"  Цена без скидки:  {price} руб.")
        print(f"  Цена со скидкой:  {final_price:.2f} руб.")
        print(f"  Экономия:         {price - final_price:.2f} руб.")
    
    print("=" * 70)
    
    # Финальный вопрос
    final_confirmed = ask_confirmation("\nОформляем заявку по специальному предложению? (y/n): ")
    
    if final_confirmed:
        filename = create_order_file(final_product, region, final_price, discount_applied)
        print(f"\n✓ Заявка успешно оформлена!")
        print(f"✓ Файл заявки: {filename}")
    else:
        print("\nЖаль, что вы отказались. Будем рады видеть вас снова!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nРабота приложения прервана.")
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")
