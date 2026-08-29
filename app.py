from flask import Flask, request, redirect, render_template_string
import json, os
from datetime import datetime, timedelta

app = Flask(__name__)
DATA_FILE = "store_data.json"

def get_local_time():
    return datetime.utcnow() + timedelta(hours=1)

def load_data():
    if not os.path.exists(DATA_FILE):
        expiry_date = (get_local_time() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
        return {"products": [], "sales": [], "invoice_number": 1, "created_at": get_local_time().strftime("%Y-%m-%d %H:%M"), "expiry_date": expiry_date}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        d.setdefault("products", [])
        d.setdefault("sales", [])
        d.setdefault("invoice_number", 1)
        if "expiry_date" not in d:
            d["expiry_date"] = (get_local_time() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
        return d
    except:
        expiry_date = (get_local_time() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
        return {"products": [], "sales": [], "invoice_number": 1, "expiry_date": expiry_date}

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

STYLE = """
*{box-sizing:border-box} body{margin:0;font-family:Arial,sans-serif;background:#f4f6f8;color:#222}
.header{background:#1f2937;color:#fff;padding:25px 15px;text-align:center}.header h1{margin:0;font-size:28px}
.container{width:94%;max-width:750px;margin:20px auto}.card,.invoice{background:#fff;border-radius:18px;padding:20px;margin-bottom:18px;box-shadow:0 4px 12px #0001}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.btn{display:block;text-decoration:none;border:0;border-radius:14px;padding:16px 8px;margin-top:10px;background:#2563eb;color:#fff;text-align:center;font-size:17px;font-weight:bold;cursor:pointer}
.green{background:#16a34a}.red{background:#dc2626}.orange{background:#ea580c}.gray{background:#4b5563}.purple{background:#7c3aed}
input,select{width:100%;padding:14px;margin:8px 0 15px;border:1px solid #d1d5db;border-radius:12px;font-size:17px;background:#fff}
label{display:block;font-size:17px;font-weight:bold;margin-top:8px}.product{border:1px solid #ddd;border-radius:15px;padding:16px;margin-top:13px}
.product-name{font-size:21px;font-weight:bold;margin-bottom:8px}.info{font-size:16px;margin-top:6px}.actions{display:flex;gap:8px}.actions a{flex:1}
.stat{text-align:center;padding:15px;border-radius:15px;background:#eef2ff;margin-bottom:12px}.stat-number{font-size:24px;font-weight:bold}
.empty{text-align:center;padding:20px;color:#777;font-size:17px}.warning{background:#fff7ed;border:1px solid #fed7aa;padding:15px;border-radius:13px;margin-top:10px}
.back{display:block;text-align:center;margin:20px;color:#2563eb;text-decoration:none;font-size:18px}
.invoice-title{text-align:center;font-size:26px;font-weight:bold;margin-bottom:20px}.invoice-line{border-bottom:1px dashed #aaa;padding:10px 0;font-size:17px}
.invoice-total{font-size:22px;font-weight:bold;text-align:center;margin-top:20px}.print-btn{background:#111827;color:#fff;border:0;border-radius:14px;padding:16px;width:100%;font-size:18px;margin-top:20px}
.stat-row {display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee; direction: rtl;}

@media print {
  body * { visibility: hidden; }
  #printable-area, #printable-area * { visibility: visible; }
  #printable-area { position: absolute; left: 0; top: 0; width: 100%; }
  .no-print { display: none !important; }
}
"""

PAGE = """<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{{ title }}</title><style>{{ style|safe }}</style></head><body>{{ body|safe }}</body></html>"""

def page(title, body, **ctx):
    return render_template_string(PAGE, title=title, style=STYLE, body=render_template_string(body, **ctx))

def check_trial():
    d = load_data()
    try:
        expiry = datetime.strptime(d["expiry_date"], "%Y-%m-%d %H:%M")
        if get_local_time() > expiry:
            return False
    except:
        pass
    return True

@app.route("/")
def home():
    if not check_trial():
        return page("انتهت الفترة التجريبية", '<div class="header"><h1>⏳ انتهت التجربة المجانية</h1></div><div class="container"><div class="card" style="text-align:center;"><p style="font-size:20px;">عذراً، انتهت مدة التجربة المجانية (3 أيام). يرجى التواصل مع مطور التطبيق لتجديد الاشتراك.</p></div></div>')
    d=load_data()
    stock=sum(sum(p["colors"].values()) for p in d["products"])
    revenue=sum(s.get("total",0) for s in d["sales"])
    profit=sum(s.get("profit",0) for s in d["sales"])
    body="""<div class="header"><h1>🛍️ لوحة تحكم المتجر</h1><p>نظام إدارة المبيعات والأرباح المتقدم</p></div>
    <div class="container">
    <div class="card" style="background:#eef2ff; text-align:center; font-weight:bold; color:#1e40af;">⏳ التجربة المجانية تنتهي في: {{ expiry }}</div>
    <div class="card"><h2>الرئيسية والعمليات</h2><div class="grid">
    <a class="btn" href="/products">📦<br>المنتجات</a><a class="btn green" href="/sales">🛒<br>المبيعات</a>
    <a class="btn purple" href="/statistics">📊<br>التقارير والأرباح</a><a class="btn" href="/search">🔎<br>البحث</a>
    <a class="btn red" href="/low-stock">⚠️<br>المخزون المنخفض</a><a class="btn gray" href="/add-product">➕<br>إضافة منتج</a>
    </div></div><div class="card"><h2>📊 نظرة عامة</h2>
    <div class="stat"><div class="stat-number">{{ pc }}</div>عدد المنتجات</div>
    <div class="stat"><div class="stat-number">{{ stock }}</div>إجمالي القطع في المخزون</div>
    <div class="stat"><div class="stat-number">{{ "%.0f"|format(revenue) }} DA</div>إجمالي المبيعات العامة</div>
    <div class="stat" style="background:#dcfce7; color:#166534;"><div class="stat-number">{{ "%.0f"|format(profit) }} DA</div>إجمالي صافي الأرباح</div>
    </div></div>"""
    return page("إدارة المتجر",body,pc=len(d["products"]),stock=stock,revenue=revenue,profit=profit,expiry=d["expiry_date"])

@app.route("/products")
def products():
    if not check_trial(): return redirect("/")
    d=load_data()
    body="""<div class="header"><h1>📦 إدارة المنتجات</h1></div><div class="container"><div class="card">
    <a class="btn green" href="/add-product">➕ إضافة منتج جديد</a>
    {% if products %}{% for p in products %}<div class="product">
    <div class="product-name">{{ p.name }}</div>
    <div class="info">🏷️ الباركود: <strong>{{ p.barcode if p.barcode else 'بدون باركود' }}</strong></div>
    <div class="info">📥 ثمن الشراء: {{ "%.0f"|format(p.cost_price) }} DA</div>
    <div class="info">💰 سعر البيع: {{ "%.0f"|format(p.price) }} DA</div>
    <div class="info">📦 المخزون حسب الألوان:</div>
    {% for c,q in p.colors.items() %}<div class="info">• {{ c }} : {{ q }} قطعة</div>{% endfor %}
    <div class="actions"><a class="btn orange" href="/edit-product/{{ loop.index0 }}">✏️ تعديل</a>
    <a class="btn red" href="/delete-product/{{ loop.index0 }}" onclick="return confirm('هل أنت متأكد من الحذف؟')">🗑️ حذف</a></div></div>{% endfor %}
    {% else %}<div class="empty">لا توجد منتجات حتى الآن.</div>{% endif %}</div></div><a class="back" href="/">← العودة للرئيسية</a>"""
    return page("المنتجات",body,products=d["products"])

@app.route("/add-product",methods=["GET","POST"])
def add_product():
    if not check_trial(): return redirect("/")
    if request.method=="POST":
        d=load_data()
        name=request.form.get("name","").strip()
        barcode=request.form.get("barcode","").strip()
        colors=[x.strip() for x in request.form.get("colors","").split(",") if x.strip()]
        qs=[x.strip() for x in request.form.get("quantities","").split(",")]
        try: cost_price=float(request.form.get("cost_price","0"))
        except: cost_price=0
        try: price=float(request.form.get("price","0"))
        except: price=0
        stock={}
        for i,c in enumerate(colors):
            try:q=int(qs[i])
            except:q=0
            stock[c]=q
        if name and colors and price>0:
            d["products"].append({"name":name,"barcode":barcode,"cost_price":cost_price,"price":price,"colors":stock})
            save_data(d)
        return redirect("/products")
    body="""<div class="header"><h1>➕ إضافة منتج جديد</h1></div>
    <div class="container"><div class="card">
    <div style="margin-bottom:15px;"><button type="button" class="btn" onclick="startScanner('barcode')">📷 مسح باركود بالكاميرا (اختياري)</button></div>
    <div id="reader" style="width:100%; display:none; margin-bottom:15px;"></div>
    <form method="POST">
    <label>اسم المنتج</label><input name="name" placeholder="مثال: قندورة صيفية" required>
    <label>رمز الباركود (اختياري - اتركه فارغاً إذا لم يوجد)</label><input id="barcode" name="barcode" placeholder="امسح الباركود أو اتركه فارغاً...">
    <label>ثمن الشراء للقطعة (DA)</label><input type="number" name="cost_price" placeholder="1500" required>
    <label>سعر البيع للقطعة (DA)</label><input type="number" name="price" placeholder="2200" required>
    <label>الألوان المتاحة (مفصولة بفاصلة)</label><input name="colors" placeholder="أحمر, أزرق, أسود" required>
    <label>الكميات لكل لون (حسب ترتيب الألوان تماماً)</label><input name="quantities" placeholder="5, 10, 3" required>
    <button class="btn green" type="submit">✅ حفظ المنتج</button></form></div></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    function startScanner(fieldId) {
        var r = document.getElementById('reader');
        r.style.display = 'block';
        function onScanSuccess(decodedText, decodedResult) {
            document.getElementById(fieldId).value = decodedText;
            html5QrcodeScanner.clear();
            r.style.display = 'none';
        }
        var html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess, (err) => {});
    }
    </script>
    <a class="back" href="/products">← العودة للمنتجات</a>"""
    return page("إضافة منتج",body)

@app.route("/edit-product/<int:i>",methods=["GET","POST"])
def edit_product(i):
    if not check_trial(): return redirect("/")
    d=load_data()
    if not 0<=i<len(d["products"]): return redirect("/products")
    p=d["products"][i]
    if request.method=="POST":
        p["name"]=request.form.get("name","").strip()
        p["barcode"]=request.form.get("barcode","").strip()
        try:p["cost_price"]=float(request.form.get("cost_price","0"))
        except:p["cost_price"]=0
        try:p["price"]=float(request.form.get("price","0"))
        except:p["price"]=0
        cs=[x.strip() for x in request.form.get("colors","").split(",") if x.strip()]
        qs=[x.strip() for x in request.form.get("quantities","").split(",")]
        p["colors"]={}
        for j,c in enumerate(cs):
            try:q=int(qs[j])
            except:q=0
            p["colors"][c]=q
        save_data(d);return redirect("/products")
    body="""<div class="header"><h1>✏️ تعديل المنتج</h1></div><div class="container"><div class="card"><form method="POST">
    <label>اسم المنتج</label><input name="name" value="{{ p.name }}" required>
    <label>الباركود</label><input name="barcode" value="{{ p.barcode }}">
    <label>ثمن الشراء</label><input type="number" name="cost_price" value="{{ p.cost_price }}" required>
    <label>سعر البيع</label><input type="number" name="price" value="{{ p.price }}" required>
    <label>الألوان</label><input name="colors" value="{{ p.colors.keys()|join(', ') }}" required>
    <label>الكميات</label><input name="quantities" value="{{ p.colors.values()|join(', ') }}" required>
    <button class="btn green">💾 حفظ التعديلات</button></form></div></div><a class="back" href="/products">← العودة</a>"""
    return page("تعديل المنتج",body,p=p)

@app.route("/delete-product/<int:i>")
def delete_product(i):
    if not check_trial(): return redirect("/")
    d=load_data()
    if 0<=i<len(d["products"]): del d["products"][i];save_data(d)
    return redirect("/products")

@app.route("/sales",methods=["GET","POST"])
def sales():
    if not check_trial(): return redirect("/")
    d=load_data()
    if request.method=="POST":
        barcode_input=request.form.get("barcode","").strip()
        color_input=request.form.get("color","").strip()
        try: qty=int(request.form["quantity"])
        except: qty=0
        
        p = next((prod for prod in d["products"] if (prod.get("barcode","") and prod.get("barcode","").lower() == barcode_input.lower()) or prod.get("name","").lower() == barcode_input.lower()), None)
        
        if p and qty > 0:
            color = next((c for c in p["colors"] if c.lower() == color_input.lower()), None)
            if color is not None and qty <= p["colors"][color]:
                p["colors"][color] -= qty
                inv = d["invoice_number"]
                total = qty * p["price"]
                total_cost = qty * p.get("cost_price", 0)
                profit = total - total_cost
                now = get_local_time()
                d["sales"].append({
                    "invoice": inv,
                    "product": p["name"],
                    "barcode": p.get("barcode",""),
                    "color": color,
                    "quantity": qty,
                    "price": p["price"],
                    "total": total,
                    "profit": profit,
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M")
                })
                d["invoice_number"] += 1
                save_data(d)
                return redirect(f"/invoice/{inv}")
        return redirect("/sales")
        
    body="""<div class="header"><h1>🛒 صفحة المبيعات</h1></div>
    <div class="container"><div class="card"><h2>تسجيل عملية بيع جديدة</h2>
    <div style="margin-bottom:15px;"><button type="button" class="btn" onclick="startScanner('barcode')">📷 مسح باركود بالكاميرا</button></div>
    <div id="reader" style="width:100%; display:none; margin-bottom:15px;"></div>
    <form method="POST">
    <label>رمز الباركود أو اسم المنتج تماماً</label><input id="barcode" name="barcode" placeholder="امسح الكود أو اكتب اسم المنتج..." required>
    <label>اللون المطلوب</label><input name="color" placeholder="مثال: أحمر" required>
    <label>الكمية المباعة</label><input type="number" name="quantity" min="1" value="1" required>
    <button class="btn green">✅ تسجيل البيع وإنشاء الفاتورة</button></form></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    function startScanner(fieldId) {
        var r = document.getElementById('reader');
        r.style.display = 'block';
        function onScanSuccess(decodedText, decodedResult) {
            document.getElementById(fieldId).value = decodedText;
            html5QrcodeScanner.clear();
            r.style.display = 'none';
        }
        var html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess, (err) => {});
    }
    </script>
    <div class="card"><h2>آخر المبيعات المسجلة</h2>{% for s in sales %}<div class="product"><div class="product-name">🧾 فاتورة #{{ "%05d"|format(s.invoice) }}</div>
    <div class="info">المنتج: {{ s.product }}</div><div class="info">اللون: {{ s.color }} | الكمية: {{ s.quantity }}</div>
    <div class="info">الإجمالي: {{ "%.0f"|format(s.total) }} DA</div>
    <div class="info" style="color:#16a34a; font-weight:bold;">الربح الصافي: {{ "%.0f"|format(s.profit) }} DA</div>
    <div class="info">{{ s.date }} — {{ s.time }}</div>
    <a class="btn" href="/invoice/{{ s.invoice }}">🧾 عرض الفاتورة</a></div>{% else %}<div class="empty">لا توجد مبيعات حتى الآن.</div>{% endfor %}</div></div><a class="back" href="/">← العودة</a>"""
    return page("المبيعات",body,sales=list(reversed(d["sales"]))[:10])

@app.route("/invoice/<int:n>")
def invoice(n):
    if not check_trial(): return redirect("/")
    d=load_data();s=next((x for x in d["sales"] if x.get("invoice")==n),None)
    if not s:return redirect("/sales")
    body="""<div class="container"><div id="printable-area" class="invoice"><div class="invoice-title">🧾 الفاتورة التجارية</div>
    <div class="invoice-line">رقم الفاتورة: <strong>{{ "%05d"|format(s.invoice) }}</strong></div>
    <div class="invoice-line">المنتج: <strong>{{ s.product }}</strong></div>
    <div class="invoice-line">اللون: <strong>{{ s.color }}</strong></div>
    <div class="invoice-line">الكمية: <strong>{{ s.quantity }}</strong></div>
    <div class="invoice-line">سعر القطعة: <strong>{{ "%.0f"|format(s.price) }} DA</strong></div>
    <div class="invoice-total">المبلغ الإجمالي:<br>{{ "%.0f"|format(s.total) }} DA</div>
    <div class="invoice-line" style="text-align:center; color:#16a34a; font-weight:bold; margin-top:10px;">صافي ربح هذه العملية: {{ "%.0f"|format(s.profit) }} DA</div>
    <div class="invoice-line">التاريخ: {{ s.date }} — الوقت: {{ s.time }}</div>
    <div style="text-align:center;margin-top:25px;font-size:17px">شكراً لثقتكم بنا ❤️</div>
    </div>
    <button class="print-btn no-print" onclick="window.print()">🖨️ طباعة / حفظ الفاتورة</button><a class="btn no-print" href="/sales">← العودة للمبيعات</a></div>"""
    return page("الفاتورة",body,s=s)

@app.route("/statistics")
def statistics():
    if not check_trial(): return redirect("/")
    d = load_data()
    
    now_dt = get_local_time()
    today_str = now_dt.strftime("%Y-%m-%d")
    
    day_sales = [s for s in d["sales"] if s.get("date") == today_str]
    week_ago = now_dt - timedelta(days=7)
    month_ago = now_dt - timedelta(days=30)
    
    week_sales = []
    month_sales = []
    
    for s in d["sales"]:
        try:
            s_dt = datetime.strptime(s.get("date", ""), "%Y-%m-%d")
            if s_dt >= week_ago:
                week_sales.append(s)
            if s_dt >= month_ago:
                month_sales.append(s)
        except:
            pass

    d_rev = sum(s.get("total", 0) for s in day_sales)
    d_prof = sum(s.get("profit", 0) for s in day_sales)
    w_rev = sum(s.get("total", 0) for s in week_sales)
    w_prof = sum(s.get("profit", 0) for s in week_sales)
    m_rev = sum(s.get("total", 0) for s in month_sales)
    m_prof = sum(s.get("profit", 0) for s in month_sales)

    # حصر جميع المنتجات الموجودة في المتجر وإعطاؤها قيمة مبيعات ابتدائية 0
    product_stats = {p["name"]: 0 for p in d["products"]}
    for s in d["sales"]:
        p_name = s.get("product", "غير معروف")
        qty = s.get("quantity", 0)
        if p_name in product_stats:
            product_stats[p_name] += qty
        else:
            product_stats[p_name] = qty
        
    # ترتيب المنتجات تنازلياً حسب الأكثر مبيعاً
    sorted_products = sorted(product_stats.items(), key=lambda x: x[1], reverse=True)
    
    # 1. أكثر المنتجات مبيعاً: المنتجات التي حققت مبيعات أكبر من 0 وتتصدر القائمة
    top_products = [item for item in sorted_products if item[1] > 0]
    
    # أسماء المنتجات في قائمة الأكثر مبيعاً لمنع تكرارها نهائياً في الراكدة
    top_names = {item[0] for item in top_products}
    
    # 2. المنتجات الراكدة: المنتجات التي لم يُبَع منها أي شيء (0) تماماً وغير موجودة في قائمة الأكثر مبيعاً
    low_products = [item for item in sorted_products if item[1] == 0 and item[0] not in top_names]

    body="""<div class="header"><h1>📊 التقارير والإحصائيات الشاملة</h1></div>
    <div class="container">
    
    <div class="card">
        <h2>📅 مبيعات اليوم</h2>
        <div class="stat"><div class="stat-number">{{ "%.0f"|format(d_rev) }} DA</div>إيرادات اليوم</div>
        <div class="stat" style="background:#dcfce7; color:#166534;"><div class="stat-number">{{ "%.0f"|format(d_prof) }} DA</div>صافي ربح اليوم</div>
    </div>

    <div class="card">
        <h2>📈 مبيعات الأسبوع والشهر</h2>
        <div class="grid">
            <div class="stat" style="background:#f0fdf4;">
                <div style="font-size:14px; font-weight:bold; color:#166534;">آخر 7 أيام</div>
                <div class="stat-number" style="font-size:20px;">{{ "%.0f"|format(w_rev) }} DA</div>
                <div style="font-size:13px; color:#15803d; margin-top:5px;">الربح: {{ "%.0f"|format(w_prof) }} DA</div>
            </div>
            <div class="stat" style="background:#eff6ff;">
                <div style="font-size:14px; font-weight:bold; color:#1e40af;">آخر 30 يوم</div>
                <div class="stat-number" style="font-size:20px;">{{ "%.0f"|format(m_rev) }} DA</div>
                <div style="font-size:13px; color:#1d4ed8; margin-top:5px;">الربح: {{ "%.0f"|format(m_prof) }} DA</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>🔥 أكثر المنتجات مبيعاً</h2>
        {% if top_products %}
            {% for name, q in top_products %}
                <div class="stat-row">
                    <span>📦 <strong>{{ name }}</strong></span>
                    <span style="color:#2563eb; font-weight:bold;">{{ q }} قطعة مباعة</span>
                </div>
            {% endfor %}
        {% else %}
            <div class="empty">لا توجد مبيعات مسجلة حتى الآن.</div>
        {% endif %}
    </div>

    <div class="card">
        <h2>❄️ أقل المنتجات مبيعاً (الراكدة)</h2>
        {% if low_products %}
            {% for name, q in low_products %}
                <div class="stat-row">
                    <span>📦 <strong>{{ name }}</strong></span>
                    <span style="color:#dc2626; font-weight:bold;">{{ q }} قطعة مباعة</span>
                </div>
            {% endfor %}
        {% else %}
            <div class="empty">لا توجد منتجات راكدة (جميع المنتجات تم بيعها).</div>
        {% endif %}
    </div>

    </div><a class="back" href="/">← العودة للرئيسية</a>"""
    
    return page("الإحصائيات والأرباح", body, d_rev=d_rev, d_prof=d_prof, w_rev=w_rev, w_prof=w_prof, m_rev=m_rev, m_prof=m_prof, top_products=top_products, low_products=low_products)

@app.route("/search")
def search():
    if not check_trial(): return redirect("/")
    q=request.args.get("q","").strip().lower();d=load_data();results=[p for p in d["products"] if q in p["name"].lower() or q in p.get("barcode","").lower()]
    body="""<div class="header"><h1>🔎 البحث عن منتج</h1></div><div class="container"><div class="card"><form><input name="q" placeholder="اكتب اسم أو باركود المنتج..." value="{{ q }}"><button class="btn">🔎 بحث</button></form></div>
    <div class="card">{% for p in results %}<div class="product"><div class="product-name">{{ p.name }}</div><div class="info">الباركود: {{ p.barcode if p.barcode else 'بدون باركود' }}</div><div class="info">السعر: {{ "%.0f"|format(p.price) }} DA</div></div>
    {% else %}<div class="empty">{% if q %}لم يتم العثور على المنتج.{% else %}اكتب اسم أو باركود المنتج للبحث.{% endif %}</div>{% endfor %}</div></div><a class="back" href="/">← العودة</a>"""
    return page("البحث",body,q=q,results=results)

@app.route("/low-stock")
def low_stock():
    if not check_trial(): return redirect("/")
    d=load_data();low=[(p["name"],p.get("barcode",""),c,q) for p in d["products"] for c,q in p["colors"].items() if q<=3]
    body="""<div class="header"><h1>⚠️ المخزون المنخفض</h1></div><div class="container"><div class="card">
    {% for name,barcode,color,q in low %}<div class="warning"><strong>{{ name }}</strong> (باركود: {{ barcode if barcode else 'بدون باركود' }})<br>اللون: {{ color }}<br>المتبقي في المخزون: {{ q }} قطعة فقط</div>
    {% else %}<div class="empty">✅ ممتاز! لا توجد منتجات ذات مخزون منخفض حالياً.</div>{% endfor %}</div></div><a class="back" href="/">← العودة</a>"""
    return page("المخزون المنخفض",body,low=low)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
