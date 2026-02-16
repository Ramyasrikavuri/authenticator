import streamlit as st
import sqlite3
import hashlib
import cv2
import numpy as np
from PIL import Image

# ================= DATABASE =================

def create_connection():
    return sqlite3.connect("users.db", check_same_thread=False)

def create_table():
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            images_processed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(email, password):
    conn = create_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users(email, password) VALUES (?, ?)",
            (email, hash_password(password))
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False

def login_user(email, password):
    conn = create_connection()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, hash_password(password))
    )
    data = c.fetchone()
    conn.close()
    return data

def increment_image_count(email):
    conn = create_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET images_processed = images_processed + 1 WHERE email=?",
        (email,)
    )
    conn.commit()
    conn.close()

def get_image_count(email):
    conn = create_connection()
    c = conn.cursor()
    c.execute(
        "SELECT images_processed FROM users WHERE email=?",
        (email,)
    )
    count = c.fetchone()
    conn.close()
    return count[0] if count else 0

create_table()

# ================= SESSION =================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

st.set_page_config(page_title="Toonify AI", layout="wide")

# ================= SIDEBAR =================

st.sidebar.title("🎨 Toonify")
menu = st.sidebar.selectbox("Menu", ["Login", "Sign Up"])

# ================= AUTH =================

if not st.session_state.logged_in:

    st.title("🔐 Toonify Authentication")

    if menu == "Sign Up":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Create Account"):
            if add_user(email, password):
                st.success("Account Created Successfully ✅")
            else:
                st.error("Email already exists!")

    if menu == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Invalid Credentials")

# ================= DASHBOARD =================

else:

    st.markdown("## 🎨 Toonify AI Studio")
    st.write(f"Welcome back, **{st.session_state.user_email}** 👋")

    images_count = get_image_count(st.session_state.user_email)

    col1, col2, col3 = st.columns(3)
    col1.metric("Images Processed", images_count)
    col2.metric("Filters Available", "2")
    col3.metric("Account Status", "Active")

    st.markdown("---")

    left, right = st.columns([1, 1])

    # ===== LEFT SIDE =====
    with left:
        st.subheader("📤 Upload & Settings")

        uploaded_file = st.file_uploader(
            "Upload Image",
            type=["jpg", "jpeg", "png"]
        )

        filter_option = st.selectbox(
            "Choose Filter",
            ["Cartoon", "Sketch"],
            disabled=uploaded_file is None
        )

        apply_button = st.button(
            "✨ Apply Filter",
            disabled=uploaded_file is None
        )

    # ===== RIGHT SIDE =====
    with right:
        st.subheader("🖼 Preview")

        if uploaded_file is not None and apply_button:

            image = Image.open(uploaded_file)
            img = np.array(image)

            colA, colB = st.columns(2)

            # ORIGINAL IMAGE
            with colA:
                st.markdown("### Original Image")
                st.image(img, width=350)

            # APPLY FILTER
            if filter_option == "Cartoon":
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                gray = cv2.medianBlur(gray, 5)
                edges = cv2.adaptiveThreshold(
                    gray,
                    255,
                    cv2.ADAPTIVE_THRESH_MEAN_C,
                    cv2.THRESH_BINARY,
                    9,
                    9
                )
                color = cv2.bilateralFilter(img, 9, 300, 300)
                output = cv2.bitwise_and(color, color, mask=edges)

                with colB:
                    st.markdown("### Cartoon Output")
                    st.image(output, width=350)

            elif filter_option == "Sketch":
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                inv = 255 - gray
                blur = cv2.GaussianBlur(inv, (21, 21), 0)
                inv_blur = 255 - blur
                output = cv2.divide(gray, inv_blur, scale=256.0)

                with colB:
                    st.markdown("### Sketch Output")
                    st.image(output, width=350)

            increment_image_count(st.session_state.user_email)
