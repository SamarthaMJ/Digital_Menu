from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import base64
import io
import PIL.Image
from PIL import Image


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
        price REAL,
        category TEXT
    )
''')
conn_main.commit()

cursor_removed.execute('''
    CREATE TABLE IF NOT EXISTS removed_items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        image BLOB,
        price REAL,
        category TEXT
    )
''')
conn_removed.commit()

# Create a connection to the special items database (or create it if it doesn't exist)
conn_special = sqlite3.connect('special_items.db')
cursor_special = conn_special.cursor()

# Create a table for special items if it doesn't exist
cursor_special.execute('''
    CREATE TABLE IF NOT EXISTS special_items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        image BLOB,
        price REAL,
        category TEXT
    )
''')
conn_special.commit()

# Create a connection to the removed special items database (or create it if it doesn't exist)
conn_removed_special = sqlite3.connect('removed_special_items.db')
cursor_removed_special = conn_removed_special.cursor()

# Create a table for removed special items if it doesn't exist
cursor_removed_special.execute('''
    CREATE TABLE IF NOT EXISTS removed_special_items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        image BLOB,
        price REAL,
        category TEXT
    )
''')
conn_removed_special.commit()

def resize_image(image):
    img = Image.open(image)
    img = img.resize((125, 125), PIL.Image.LANCZOS)
    return img

def get_all_special_items_grouped_by_category():
    conn_special = sqlite3.connect('special_items.db')
    cursor_special = conn_special.cursor()
    cursor_special.execute('SELECT id, name, image, price, category FROM special_items ORDER BY category')
    special_items = cursor_special.fetchall()

    grouped_special_items = {}
    for special_item in special_items:
        category = special_item[4]
        if category not in grouped_special_items:
            grouped_special_items[category] = []
        grouped_special_items[category].append(special_item)

    return grouped_special_items


def get_all_items_grouped_by_category():
    conn_main = sqlite3.connect('items_main.db')
    cursor_main = conn_main.cursor()
    cursor_main.execute('SELECT id, name, image, price, category FROM items ORDER BY category')
    items = cursor_main.fetchall()

    grouped_items = {}
    for item in items:
        category = item[4]
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append(item)

    return grouped_items


def get_all_removed_items_grouped_by_category():
    conn_removed = sqlite3.connect('removed_items.db')
    cursor_removed = conn_removed.cursor()
    cursor_removed.execute('SELECT id, name, image, price, category FROM removed_items ORDER BY category')
    removed_items = cursor_removed.fetchall()

    grouped_removed_items = {}
    for removed_item in removed_items:
        category = removed_item[4]
        if category not in grouped_removed_items:
            grouped_removed_items[category] = []
        grouped_removed_items[category].append(removed_item)

    return grouped_removed_items


def get_all_removed_special_items_grouped_by_category():
    conn_removed_special = sqlite3.connect('removed_special_items.db')
    cursor_removed_special = conn_removed_special.cursor()
    cursor_removed_special.execute('SELECT id, name, image, price, category FROM removed_special_items ORDER BY category')
    removed_special_items = cursor_removed_special.fetchall()

    grouped_removed_special_items = {}
    for removed_special_item in removed_special_items:
        category = removed_special_item[4]
        if category not in grouped_removed_special_items:
            grouped_removed_special_items[category] = []
        grouped_removed_special_items[category].append(removed_special_item)

    return grouped_removed_special_items


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
    conn_special = sqlite3.connect('special_items.db')
    cursor_special = conn_special.cursor()

    if request.method == 'POST':
        name = request.form['name']
        image = request.files['image_path']  # Access the uploaded file
        price = float(request.form['price'])
        is_special = 'special' in request.form  # Check if the item is special
        category = request.form['category']

        if image:
            # Resize the image before saving
            resized_image = resize_image(image)
            img_io = io.BytesIO()

            # Get the file extension in lowercase
            file_extension = image.filename.split('.')[-1].lower()

            # Map common extensions to PIL formats
            PIL_formats = {
                'jpg': 'JPEG',
                'jpeg': 'JPEG',
                'png': 'PNG',
                'gif': 'GIF'
                # Add more if needed
            }

            # Save the image using the appropriate format
            pil_format = PIL_formats.get(file_extension, 'JPEG')  # Default to JPEG if extension not found
            resized_image.save(img_io, format=pil_format)
            image_binary = img_io.getvalue()

            if is_special:
                cursor_special.execute('INSERT INTO special_items (name, image, price, category) VALUES (?, ?, ?, ?)',
                                       (name, image_binary, price, category))
                conn_special.commit()
            else:
                cursor_main.execute('INSERT INTO items (name, image, price, category) VALUES (?, ?, ?, ?)',
                                    (name, image_binary, price, category))
                conn_main.commit()

            return redirect(url_for('index'))

    return render_template('add_item.html')


@app.route('/remove_item', methods=['POST'])
def remove_item():
    if request.method == 'POST':
        item_id = int(request.form['item_id'])

        # Connect to the main items database
        conn_main = sqlite3.connect('items_main.db')
        cursor_main = conn_main.cursor()

        # Connect to the removed items database
        conn_removed = sqlite3.connect('removed_items.db')
        cursor_removed = conn_removed.cursor()

        # Fetch the item by ID from the main database
        cursor_main.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        removed_item = cursor_main.fetchone()

        if removed_item:
            # Delete the item from the main database
            cursor_main.execute('DELETE FROM items WHERE id = ?', (item_id,))
            conn_main.commit()

            # Insert the removed item into the removed items database
            cursor_removed.execute('INSERT INTO removed_items (id, name, image, price, category) VALUES (?, ?, ?, ?, ?)', removed_item)
            conn_removed.commit()

            # Redirect to the appropriate route after removal


    # Handle other cases if necessary
    return redirect(url_for('index'))

@app.route('/view_items')
def view_items():
    grouped_items = get_all_items_grouped_by_category()
    return render_template('view_items.html', grouped_items=grouped_items, encode_image=encode_image)


@app.route('/view_special_items')
def view_special_items():
    grouped_special_items = get_all_special_items_grouped_by_category()
    return render_template('view_special_items.html', grouped_special_items=grouped_special_items, encode_image=encode_image)


@app.route('/view_removed_special_items')
def view_removed_special_items():
    grouped_removed_special_items = get_all_removed_special_items_grouped_by_category()
    return render_template('view_removed_special_items.html', grouped_removed_special_items=grouped_removed_special_items, encode_image=encode_image)


@app.route('/display_existing_items')
def display_existing_items():
    items = get_all_items_grouped_by_category()
    special_items = get_all_special_items_grouped_by_category()
    return render_template('counter_display.html', items=items, special_items=special_items, encode_image=encode_image)


@app.route('/view_removed_items')
def view_removed_items():
    grouped_removed_items = get_all_removed_items_grouped_by_category()
    return render_template('view_removed_items.html', grouped_removed_items=grouped_removed_items, encode_image=encode_image)


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

            cursor_main.execute('INSERT INTO items (name, image, price, category) VALUES (?, ?, ?, ?)', restored_item[1:])
            conn_main.commit()

            return redirect(url_for('index'))
    return render_template('view_removed_items.html')

@app.route('/remove_special_item', methods=['POST'])
def remove_special_item():
    conn_special = sqlite3.connect('special_items.db')
    cursor_special = conn_special.cursor()
    conn_removed_special = sqlite3.connect('removed_special_items.db')
    cursor_removed_special = conn_removed_special.cursor()

    if request.method == 'POST':
        item_id = int(request.form['item_id'])

        # Fetch the special item by ID
        cursor_special.execute('SELECT * FROM special_items WHERE id = ?', (item_id,))
        special_item = cursor_special.fetchone()

        if special_item:
            # Remove the special item from the special items database
            cursor_special.execute('DELETE FROM special_items WHERE id = ?', (item_id,))
            conn_special.commit()

            # Insert the removed special item into the removed special items database
            cursor_removed_special.execute('INSERT INTO removed_special_items (name, image, price, category) VALUES (?, ?, ?, ?)',
                                           special_item[1:])
            conn_removed_special.commit()
            return redirect(url_for('index'))
    return redirect(url_for('view_special_items'))

@app.route('/restore_special_item', methods=['POST'])
def restore_special_item():
    conn_special = sqlite3.connect('special_items.db')
    cursor_special = conn_special.cursor()
    conn_removed_special = sqlite3.connect('removed_special_items.db')
    cursor_removed_special = conn_removed_special.cursor()

    if request.method == 'POST':
        item_id = int(request.form['item_id'])

        # Fetch the removed special item by ID
        cursor_removed_special.execute('SELECT * FROM removed_special_items WHERE id = ?', (item_id,))
        removed_special_item = cursor_removed_special.fetchone()

        if removed_special_item:
            # Remove the item from the removed special items database
            cursor_removed_special.execute('DELETE FROM removed_special_items WHERE id = ?', (item_id,))
            conn_removed_special.commit()

            # Insert the restored special item into the special items database
            cursor_special.execute('INSERT INTO special_items (name, image, price, category) VALUES (?, ?, ?, ?)',
                                   removed_special_item[1:])
            conn_special.commit()
            return redirect(url_for('index'))
    return redirect(url_for('view_removed_special_items'))


@app.route('/edit_item', methods=['GET', 'POST'])
def edit_item():
    conn_main = sqlite3.connect('items_main.db')
    cursor_main = conn_main.cursor()

    if request.method == 'POST':
        item_id = int(request.form['item_id'])

        # Fetch the item by ID
        cursor_main.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        item = cursor_main.fetchone()

        if item:
            # Render the edit item form with the existing data
            return render_template('edit_item.html', item=item)

    return redirect(url_for('view_items'))

@app.route('/update_item', methods=['POST'])
def update_item():
    conn_main = sqlite3.connect('items_main.db')
    cursor_main = conn_main.cursor()

    if request.method == 'POST':
        item_id = int(request.form['item_id'])
        name = request.form['name']
        price = float(request.form['price'])
        image = request.files['image']  # Use 'files' instead of 'form' for file uploads
        category = request.form['category']

        # Process the image if it's present
        if image:
            resized_image = resize_image(image)
            img_io = io.BytesIO()
            file_extension = image.filename.split('.')[-1].lower()
            PIL_formats = {
                'jpg': 'JPEG',
                'jpeg': 'JPEG',
                'png': 'PNG',
                'gif': 'GIF'
                # Add more if needed
            }
            pil_format = PIL_formats.get(file_extension, 'JPEG')
            resized_image.save(img_io, format=pil_format)
            image_binary = img_io.getvalue()
        else:
            # If no new image is uploaded, keep the existing image in the database
            cursor_main.execute('SELECT image FROM items WHERE id=?', (item_id,))
            image_binary = cursor_main.fetchone()[0]

        # Update the item in the database
        cursor_main.execute('UPDATE items SET name=?, price=?, image=?, category=? WHERE id=?',
                            (name, price, image_binary, category, item_id))
        conn_main.commit()

    return redirect(url_for('view_items'))

@app.route('/edit_special_item', methods=['POST'])
def edit_special_item():
    conn_special = sqlite3.connect('special_items.db')
    cursor_special = conn_special.cursor()

    if request.method == 'POST':
        item_id = int(request.form['item_id'])

        # Fetch the special item by ID
        cursor_special.execute('SELECT * FROM special_items WHERE id = ?', (item_id,))
        special_item = cursor_special.fetchone()

        if special_item:
            # Render the edit special item form with the existing data
            return render_template('edit_special_item.html', special_item=special_item)

    return redirect(url_for('view_special_items'))


@app.route('/update_special_item', methods=['POST'])
def update_special_item():
    conn_special = sqlite3.connect('special_items.db')
    cursor_special = conn_special.cursor()

    if request.method == 'POST':
        item_id = int(request.form['item_id'])
        name = request.form['name']
        price = float(request.form['price'])
        image = request.files['image']  # Use 'files' instead of 'form' for file uploads
        category = request.form['category']

        # Process the image if it's present
        if image:
            # Resize and save the image
            resized_image = resize_image(image)
            img_io = io.BytesIO()
            file_extension = image.filename.split('.')[-1].lower()
            PIL_formats = {
                'jpg': 'JPEG',
                'jpeg': 'JPEG',
                'png': 'PNG',
                'gif': 'GIF'
                # Add more if needed
            }
            pil_format = PIL_formats.get(file_extension, 'JPEG')
            resized_image.save(img_io, format=pil_format)
            image_binary = img_io.getvalue()
        else:
            # If no new image is uploaded, keep the existing image in the database
            cursor_special.execute('SELECT image FROM special_items WHERE id=?', (item_id,))
            image_binary = cursor_special.fetchone()[0]

        # Update the special item in the database
        cursor_special.execute('UPDATE special_items SET name=?, price=?, image=?, category=? WHERE id=?',
                                (name, price, image_binary, category, item_id))
        conn_special.commit()
        return redirect(url_for('index'))

    return redirect(url_for('view_special_items'))



if __name__ == '__main__':
    app.run(debug=True)
