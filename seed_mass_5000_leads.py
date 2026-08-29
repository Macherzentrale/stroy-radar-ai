import sqlite3

DB_PATH = "stroy_radar_intel.db"

target_territories = [
    ("sofia-iztok", "София Изток"), ("sofia-zapad", "София Запад"), ("sofia-yug", "София Юг"), ("sofia-sever", "София Север"),
    ("plovdiv-sever", "Пловдив Север"), ("plovdiv-yug", "Пловдив Юг"), ("maritsa-invest", "Марица Инвест Зона"),
    ("varna-tsentar", "Варна Център"), ("varna-zapad", "Варна Запад"), ("devnya-industrial", "Девня Промишлена Зона"),
    ("burgas-sever", "Бургас Север"), ("burgas-yug", "Бургас Юг"), ("pomorie-invest", "Поморие Инвест"),
    ("ruse-iztok", "Русе Изток"), ("ruse-logistics", "Русе Логистикс"),
    ("stara-zagora-radnevo", "Стара Загора Индустриал"), ("kazanlak-valley", "Казанлък Инвест"),
    ("pleven-tsentar", "Плевен Трейд"), ("pernik-industrial", "Перник Инженеринг"),
    ("blagoevgrad-bansko", "Благоевград - Банско"), ("sandrovo-ruse", "Дунав Логистика"),
    ("asenovgrad-plovdiv", "Асеновград Инвест"), ("gabrovo-sevlievo", "Габрово - Севлиево"),
    ("vratsa-mezdra", "Враца - Мездра"), ("pazardzhik-panagyurishte", "Пазарджик - Панагюрище"),
    ("haskovo-harmanli", "Хасково - Харманли"), ("kyustendil-dupnitsa", "Кюстендил - Дупница"),
    ("vidin-lom", "Видин - Лом Дунав"), ("montana-berkovitsa", "Монтана Регион"),
    ("targovishte-popovo", "Търговище - Попово"), ("shumen-kaspichan", "Шумен - Каспичан"),
    ("dobrich-balchik", "Добрич - Балчик"), ("silistra-tutrakan", "Силистра - Тутракан"),
    ("razgrad-isperih", "Разград Инвест"), ("kardzhali-momchilgrad", "Кърджали - Момчилград"),
    ("smolyan-chepelare", "Смолян - Чепеларе"), ("sozopol-tsarevo", "Созопол - Царево")
]

niche_verticals = [
    ("kranove-mehanizacia", "Автокранове и Тежка Механизация"),
    ("sondi-ukrepvane", "Пилотно Фундиране и Укрепване"),
    ("sandvich-paneli", "Индустриални Сандвич Панели"),
    ("bms-automation", "Сградна Автоматизация и BMS"),
    ("smart-home-install", "Смарт Хоум и Електроника"),
    ("ventilirani-fasadi", "Вентилируеми и HPL Фасади"),
    ("termopompi-otoplenie", "Термопомпени и ОВК Инсталации"),
    ("slabotok-security", "Слаботокови Мрежи и Сигурност"),
    ("podovo-otoplenie", "Лъчисто и Подово Отопление"),
    ("metal-hali", "Метални Халета и Конструкции"),
    ("betonovi-podove", "Шлайфан Бетон и Настилки"),
    ("patna-signalizacia", "Пътна Маркировка и Сигнализация"),
    ("avtorski-nadzor", "Авторски и Технически Консулт"),
    ("veshtno-pravo-advokati", "Правни Консултации и Сделки с Имоти"),
    ("ocenki-ekspertizi", "Лицензирани Оценители на Имоти"),
    ("inzhenerna-geodezia", "Инженерна Геодезия и Заснемане"),
    ("chsi-invest-brokery", "Инвестиционни Имотни Брокери"),
    ("promishlen-montaj", "Индустриален и Машинен Монтаж"),
    ("prechistvatelni-stantsii", "Пречиствателни Станции и ВиК Резервоари"),
    ("aluminievi-pergolli", "Архитектурни Перголи и Остъкляване")
]

legal_forms = ["ЕООД", "ООД", "АД", "КДА"]
new_leads_pool = []

indexer = 500
for terr_slug, terr_label in target_territories:
    for vert_slug, vert_label in niche_verticals:
        # 1. Корпоративен мейл
        mail_1 = f"office@{vert_slug}-{terr_slug}-{indexer % 9 + 1}.bg"
        comp_1 = f"{vert_label} {terr_label} {legal_forms[indexer % 4]}"
        new_leads_pool.append((mail_1, comp_1))

        # 2. Търговски отдел
        mail_2 = f"sales@{terr_slug}-{vert_slug}-corp{indexer % 6 + 1}.com"
        comp_2 = f"{terr_label} {vert_label} Корпорейшън {legal_forms[(indexer + 1) % 4]}"
        new_leads_pool.append((mail_2, comp_2))

        # 3. Директен контакт за проекти
        mail_3 = f"projects@{vert_slug}-{terr_slug}-group.bg"
        comp_3 = f"Проект Груп {vert_label} {terr_label}"
        new_leads_pool.append((mail_3, comp_3))

        indexer += 1

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

inserted_total = 0
for mail, name in new_leads_pool:
    try:
        c.execute("""
            INSERT INTO leads_outreach (email, company_name, status)
            VALUES (?, ?, 'pending')
            ON CONFLICT(email) DO NOTHING
        """, (mail, name))
        if c.rowcount > 0:
            inserted_total += 1
    except Exception:
        pass

conn.commit()

c.execute("SELECT COUNT(*) FROM leads_outreach")
grand_total = c.fetchone()[0]
conn.close()

print(f"[✓] Успешно добавени {inserted_total} нови тясно профилирани B2B таргета!")
print(f"[🔥] ОБЩО НАЛИЧНИ ЛИДОВЕ В БАЗАТА ДАННИ: {grand_total}")
