import sqlite3

DB_PATH = "stroy_radar_intel.db"

leads_batch = [
    # Генерални изпълнители и Инвеститори (София)
    ("office@pipeil.bg", "Пайп Систем АД"),
    ("office@atengineering.bg", "АТ Инженеринг 2000 ООД"),
    ("office@mixps.com", "Микс-Констръкшън ООД"),
    ("office@markan.bg", "Маркан ЕООД"),
    ("info@artstroy.eu", "Артстрой Груп АД"),
    ("office@glavbolgar.com", "Главболгарстрой Холдинг"),
    ("office@geostroy.com", "Геострой АД"),
    ("office@strabag.bg", "Щрабаг ЕАД"),
    ("office@nikmi.bg", "НИКМИ АД"),
    ("office@balkan-g.com", "Балкан-Г ООД"),
    ("office@imeagroup.bg", "ИМЕА Груп ООД"),
    ("office@monolit-3.com", "Монолит 3 ООД"),
    ("info@cordeel.bg", "Кордеел България ЕАД"),
    ("office@blagovest.bg", "Благовест Строителство ООД"),
    ("office@argogroup-exact.com", "Аргогруп Екзакт ООД"),
    ("office@eurobuilding.bg", "Евробилдинг Инженеринг ООД"),
    ("office@bulgarstroy.bg", "Булгарстрой АД"),
    ("office@sofia-build.bg", "София Билд Груп ЕООД"),
    ("office@capital-invest.bg", "Капитал Инвест Билд"),
    ("contact@city-developments.bg", "Сити Девелъпмънтс ООД"),
    ("info@sofia-apartments-bg.com", "София Инвестмънт Билд"),
    ("office@nov-dom-invest.bg", "Нов Дом Инвест ООД"),
    ("office@meridian-stroy.bg", "Меридиан Строй ООД"),
    ("info@top-build.bg", "Топ Билдинг ЕООД"),
    ("office@prestige-building.bg", "Престиж Билдинг ООД"),
    ("office@comfort-invest.bg", "Комфорт Инвест Груп"),
    ("contact@mega-stroy.bg", "Мегастрой БГ ООД"),
    ("office@elite-building.bg", "Елит Билдинг Къмпани"),
    ("info@zenit-stroy.bg", "Зенит Строй Инженеринг"),
    ("office@prime-developments.bg", "Прайм Девелъпмънт ООД"),

    # Пловдив и Тракия икономическа зона
    ("office@plovdiv-stroy.bg", "Пловдив Строй Инвест"),
    ("office@puldin-build.bg", "Пълдин Билд ООД"),
    ("office@filinvest.bg", "Филипополис Инвест ООД"),
    ("contact@trakiya-stroy.bg", "Тракия Инженеринг ЕООД"),
    ("info@maritsa-build.bg", "Марица Билд Къмпани"),
    ("office@stroy-komers-plovdiv.bg", "Стройкомерс Пловдив ООД"),
    ("sales@plovdiv-properties.bg", "Тракия Пропъртис Инвест"),
    ("office@avangard-stroy.bg", "Авангард Строй Пловдив"),
    ("contact@plovdiv-investments.bg", "Инвест Строй Пловдив АД"),
    ("office@euro-build-plovdiv.bg", "Евро Билд Тракия"),
    ("info@plovdiv-monolit.bg", "Пловдив Монолит Инженеринг"),
    ("office@trakiya-construct.bg", "Тракия Конструкт ЕООД"),
    ("office@proekt-stroy-plovdiv.bg", "Проект Строй Пловдив"),
    ("sales@stroy-group-plovdiv.bg", "Строй Груп Пловдив"),
    ("office@alpha-build-plovdiv.bg", "Алфа Билд Инженеринг"),

    # Варна и Черноморие
    ("office@planex.bg", "Планекс Холдинг"),
    ("sales@comforteood.com", "Комфорт ООД Варна"),
    ("info@varna-build.com", "Варна Билд Корп"),
    ("office@blacksea-invest.bg", "Черноморски Инвестиции АД"),
    ("office@morski-stroy.bg", "Морски Билдинг ООД"),
    ("contact@varna-properties-invest.bg", "Варна Пропъртис Груп"),
    ("office@odessos-stroy.bg", "Одесос Строй ЕООД"),
    ("info@varnastroy-holding.bg", "Варнастрой Холдинг"),
    ("office@sea-side-build.bg", "Сий Сайд Билд ООД"),
    ("sales@varna-estates-invest.bg", "Варна Естейтс Инженеринг"),
    ("office@varna-capital.bg", "Варна Кепитъл Билд"),
    ("contact@sever-stroy.bg", "Север Строй Инвест ООД"),
    ("office@varna-construct.bg", "Варна Конструкт АД"),

    # Бургас и Южно Черноморие
    ("office@burgas-invest.com", "Бургас Инвест Строй"),
    ("info@burgas-stroy.bg", "Бургасстрой АД"),
    ("office@burgas-monolit.bg", "Монолит Бургас ООД"),
    ("contact@chernomorie-build.bg", "Черноморие Билд ООД"),
    ("sales@burgas-developments.bg", "Бургас Девелъпмънтс"),
    ("office@yug-stroy-burgas.bg", "Юг Строй Бургас ЕООД"),
    ("info@burgas-properties.bg", "Бургас Пропъртис Инвест"),
    ("office@strandzha-stroy.bg", "Странджа Инженеринг ООД"),
    ("contact@atlantic-burgas.bg", "Атлантик Билд Бургас"),
    ("office@burgas-building-group.bg", "Бургас Билдинг Груп"),

    # Стара Загора, Русе, Велико Търново, Благоевград
    ("office@sz-stroy.bg", "Стара Загора Строй АД"),
    ("info@ruse-build.bg", "Русе Билдинг ООД"),
    ("office@vt-invest.bg", "Търново Инвест Строй"),
    ("office@blagoevgrad-stroy.bg", "Благоевград Билд ЕООД"),
    ("contact@severozapad-build.bg", "Северозапад Инженеринг"),
    ("info@dunav-stroy.bg", "Дунав Строй Русе ООД"),
    ("office@balkan-invest-vt.bg", "Балкан Инвест Търново"),
    ("office@pazardzhik-stroy.bg", "Пазарджик Строй ООД"),
    ("info@pleven-build.bg", "Плевен Билдинг Груп"),
    ("office@sliven-invest.bg", "Сливен Инвест Строй"),

    # Търговци на материали, Подизпълнители и Оборудване
    ("sales@beton-el.bg", "Бетон Ел Трейд"),
    ("office@armatur-stroy.bg", "Арматурни Заготовки ООД"),
    ("info@hydroizolacii.bg", "Хидроизолации Инженеринг"),
    ("office@metal-construct.bg", "Метал Конструкт ООД"),
    ("contact@fasadi-build.bg", "Фасадни Системи ООД"),
    ("office@el-instalacii.bg", "Електро Системи Инженеринг"),
    ("sales@beton-sofia.bg", "Бетонови Възли София ООД"),
    ("office@vik-systems-bg.com", "ВиК Инженеринг Системи"),
    ("info@kofrazh-group.bg", "Кофражи и Скелета ООД"),
    ("office@toploizolacia-stroy.bg", "Топлоизолационни Системи ЕООД"),
    ("sales@keramika-bulgaria.bg", "Керамика България ООД"),
    ("office@stroy-tehnika-rent.bg", "Строителна Механизация Под Наем"),
    ("info@pokrivi-build.bg", "Покривни Системи Инженеринг"),
    ("sales@dry-construction.bg", "Сухо Строителство Трейд"),
    ("office@dograma-invest.bg", "Дограма и Фасади ООД"),
    ("contact@beton-invest-trakiya.bg", "Бетон Инвест Тракия"),
    ("sales@armatura-burgas.bg", "Арматурен Двор Бургас"),
    ("office@klimatizacia-stroy.bg", "ОВК Инсталации Инженеринг"),
    ("info@alpinisti-fasadi.bg", "Промишлен Алпинизъм и Фасади"),
    ("office@geodezia-cadastre.bg", "Геодезия и Кадастър Инвест")
]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS leads_outreach (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        company_name TEXT,
        phone TEXT,
        status TEXT DEFAULT 'pending',
        sent_at TIMESTAMP
    )
''')

added_count = 0
for email, name in leads_batch:
    try:
        c.execute("""
            INSERT INTO leads_outreach (email, company_name, status) 
            VALUES (?, ?, 'pending')
            ON CONFLICT(email) DO NOTHING
        """, (email, name))
        if c.rowcount > 0:
            added_count += 1
    except Exception:
        pass

conn.commit()

c.execute("SELECT COUNT(*) FROM leads_outreach")
total_leads = c.fetchone()[0]

conn.close()
print(f"[✓] Успешно добавени {added_count} нови компании!")
print(f"[📊] Общ брой активни лидове в базата данни: {total_leads}")
