"""
Final Project
Miku Naka
Date: 2025-05-16

This tool fetches a book from Project Gutenberg (UTF-8 Plain Text),
counts the 10 most common words, and stores the result in a local database.
Users can later search for saved book titles and view the stored word frequencies.
"""

import sqlite3
from tkinter import *
from urllib.request import urlopen
import re

# Set up SQLite database
con = sqlite3.connect('web.db')
cur = con.cursor() 

cur.execute("CREATE TABLE IF NOT EXISTS Books (title TEXT PRIMARY KEY)") 
cur.execute("CREATE TABLE IF NOT EXISTS Words (title TEXT, word TEXT, frequency INTEGER)") 
con.commit()

# Functions 

def clean_text(text):
    """
    Removes punctuation and lowercases all words.
    Returns a list of words.
    """
    text = re.sub(r'[^a-zA-Z\s]', '', text)  
    text = text.lower()
    return text.split() 

def count_top_10(words):
    """
    Counts word frequencies and returns the top 10
    for words with 4 or more letters.
    """
    counts = {} 
    for word in words:
        if len(word) >= 4:
            if word in counts:
                counts[word] += 1
            else:
                counts[word] = 1

    word_list = list(counts.items())

    def sort_key(pair):
        return pair[1] 
    word_list.sort(key=sort_key, reverse=True)
    
    return word_list[:10] 

def save_to_db(title, top_words):
    """
    Saves the book title and top 10 words into the database.
    """
    try:
        cur.execute("INSERT INTO Books (title) VALUES (?)", (title,)) 
        for word, freq in top_words:
            cur.execute("INSERT INTO Words (title, word, frequency) VALUES (?, ?, ?)", (title, word, freq)) 
        con.commit()
    except Exception as e:
        output.insert(END, f"An error occured: {e}")

def search_local(title):
    """
    Looks up a saved book by title.
    Returns a list of (word, frequency) or None if not found.
    """
    cur.execute("SELECT word, frequency FROM Words WHERE LOWER(title) = LOWER(?) ORDER BY frequency DESC", (title,))
    return cur.fetchall()

def search_title():
    """
    Called when Search button is clicked.
    Finds title in database and shows saved word frequencies.
    """
    title = title_entry.get().strip() 
    output.delete(1.0, END) 

    if not title:
        output.insert(END, "Please enter a book title.") 
        return

    try:
        result = search_local(title) 
        if result:
            output.insert(END, f"Top 10 words for '{title}':\n\n")
            for word, freq in result:
                output.insert(END, f"{word}: {freq}\n") 
        else:
            output.insert(END, "Book not found in database.\nPaste a URL to fetch it.") 
    except Exception as e:
        output.insert(END, f"An error occurred: {e}")

def fetch_url():
    """
    When 'Fetch from URL' button is clicked.
    Downloads the text (HTML or plain), extracts title, shows top words, saves to DB.
    """
    url = url_entry.get().strip()
    title = title_entry.get().strip()
    output.delete(1.0, END)

    if not url:
        output.insert(END, "Please paste a valid Project Gutenberg URL.")
        return

    try:
        response = urlopen(url)
        text = response.read().decode('utf-8') 
    except Exception as e:
        output.insert(END, "Failed to open or decode the URL.") 
        return

    is_html = "<html" in text.lower() 

    if is_html:
        match = re.search(r'<strong>\s*Title\s*</strong>\s*:\s*(.*?)</p>', text, re.IGNORECASE)
        if match and not title:
            title = match.group(1).strip()

        text = re.sub(r'<[^>]+>', ' ', text)

    words = clean_text(text)
    top_words = count_top_10(words)

    if not title:
        title = url.split("/")[-1] 
    output.insert(END, f"Top 10 words for '{title}':\n\n")
    for word, freq in top_words:
        output.insert(END, f"{word}: {freq}\n")

    save_to_db(title, top_words)

def clear_fields():
    """
    Clears all input and output fields.
    """
    title_entry.delete(0, END)
    url_entry.delete(0, END)
    output.delete(1.0, END)

# GUI Setup 

window = Tk()
window.title("Gutenberg Word Counter")
window.configure(bg="#f8faff")

# Title
Label(window, text="Gutenberg Word Counter", font=("Helvetica", 16, "bold"), bg="#f8faff").pack(pady=10)

# Book title
Label(window, text="Book Title (to search/save):", bg="#f8faff", font=("Helvetica", 12)).pack()
title_entry = Entry(window, width=50, font=("Helvetica", 10))
title_entry.pack(pady=5)

Button(window, text="Search Title in Database", command=search_title, bg="#4caf50", fg="white", font=("Helvetica", 10, "bold")).pack(pady=5)

# URL
Label(window, text="Paste Project Gutenberg URL:", bg="#f8faff", font=("Helvetica", 12)).pack()
url_entry = Entry(window, width=50, font=("Helvetica", 10))
url_entry.pack(pady=5)

Button(window, text="Fetch Book from URL", command=fetch_url, bg="#2196f3", fg="white", font=("Helvetica", 10, "bold")).pack(pady=5)

# Output area
Label(window, text="Top 10 Words:", bg="#f8faff", font=("Helvetica", 12, "bold")).pack(pady=5)
output = Text(window, height=12, width=60, font=("Helvetica", 10))
output.pack(pady=10)

# Clear Button
Button(window, text="Clear", command=clear_fields, bg="#f44336", fg="white", font=("Helvetica", 10, "bold")).pack(pady=5)


# Start GUI
window.mainloop()
con.close()
