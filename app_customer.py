import os
import urllib.parse
import time
from datetime import datetime
import sqlite3
import streamlit as st

# إعدادات الصفحة
st.set_page_config(
    page_title="بوابة الكرك - Karak Gate", page_icon="🛒", layout="wide"
)

# كود إخفاء شريط القائمة العلوي وترويسة Streamlit بالكامل وأزرار النشر و GitHub Fork
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    .stDeployButton {display: none;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, span {
        color: #000000 !important;
    }
    .stTextInput>div>div>input {
        background-color: #F9F9F9 !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
    }
    div.stButton > button[kind="secondary"], div.stButton > button {
        background-color: #FF5722 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover {
        background-color: #E64A19 !important;
        color: white !important;
    }
    .orange-card {
        background-color: #FF5722 !important;
        color: white !important;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
    }
    .orange-card h3, .orange-card p, .orange-card span, .orange-card label, .orange-card div {
        color: white !important;
    }
    .map-box {
        border-radius: 10px;
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
            image_path TEXT
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

# تهيئة كافة المتغيرات الضرورية في st.session_state لمنع ظهور أخطاء الـ KeyError
if "splash_shown" not in st.session_state:
  st.session_state.splash_shown = False
if "step" not in st.session_state:
  st.session_state.step = "enter_phone"
if "phone" not in st.session_state:
  st.session_state.phone = ""
if "customer_name" not in st.session_state:
  st.session_state.customer_name = ""
if "customer_address" not in st.session_state:
  st.session_state.customer_address = ""
if "cust_lat" not in st.session_state:
  st.session_state.cust_lat = 31.1854
if "cust_lng" not in st.session_state:
  st.session_state.cust_lng = 35.7048
if "selected_category" not in st.session_state:
  st.session_state.selected_category = "الكل"
if "cart" not in st.session_state:
  st.session_state.cart = []

# الشاشة الترحيبية المتحركة عند أول فتح للتطبيق
if not st.session_state.splash_shown:
  splash_placeholder = st.empty()
  with splash_placeholder.container():
    st.markdown(
        """
            <div style="background-color: #FF5722; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; text-align: center;">
                <h1 style="font-size: 3.5rem; margin-bottom: 10px; font-weight: bold; color: white !important;">🛒 بوابة الكرك للطلبات</h1>
                <h3 style="font-size: 1.8rem; font-weight: normal; opacity: 0.9; color: white !important;">أهلاً بكم في خدمتنا</h3>
                <h2 style="font-size: 2rem; margin-top: 20px; letter-spacing: 2px; font-style: italic; color: white !important;">Karak Gate</h2>
            </div>
            """,
        unsafe_allow_html=True,
    )
  time.sleep(3)
  splash_placeholder.empty()
  st.session_state.splash_shown = True
  st.rerun()

if st.session_state.step == "enter_phone":
  st.markdown(
      "<style>.stApp { background-color: #FF5722; color: white; }</style>",
      unsafe_allow_html=True,
  )
  st.subheader("📱 تسجيل دخول الزبون")
  with st.form("phone_form"):
    phone_input = st.text_input("أدخل رقم الهاتف المحمول (مثال: 079xxxxxxx)")
    submit_phone = st.form_submit_button("إرسال رمز التحقق (OTP)")

    if submit_phone and phone_input:
      st.session_state.phone = phone_input
      st.session_state.step = "verify_otp"
      st.rerun()

elif st.session_state.step == "verify_otp":
  st.markdown(
      "<style>.stApp { background-color: #FF5722; color: white; }</style>",
      unsafe_allow_html=True,
  )
  st.subheader("🔐 إدخال رمز التحقق")
  st.info(
      f"الرقم المرسل إليه: {st.session_state.phone} | (الرمز التجريبي هو: 1234)"
  )

  with st.form("otp_form"):
    entered_otp = st.text_input("أدخل رمز التحقق (1234)", type="password")
    submit_otp = st.form_submit_button("تحقق من الرمز")

    if submit_otp:
      if entered_otp == "1234":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, address FROM customers WHERE phone = ?",
            (st.session_state.phone,),
        )
        existing_customer = cursor.fetchone()
        conn.close()

        if existing_customer:
          st.session_state.customer_name = existing_customer[0]
          st.session_state.customer_address = existing_customer[1]
          st.session_state.step = "main_shop"
          st.rerun()
        else:
          st.session_state.step = "setup_profile"
          st.rerun()
      else:
        st.error("رمز التحقق غير صحيح! الرجاء إدخال 1234")

elif st.session_state.step == "setup_profile":
  st.markdown(
      "<style>.stApp { background-color: #FF5722; color: white; }</style>",
      unsafe_allow_html=True,
  )
  st.subheader("⚙ إعدادات الحساب والعنوان وتحديد الموقع الجغرافي")

  temp_name = st.text_input("الاسم الكامل", value=st.session_state.customer_name)
  temp_address = st.text_area(
      "العنوان التفصيلي (المدينة، الحي، الشارع)",
      value=st.session_state.customer_address,
  )

  st.markdown("### 📍 إحداثيات خريطة جوجل (GPS)")
  col_lat, col_lng = st.columns(2)
  with col_lat:
    lat_in = st.number_input(
        "خط العرض (Latitude)",
        value=float(st.session_state.cust_lat),
        format="%.6f",
    )
  with col_lng:
    lng_in = st.number_input(
        "خط الطول (Longitude)",
        value=float(st.session_state.cust_lng),
        format="%.6f",
    )

  setup_map_url = f"https://maps.google.com/maps?q={lat_in},{lng_in}&t=&z=15&ie=UTF8&iwloc=&output=embed"
  st.markdown(
      f"""
        <div class="map-box">
            <iframe width="100%" height="220" frameborder="0" scrolling="no" src="{setup_map_url}"></iframe>
        </div>
    """,
      unsafe_allow_html=True,
  )

  if st.button("حفظ البيانات والدخول للمتجر"):
    if temp_name and temp_address:
      conn = get_db()
      cursor = conn.cursor()
      full_addr = f"{temp_address} | خريطة: https://maps.google.com/?q={lat_in},{lng_in}"
      cursor.execute(
          """
                INSERT OR REPLACE INTO customers (name, phone, address) 
                VALUES (?, ?, ?)
            """,
          (temp_name, st.session_state.phone, full_addr),
      )
      conn.commit()
      conn.close()

      # تحديث الـ session_state بالقيم الجديدة لضمان عدم حدوث خطأ KeyError
      st.session_state.customer_name = temp_name
      st.session_state.customer_address = full_addr
      st.session_state.cust_lat = lat_in
      st.session_state.cust_lng = lng_in
      st.session_state.step = "main_shop"
      st.rerun()
    else:
      st.error("الرجاء إدخال الاسم الكامل والعنوان التفصيلي.")

elif st.session_state.step == "main_shop":
  col_top1, col_top2 = st.columns([3, 1])
  with col_top1:
    st.success(
        f"أهلاً بك يا {st.session_state.customer_name} | عنوانك:"
        f" {st.session_state.customer_address}"
    )
  with col_top2:
    if st.button("🔄 تحديث المتاجر والأصناف"):
      st.rerun()

  main_tab1, main_tab2 = st.tabs([
      "🛍 متجر الكرك والأصناف",
      "📍 تتبع طلباتي النشطة (Live GPS)",
  ])

  with main_tab1:
    search_query = st.text_input(
        "🔍 بحث سريع عن أصناف أو متاجر في الكرك...", ""
    )
    st.markdown("---")

    st.subheader("📁 الأقسام الرئيسية")
    categories = [
        "الكل",
        "مطاعم",
        "حلويات",
        "ماركت",
        "محامص ومكسرات",
        "خضروات وفواكه",
        "لحوم",
        "صيدليات ومستلزمات طبيه",
    ]

    cols_cat = st.columns(len(categories))
    for i, cat in enumerate(categories):
      with cols_cat[i]:
        if st.button(cat, key=f"cat_btn_{i}", use_container_width=True):
          st.session_state.selected_category = cat
          st.rerun()

    st.write(
        f"**القسم الحالي:** `{st.session_state.selected_category}`"
    )
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
      st.subheader("🏬 المتاجر المعتمدة والأصناف المتاحة")

      conn = get_db()
      cursor = conn.cursor()

      if st.session_state.selected_category == "الكل":
        cursor.execute(
            "SELECT name, category, phone, location, image_path FROM merchants"
            " WHERE status='معتمد'"
        )
      else:
        cursor.execute(
            "SELECT name, category, phone, location, image_path FROM merchants"
            " WHERE status='معتمد' AND category=?",
            (st.session_state.selected_category,),
        )

      merchants = cursor.fetchall()

      if not merchants:
        st.info("لا توجد متاجر معتمدة حالياً في هذا القسم.")
      else:
        for m_idx, m in enumerate(merchants):
          m_name, m_cat, m_phone, m_loc, m_img = m

          if (
              search_query
              and search_query.lower() not in m_name.lower()
              and search_query.lower() not in m_cat.lower()
          ):
            continue

          if m_img and os.path.exists(m_img):
            st.image(m_img, width=120)

          st.markdown(f"### 🏬 {m_name}")
          st.write(f"التصنيف: **{m_cat}** | الموقع: {m_loc}")

          cursor.execute(
              "SELECT id, item_name, price, quantity, unit, image_path FROM"
              " products WHERE merchant_name = ?",
              (m_name,),
          )
          products = cursor.fetchall()

          if products:
            st.write("📋 **الأصناف المتوفرة:**")
            for idx_p, p in enumerate(products):
              p_id, p_name, p_price, p_qty, p_unit, p_img = p

              p_col1, p_col2, p_col3 = st.columns([1, 3, 1])
              with p_col1:
                if p_img and os.path.exists(p_img):
                  st.image(p_img, width=50)
                else:
                  st.write("📷")
              with p_col2:
                st.write(
                    f"**{p_name}** ({p_qty} {p_unit}) - {p_price} د.أ"
                )
              with p_col3:
                if st.button("➕ إضافة", key=f"add_p_{m_idx}_{p_id}_{idx_p}"):
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
        st.write(f"🏷️ **مجموع الأصناف:** {subtotal:.2f} د.أ")
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
            items_summary += (
                f"- {item['name']} ({item['price']} د.أ) [المتجر:"
                f" {item['merchant']}]\n"
            )

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

  with main_tab2:
    st.subheader("📍 تتبع طلباتي النشطة")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, order_status, driver_name, total_amount, created_at, lat,"
        " lng FROM orders WHERE customer_phone = ? ORDER BY id DESC",
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

        # عرض الخريطة للطلب النشط
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