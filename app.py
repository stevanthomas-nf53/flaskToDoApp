from flask import Flask, render_template, request, redirect, url_for,jsonify
from datetime import datetime
import sqlite3
import logging
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

app.logger.setLevel("DEBUG")

file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

def init_db() -> None:
    """Initialize SQLite db"""
    app.logger.debug("Connecting to database")
    conn = sqlite3.connect("todos.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS todos(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,priority TEXT,timestamp TEXT,done int)")
    app.logger.debug("Todo table created")
    conn.commit()
    conn.close()


def load_todos() -> list:
    """Load todos from db"""
    conn = sqlite3.connect("todos.db")
    conn.row_factory  = sqlite3.Row
    cursor = conn.cursor()
    todos = cursor.execute("SELECT * FROM todos").fetchall()
    app.logger.debug("Todos fetched")
    conn.close()
    return todos


#Error Handlers

@app.errorhandler(404)
def not_found(e):
    app.logger.error("Page not found")
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error("Server error - 500")
    return render_template("500.html"), 500


#Functions for HTML 
@app.route("/")
def index():
    return render_template("index.html", todos = load_todos())


@app.route("/add", methods=["POST"])
def add():
    conn = sqlite3.connect("todos.db")
    cursor = conn.cursor()
    todo = request.form.get("todo")
    priority = request.form.get("priority")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    # Formatting the todo to check strip white spaces and limit the number of characters so that it doesn't break the UI or the database
    todo = todo.strip()

    if len(todo) <= 200 and todo :
        cursor.execute("INSERT INTO todos (title,priority,timestamp,done) VALUES (?,?,?,0)",(todo,priority,timestamp))
        conn.commit()
        app.logger.info(f"Todo added: {todo}")
    else:
        app.logger.warning("Rejected invalid input")
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    conn = sqlite3.connect("todos.db")
    cursor = conn.cursor()
    cursor.execute ("DELETE FROM todos WHERE id = ?", (todo_id,))
    app.logger.info(f"Todo {todo_id} deleted")
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
def toggle(todo_id):
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE todos SET DONE = NOT DONE WHERE id = ?",(todo_id,))
    app.logger.info(f"Todo {todo_id} status reversed")
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/clearall", methods=["POST"])
def clearall():
    conn = sqlite3.connect("todos.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos")
    cursor.execute("DELETE FROM SQLITE_SEQUENCE WHERE name ='todos'")
    app.logger.info("All todos cleared")
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# API routes

## Gets all todos
@app.route("/api/todos", methods=["GET"]) 
def apigetalltodos() -> dict:
    conn = sqlite3.connect("todos.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    todos = cursor.execute("SELECT * FROM todos").fetchall()
    app.logger.info("API call to fetch all todos")
    conn.commit()
    conn.close()
    row_dict = [dict(row) for row in todos]
    return jsonify(row_dict)

## Gets a specific todo by id
@app.route("/api/todos/<int:todo_id>", methods=["GET"])
def apigetspecifictodo(todo_id) -> dict :
    conn = sqlite3.connect("todos.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    todo = cursor.execute("SELECT * FROM todos WHERE id = ?",(todo_id,)).fetchone()
    app.logger.info(f"API call to fetch Todo {todo_id}")
    conn.commit()
    conn.close()
    row_dict = [dict(todo)]
    return jsonify(row_dict)

## Adds a todo
@app.route("/api/todos",methods=["POST"])
def apiaddtodo():
    conn = sqlite3.connect("todos.db")
    cursor = conn.cursor()
    todo = request.get_json()
    try:
        cursor.execute("INSERT INTO todos (title,priority,timestamp,done) VALUES (?,?,?,0)" ,(todo['title'],todo['priority'],datetime.now().strftime("%Y-%m-%d %H:%M")))
        app.logger.debug(f"Row inserted: {todo}")
        conn.commit()

    except Exception as e:
        app.logger.error(f"Error: {e}")
    conn.close()
    return jsonify(todo),201
    





if __name__ == "__main__":
    init_db()
    app.run(debug=os.getenv("DEBUG","False") == "True")

