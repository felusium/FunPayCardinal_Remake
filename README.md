# FunPay Cardinal Remake

Модифікована збірка FunPayCardinalRemake для автоматизації роботи з FunPay.

У цій версії прибрані рекламні інтеграції, віддалені оголошення, автозавантаження оновлень і автоматична зміна профілю Telegram-бота. Інтерфейс бота залишено тільки українською мовою, а всі суми для користувача показуються в UAH.

## Можливості

- Автовидача товарів.
- Автопідняття лотів.
- Автовідповідь на налаштовані команди.
- Автовідновлення лотів після продажу.
- Автодеактивація лотів, якщо товари закінчилися.
- Сповіщення про замовлення, повідомлення та зміни в Telegram.
- Керування налаштуваннями через Telegram-панель.
- Окремі налаштування сповіщень для кожного авторизованого Telegram-акаунта.
- Підтримка шаблонів і змінних у текстах.
- Система плагінів для розширення функціональності.
- Ручний вивід коштів через збережені гаманці FunPay.

## Що змінено

- Видалено авторські рекламні посилання та згадки.
- Видалено віддалені оголошення і завантаження рекламних фото.
- Видалено приховані preview-посилання на сторонні зображення.
- Вимкнено автооновлення з чужих джерел.
- Вимкнено автоматичну зміну назви й опису Telegram-бота.
- Прибрано вимогу, щоб username Telegram-бота починався з `funpay`.
- Видалено сторонні Telegram-канали, донати й чати.
- Видалено команди та обробники backup-архівів.
- Видалено водяний знак і автоматичне додавання підпису в повідомлення.
- Видалено зайві команди Telegram-меню: `/about`, `/sys`, `/power_off`, `/upload_chat_img`, `/upload_offer_img`.
- Залишено тільки українську локалізацію бота.
- Профіль, сповіщення, покупки та ручний вивід показуються в UAH.
- Неавторизований користувач отримує коротку відповідь `⛔ У тебе немає доступу`.
- Авторизовані користувачі отримують критичне сповіщення про спробу входу стороннього користувача.
- Сповіщення про нове замовлення приходить незалежно від того, чи прив'язана до лота автовидача.
- Очищено тимчасові файли, кеші, старі update-файли та funding-налаштування.

## Важливо

Після налаштування не публікуйте й не передавайте іншим людям:

- `golden_key`;
- токен Telegram-бота;
- файли з `configs/`;
- файли з `storage/`;
- логи з `logs/`;
- приватні архіви з даними бота.

Ці дані можуть дати доступ до вашого акаунта або панелі керування.

## Встановлення на Windows

1. Встановіть Python 3.11 або новіше.
2. Під час встановлення Python увімкніть `Add python.exe to PATH`.
3. Скачайте архів проєкту зі сторінки репозиторію або з розділу Releases.
4. Розпакуйте архів у зручну папку.
5. Запустіть `Setup.bat` і дочекайтеся встановлення залежностей.
6. Запустіть `Start.bat`.
7. При першому запуску пройдіть налаштування в консолі.

Якщо вікно одразу закривається, відкрийте папку проєкту в `cmd` або PowerShell і виконайте:

```bat
python main.py
```

## Встановлення на Ubuntu/Debian

Автоматичний встановлювач підходить для Ubuntu/Debian-серверів із `systemd`.

```bash
wget https://raw.githubusercontent.com/felusium/FunPayCardinal_Remake/main/install-fpc.sh -O install-fpc.sh && bash install-fpc.sh
```

Встановлювач:

- завантажує файли тільки з цього репозиторію;
- встановлює системні залежності;
- створює окремого Linux-користувача для запуску;
- створює віртуальне оточення Python;
- встановлює Python-залежності з `requirements.txt`;
- створює systemd-сервіс `FunPayCardinalRemake`;
- пропонує додати сервіс в автозапуск;
- запускає первинне налаштування.

При повторному запуску встановлювач оновлює файли проєкту, але не видаляє приватні папки:

