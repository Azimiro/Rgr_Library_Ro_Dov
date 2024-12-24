import re
from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Функція для підключення до бази даних
def get_db_connection():
    try:
        user = session.get("username") if session.get("role") == "admin" else "guest"
        password = session.get("password") if session.get("role") == "admin" else "admin"
        return psycopg2.connect(
            dbname="library",
            user=user,
            password=password,
            host="localhost",
            port=5432
        )
    except KeyError:
        flash("Сесія недійсна. Будь ласка, увійдіть ще раз.", "danger")
        return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "admin":
            # Обробка входу як адміністратор
            username = request.form.get("username").strip()
            password = request.form.get("password").strip()

            # Перевірка на порожні поля
            if not username or not password:
                flash("Логін і пароль не можуть бути порожніми.", "danger")
                return render_template("login.html")

            # Перевірка логіна на допустимі символи
            if not re.match(r"^[a-zA-Z0-9_]+$", username):
                flash("Логін може містити лише літери, цифри та підкреслення.", "danger")
                return render_template("login.html")

            try:
                conn = psycopg2.connect(
                    dbname="library",
                    user=username,
                    password=password,
                    host="localhost",
                    port=5432
                )
                conn.close()
                session["role"] = "admin"
                session["username"] = username
                session["password"] = password
                flash("Успішний вхід як адміністратор.", "success")
                return redirect(url_for("view_kafedra"))
            except psycopg2.OperationalError as e:
                app.logger.error(f"Database connection failed: {str(e)}")
                flash("Неправильний логін або пароль. Спробуйте ще раз.", "danger")
            except UnicodeDecodeError as e:
                app.logger.error(f"Unicode decoding error: {str(e)}")
                flash("Логін або пароль містять недопустимі символи. Спробуйте ще раз.", "danger")
            except psycopg2.Error as e:
                app.logger.error(f"Database error: {e.pgerror}")
                flash("Сталася помилка бази даних. Зверніться до адміністратора.", "danger")
            return render_template("login.html")
        
        elif action == "guest":
            # Обробка входу як гість
            session["role"] = "guest"
            flash("Успішний вхід як гість.", "success")
            return redirect(url_for("view_kafedra"))
        
        else:
            flash("Невідома дія. Спробуйте ще раз.", "danger")
            return render_template("login.html")
    
    return render_template("login.html")

# Роут для виходу
@app.route('/logout')
def logout():
    try:
        session.clear()
        flash("Ви успішно вийшли.", "info")
        return redirect(url_for('login'))
    except Exception as e:
        app.logger.error(f"Logout error: {str(e)}")
        flash("Сталася помилка під час виходу.", "danger")
        return redirect(url_for('login'))

# Роут для перегляду кафедр
@app.route("/kafedra")
def view_kafedra():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT kafedra_id, name, description FROM kafedra;")
        kafedra_data = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("kafedra.html", kafedra_data=kafedra_data)
    except psycopg2.Error as e:
        app.logger.error(f"Database access error: {e.pgerror}")
        flash(f"Помилка доступу до бази даних. Зверніться до адміністратора.", "danger")
        return redirect(url_for("login"))
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        flash("Сталася помилка. Зверніться до адміністратора.", "danger")
        return redirect(url_for("login"))

