from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import datetime
import mysql.connector
import hashlib

# Establish the connection
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="e_commerce"
)
cursor = db.cursor()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = '123'
jwt = JWTManager(app)

def hash_password(password):
    # Simulate password hashing using SHA-256 (replace with a secure hashing library)
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password

# Route for user registration
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        return jsonify({'message': 'Username already taken'}), 400

    hashed_password = hash_password(password)
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    db.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# Route for admin login
@app.route('/api/admin/login', methods=['POST'])
def login_admin():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cursor.execute("SELECT * FROM admins WHERE username = %s AND password = %s", (username, hash_password(password)))
    admin_data = cursor.fetchone()
    if admin_data:
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200
    else:
        return jsonify({'message': 'Invalid admin credentials'}), 401

# Route for user login
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hash_password(password)))
    user_data = cursor.fetchone()
    if user_data:
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200
    else:
        return jsonify({'message': 'Invalid user credentials'}), 401

# Route for refreshing access tokens
@app.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify(access_token=access_token), 200

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


class Authors:
    def __init__(self, id_Author, author_name, biography, books_written):
        self.id_Author = id_Author
        self.author_name = author_name
        self.biography = biography
        self.books_written = books_written

    def save(self):
        cursor.execute("INSERT INTO authors (id_Author, author_name, biography, books_written) VALUES (%s, %s, %s, %s)",
                       (self.id_Author, self.author_name, self.biography, self.books_written))
        db.commit()

    @staticmethod
    def get_one(author_id):
        cursor.execute("SELECT * FROM authors WHERE id_Author = %s", (author_id,))
        author = cursor.fetchone()
        if author is None:
            return None
        return Authors(author[0], author[1], author[2], author[3])

class Books:
    def __init__(self, id_Book, book_name, publish_year, short_description, body_text, fk_Authorid_Author):
        self.id_Book = id_Book
        self.book_name = book_name
        self.publish_year = publish_year
        self.short_description = short_description
        self.body_text = body_text
        self.fk_Authorid_Author = fk_Authorid_Author

    def save(self):
        cursor.execute("INSERT INTO books (id_Book, book_name, publish_year, short_description, body_text, fk_Authorid_Author) VALUES (%s, %s, %s, %s, %s, %s)",
                       (self.id_Book, self.book_name, self.publish_year, self.short_description, self.body_text, self.fk_Authorid_Author))
        db.commit()

    @staticmethod
    def get_one(book_id, author_id):
        cursor.execute("SELECT * FROM books WHERE fk_Authorid_Author = %s AND id_Book = %s", (author_id, book_id,))
        book = cursor.fetchone()
        if book is None:
            return None
        return Books(book[0], book[1], book[2], book[3], book[4], book[5])

class Stores:
    def __init__(self, id_Store, address, working_time, number_of_books):
        self.id_Store = id_Store
        self.address = address
        self.working_time = working_time
        self.number_of_books = number_of_books

    def save(self):
        cursor.execute("INSERT INTO stores (id_Store, address, working_time, number_of_books) VALUES (%s, %s, %s, %s)",
                       (self.id_Store, self.address, self.working_time, self.number_of_books))
        db.commit()

    @staticmethod
    def get_one(author_id, book_id, store_id):
        # cursor.execute("SELECT Stores.* FROM Stores JOIN Book_Stores ON "
        #                "Stores.id_Store = Book_Stores.fk_Storeid_Store WHERE "
        #                "Book_Stores.fk_Bookid_Book = %s AND id_Store = %s", (book_id, store_id,))

        cursor.execute("SELECT Stores.* FROM Stores "
                       "JOIN Book_Stores ON Stores.id_Store = Book_Stores.fk_Storeid_Store "
                       "JOIN Books ON Book_Stores.fk_Bookid_Book = Books.id_Book "
                       "JOIN Authors ON Books.fk_Authorid_Author = Authors.id_Author "
                       "WHERE Authors.id_Author = %s AND Books.id_Book = %s "
                       "AND Stores.id_Store = %s", (author_id, book_id, store_id,))
        store = cursor.fetchone()
        if store is None:
            return None
        return Stores(store[3],store[0],store[2],store[1])

class Book_stores:
    def __init__(self, id_Book_Store, fk_Storeid_Store, fk_Bookid_Book):
        self.id_Book_Store = id_Book_Store
        self.fk_Bookid_Book = fk_Bookid_Book
        self.fk_Storeid_Store = fk_Storeid_Store

    def save(self):
        cursor.execute("INSERT INTO book_stores (id_Book_Store, fk_Storeid_Store, fk_Bookid_Book) VALUES (%s, %s, %s)",
                       (self.id_Book_Store, self.fk_Storeid_Store, self.fk_Bookid_Book))
        db.commit()


