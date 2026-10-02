import sys
import io
import os
import base64
from datetime import datetime
import sqlite3
import streamlit as st
import pandas as pd

# فرض ترميز UTF-8 لمنع مشاكل الحروف العربية
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
    .admin-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 5px solid #FF5722;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            vehicle_type TEXT,
            status TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            discount_details TEXT,
            valid_until TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """
    )

    # الرقم السري الافتراضي (2026)
    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_password', '2026')"
    )

    # تحديث وتعديل الجداول تلقائياً إذا كانت ناقصة أعمدة
    cursor.execute("PRAGMA table_info(merchants)")
    merchant_columns = [col[1] for col in cursor.fetchall()]
    if "image_data" not in merchant_columns:
        try:
            cursor.execute("ALTER TABLE merchants ADD COLUMN image_data TEXT;")
        except Exception:
            pass

    cursor.execute("PRAGMA table_info(products)")
    product_columns = [col[1] for col in cursor.fetchall()]
    if "quantity" not in product_columns:
        cursor.execute("ALTER TABLE products ADD COLUMN quantity TEXT")
    if "unit" not in product_columns:
        cursor.execute("ALTER TABLE products ADD COLUMN unit TEXT")
    if "image_path" not in product_columns:
        cursor.execute("ALTER TABLE products ADD COLUMN image_path TEXT")

    conn.commit()
    conn.close()


init_db()

# متغيرات الجلسة الافتراضية
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

# تسجيل الزبون افتراضياً
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

# ==========================================
# شريط التنقل الأفقي العلوي (شامل الرئيسية، الطلبات، الحساب، والإدارة)
# ==========================================
st.markdown(
    """
    <div style="background-color: #FFFFFF; padding: 12px; border-radius: 12px; border: 1px solid #E0E0E0; margin-bottom: 20px; text-align: center;">
        <h2 style="margin: 0; color: #FF5722 !important;">🏰 بوابة الكرك (Karak Gate)</h2>
        <p style="margin: 0; font-size: 13px; color: #666 !important;">منصة التوصيل الأولى في محافظة الكرك</p>
    </div>