# Роут для додавання кафедри
@app.route("/kafedra/add", methods=["GET", "POST"])
def add_kafedra():
    if session.get("role") != "admin":
        flash("У вас немає прав для додавання кафедр.", "danger")
        return redirect(url_for("view_kafedra"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Назва кафедри не може бути порожньою.", "danger")
            return render_template("edit_kafedra.html", action="Додати", kafedra=None)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO kafedra (name, description) VALUES (%s, %s);", (name, description))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Кафедра успішно додана.", "success")
            return redirect(url_for("view_kafedra"))
        except psycopg2.Error as e:
            app.logger.error(f"Database error: {e.pgerror}")
            flash(f"Помилка роботи з базою даних. Зверніться до адміністратора.", "danger")
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            flash("Сталася помилка. Зверніться до адміністратора.", "danger")
    return render_template("edit_kafedra.html", action="Додати", kafedra=None)

# Роут для редагування кафедри
@app.route("/kafedra/edit/<int:kafedra_id>", methods=["GET", "POST"])
def edit_kafedra(kafedra_id):
    if session.get("role") != "admin":
        flash("У вас немає прав для редагування кафедр.", "danger")
        return redirect(url_for("view_kafedra"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Назва кафедри не може бути порожньою.", "danger")
            return redirect(url_for("edit_kafedra", kafedra_id=kafedra_id))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE kafedra SET name = %s, description = %s WHERE kafedra_id = %s;",
                (name, description, kafedra_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Кафедра успішно оновлена.", "success")
            return redirect(url_for("view_kafedra"))
        except psycopg2.Error as e:
            app.logger.error(f"Database error: {e.pgerror}")
            flash(f"Помилка роботи з базою даних. Зверніться до адміністратора.", "danger")
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            flash("Сталася помилка. Зверніться до адміністратора.", "danger")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, description FROM kafedra WHERE kafedra_id = %s;", (kafedra_id,))
        kafedra = cursor.fetchone()
        cursor.close()
        conn.close()

        if kafedra is None:
            flash("Кафедра не знайдена.", "danger")
            return redirect(url_for("view_kafedra"))

        return render_template("edit_kafedra.html", action="Редагувати", kafedra={"name": kafedra[0], "description": kafedra[1]})
    except psycopg2.Error as e:
        app.logger.error(f"Database error: {e.pgerror}")
        flash(f"Помилка роботи з базою даних. Зверніться до адміністратора.", "danger")
        return redirect(url_for("view_kafedra"))
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        flash("Сталася помилка. Зверніться до адміністратора.", "danger")
        return redirect(url_for("view_kafedra"))

# Роут для видалення кафедри
@app.route("/kafedra/delete/<int:kafedra_id>", methods=["POST"])
def delete_kafedra(kafedra_id):
    if session.get("role") != "admin":
        flash("У вас немає прав для видалення кафедр.", "danger")
        return redirect(url_for("view_kafedra"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kafedra WHERE kafedra_id = %s;", (kafedra_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Кафедра успішно видалена.", "success")
    except psycopg2.Error as e:
        app.logger.error(f"Database error: {e.pgerror}")
        flash(f"Помилка роботи з базою даних. Зверніться до адміністратора.", "danger")
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        flash("Сталася помилка. Зверніться до адміністратора.", "danger")
    return redirect(url_for("view_kafedra"))

@app.route("/predmet/<int:kafedra_id>")
def view_predmet(kafedra_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT predmet_id, name, description FROM predmet WHERE kafedra_id = %s;", (kafedra_id,))
        predmet_data = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("predmet.html", predmet_data=predmet_data, kafedra_id=kafedra_id)
    except psycopg2.Error as e:
        app.logger.error(f"Database access error: {e.pgerror}")
        flash(f"Помилка доступу до бази даних. Зверніться до адміністратора.", "danger")
        return redirect(url_for("view_kafedra"))
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        flash("Сталася помилка. Зверніться до адміністратора.", "danger")
        return redirect(url_for("view_kafedra"))


@app.route("/predmet/add/<int:kafedra_id>", methods=["GET", "POST"])
def add_predmet(kafedra_id):
    if session.get("role") != "admin":
        flash("У вас немає прав для додавання предметів.", "danger")
        return redirect(url_for("view_predmet", kafedra_id=kafedra_id))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        if not name or not description:
            flash("Назва та опис не можуть бути порожніми.", "danger")
            return render_template("edit_predmet.html", action="Додати", predmet=None, kafedra_id=kafedra_id)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO predmet (name, description, kafedra_id) VALUES (%s, %s, %s);",
                (name, description, kafedra_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Предмет успішно додано.", "success")
            return redirect(url_for("view_predmet", kafedra_id=kafedra_id))
        except psycopg2.Error as e:
            app.logger.error(f"Database error: {e.pgerror}")
            flash(f"Помилка роботи з базою даних. Зверніться до адміністратора.", "danger")
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            flash("Сталася помилка. Зверніться до адміністратора.", "danger")

    return render_template("edit_predmet.html", action="Додати", predmet=None, kafedra_id=kafedra_id)


@app.route("/predmet/edit/<int:predmet_id>", methods=["GET", "POST"])
def edit_predmet(predmet_id):
    if session.get("role") != "admin":
        flash("У вас немає прав для редагування предметів.", "danger")
        return redirect(url_for("view_kafedra"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Отримуємо kafedra_id
        cursor.execute("SELECT kafedra_id FROM predmet WHERE predmet_id = %s;", (predmet_id,))
        result = cursor.fetchone()
        if not result:
            flash("Предмет не знайдено.", "danger")
            return redirect(url_for("view_kafedra"))
        kafedra_id = result[0]

        if request.method == "POST":
            name = request.form.get("name")
            description = request.form.get("description")
            if not name or not description:
                flash("Назва та опис не можуть бути порожніми.", "danger")
                return redirect(request.url)

            cursor.execute(
                "UPDATE predmet SET name = %s, description = %s WHERE predmet_id = %s;",
                (name, description, predmet_id),
            )
            conn.commit()
            flash("Предмет успішно оновлено.", "success")
            return redirect(url_for("view_predmet", kafedra_id=kafedra_id))

        # Отримуємо дані предмета
        cursor.execute("SELECT name, description FROM predmet WHERE predmet_id = %s;", (predmet_id,))
        predmet = cursor.fetchone()
        cursor.close()
        conn.close()

        predmet_dict = {"name": predmet[0], "description": predmet[1]} if predmet else None
        return render_template("edit_predmet.html", action="Редагувати", predmet=predmet_dict, kafedra_id=kafedra_id)
    except psycopg2.Error as e:
            app.logger.error(f"Database error: {e.pgerror}")
            flash(f"Помилка роботи з базою даних. Зверніться до адміністратора.", "danger")
    except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            flash("Сталася помилка. Зверніться до адміністратора.", "danger")


@app.route("/predmet/delete/<int:predmet_id>", methods=["POST"])
def delete_predmet(predmet_id):
    if session.get("role") != "admin":
        flash("У вас немає прав для видалення предметів.", "danger")
        return redirect(url_for("view_kafedra"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Отримуємо kafedra_id
        cursor.execute("SELECT kafedra_id FROM predmet WHERE predmet_id = %s;", (predmet_id,))
        result = cursor.fetchone()
        if not result:
            flash("Предмет не знайдено.", "danger")
            return redirect(url_for("view_kafedra"))

        kafedra_id = result[0]

        # Видаляємо предмет
        cursor.execute("DELETE FROM predmet WHERE predmet_id = %s;", (predmet_id,))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Предмет успішно видалено.", "success")
        return redirect(url_for("view_predmet", kafedra_id=kafedra_id))
    except psycopg2.Error as e:
        app.logger.error(f"Database error: {e.pgerror}")
        flash(f"Помилка роботи з базою даних. Зверніться до адміністратора.", "danger")
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        flash("Сталася помилка. Зверніться до адміністратора.", "danger")

@app.route("/literatura/<int:predmet_id>")
def view_literatura(predmet_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Отримуємо kafedra_id на основі predmet_id
        cursor.execute("SELECT kafedra_id FROM predmet WHERE predmet_id = %s;", (predmet_id,))
        result = cursor.fetchone()
        if not result:
            flash("Кафедру не знайдено для предмета.", "danger")
            return redirect(url_for("view_kafedra"))
        kafedra_id = result[0]

        # Отримуємо літературу для обраного предмета
        cursor.execute("SELECT literatura_id, title, author, year, description FROM literatura WHERE predmet_id = %s;", (predmet_id,))
        literatura_data = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("literatura.html", literatura_data=literatura_data, predmet_id=predmet_id, kafedra_id=kafedra_id)
    except psycopg2.Error as e:
        app.logger.error(f"Database access error: {e.pgerror}")
        flash(f"Помилка доступу до бази даних. Зверніться до адміністратора.", "danger")
        return redirect(url_for("view_kafedra"))
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        flash("Сталася помилка. Зверніться до адміністратора.", "danger")
        return redirect(url_for("view_kafedra"))


@app.route("/literatura/add/<int:predmet_id>", methods=["GET", "POST"])
def add_literatura(predmet_id):
    if session.get("role") != "admin":
        flash("У вас немає прав для додавання літератури.", "danger")
        return redirect(url_for("view_literatura", predmet_id=predmet_id))

    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        year = request.form.get("year")
        description = request.form.get("description")

        if not title or title.strip() == "":
            flash("Поле 'Назва' не може бути порожнім.", "danger")
            return render_template("edit_literatura.html", action="Додати", literatura=None, predmet_id=predmet_id)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO literatura (title, author, year, description, predmet_id) VALUES (%s, %s, %s, %s, %s);",
                (title, author, year, description, predmet_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Література успішно додана.", "success")
            return redirect(url_for("view_literatura", predmet_id=predmet_id))
        except psycopg2.Error as e:
            app.logger.error(f"Database error: {e.pgerror}")
            flash(f"Помилка роботи з базою даних. Зверніться до адміністратора.", "danger")
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            flash("Сталася помилка. Зверніться до адміністратора.", "danger")

    return render_template("edit_literatura.html", action="Додати", literatura=None, predmet_id=predmet_id)


@app.route("/literatura/edit/<int:literatura_id>", methods=["GET", "POST"])
def edit_literatura(literatura_id):
    if session.get("role") != "admin":
        flash("У вас немає прав для редагування літератури.", "danger")
        return redirect(url_for("view_kafedra"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        year = request.form.get("year")
        description = request.form.get("description")

        if not title or title.strip() == "":
            flash("Поле 'Назва' не може бути порожнім.", "danger")
            return redirect(url_for("edit_literatura", literatura_id=literatura_id))

        try:
            cursor.execute(
                "UPDATE literatura SET title = %s, author = %s, year = %s, description = %s WHERE literatura_id = %s;",
                (title, author, year, description, literatura_id),
            )
            conn.commit()

            # Отримуємо `predmet_id` для повернення
            cursor.execute("SELECT predmet_id FROM literatura WHERE literatura_id = %s;", (literatura_id,))
            predmet_id = cursor.fetchone()[0]

            flash("Дані успішно оновлено.", "success")
            return redirect(url_for("view_literatura", predmet_id=predmet_id))
        except psycopg2.Error as e:
            app.logger.error(f"Database error: {e.pgerror}")
            flash(f"Помилка роботи з базою даних. Зверніться до адміністратора.", "danger")
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            flash("Сталася помилка. Зверніться до адміністратора.", "danger")
    else:
        cursor.execute("SELECT title, author, year, description, predmet_id FROM literatura WHERE literatura_id = %s;", (literatura_id,))
        literatura = cursor.fetchone()
        if literatura is None:
            flash("Кафедра не знайдена.", "danger")
            return redirect(url_for("view_kafedra"))

        title, author, year, description, predmet_id = literatura

    cursor.close()
    conn.close()

    return render_template(
        "edit_literatura.html",
        action="Редагувати",
        literatura={"title": title, "author": author, "year": year, "description": description},
        predmet_id=predmet_id
    )


@app.route("/literatura/delete/<int:literatura_id>", methods=["POST"])
def delete_literatura(literatura_id):
    if session.get("role") != "admin":
        flash("У вас немає прав для видалення літератури.", "danger")
        return redirect(url_for("view_kafedra"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT predmet_id FROM literatura WHERE literatura_id = %s;", (literatura_id,))
        result = cursor.fetchone()
        if not result:
            flash("Предмет не знайдено для цієї літератури.", "danger")
            return redirect(url_for("view_kafedra"))

        predmet_id = result[0]
        cursor.execute("DELETE FROM literatura WHERE literatura_id = %s;", (literatura_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Література успішно видалена.", "success")
    except psycopg2.Error as e:
        app.logger.error(f"Database error: {e.pgerror}")
        flash(f"Помилка роботи з базою даних. Зверніться до адміністратора.", "danger")
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        flash("Сталася помилка. Зверніться до адміністратора.", "danger")

    return redirect(url_for("view_literatura", predmet_id=predmet_id))

if __name__ == "__main__":
    app.run(debug=True)