# Route to get all authors
@app.route('/api/authors', methods=['GET'])
def get_authors():
    cursor.execute("SELECT * FROM authors")
    authors = cursor.fetchall()
    return jsonify({'authors': authors})

# Route to get all books
@app.route('/api/authors/<int:author_id>/books', methods=['GET'])
def get_books(author_id):
    cursor.execute("SELECT * FROM books WHERE fk_Authorid_Author = %s", (author_id,))
    books = cursor.fetchall()
    return jsonify({'books': books})

# Route to get all stores
@app.route('/api/authors/<int:author_id>/books/<int:book_id>/stores', methods=['GET'])
def get_stores(author_id, book_id):
    # cursor.execute("SELECT Stores.* FROM Stores JOIN Book_Stores ON Stores.id_Store = "
    #                "Book_Stores.fk_Storeid_Store WHERE Book_Stores.fk_Bookid_Book = %s"
    #                "AND Books.fk_Authorid_Author = %s", (book_id, author_id,))
    cursor.execute("SELECT Stores.* FROM Stores "
                   "JOIN Book_Stores ON Stores.id_Store = Book_Stores.fk_Storeid_Store "
                   "JOIN Books ON Book_Stores.fk_Bookid_Book = Books.id_Book "
                   "JOIN Authors ON Books.fk_Authorid_Author = Authors.id_Author "
                   "WHERE Authors.id_Author = %s AND Books.id_Book = %s", (author_id, book_id,))
    stores = cursor.fetchall()
    return jsonify({'stores': stores})


# Route to add a new author
@app.route('/api/authors', methods=['POST'])
def add_author():
    data = request.get_json()
    existing_author = Authors.get_one(data['id_Author'])
    if existing_author:
        return jsonify({'message': 'Author with this ID already exists'}), 400

    new_author = Authors(data['id_Author'], data['author_name'], data['biography'], data['books_written'])
    new_author.save()
    return jsonify({'message': 'Author added successfully'}), 201

# Route to add a new book
@app.route('/api/authors/<int:author_id>/books', methods=['POST'])
def add_book(author_id):
    data = request.get_json()
    existing_book = Books.get_one(data['id_Book'], author_id)
    if existing_book:
        return jsonify({'message': 'Book with this ID already exists for the specified author'}), 400

    new_book = Books(data['id_Book'], data['book_name'], data['publish_year'], data['short_description'],
                     data['body_text'], author_id)
    new_book.save()
    return jsonify({'message': 'Book added successfully'}), 201

# Route to add a new store
@app.route('/api/authors/<int:author_id>/books/<int:book_id>/stores', methods=['POST'])
def add_store(author_id, book_id):

    books = Books.get_one(book_id, author_id)
    if books is None:
        return jsonify({'message': 'Book not found'})
    data = request.get_json()
    existing_store = Stores.get_one(author_id, book_id, data['id_Store'])
    if existing_store:
        return jsonify({'message': 'Store with this ID already exists'}), 400

    new_store = Stores(data['id_Store'], data['address'], data['working_time'], data['number_of_books'])
    new_store.save()
    cursor.execute("SELECT id_Book_Store FROM book_stores ORDER BY id_Book_Store DESC LIMIT 1")
    number = cursor.fetchone()
    book_store = Book_stores(number[0]+1, data['id_Store'], book_id)
    book_store.save()

    return jsonify({'message': 'Store added successfully'}), 201



@app.route('/api/authors/<int:author_id>', methods=['PUT'])
def update_author(author_id):
    data = request.get_json()
    author = Authors.get_one(author_id)
    if author is None:
        return jsonify({'message': 'Author not found'})

    author = Authors(data['id_Author'], data['author_name'], data['biography'], data['books_written'])
    cursor.execute("UPDATE authors SET author_name = %s, biography = %s, books_written = %s WHERE id_Author = %s",
                   (author.author_name, author.biography, author.books_written, author.id_Author))
    db.commit()
    return jsonify({'message': 'Author updated successfully'}), 201


