import sys
import io
import os
import base64
from datetime import datetime
import sqlite3
import streamlit as st

# فرض ترميز UTF-8 لمنع مشاكل الحروف العربية وـ ASCII نهائياً
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception:
    pass

# إعدادات الصفحة
st.set_page_config(
    page_title="بوابة الكرك - Karak Gate", page_icon="🛒", layout="wide"
)

# التصميم الأنيق والهادئ
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    .stDeployButton {display: none;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    .stApp {
        background-color: #F8F9FA !important;
        color: #2D3142 !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, span {
        color: #2D3142 !important;
    }
    .stTextInput>div>div>input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 12px !important;
    }
    div.stButton > button[kind="secondary"], div.stButton > button {
        background-color: #FF5722 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 4px 6px rgba(255, 87, 34, 0.2);
    }
    div.stButton > button:hover {
        background-color: #E64A19 !important;
        color: white !important;
    }
    .map-box {
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #E0E0E0;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def get_db():
    return sqlite3.connect("karak_gate.db", check_same_thread=False)


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT UNIQUE,
            address TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS merchants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            phone TEXT,
            location TEXT,
            status TEXT,
            image_data TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_name TEXT,
            item_name TEXT,
            price REAL,
            quantity TEXT,
            unit TEXT,
            image_path TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            customer_address TEXT,
            order_details TEXT,
            total_amount REAL,
            payment_method TEXT,
            order_status TEXT DEFAULT 'قيد التجهيز',
            driver_name TEXT DEFAULT '',
            lat REAL DEFAULT 31.1854,
            lng REAL DEFAULT 35.7048,
            created_at TEXT
        )
    """
    )
    conn.commit()
    conn.close()


init_db()

# تهيئة المتغيرات الافتراضية
if "phone" not in st.session_state:
    st.session_state.phone = "0790000000"
if "customer_name" not in st.session_state:
    st.session_state.customer_name = "أبو عدي"
if "customer_address" not in st.session_state:
    st.session_state.customer_address = (
        "الكرك - المرج | خريطة: https://maps.google.com/?q=31.1854,35.7048"
    )
if "cust_lat" not in st.session_state:
    st.session_state.cust_lat = 31.1854
if "cust_lng" not in st.session_state:
    st.session_state.cust_lng = 35.7048
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "الكل"
if "cart" not in st.session_state:
    st.session_state.cart = []
if "nav_tab" not in st.session_state:
    st.session_state.nav_tab = "الرئيسية"

# التأكد من حفظ الزبون افتراضياً
try:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO customers (name, phone, address) VALUES (?, ?, ?)",
        (
            st.session_state.customer_name,
            st.session_state.phone,
            st.session_state.customer_address,
        ),
    )
    conn.commit()
    conn.close()
except Exception:
    pass

# شريط التنقل السفلي الثابت
st.markdown(
    """
    <div style="background-color: #FFFFFF; padding: 10px; border-radius: 12px; border: 1px solid #E0E0E0; margin-bottom: 15px; display: flex; justify-content: space-around; text-align: center;">
    """,
    unsafe_allow_html=True,
)
nav_col1, nav_col2, nav_col3 = st.columns(3)
with nav_col1:
    if st.button("🏠 الرئيسية (Home)", use_container_width=True):
        st.session_state.nav_tab = "الرئيسية"
        st.rerun()
with nav_col2:
    if st.button("📦 طلباتي (Orders)", use_container_width=True):
        st.session_state.nav_tab = "الطلبات"
        st.rerun()
with nav_col3:
    if st.button("👤 تعديل حسابي (Account)", use_container_width=True):
        st.session_state.nav_tab = "الحساب"
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.nav_tab == "الرئيسية":
    col_top1, col_top2 = st.columns([3, 1])
    with col_top1:
        st.success(
            f"أهلاً بك يا {st.session_state.customer_name} | عنوانك: {st.session_state.customer_address}"
        )
    with col_top2:
        if st.button("🔄 تحديث"):
            st.rerun()

    search_query = st.text_input("🔍 بحث سريع عن أصناف أو متاجر في الكرك...", "")
    st.markdown("---")

    st.subheader("📁 الأقسام الرئيسية")

    categories_data = [
        {
            "name": "الكل",
            "img": "https://img.icons8.com/external-flat-wichai-wi/64/external-fast-food-fast-food-flat-wichai-wi.png",
        },
        {
            "name": "مطاعم",
            "img": "https://img.icons8.com/color/96/hamburger.png",
        },
        {
            "name": "حلويات",
            "img": "https://img.icons8.com/color/96/birthday-cake.png",
        },
        {
            "name": "ماركت",
            "img": "https://img.icons8.com/color/96/shopping-cart.png",
        },
        {
            "name": "محامص ومكسرات",
            "img": "https://img.icons8.com/color/96/peanuts.png",
        },
        {
            "name": "خضروات وفواكه",
            "img": "https://img.icons8.com/color/96/basket.png",
        },
        {
            "name": "لحوم",
            "img": "https://img.icons8.com/color/96/steak.png",
        },
        {
            "name": "صيدليات ومستلزمات طبيه",
            "img": "https://img.icons8.com/color/96/pills.png",
        },
    ]

    cols_cat = st.columns(len(categories_data))
    for i, cat_info in enumerate(categories_data):
        with cols_cat[i]:
            st.markdown(
                f"""
                <div style="background-color: #F1F3F5; border-radius: 12px; padding: 10px; text-align: center; border: 1px solid #DEE2E6; margin-bottom: 5px;">
                    <img src="{cat_info['img']}" width="42" style="margin-bottom: 6px;"><br>
                    <span style="font-size: 11px; font-weight: bold; color: #333;">{cat_info['name']}</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
            if st.button("اختر", key=f"cat_btn_{i}", use_container_width=True):
                st.session_state.selected_category = cat_info["name"]
                st.rerun()

    st.write(f"**القسم الحالي المختار:** `{st.session_state.selected_category}`")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🏬 المتاجر المعتمدة والأصناف المتاحة")

        conn = get_db()
        cursor = conn.cursor()

        if st.session_state.selected_category == "الكل":
            cursor.execute(
                "SELECT name, category, phone, location, image_data FROM merchants WHERE status='معتمد'"
            )
        else:
            cursor.execute(
                "SELECT name, category, phone, location, image_data FROM merchants WHERE status='معتمد' AND category=?",
                (st.session_state.selected_category,),
            )

        merchants = cursor.fetchall()

        if not merchants:
            st.info("لا توجد متاجر معتمدة حالياً في هذا القسم.")
        else:
            for m_idx, m in enumerate(merchants):
                m_name, m_cat, m_phone, m_loc, m_img_data = m

                if (
                    search_query
                    and search_query.lower() not in m_name.lower()
                    and search_query.lower() not in m_cat.lower()
                ):
                    continue

                # عرض صورة المتجر المخزنة كـ Base64
                if m_img_data:
                    if m_img_data.startswith("data:image"):
                        st.markdown(
                            f'<img src="{m_img_data}" width="120" style="border-radius:10px; margin-bottom:10px;">',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<img src="data:image/jpeg;base64,{m_img_data}" width="120" style="border-radius:10px; margin-bottom:10px;">',
                            unsafe_allow_html=True,
                        )

                st.markdown(f"### 🏬 {m_name}")
                st.write(f"التصنيف: **{m_cat}** | الموقع: {m_loc}")

                cursor.execute(
                    "SELECT id, item_name, price, quantity, unit, image_path FROM products WHERE merchant_name = ?",
                    (m_name,),
                )
                products = cursor.fetchall()

                if products:
                    st.write("📋 **الأصناف المتوفرة:**")
                    for idx_p, p in enumerate(products):
                        p_id, p_name, p_price, p_qty, p_unit, p_img_data = p

                        p_col1, p_col2, p_col3 = st.columns([1, 3, 1])
                        with p_col1:
                            if p_img_data:
                                if p_img_data.startswith("data:image"):
                                    st.markdown(
                                        f'<img src="{p_img_data}" width="50" style="border-radius:8px;">',
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(
                                        f'<img src="data:image/jpeg;base64,{p_img_data}" width="50" style="border-radius:8px;">',
                                        unsafe_allow_html=True,
                                    )
                            else:
                                st.write("📷")
                        with p_col2:
                            st.write(
                                f"**{p_name}** ({p_qty} {p_unit}) - {p_price} د.أ"
                            )
                        with p_col3:
                            if st.button(
                                "➕ إضافة", key=f"add_p_{m_idx}_{p_id}_{idx_p}"
                            ):
                                item_label = f"{p_name} ({p_qty} {p_unit})"
                                st.session_state.cart.append({
                                    "name": item_label,
                                    "price": p_price,
                                    "merchant": m_name,
                                })
                                st.toast(f"تمت إضافة {p_name} إلى السلة!")
                else:
                    st.info("لا توجد أصناف مضافة حالياً من هذا المتجر.")
                st.markdown("---")
        conn.close()

    with col2:
        st.subheader("🛍 سلة الطلبات والفاتورة")
        if not st.session_state.cart:
            st.info("السلة فارغة حالياً.")
        else:
            subtotal = 0.0
            for item in st.session_state.cart:
                st.write(f"🔹 {item['name']} - {item['price']} د.أ")
                subtotal += item["price"]

            delivery_fee = 1.50
            service_fee = 0.25
            total = subtotal + delivery_fee + service_fee

            st.markdown("---")
            st.write(f"🏷 **مجموع الأصناف:** {subtotal:.2f} د.أ")
            st.write(f"🛵 **التوصيل:** {delivery_fee:.2f} د.أ")
            st.write(f"⚙️ **الخدمة:** {service_fee:.2f} د.أ")
            st.markdown(f"### 💰 الإجمالي النهائي: {total:.2f} د.أ")

            if st.button("🗑️ تفريغ السلة"):
                st.session_state.cart = []
                st.rerun()

            payment_method = st.radio(
                "اختر طريقة الدفع:",
                [
                    "نقداً عند الاستلام",
                    "CliQ (0797088219 - البنك الإسلامي)",
                    "samarza (بنك الاتحاد)",
                ],
            )

            if st.button("📌 تأكيد وإرسال الطلب للإدارة", use_container_width=True):
                items_summary = ""
                for item in st.session_state.cart:
                    items_summary += f"- {item['name']} ({item['price']} د.أ) [المتجر: {item['merchant']}]\n"

                try:
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                            INSERT INTO orders (customer_name, customer_phone, customer_address, order_details, total_amount, payment_method, order_status, driver_name, lat, lng, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, 'قيد التجهيز', '', ?, ?, ?)
                        """,
                        (
                            st.session_state.customer_name,
                            st.session_state.phone,
                            st.session_state.customer_address,
                            items_summary,
                            total,
                            payment_method,
                            st.session_state.cust_lat,
                            st.session_state.cust_lng,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success("🎉 تم تأكيد طلبك بنجاح وحفظه للإدارة!")
                    st.session_state.cart = []
                except Exception as e:
                    st.error(f"خطأ: {e}")

elif st.session_state.nav_tab == "الطلبات":
    st.subheader("📍 تتبع طلباتي النشطة (Live GPS)")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, order_status, driver_name, total_amount, created_at, lat, lng FROM orders WHERE customer_phone = ? ORDER BY id DESC",
        (st.session_state.phone,),
    )
    my_orders = cursor.fetchall()
    conn.close()

    if my_orders:
        for o in my_orders:
            o_id, o_status, o_driver, o_total, o_time, o_lat, o_lng = o
            st.markdown(
                f"📦 **طلب رقم #{o_id}** | وقت الطلب: {o_time} | الحالة: **{o_status}** | السائق: **{o_driver if o_driver else 'قيد الإسناد'}** | الإجمالي: {o_total} د.أ"
            )

            live_map_url = f"https://maps.google.com/maps?q={o_lat},{o_lng}&t=&z=15&ie=UTF8&iwloc=&output=embed"
            st.markdown(
                f"""
                    <div class="map-box">
                        <iframe width="100%" height="220" frameborder="0" scrolling="no" src="{live_map_url}"></iframe>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("---")
    else:
        st.info("لا توجد طلبات نشطة حالياً.")

elif st.session_state.nav_tab == "الحساب":
    st.subheader("👤 تعديل معلومات الحساب (Account Settings)")
    st.write(
        "يمكنك هنا تعديل اسمك، رقم هاتفك، وعنوانك أو موقع الخريطة ليتم اعتماده مباشرة في طلباتك القادمة:"
    )

    with st.form("account_edit_form"):
        new_name = st.text_input("الاسم الكريم:", value=st.session_state.customer_name)
        new_phone = st.text_input(
            "رقم الهاتف:", value=st.session_state.phone
        )
        new_address = st.text_area(
            "العنوان التفصيلي / رابط الخريطة:",
            value=st.session_state.customer_address,
        )

        submitted = st.form_submit_button(
            "💾 حفظ التعديلات", use_container_width=True
        )
        if submitted:
            st.session_state.customer_name = new_name
            st.session_state.phone = new_phone
            st.session_state.customer_address = new_address

            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO customers (name, phone, address) VALUES (?, ?, ?)",
                    (new_name, new_phone, new_address),
                )
                conn.commit()
                conn.close()
                st.success("✅ تم تحديث وحفظ معلومات الحساب بنجاح!")
            except Exception as e:
                st.error(f"حدث خطأ أثناء الحفظ: {e}")