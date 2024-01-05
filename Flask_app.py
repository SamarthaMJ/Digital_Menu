from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import base64


# Create a connection to the main database (or create it if it doesn't exist)
conn_main = sqlite3.connect('items_main.db')
cursor_main = conn_main.cursor()

# Create a connection to the removed item's database (or create it if it doesn't exist)
conn_removed = sqlite3.connect('removed_items.db')
cursor_removed = conn_removed.cursor()

# Create tables for main and removed items if they don't exist
cursor_main.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        image BLOB,
        price REAL
    )
''')
conn_main.commit()

cursor_removed.execute('''
    CREATE TABLE IF NOT EXISTS removed_items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        image BLOB,
        price REAL
    )
''')
conn_removed.commit()


# Function to fetch all items from the main database
def get_all_items():
    # Create a connection to the main database (or create it if it doesn't exist)
    conn_main = sqlite3.connect('items_main.db')
    cursor_main = conn_main.cursor()
    cursor_main.execute('SELECT id, name, image, price FROM items')
    items = cursor_main.fetchall()
    return items


# Function to fetch all removed items from the removed items database
def get_all_removed_items():
    # Create a connection to the removed item's database (or create it if it doesn't exist)
    conn_removed = sqlite3.connect('removed_items.db')
    cursor_removed = conn_removed.cursor()
    cursor_removed.execute('SELECT id, name, image, price FROM removed_items')
    removed_items = cursor_removed.fetchall()
    return removed_items


# Function to encode image data to base64 for display
def encode_image(image):
    return base64.b64encode(image).decode('utf-8')


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    conn_main = sqlite3.connect('items_main.db')
    cursor_main = conn_main.cursor()
    if request.method == 'POST':
        name = request.form['name']
        image = request.files['image_path']  # Access the uploaded file
        price = float(request.form['price'])

        if image:
            image_binary = image.read()  # Read the file contents
            cursor_main.execute('INSERT INTO items (name, image, price) VALUES (?, ?, ?)', (name, image_binary, price))
            conn_main.commit()

            return redirect(url_for('index'))
    return render_template('add_item.html')


@app.route('/remove_item', methods=['GET', 'POST'])
def remove_item():
    conn_removed = sqlite3.connect('removed_items.db')
    cursor_removed = conn_removed.cursor()
    conn_main = sqlite3.connect('items_main.db')
    cursor_main = conn_main.cursor()
    if request.method == 'POST':
        item_name = request.form['item_name']

        cursor_main.execute('SELECT * FROM items WHERE name = ?', (item_name,))
        removed_item = cursor_main.fetchone()

        if removed_item:
            cursor_main.execute('DELETE FROM items WHERE name = ?', (item_name,))
            conn_main.commit()

            cursor_removed.execute('INSERT INTO removed_items (name, image, price) VALUES (?, ?, ?)', removed_item[1:])
            conn_removed.commit()

            # Redirect to the view_items route after removal
            return redirect(url_for('index'))
    return render_template('view_items.html', items=get_all_items(), encode_image=encode_image)


@app.route('/view_items')
def view_items():
    items = get_all_items()
    return render_template('view_items.html', items=items, encode_image=encode_image)


@app.route('/display_existing_items')
def display_existing_items():
    items = get_all_items()
    return render_template('counter_display.html', items=items, encode_image=encode_image)


@app.route('/view_removed_items')
def view_removed_items():
    removed_items = get_all_removed_items()
    return render_template('view_removed_items.html', removed_items=removed_items, encode_image=encode_image)


@app.route('/restore_item', methods=['GET', 'POST'])
def restore_item():
    conn_main = sqlite3.connect('items_main.db')
    cursor_main = conn_main.cursor()
    conn_removed = sqlite3.connect('removed_items.db')
    cursor_removed = conn_removed.cursor()

    if request.method == 'POST':
        item_name = request.form['item_name']  # Fetch item name instead of serial number

        cursor_removed.execute('SELECT * FROM removed_items WHERE name = ?', (item_name,))
        restored_item = cursor_removed.fetchone()

        if restored_item:
            cursor_removed.execute('DELETE FROM removed_items WHERE name = ?', (item_name,))
            conn_removed.commit()

            cursor_main.execute('INSERT INTO items (name, image, price) VALUES (?, ?, ?)', restored_item[1:])
            conn_main.commit()

            return redirect(url_for('index'))
    return render_template('view_removed_items.html')


if __name__ == '__main__':
    app.run(debug=True)