@app.route('/api/authors/<int:author_id>/books/<int:books_id>', methods=['PUT'])
def update_book(author_id, books_id):
    data = request.get_json()
    book = Books.get_one(books_id, author_id)
    if book is None:
        return jsonify({'message': 'Book not found'})
    book = Books(data['id_Book'], data['book_name'], data['publish_year'], data['short_description'], data['body_text'], data['fk_Authorid_Author'])
    cursor.execute("UPDATE books SET book_name = %s, publish_year = %s, short_description = %s, "
                   "body_text = %s, fk_Authorid_Author = %s WHERE id_Book = %s",
                   (book.book_name, book.publish_year, book.short_description, book.body_text,
                    book.fk_Authorid_Author, book.id_Book))
    db.commit()
    return jsonify({'message': 'Book updated successfully'}), 201


@app.route('/api/authors/<int:author_id>/books/<int:books_id>/stores/<int:store_id>', methods=['PUT'])
def update_store(author_id, books_id, store_id):
    store = Stores.get_one(author_id, books_id, store_id)
    if store is None:
        return jsonify({'message': 'Store not found'})
    store = Stores(store_id, "new_address", "8:00-10:00", 100)
    cursor.execute("UPDATE stores SET address = %s, working_time = %s, number_of_books = %s WHERE id_Store = %s",
                   (store.address, store.working_time, store.number_of_books, store.id_Store))
    # id_Store, address, working_time, number_of_books
    db.commit()
    return jsonify({'message': 'Store updated successfully'}), 201



@app.route('/api/authors/<int:author_id>', methods=['GET'])
def get_one_author(author_id):
    author = Authors.get_one(author_id)
    if author is None:
        return jsonify({'message': 'Author not found'}), 404
    return jsonify({'author': {'id_Author': author.id_Author, 'author_name': author.author_name, 'biography': author.biography, 'books_written': author.books_written}})


# Route to get one book
@app.route('/api/authors/<int:author_id>/books/<int:book_id>', methods=['GET'])
def get_one_book(book_id, author_id):
    book = Books.get_one(book_id, author_id)
    if book is None:
        return jsonify({'message': 'Book not found'}), 404
    return jsonify({'book': {'id_Book': book.id_Book, 'book_name': book.book_name, 'publish_year': book.publish_year, 'short_description': book.short_description, 'body_text': book.body_text, 'fk_Authorid_Author': book.fk_Authorid_Author}})


# Route to get one store
@app.route('/api/authors/<int:author_id>/books/<int:book_id>/stores/<int:store_id>', methods=['GET'])
def get_one_store(author_id, book_id, store_id):
    store = Stores.get_one(author_id, book_id, store_id)
    if store is None:
        return jsonify({'message': 'Store not found'})
    return jsonify({'store': {'id_Store': store.id_Store, 'address': store.address, 'working_time': store.working_time, 'number_of_books': store.number_of_books}})



# Route to delete an author
@app.route('/api/authors/<int:author_id>', methods=['DELETE'])
def delete_author(author_id):
    author = Authors.get_one(author_id)
    if author is None:
        return jsonify({'message': 'Author not found'})
    cursor.execute("DELETE FROM book_stores WHERE fk_Bookid_Book IN "
                   "(SELECT id_Book FROM books WHERE fk_Authorid_Author = %s)", (author_id,))
    db.commit()
    cursor.execute("DELETE FROM books WHERE fk_Authorid_Author = %s", (author_id,))
    db.commit()
    cursor.execute("DELETE FROM authors WHERE id_Author = %s", (author_id,))
    db.commit()
    return jsonify({'message': 'Author deleted successfully'}), 200


# Route to delete a book
@app.route('/api/authors/<int:author_id>/books/<int:book_id>', methods=['DELETE'])
def delete_book(author_id, book_id):
    book = Books.get_one(author_id, book_id)
    if book is None:
        return jsonify({'message': 'Book not found'})
    cursor.execute("DELETE FROM book_stores WHERE book_stores.fk_Bookid_Book = %s", (book_id,))
    db.commit()
    cursor.execute("DELETE FROM books WHERE id_Book = %s", (book_id,))
    db.commit()
    return jsonify({'message': 'Book deleted successfully'}), 200


# Route to delete a store
@app.route('/api/authors/<int:author_id>/books/<int:book_id>/stores/<int:store_id>', methods=['DELETE'])
def delete_store(author_id, book_id, store_id):
    store = Stores.get_one(author_id, book_id, store_id)
    if store is None:
        return jsonify({'message': 'Store not found'})
    cursor.execute("DELETE FROM book_stores WHERE fk_Storeid_Store = %s", (store_id,))
    db.commit()
    cursor.execute("DELETE FROM stores WHERE id_Store = %s", (store_id,))
    db.commit()
    return jsonify({'message': 'Store deleted successfully'}), 200


if __name__ == '__main__':
    app.run(debug=True)