- `configs/`;
- `storage/`;
- `plugins/`;
- `logs/`.

Корисні команди після встановлення:

```bash
sudo systemctl status FunPayCardinalRemake@fpc.service -n 100
sudo systemctl stop FunPayCardinalRemake@fpc.service
sudo systemctl start FunPayCardinalRemake@fpc.service
sudo systemctl restart FunPayCardinalRemake@fpc.service
sudo systemctl enable FunPayCardinalRemake@fpc.service
sudo journalctl -u FunPayCardinalRemake@fpc.service -n 100 --no-pager
```

Якщо під час встановлення ви вказали іншого Linux-користувача замість `fpc`, замініть `fpc` у командах на своє ім'я користувача.

## Ручне встановлення на Linux

Цей варіант підходить для Linux без автоматичного встановлювача або якщо потрібно запускати бота вручну без `systemd`.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
git clone https://github.com/felusium/FunPayCardinal_Remake.git
cd FunPayCardinal_Remake
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
python main.py
```

Для повторного запуску:

```bash
cd FunPayCardinal_Remake
source .venv/bin/activate
python main.py
```

## Встановлення на Android через Termux

Termux не використовує `systemd`, тому Ubuntu-встановлювач для нього не підходить. Запускайте бота вручну або через `tmux`.

```bash
pkg update && pkg upgrade
pkg install python git clang rust make pkg-config libjpeg-turbo zlib libxml2 libxslt openssl libffi
git clone https://github.com/felusium/FunPayCardinal_Remake.git
cd FunPayCardinal_Remake
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install --no-cache-dir -r requirements.txt
python main.py
```

Щоб бот продовжував працювати після закриття сесії, використовуйте `tmux`:

```bash
pkg install tmux
termux-wake-lock
cd FunPayCardinal_Remake
tmux new -s fpc
source .venv/bin/activate
python main.py
```

Вийти з `tmux`, не зупиняючи бота: натисніть `Ctrl+B`, потім `D`.

Повернутися до бота:

```bash
tmux attach -t fpc
```

На Android робота у фоні залежить від прошивки та енергозбереження. Для стабільності вимкніть оптимізацію батареї для Termux.

## Плаґіни

Не встановлюйте плаґіни з неперевірених джерел. Плаґін виконується як звичайний Python-код і може отримати доступ до файлів, конфігів та акаунта.

Встановлення плаґіна через Telegram-панель:

1. Напишіть Telegram-боту команду `/menu`.
2. Відкрийте розділ `Плаґіни`.
3. Натисніть `Додати плаґін`.
4. Відправте файл плаґіна.
5. Перезапустіть бота.

## Курси та UAH

Бот показує суми в UAH через прямий курс FunPay з виводу на банківську карту UA.
Наприклад, якщо FunPay показує `курс 0.543`, то `4674.86 ₽` рахується як `4674.86 × 0.543`.

```text
/UAH
/UAH 0.543
/UAH auto
```

Команда `/usdt` залишена як сумісний alias для старих установок, але теж працює з прямим курсом UAH/RUB.

```text
/usdt
/usdt 0.543
/usdt auto
```

Покупки, баланс у `/profile` і ручний вивід відображаються прямим перерахунком у UAH без додаткової 6% комісії в боті.

## Оновлення

Автоматичні оновлення з чужих джерел вимкнені.

Щоб оновити проєкт вручну:

1. Зупиніть бота.
2. Збережіть приватні папки `configs/`, `storage/` і `plugins/`.
3. Скачайте нову версію вручну або запустіть `/update`, якщо хочете оновитися з цього репозиторію.
4. Перевірте роботу бота перед запуском у постійному режимі.

На Ubuntu/Debian можна повторно запустити `install-fpc.sh`: він оновить файли проєкту та збереже `configs/`, `storage/`, `plugins/`, `logs/`.

## Відповідальність

Використовуйте проєкт на свій ризик. Дотримуйтеся правил FunPay, Telegram і GitHub. Не публікуйте приватні ключі, токени, cookie, конфіги, товари й логи.
