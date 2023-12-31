from b2sdk.v1 import DownloadDestLocalFile
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import base64
from b2sdk.v2 import *


# Initialize B2 Cloud Storage
b2_api = B2Api()
application_key_id = 'fc58c8a67d36'
application_key = '005e83fe4dfcc9c78e7c429652b67e23806fa30047'
b2_api.authorize_account("production", application_key_id, application_key)
bucket_name = 'sqlite3-data'
bucket = b2_api.get_bucket_by_name(bucket_name)

# Create a connection to the main database (or create it if it doesn't exist)
# conn_main = sqlite3.connect('items_main.db')
# cursor_main = conn_main.cursor()
#
# # Create a connection to the removed item's database (or create it if it doesn't exist)
# conn_removed = sqlite3.connect('removed_items.db')
# cursor_removed = conn_removed.cursor()
#
# # Create tables for main and removed items if they don't exist
# cursor_main.execute('''
#     CREATE TABLE IF NOT EXISTS items (
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         image BLOB,
#         price REAL
#     )
# ''')
# conn_main.commit()
#
# cursor_removed.execute('''
#     CREATE TABLE IF NOT EXISTS removed_items (
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         image BLOB,
#         price REAL
#     )
# ''')
# conn_removed.commit()


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
    local_save_path = 'items_downloaded.db'
    file_name = 'items_main.db'
    bucket = b2_api.get_bucket_by_name(bucket_name)
    download_dest = DownloadDestLocalFile(local_save_path)
    bucket.download_file_by_name(file_name, download_dest)
    print("Downloaded database")
    delete_previous_files()
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
    upload_to_backblaze("items_main.db")
    return render_template('add_item.html')


@app.route('/remove_item', methods=['GET', 'POST'])
def remove_item():
    local_save_path = 'items_downloaded.db'
    file_name = 'removed_items.db'
    file_name_2 = 'items_main.db'
    bucket = b2_api.get_bucket_by_name(bucket_name)
    download_dest = DownloadDestLocalFile(local_save_path)
    bucket.download_file_by_name(file_name, download_dest)
    bucket.download_file_by_name(file_name_2, download_dest)
    print("Downloaded databases")
    delete_previous_files()
    conn_removed = sqlite3.connect('removed_items.db')
    cursor_removed = conn_removed.cursor()
    conn_main = sqlite3.connect('items_main.db')
    cursor_main = conn_main.cursor()
    if request.method == 'POST':
        serial_number = int(request.form['serial_number'])

        cursor_main.execute('SELECT * FROM items WHERE id = ?', (serial_number,))
        removed_item = cursor_main.fetchone()

        if removed_item:
            cursor_main.execute('DELETE FROM items WHERE id = ?', (serial_number,))
            conn_main.commit()

            cursor_removed.execute('INSERT INTO removed_items (name, image, price) VALUES (?, ?, ?)', removed_item[1:])
            conn_removed.commit()

            return redirect(url_for('index'))
    upload_to_backblaze("items_main.db")
    upload_to_backblaze("removed_items.db")
    return render_template('remove_item.html')


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
    local_save_path = 'items_downloaded.db'
    file_name = 'removed_items.db'
    file_name_2 = 'items_main.db'
    bucket = b2_api.get_bucket_by_name(bucket_name)
    download_dest = DownloadDestLocalFile(local_save_path)
    bucket.download_file_by_name(file_name, download_dest)
    bucket.download_file_by_name(file_name_2, download_dest)
    print("Downloaded databases")
    delete_previous_files()
    conn_main = sqlite3.connect('items_main.db')
    cursor_main = conn_main.cursor()
    conn_removed = sqlite3.connect('removed_items.db')
    cursor_removed = conn_removed.cursor()

    if request.method == 'POST':
        serial_number = int(request.form['serial_number'])

        cursor_removed.execute('SELECT * FROM removed_items WHERE id = ?', (serial_number,))
        restored_item = cursor_removed.fetchone()

        if restored_item:
            cursor_removed.execute('DELETE FROM removed_items WHERE id = ?', (serial_number,))
            conn_removed.commit()

            cursor_main.execute('INSERT INTO items (name, image, price) VALUES (?, ?, ?)', restored_item[1:])
            conn_main.commit()

            return redirect(url_for('index'))
    upload_to_backblaze("items_main.db")
    upload_to_backblaze("removed_items.db")
    return render_template('restore_item.html')


def upload_to_backblaze(file_name):
    bucket.upload_local_file(local_file=file_name, file_name=file_name)
    print(f"File '{file_name}' uploaded to Backblaze B2")


def delete_previous_files():
    try:
        file_one = "Positive_Feedbacks.txt"
        file_two = "Negative_Feedbacks.txt"
        for version in bucket.list_file_versions(file_one and file_two):
            bucket.delete_file_version(version.id_, version.file_name)
        print("Previous files deleted successfully")
    except Exception as e:
        print("Error deleting previous files:", e)


if __name__ == '__main__':
    app.run(debug=True)