""",
    unsafe_allow_html=True,
)

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
with nav_col1:
    if st.button("🏠 الرئيسية", use_container_width=True):
        st.session_state.nav_tab = "الرئيسية"
        st.rerun()
with nav_col2:
    if st.button("📦 طلباتي", use_container_width=True):
        st.session_state.nav_tab = "الطلبات"
        st.rerun()
with nav_col3:
    if st.button("👤 حسابي", use_container_width=True):
        st.session_state.nav_tab = "الحساب"
        st.rerun()
with nav_col4:
    if st.button("🔐 الإدارة", use_container_width=True):
        st.session_state.nav_tab = "الإدارة"
        st.rerun()

st.markdown("---")

# ==========================================
# 1. قسم لوحة تحكم الإدارة المحمية (عبر الشريط الأفقي)
# ==========================================
if st.session_state.nav_tab == "الإدارة":
    st.subheader("⚙️ بوابة دخول الإدارة المحمية")

    # جلب الرقم السري الحالي من قاعدة البيانات
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'admin_password'")
    db_pass_row = cursor.fetchone()
    current_admin_pass = db_pass_row[0] if db_pass_row else "2026"
    conn.close()

    admin_password = st.text_input(
        "أدخل الرقم السري للوحة الإدارة:", type="password"
    )

    if admin_password == current_admin_pass:
        st.success("تم التحقق بنجاح. أهلاً بك يا أبو عدي في لوحة التحكم.")
        st.markdown("---")

        admin_menu = st.selectbox(
            "اختر قسم الإدارة:",
            [
                "📦 طلبات الزبائن الواردة",
                "🏬 إدارة المتاجر",
                "📋 إدارة الأصناف والقوائم",
                "🛵 إدارة السائقين",
                "🏷️ إدارة العروض",
                "📊 التقرير المالي",
                "👥 سجل الزبائن المسجلين",
                "🔑 تغيير الرقم السري للإدارة",
            ],
        )

        conn = get_db()
        cursor = conn.cursor()

        # أ. طلبات الزبائن
        if admin_menu == "📦 طلبات الزبائن الواردة":
            st.subheader("📦 طلبات الزبائن الواردة وتتبع حالتها")
            cursor.execute(
                "SELECT id, customer_name, customer_phone, customer_address, order_details, total_amount, payment_method, order_status, created_at FROM orders ORDER BY id DESC"
            )
            orders = cursor.fetchall()

            if not orders:
                st.info("لا توجد طلبات واردة حتى الآن.")
            else:
                for ord_data in orders:
                    (
                        o_id,
                        o_name,
                        o_phone,
                        o_addr,
                        o_details,
                        o_total,
                        o_pay,
                        o_status,
                        o_time,
                    ) = ord_data
                    with st.container():
                        st.markdown(
                            f"""
                        <div class="admin-card">
                            <h4>🛒 طلب رقم #{o_id} | الزبون: {o_name}</h4>
                            <p><b>📞 الهاتف:</b> {o_phone} | <b>📍 العنوان:</b> {o_addr}</p>
                            <p><b>🕒 وقت الطلب:</b> {o_time} | <b>💳 طريقة الدفع:</b> {o_pay}</p>
                            <hr style="border: 0.5px solid #CFD8DC;">
                            <p><b>📋 تفاصيل الأصناف المطلوبة:</b></p>
                            <pre style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; color: #333;">{o_details}</pre>
                            <p style="font-size: 18px; color: #D84315;"><b>💰 المجموع الإجمالي:</b> {o_total:.2f} دينار</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        col_status, col_btn = st.columns([2, 1])
                        with col_status:
                            new_status = st.selectbox(
                                f"تحديث حالة الطلب #{o_id}",
                                [
                                    "قيد التجهيز",
                                    "مع السائق (في الطريق)",
                                    "تم التسليم",
                                    "ملغي",
                                ],
                                index=(
                                    [
                                        "قيد التجهيز",
                                        "مع السائق (في الطريق)",
                                        "تم التسليم",
                                        "ملغي",
                                    ].index(o_status)
                                    if o_status
                                    in [
                                        "قيد التجهيز",
                                        "مع السائق (في الطريق)",
                                        "تم التسليم",
                                        "ملغي",
                                    ]
                                    else 0
                                ),
                                key=f"status_sel_{o_id}",
                            )
                        with col_btn:
                            st.write("")
                            if st.button(
                                "💾 حفظ الحالة", key=f"save_status_{o_id}"
                            ):
                                cursor.execute(
                                    "UPDATE orders SET order_status = ? WHERE id = ?",
                                    (new_status, o_id),
                                )
                                conn.commit()
                                st.success(
                                    f"تم تحديث حالة الطلب #{o_id} بنجاح!"
                                )
                                st.rerun()

                        wa_link = f"https://wa.me/962{o_phone.lstrip('0')}?text=مرحباً يا {o_name}، بخصوص طلبك رقم #{o_id} من بوابة الكرك..."
                        st.markdown(
                            f"""
                            <a href="{wa_link}" target="_blank">
                                <button style="background-color: #25D366; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;">
                                    💬 مراسلة الزبون عبر الواتساب
                                </button>
                            </a>
                        """,
                            unsafe_allow_html=True,
                        )
                        st.markdown("---")

        # ب. إدارة المتاجر
        elif admin_menu == "🏬 إدارة المتاجر":
            st.subheader("🏬 إضافة وتعديل وحذف المتاجر في الكرك")
            with st.form("add_merchant_form"):
                st.write("### إدخال متجر جديد:")
                m_name = st.text_input("اسم المتجر")
                m_category = st.selectbox(
                    "القسم الرئيسي:",
                    [
                        "مطاعم",
                        "حلويات",
                        "ماركت",
                        "محامص ومكسرات",
                        "خضروات وفواكه",
                        "لحوم",
                        "صيدليات ومستلزمات طبيه",
                    ],
                )
                m_phone = st.text_input("رقم هاتف المتجر")
                m_location = st.text_input("عنوان المتجر / المنطقة")
                m_status = st.selectbox(
                    "حالة المتجر", ["معتمد", "قيد المراجعة"]
                )
                m_image = st.file_uploader(
                    "تنزيل صورة المتجر", type=["jpg", "png", "jpeg"]
                )

                submit_merchant = st.form_submit_button(
                    "إضافة المتجر للنظام"
                )
                if submit_merchant and m_name:
                    image_base64 = ""
                    if m_image is not None:
                        bytes_data = m_image.getvalue()
                        image_base64 = f"data:image/jpeg;base64,{base64.b64encode(bytes_data).decode('utf-8')}"
                    try:
                        cursor.execute(
                            "INSERT INTO merchants (name, category, phone, location, status, image_data) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                m_name,
                                m_category,
                                m_phone,
                                m_location,
                                m_status,
                                image_base64,
                            ),
                        )
                        conn.commit()
                        st.success(f"تم إضافة المتجر ({m_name}) بنجاح!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء إضافة المتجر: {e}")

            st.markdown("---")
            st.subheader("📋 تعديل أو حذف المتاجر المسجلة")
            cursor.execute(
                "SELECT id, name, category, phone, location, status FROM merchants"
            )
            merchants_list = cursor.fetchall()
            if merchants_list:
                df_merchants = pd.DataFrame(
                    merchants_list,
                    columns=[
                        "المعرف",
                        "اسم المتجر",
                        "القسم",
                        "الهاتف",
                        "الموقع",
                        "الحالة",
                    ],
                )
                st.dataframe(df_merchants, use_container_width=True)
                selected_m_name = st.selectbox(
                    "اختر متجراً للتعديل أو الحذف:",
                    [m[1] for m in merchants_list],
                )
                if selected_m_name:
                    cursor.execute(
                        "SELECT name, category, phone, location, status FROM merchants WHERE name = ?",
                        (selected_m_name,),
                    )
                    m_data = cursor.fetchone()
                    with st.form("edit_merchant_form"):
                        st.write(
                            f"### تعديل بيانات المتجر: {selected_m_name}"
                        )
                        edit_name = st.text_input(
                            "اسم المتجر الجديد", value=m_data[0]
                        )
                        edit_cat = st.selectbox(
                            "القسم",
                            [
                                "مطاعم",
                                "حلويات",
                                "ماركت",
                                "محامص ومكسرات",
                                "خضروات وفواكه",
                                "لحوم",
                                "صيدليات ومستلزمات طبيه",
                            ],
                            index=0,
                        )
                        edit_phone = st.text_input("الهاتف", value=m_data[2])
                        edit_loc = st.text_input("الموقع", value=m_data[3])
                        edit_status = st.selectbox(
                            "الحالة",
                            ["معتمد", "قيد المراجعة"],
                            index=0 if m_data[4] == "معتمد" else 1,
                        )
                        if st.form_submit_button("حفظ التعديلات"):
                            cursor.execute(
                                "UPDATE merchants SET name=?, category=?, phone=?, location=?, status=? WHERE name=?",
                                (
                                    edit_name,
                                    edit_cat,
                                    edit_phone,
                                    edit_loc,
                                    edit_status,
                                    selected_m_name,
                                ),
                            )
                            conn.commit()
                            st.success("تم تحديث بيانات المتجر بنجاح!")
                            st.rerun()
                    if st.button("🗑️ حذف هذا المتجر نهائياً"):
                        cursor.execute(
                            "DELETE FROM merchants WHERE name = ?",
                            (selected_m_name,),
                        )
                        cursor.execute(
                            "DELETE FROM products WHERE merchant_name = ?",
                            (selected_m_name,),
                        )
                        conn.commit()
                        st.success(
                            f"تم حذف المتجر ({selected_m_name}) بنجاح!"
                        )
                        st.rerun()

        # ج. إدارة الأصناف والقوائم
        elif admin_menu == "📋 إدارة الأصناف والقوائم":
            st.subheader(
                "📋 إضافة الأصناف مع الكمية والوحدة والصورة للمتاجر المعتمدة"
            )
            cursor.execute("SELECT name FROM merchants WHERE status='معتمد'")
            active_merchants = [row[0] for row in cursor.fetchall()]
            if not active_merchants:
                st.warning("لا توجد متاجر معتمدة حالياً.")
            else:
                with st.form("add_product_form"):
                    selected_merchant = st.selectbox(
                        "اختر المتجر:", active_merchants
                    )
                    item_name = st.text_input("اسم الصنف أو الوجبة")
                    col_q1, col_q2 = st.columns(2)
                    with col_q1:
                        item_quantity = st.text_input("الكمية", value="1")
                    with col_q2:
                        item_unit = st.selectbox(
                            "الوحدة",
                            [
                                "وجبة",
                                "صحن",
                                "كيلو",
                                "غرام",
                                "حبة",
                                "باكيت",
                                "عبوة",
                                "لتر",
                                "قطعة",
                                "دستة",
                            ],
                        )
                    item_price = st.number_input(
                        "السعر بالدينار الأردني",
                        min_value=0.1,
                        value=1.0,
                        step=0.25,
                    )
                    item_image = st.file_uploader(
                        "تنزيل صورة الصنف", type=["jpg", "png", "jpeg"]
                    )

                    if (
                        st.form_submit_button("إضافة الصنف للمتجر")
                        and item_name
                    ):
                        image_base64 = ""
                        if item_image is not None:
                            bytes_data = item_image.getvalue()
                            image_base64 = f"data:image/jpeg;base64,{base64.b64encode(bytes_data).decode('utf-8')}"
                        cursor.execute(
                            "INSERT INTO products (merchant_name, item_name, price, quantity, unit, image_path) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                selected_merchant,
                                item_name,
                                item_price,
                                item_quantity,
                                item_unit,
                                image_base64,
                            ),
                        )
                        conn.commit()
                        st.success("تم إضافة الصنف بنجاح!")
                        st.rerun()

                st.markdown("---")
                cursor.execute(
                    "SELECT id, merchant_name, item_name, quantity, unit, price FROM products"
                )
                products_list = cursor.fetchall()
                if products_list:
                    st.dataframe(
                        pd.DataFrame(
                            products_list,
                            columns=[
                                "المعرف",
                                "المتجر",
                                "اسم الصنف",
                                "الكمية",
                                "الوحدة",
                                "السعر (د.أ)",
                            ],
                        ),
                        use_container_width=True,
                    )

        # د. إدارة السائقين
        elif admin_menu == "🛵 إدارة السائقين":
            st.subheader("🛵 إدارة فريق التوصيل والسائقين")

            with st.form("driver_form"):
                st.write("### إدخال سائق جديد:")
                d_name = st.text_input("اسم السائق الكامل")
                d_phone = st.text_input("رقم الهاتف المحمول")
                d_vehicle = st.selectbox(
                    "نوع المركبة",
                    ["سكوتر / دراجة نارية", "سيارة صغيرة", "باص توصيل"],
                )
                d_status = st.selectbox(
                    "حالة السائق",
                    ["متاح للتوصيل", "في مهمة توصيل", "غير متاح"],
                )

                if st.form_submit_button("إضافة السائق للنظام") and d_name:
                    cursor.execute(
                        "INSERT INTO drivers (name, phone, vehicle_type, status) VALUES (?, ?, ?, ?)",
                        (d_name, d_phone, d_vehicle, d_status),
                    )
                    conn.commit()
                    st.success(f"تم إضافة السائق ({d_name}) بنجاح!")
                    st.rerun()

            st.markdown("---")
            st.subheader("📋 تعديل أو حذف السائقين المسجلين")
            cursor.execute(
                "SELECT id, name, phone, vehicle_type, status FROM drivers"
            )
            drivers_list = cursor.fetchall()

            if not drivers_list:
                st.info("لا توجد سائقين مسجلين في النظام حالياً.")
            else:
                df_drivers = pd.DataFrame(
                    drivers_list,
                    columns=[
                        "المعرف",
                        "اسم السائق",
                        "رقم الهاتف",
                        "نوع المركبة",
                        "الحالة",
                    ],
                )
                st.dataframe(df_drivers, use_container_width=True)

                st.write("---")
                st.write("### ⚙️ لوحة التعديل والحذف الفوري للسائقين:")

                driver_options = {
                    f"معرف رقم ({d[0]}): {d[1]}": d[0] for d in drivers_list
                }
                selected_driver_label = st.selectbox(
                    "اختر السائق المراد تعديل بياناته أو حذفه:",
                    list(driver_options.keys()),
                )

                if selected_driver_label:
                    selected_d_id = driver_options[selected_driver_label]
                    cursor.execute(
                        "SELECT id, name, phone, vehicle_type, status FROM drivers WHERE id = ?",
                        (selected_d_id,),
                    )
                    d_data = cursor.fetchone()

                    if d_data:
                        with st.form("edit_driver_form_direct"):
                            st.write(f"#### تعديل بيانات السائق: {d_data[1]}")
                            ed_name = st.text_input(
                                "اسم السائق الجديد", value=d_data[1]
                            )
                            ed_phone = st.text_input(
                                "رقم الهاتف الجديد", value=d_data[2]
                            )

                            vehicles_list = [
                                "سكوتر / دراجة نارية",
                                "سيارة صغيرة",
                                "باص توصيل",
                                "سيارة خاصة",
                            ]
                            curr_veh = (
                                d_data[3]
                                if d_data[3] in vehicles_list
                                else "سكوتر / دراجة نارية"
                            )
                            ed_vehicle = st.selectbox(
                                "نوع المركبة",
                                vehicles_list,
                                index=vehicles_list.index(curr_veh),
                            )

                            statuses_list = [
                                "متاح للتوصيل",
                                "في مهمة توصيل",
                                "غير متاح",
                                "متاح",
                            ]
                            curr_stat = (
                                d_data[4]
                                if d_data[4] in statuses_list
                                else "متاح للتوصيل"
                            )
                            ed_status = st.selectbox(
                                "حالة السائق",
                                statuses_list,
                                index=(
                                    statuses_list.index(curr_stat)
                                    if curr_stat in statuses_list
                                    else 0
                                ),
                            )

                            update_driver_btn = st.form_submit_button(
                                "💾 حفظ تعديلات السائق"
                            )
                            if update_driver_btn:
                                cursor.execute(
                                    "UPDATE drivers SET name = ?, phone = ?, vehicle_type = ?, status = ? WHERE id = ?",
                                    (
                                        ed_name,
                                        ed_phone,
                                        ed_vehicle,
                                        ed_status,
                                        selected_d_id,
                                    ),
                                )
                                conn.commit()
                                st.success("تم تحديث بيانات السائق بنجاح!")
                                st.rerun()

                        st.write("")
                        if st.button(
                            "🗑 حذف هذا السائق نهائياً من النظام",
                            key=f"del_drv_{selected_d_id}",
                        ):
                            cursor.execute(
                                "DELETE FROM drivers WHERE id = ?",
                                (selected_d_id,),
                            )
                            conn.commit()
                            st.success("تم حذف السائق بنجاح!")
                            st.rerun()

        # هـ. إدارة العروض
        elif admin_menu == "🏷️ إدارة العروض":
            st.subheader("🏷️ إضافة عروض التخفيضات والخصومات")
            with st.form("offer_form"):
                offer_title = st.text_input("عنوان العرض")
                offer_desc = st.text_area("تفاصيل الخصم أو العرض")
                valid_date = st.text_input("صالح لغاية تاريخ", "2026-10-31")
                if st.form_submit_button("نشر العرض في النظام") and offer_title:
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='offers'"
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            "CREATE TABLE offers (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, discount_details TEXT, valid_until TEXT)"
                        )
                    cursor.execute(
                        "INSERT INTO offers (title, discount_details, valid_until) VALUES (?, ?, ?)",
                        (offer_title, offer_desc, valid_date),
                    )
                    conn.commit()
                    st.success("تم نشر العرض بنجاح!")
                    st.rerun()

        # و. التقرير المالي
        elif admin_menu == "📊 التقرير المالي":
            st.subheader("📊 التقارير المالية والإحصائيات الشاملة")
            try:
                cursor.execute(
                    "SELECT COUNT(*), SUM(total_amount) FROM orders"
                )
                order_stats = cursor.fetchone()
                total_orders_count = (
                    order_stats[0] if order_stats and order_stats[0] else 0
                )
                total_revenue = (
                    order_stats[1] if order_stats and order_stats[1] else 0.0
                )
            except:
                total_orders_count, total_revenue = 0, 0.0

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric(
                    label="📦 إجمالي عدد الطلبات", value=total_orders_count
                )
            with col_m2:
                st.metric(
                    label="💰 إجمالي المبيعات (دينار أردني)",
                    value=f"{total_revenue:.2f} د.أ",
                )

        # ز. سجل الزبائن
        elif admin_menu == "👥 سجل الزبائن المسجلين":
            st.subheader("👥 بيانات الزبائن المسجلين في التطبيق")
            try:
                cursor.execute("SELECT id, name, phone, address FROM customers")
                customers_list = cursor.fetchall()
            except:
                customers_list = []
            if customers_list:
                st.dataframe(
                    pd.DataFrame(
                        customers_list,
                        columns=[
                            "المعرف",
                            "اسم الزبون",
                            "رقم الهاتف",
                            "العنوان والموقع",
                        ],
                    ),
                    use_container_width=True,
                )
            else:
                st.info("لم يتم تسجيل أي زبون حتى الآن.")

        # ح. تغيير الرقم السري
        elif admin_menu == "🔑 تغيير الرقم السري للإدارة":
            st.subheader("🔑 إعدادات الأمان وتغيير الرقم السري للوحة التحكم")
            with st.form("change_password_form"):
                new_pass1 = st.text_input(
                    "أدخل الرقم السري الجديد:", type="password"
                )
                new_pass2 = st.text_input(
                    "تأكيد الرقم السري الجديد:", type="password"
                )
                change_btn = st.form_submit_button("💾 تحديث الرقم السري")

                if change_btn:
                    if new_pass1 and new_pass1 == new_pass2:
                        cursor.execute(
                            "UPDATE settings SET value = ? WHERE key = 'admin_password'",
                            (new_pass1,),
                        )
                        conn.commit()
                        st.success(
                            "✅ تم تغيير الرقم السري بنجاح! سيتم اعتماده في عمليات الدخول القادمة."
                        )
                    else:
                        st.error(
                            "⚠️ خطأ: الحقول فارغة أو الرقمين غير متطابقين. يرجى إعادة المحاولة."
                        )

        conn.close()
    elif admin_password != "":
        st.error("الرقم السري غير صحيح! يرجى إدخال الرقم الصحيح للمتابعة.")

