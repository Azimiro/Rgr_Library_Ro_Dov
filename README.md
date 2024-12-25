# Database Project

This project is about using a database in a Python web application. This web application makes it easy to manage a library database.

## Встановлення та запуск проєкту

1. Переконайтеся, що у вас встановлений Python версії 3.12.8, JDK 21 та PostgreSQL.
2. Встановити IDE VScode для запуску проєкту.
3. Завантажте проєкт та відкрийте його в IDE VScode.
4. Підключіть до проєкту Python версії 3.12.8 та створіть віртуальне середовище.
5. Налаштуйте базу даних у PostgreSQL.
6. Якщо змінили базу даних у PostgreSQL, знайдіть у файлі `main.py` коментар: `# Функція для підключення до бази даних`, та в коді вкажіть свої дані для підключення до бази. Наприклад:
   ```python
   dbname="library"
   user="user"
   password="password"
   host="localhost"
   port=5432
   ```
7. Запустіть головний файл `main.py`.
8. Відкрийте браузер і перейдіть за адресою: [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login).
9. Щоб зупинити програму, у консолі IDE VScode натисніть сполучення клавіш `Ctrl+C`.

## Підключення до проєкту Python та створення віртуального середовища

1. Відкрийте проєкт в IDE VScode.
2. Натисніть сполучення клавіш `Ctrl+Shift+P`.
3. У полі, що з'явилося, напишіть: `Python: Select Interpreter`.
4. Виберіть опцію створення віртуального середовища.
5. Оберіть `Venv`.
6. Потім виберіть `Використовувати існуюче`.
7. Якщо все виконано правильно, IDE VScode автоматично підключить Python та створить віртуальне середовище.

## Налаштування бази даних у PostgreSQL

1. Відкрийте PostgreSQL та створіть нову базу даних під назвою: `library`.
2. Клацніть ПКМ по базі даних `library` та виберіть створення скрипта (Create script).
3. Виконайте скрипт для створення таблиць та користувачів:
   ```sql
   -- Створення бази даних
   CREATE DATABASE university_db;

   -- Переключення на базу даних
   \c university_db;

   -- Створення таблиці користувачів
   CREATE TABLE users (
       id SERIAL PRIMARY KEY,
       username VARCHAR(50) UNIQUE NOT NULL,
       password VARCHAR(255) NOT NULL,
       role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'guest'))
   );

   -- Створення таблиці кафедр
   CREATE TABLE kafedra (
       id SERIAL PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       description TEXT
   );

   -- Створення таблиці предметів
   CREATE TABLE predmet (
       id SERIAL PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       kafedra_id INT NOT NULL,
       description TEXT,
       FOREIGN KEY (kafedra_id) REFERENCES kafedra (id) ON DELETE CASCADE
   );

   -- Створення таблиці літератури
   CREATE TABLE literatura (
       id SERIAL PRIMARY KEY,
       title VARCHAR(255) NOT NULL,
       author VARCHAR(100),
       predmet_id INT NOT NULL,
       type VARCHAR(50) NOT NULL CHECK (type IN ('book', 'article', 'other')),
       FOREIGN KEY (predmet_id) REFERENCES predmet (id) ON DELETE CASCADE
   );

   -- Додавання двох користувачів
   INSERT INTO users (username, password, role) VALUES
   ('admin', crypt('admin_password', gen_salt('bf')), 'admin'),
   ('guest', crypt('guest_password', gen_salt('bf')), 'guest');

   -- Створення ролей
   DO $$
   BEGIN
       IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin') THEN
           CREATE ROLE admin LOGIN PASSWORD 'admin_password';
       END IF;

       IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'guest') THEN
           CREATE ROLE guest LOGIN PASSWORD 'guest_password';
       END IF;
   END $$;

   -- Прив’язка ролей до користувачів
   GRANT CONNECT ON DATABASE university_db TO admin, guest;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO admin;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO guest;

   -- Автоматичне надання прав на майбутні таблиці
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO admin;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO guest;
   ```
4. Якщо все виконано за інструкцією, база даних буде успішно створена.

## Проблеми, які можуть виникнути під час встановлення проєкту

1. **Відсутність бібліотек `flask` та `psycopg2`.**
   - Вирішення: Відкрити термінал у VScode та встановити бібліотеки за допомогою команди:
     ```bash
     pip install flask psycopg2
     ```

2. **Помилка встановлення бібліотеки `psycopg2`.**
   - Вирішення: Завантажити та встановити [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/ru/visual-cpp-build-tools/).
   - Після встановлення у програмі оберіть `Desktop development with C++` та встановіть необхідні пакети.
   - Потім повторно виконайте команду:
     ```bash
     pip install psycopg2
     ```

3. **JDK21 не виявляється IDE VScode.**
   - Вирішення: Налаштуйте змінні оточення. [Інструкція з налаштування](https://www.youtube.com/watch?v=_g-mH7NUowI).
