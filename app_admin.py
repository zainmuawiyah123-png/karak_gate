import streamlit as st
import sqlite3
import pandas as pd
import base64

# إعدادات الصفحة وإخفاء شعار وقائمة Streamlit نهائياً
st.set_page_config(
    page_title="إدارة بوابة الكرك - Admin Dashboard", 
    page_icon="🔔", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# كود CSS لتنسيق لوحة التحكم وإخفاء العناصر الزائدة
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none !important;}
    div[data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    
    .stApp {
        background-color: #FFF3E0 !important;
        color: #000000 !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, span {
        color: #263238 !important;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
        border: none;
        background-color: #FF5722 !important;
        color: white !important;
    }
    .stButton>button:hover {
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
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .bell-alert {
        background-color: #D32F2F;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        animation: pulse 1s infinite;
        margin-bottom: 20px;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def get_db():
    return sqlite3.connect('karak_gate.db', check_same_thread=False)

def init_admin_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT UNIQUE,
            address TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS merchants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            phone TEXT,
            location TEXT,
            status TEXT,
            image_data TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_name TEXT,
            item_name TEXT,
            price REAL,
            image_path TEXT,
            quantity TEXT,
            unit TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            customer_address TEXT,
            order_details TEXT,
            total_amount REAL,
            payment_method TEXT,
            order_status TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            vehicle_type TEXT,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            discount_details TEXT,
            valid_until TEXT
        )
    ''')
    
    # تحديث وتعديل الجداول القائمة تلقائياً إذا كانت ناقصة أعمدة
    cursor.execute("PRAGMA table_info(merchants)")
    merchant_columns = [col[1] for col in cursor.fetchall()]
    if "image_path" in merchant_columns and "image_data" not in merchant_columns:
        try:
            cursor.execute("ALTER TABLE merchants RENAME COLUMN image_path TO image_data;")
        except Exception:
            pass
    elif "image_data" not in merchant_columns:
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

init_admin_db()

conn_temp = get_db()
cursor_temp = conn_temp.cursor()
try:
    cursor_temp.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'قيد التجهيز'")
    pending_count = cursor_temp.fetchone()[0]
except:
    pending_count = 0
conn_temp.close()

st.title("⚙ لوحة تحكم إدارة بوابة الكرك (Karak Gate Admin)")

if pending_count > 0:
    st.markdown(f"""
        <div class="bell-alert">
            🔔 تنبيه هام: يوجد ({pending_count}) طلب جديد قيد الانتظار ويتطلب التجهيز الفوري!
        </div>
    """, unsafe_allow_html=True)
    
    sound_html = """
    <script>
    function playBell() {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
        gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.4);
    }
    playBell();
    </script>
    """
    st.components.v1.html(sound_html, height=0)

st.sidebar.title("🛠 خيارات الإدارة")
admin_menu = st.sidebar.selectbox(
    "اختر القسم للإدارة:",
    [
        "📦 طلبات الزبائن الواردة", 
        "🏬 إدارة المتاجر", 
        "📋 إدارة الأصناف والقوائم", 
        "🛵 إدارة السائقين",
        "🏷️ إدارة العروض",
        "📊 التقرير المالي",
        "👥 سجل الزبائن المسجلين"
    ]
)

conn = get_db()
cursor = conn.cursor()

# 1. طلبات الزبائن
if admin_menu == "📦 طلبات الزبائن الواردة":
    st.subheader("📦 طلبات الزبائن الواردة وتتبع حالتها")
    cursor.execute("SELECT id, customer_name, customer_phone, customer_address, order_details, total_amount, payment_method, order_status, created_at FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()
    
    if not orders:
        st.info("لا توجد طلبات واردة حتى الآن.")
    else:
        for ord_data in orders:
            o_id, o_name, o_phone, o_addr, o_details, o_total, o_pay, o_status, o_time = ord_data
            with st.container():
                st.markdown(f"""
                <div class="admin-card">
                    <h4>🛒 طلب رقم #{o_id} | الزبون: {o_name}</h4>
                    <p><b>📞 الهاتف:</b> {o_phone} | <b>📍 العنوان:</b> {o_addr}</p>
                    <p><b>🕒 وقت الطلب:</b> {o_time} | <b>💳 طريقة الدفع:</b> {o_pay}</p>
                    <hr style="border: 0.5px solid #CFD8DC;">
                    <p><b>📋 تفاصيل الأصناف المطلوبة:</b></p>
                    <pre style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; color: #333;">{o_details}</pre>
                    <p style="font-size: 18px; color: #D84315;"><b>💰 المجموع الإجمالي:</b> {o_total:.2f} دينار</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_status, col_btn = st.columns([2, 1])
                with col_status:
                    new_status = st.selectbox(
                        f"تحديث حالة الطلب #{o_id}",
                        ["قيد التجهيز", "مع السائق (في الطريق)", "تم التسليم", "ملغي"],
                        index=["قيد التجهيز", "مع السائق (في الطريق)", "تم التسليم", "ملغي"].index(o_status) if o_status in ["قيد التجهيز", "مع السائق (في الطريق)", "تم التسليم", "ملغي"] else 0,
                        key=f"status_sel_{o_id}"
                    )
                with col_btn:
                    st.write("") 
                    if st.button("💾 حفظ الحالة", key=f"save_status_{o_id}"):
                        cursor.execute("UPDATE orders SET order_status = ? WHERE id = ?", (new_status, o_id))
                        conn.commit()
                        st.success(f"تم تحديث حالة الطلب #{o_id} بنجاح!")
                        st.rerun()
                
                wa_link = f"https://wa.me/962{o_phone.lstrip('0')}?text=مرحباً يا {o_name}، بخصوص طلبك رقم #{o_id} من بوابة الكرك..."
                st.markdown(f"""
                    <a href="{wa_link}" target="_blank">
                        <button style="background-color: #25D366; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;">
                            💬 مراسلة الزبون عبر الواتساب
                        </button>
                    </a>
                """, unsafe_allow_html=True)
                st.markdown("---")

# 2. إدارة المتاجر
elif admin_menu == "🏬 إدارة المتاجر":
    st.subheader("🏬 إضافة وتعديل وحذف المتاجر في الكرك")
    with st.form("add_merchant_form"):
        st.write("### إدخال متجر جديد:")
        m_name = st.text_input("اسم المتجر")
        m_category = st.selectbox("القسم الرئيسي:", ["مطاعم", "حلويات", "ماركت", "محامص ومكسرات", "خضروات وفواكه", "لحوم", "صيدليات ومستلزمات طبيه"])
        m_phone = st.text_input("رقم هاتف المتجر")
        m_location = st.text_input("عنوان المتجر / المنطقة")
        m_status = st.selectbox("حالة المتجر", ["معتمد", "قيد المراجعة"])
        m_image = st.file_uploader("تنزيل صورة المتجر", type=["jpg", "png", "jpeg"])
        
        submit_merchant = st.form_submit_button("إضافة المتجر للنظام")
        if submit_merchant and m_name:
            image_base64 = ""
            if m_image is not None:
                bytes_data = m_image.getvalue()
                image_base64 = f"data:image/jpeg;base64,{base64.b64encode(bytes_data).decode('utf-8')}"
            try:
                cursor.execute("INSERT INTO merchants (name, category, phone, location, status, image_data) VALUES (?, ?, ?, ?, ?, ?)", (m_name, m_category, m_phone, m_location, m_status, image_base64))
                conn.commit()
                st.success(f"تم إضافة المتجر ({m_name}) بنجاح!")
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ أثناء إضافة المتجر: {e}")

    st.markdown("---")
    st.subheader("📋 تعديل أو حذف المتاجر المسجلة")
    cursor.execute("SELECT id, name, category, phone, location, status FROM merchants")
    merchants_list = cursor.fetchall()
    if merchants_list:
        df_merchants = pd.DataFrame(merchants_list, columns=["المعرف", "اسم المتجر", "القسم", "الهاتف", "الموقع", "الحالة"])
        st.dataframe(df_merchants, use_container_width=True)
        selected_m_name = st.selectbox("اختر متجراً للتعديل أو الحذف:", [m[1] for m in merchants_list])
        if selected_m_name:
            cursor.execute("SELECT name, category, phone, location, status FROM merchants WHERE name = ?", (selected_m_name,))
            m_data = cursor.fetchone()
            with st.form("edit_merchant_form"):
                st.write(f"### تعديل بيانات المتجر: {selected_m_name}")
                edit_name = st.text_input("اسم المتجر الجديد", value=m_data[0])
                edit_cat = st.selectbox("القسم", ["مطاعم", "حلويات", "ماركت", "محامص ومكسرات", "خضروات وفواكه", "لحوم", "صيدليات ومستلزمات طبيه"], index=0)
                edit_phone = st.text_input("الهاتف", value=m_data[2])
                edit_loc = st.text_input("الموقع", value=m_data[3])
                edit_status = st.selectbox("الحالة", ["معتمد", "قيد المراجعة"], index=0 if m_data[4]=="معتمد" else 1)
                if st.form_submit_button("حفظ التعديلات"):
                    cursor.execute("UPDATE merchants SET name=?, category=?, phone=?, location=?, status=? WHERE name=?", (edit_name, edit_cat, edit_phone, edit_loc, edit_status, selected_m_name))
                    conn.commit()
                    st.success("تم تحديث بيانات المتجر بنجاح!")
                    st.rerun()
            if st.button("🗑️ حذف هذا المتجر نهائياً"):
                cursor.execute("DELETE FROM merchants WHERE name = ?", (selected_m_name,))
                cursor.execute("DELETE FROM products WHERE merchant_name = ?", (selected_m_name,))
                conn.commit()
                st.success(f"تم حذف المتجر ({selected_m_name}) بنجاح!")
                st.rerun()

# 3. إدارة الأصناف والقوائم
elif admin_menu == "📋 إدارة الأصناف والقوائم":
    st.subheader("📋 إضافة الأصناف مع الكمية والوحدة والصورة للمتاجر المعتمدة")
    cursor.execute("SELECT name FROM merchants WHERE status='معتمد'")
    active_merchants = [row[0] for row in cursor.fetchall()]
    if not active_merchants:
        st.warning("لا توجد متاجر معتمدة حالياً.")
    else:
        with st.form("add_product_form"):
            selected_merchant = st.selectbox("اختر المتجر:", active_merchants)
            item_name = st.text_input("اسم الصنف أو الوجبة")
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                item_quantity = st.text_input("الكمية", value="1")
            with col_q2:
                item_unit = st.selectbox("الوحدة", ["وجبة", "صحن", "كيلو", "غرام", "حبة", "باكيت", "عبوة", "لتر", "قطعة", "دستة"])
            item_price = st.number_input("السعر بالدينار الأردني", min_value=0.1, value=1.0, step=0.25)
            item_image = st.file_uploader("تنزيل صورة الصنف", type=["jpg", "png", "jpeg"])
            
            if st.form_submit_button("إضافة الصنف للمتجر") and item_name:
                image_base64 = ""
                if item_image is not None:
                    bytes_data = item_image.getvalue()
                    image_base64 = f"data:image/jpeg;base64,{base64.b64encode(bytes_data).decode('utf-8')}"
                cursor.execute("INSERT INTO products (merchant_name, item_name, price, quantity, unit, image_path) VALUES (?, ?, ?, ?, ?, ?)", (selected_merchant, item_name, item_price, item_quantity, item_unit, image_base64))
                conn.commit()
                st.success("تم إضافة الصنف بنجاح!")
                st.rerun()
        
        st.markdown("---")
        cursor.execute("SELECT id, merchant_name, item_name, quantity, unit, price FROM products")
        products_list = cursor.fetchall()
        if products_list:
            st.dataframe(pd.DataFrame(products_list, columns=["المعرف", "المتجر", "اسم الصنف", "الكمية", "الوحدة", "السعر (د.أ)"]), use_container_width=True)

# 4. إدارة السائقين
elif admin_menu == "🛵 إدارة السائقين":
    st.subheader("🛵 إدارة فريق التوصيل والسائقين")
    
    with st.form("driver_form"):
        st.write("### إدخال سائق جديد:")
        d_name = st.text_input("اسم السائق الكامل")
        d_phone = st.text_input("رقم الهاتف المحمول")
        d_vehicle = st.selectbox("نوع المركبة", ["سكوتر / دراجة نارية", "سيارة صغيرة", "باص توصيل"])
        d_status = st.selectbox("حالة السائق", ["متاح للتوصيل", "في مهمة توصيل", "غير متاح"])
        
        if st.form_submit_button("إضافة السائق للنظام") and d_name:
            cursor.execute("INSERT INTO drivers (name, phone, vehicle_type, status) VALUES (?, ?, ?, ?)", (d_name, d_phone, d_vehicle, d_status))
            conn.commit()
            st.success(f"تم إضافة السائق ({d_name}) بنجاح!")
            st.rerun()
            
    st.markdown("---")
    st.subheader("📋 تعديل أو حذف السائقين المسجلين")
    cursor.execute("SELECT id, name, phone, vehicle_type, status FROM drivers")
    drivers_list = cursor.fetchall()
    
    if not drivers_list:
        st.info("لا توجد سائقين مسجلين في النظام حالياً.")
    else:
        df_drivers = pd.DataFrame(drivers_list, columns=["المعرف", "اسم السائق", "رقم الهاتف", "نوع المركبة", "الحالة"])
        st.dataframe(df_drivers, use_container_width=True)
        
        st.write("---")
        st.write("### ⚙️ لوحة التعديل والحذف الفوري للسائقين:")
        
        driver_options = {f"معرف رقم ({d[0]}): {d[1]}": d[0] for d in drivers_list}
        selected_driver_label = st.selectbox("اختر السائق المراد تعديل بياناته أو حذفه:", list(driver_options.keys()))
        
        if selected_driver_label:
            selected_d_id = driver_options[selected_driver_label]
            cursor.execute("SELECT id, name, phone, vehicle_type, status FROM drivers WHERE id = ?", (selected_d_id,))
            d_data = cursor.fetchone()
            
            if d_data:
                with st.form("edit_driver_form_direct"):
                    st.write(f"#### تعديل بيانات السائق: {d_data[1]}")
                    ed_name = st.text_input("اسم السائق الجديد", value=d_data[1])
                    ed_phone = st.text_input("رقم الهاتف الجديد", value=d_data[2])
                    
                    vehicles_list = ["سكوتر / دراجة نارية", "سيارة صغيرة", "باص توصيل", "سيارة خاصة"]
                    curr_veh = d_data[3] if d_data[3] in vehicles_list else "سكوتر / دراجة نارية"
                    ed_vehicle = st.selectbox("نوع المركبة", vehicles_list, index=vehicles_list.index(curr_veh))
                    
                    statuses_list = ["متاح للتوصيل", "في مهمة توصيل", "غير متاح", "متاح"]
                    curr_stat = d_data[4] if d_data[4] in statuses_list else "متاح للتوصيل"
                    ed_status = st.selectbox("حالة السائق", statuses_list, index=statuses_list.index(curr_stat) if curr_stat in statuses_list else 0)
                    
                    update_driver_btn = st.form_submit_button("💾 حفظ تعديلات السائق")
                    if update_driver_btn:
                        cursor.execute("UPDATE drivers SET name = ?, phone = ?, vehicle_type = ?, status = ? WHERE id = ?", (ed_name, ed_phone, ed_vehicle, ed_status, selected_d_id))
                        conn.commit()
                        st.success("تم تحديث بيانات السائق بنجاح!")
                        st.rerun()
                
                st.write("")
                if st.button("🗑 حذف هذا السائق نهائياً من النظام", key=f"del_drv_{selected_d_id}"):
                    cursor.execute("DELETE FROM drivers WHERE id = ?", (selected_d_id,))
                    conn.commit()
                    st.success("تم حذف السائق بنجاح!")
                    st.rerun()

# 5. إدارة العروض
elif admin_menu == "🏷️ إدارة العروض":
    st.subheader("🏷 إضافة عروض التخفيضات والخصومات")
    with st.form("offer_form"):
        offer_title = st.text_input("عنوان العرض")
        offer_desc = st.text_area("تفاصيل الخصم أو العرض")
        valid_date = st.text_input("صالح لغاية تاريخ", "2026-10-31")
        if st.form_submit_button("نشر العرض في النظام") and offer_title:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='offers'")
            if not cursor.fetchone():
                cursor.execute("CREATE TABLE offers (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, discount_details TEXT, valid_until TEXT)")
            cursor.execute("INSERT INTO offers (title, discount_details, valid_until) VALUES (?, ?, ?)", (offer_title, offer_desc, valid_date))
            conn.commit()
            st.success("تم نشر العرض بنجاح!")
            st.rerun()

# 6. التقرير المالي
elif admin_menu == "📊 التقرير المالي":
    st.subheader("📊 التقارير المالية والإحصائيات الشاملة")
    try:
        cursor.execute("SELECT COUNT(*), SUM(total_amount) FROM orders")
        order_stats = cursor.fetchone()
        total_orders_count = order_stats[0] if order_stats and order_stats[0] else 0
        total_revenue = order_stats[1] if order_stats and order_stats[1] else 0.0
    except:
        total_orders_count, total_revenue = 0, 0.0
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="📦 إجمالي عدد الطلبات", value=total_orders_count)
    with col_m2:
        st.metric(label="💰 إجمالي المبيعات (دينار أردني)", value=f"{total_revenue:.2f} د.أ")

# 7. سجل الزبائن
elif admin_menu == "👥 سجل الزبائن المسجلين":
    st.subheader("👥 بيانات الزبائن المسجلين في التطبيق")
    try:
        cursor.execute("SELECT id, name, phone, address FROM customers")
        customers_list = cursor.fetchall()
    except:
        customers_list = []
    if customers_list:
        st.dataframe(pd.DataFrame(customers_list, columns=["المعرف", "اسم الزبون", "رقم الهاتف", "العنوان والموقع"]), use_container_width=True)
    else:
        st.info("لم يتم تسجيل أي زبون حتى الآن.")

conn.close()