# ==========================================
# 2. قسم الرئيسية (Home / تصفح المتاجر)
# ==========================================
elif st.session_state.nav_tab == "الرئيسية":
    col_top1, col_top2 = st.columns([3, 1])
    with col_top1:
        st.success(
            f"أهلاً بك يا {st.session_state.customer_name} | عنوانك: {st.session_state.customer_address}"
        )
    with col_top2:
        if st.button("🔄 تحديث الشاشة"):
            st.rerun()

    search_query = st.text_input(
        "🔍 بحث سريع عن أصناف أو متاجر في الكرك...", ""
    )
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
        {"name": "ماركت", "img": "https://img.icons8.com/color/96/shopping-cart.png"},
        {
            "name": "محامص ومكسرات",
            "img": "https://img.icons8.com/color/96/peanuts.png",
        },
        {
            "name": "خضروات وفواكه",
            "img": "https://img.icons8.com/color/96/basket.png",
        },
        {"name": "لحوم", "img": "https://img.icons8.com/color/96/steak.png"},
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
                    <img src="{cat_info['img']}" width="40" style="margin-bottom: 6px;"><br>
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

                # عرض صورة المتجر المخزنة Base64
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
                    st.success("🎉 تم تأكيد طلبك بنجاح وحفظه للإدارة بشكل فوري!")
                    st.session_state.cart = []
                except Exception as e:
                    st.error(f"خطأ: {e}")

# ==========================================
# 3. قسم تتبع الطلبات (الطلبات)
# ==========================================
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

# ==========================================
# 4. قسم تعديل الحساب (الحساب)
# ==========================================
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