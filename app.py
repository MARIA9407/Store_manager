from flask import Flask, request, redirect, render_template_string, make_response
import json, os
from datetime import datetime, timedelta
from itsdangerous import URLSafeSerializer, BadSignature

app = Flask(__name__)
# مفتاح سري لتوقيع تاريخ بداية التجربة
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "store-manager-demo-secret-2026")
TRIAL_DAYS = 1
TRIAL_COOKIE = "store_manager_trial"
TRIAL_SIGNER = URLSafeSerializer(app.config["SECRET_KEY"], salt="store-manager-trial")

DATA_FILE = "store_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"products": [], "sales": [], "invoice_number": 1}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        d.setdefault("products", [])
        d.setdefault("sales", [])
        d.setdefault("invoice_number", 1)
        return d
    except:
        return {"products": [], "sales": [], "invoice_number": 1}

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def get_trial_start():
    """إرجاع وقت أول فتح للرابط من الكوكي الموقعة."""
    raw = request.cookies.get(TRIAL_COOKIE)
    if not raw:
        return None
    try:
        value = TRIAL_SIGNER.loads(raw)
        return datetime.fromisoformat(value)
    except (BadSignature, ValueError, TypeError):
        return None

def trial_status():
    start = get_trial_start()
    if start is None:
        # لم يبدأ العميل التجربة بعد؛ ستبدأ بعد إرسال أول استجابة له.
        return True, TRIAL_DAYS
    end = start + timedelta(days=TRIAL_DAYS)
    remaining = end - datetime.now()
    seconds = int(remaining.total_seconds())
    if seconds <= 0:
        return False, 0
    days = (seconds + 86399) // 86400
    return True, days

@app.after_request
def set_trial_cookie(response):
    # أول فتح للرابط يبدأ التجربة. لا نضع انتهاءً للكوكي حتى لا تُعاد التجربة
    # تلقائيًا بعد إغلاق المتصفح.
    if request.cookies.get(TRIAL_COOKIE) is None:
        signed_start = TRIAL_SIGNER.dumps(datetime.now().isoformat())
        response.set_cookie(
            TRIAL_COOKIE,
            signed_start,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            samesite="Lax",
            secure=request.is_secure
        )
    return response

@app.before_request
def enforce_trial():
    # نسمح بطلب الصفحة الأولى ليبدأ منها العداد، ثم نمنع التطبيق بعد 3 أيام.
    active, _ = trial_status()
    if not active:
        return trial_expired_response()

def trial_expired_response():
    body = """<div class="header"><h1>🛍️ Store Manager</h1><p>نسخة تجريبية</p></div>
    <div class="container"><div class="card" style="text-align:center">
    <h2>⏰ انتهت النسخة التجريبية</h2>
    <p style="font-size:19px;line-height:1.8">
    انتهت مدة التجربة المجانية لمدة 3 أيام.
    </p>
    <p style="font-size:19px;line-height:1.8">
    للحصول على النسخة الكاملة، تواصلي مع صاحبة التطبيق.
    </p>
    <div class="warning" style="font-size:18px">
    🔓 النسخة الكاملة تتضمن استعمال التطبيق دون انتهاء التجربة.
    </div>
    </div></div>"""
    return page("انتهت التجربة", body)

STYLE = """
*{box-sizing:border-box} body{margin:0;font-family:Arial,sans-serif;background:#f4f6f8;color:#222}
.header{background:#1f2937;color:#fff;padding:25px 15px;text-align:center}.header h1{margin:0;font-size:30px}
.container{width:94%;max-width:700px;margin:20px auto}.card,.invoice{background:#fff;border-radius:18px;padding:20px;margin-bottom:18px;box-shadow:0 4px 12px #0001}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.btn{display:block;text-decoration:none;border:0;border-radius:14px;padding:16px 8px;margin-top:10px;background:#2563eb;color:#fff;text-align:center;font-size:18px;font-weight:bold;cursor:pointer}
.green{background:#16a34a}.red{background:#dc2626}.orange{background:#ea580c}.gray{background:#4b5563}
input,select{width:100%;padding:14px;margin:8px 0 15px;border:1px solid #d1d5db;border-radius:12px;font-size:17px;background:#fff}
label{display:block;font-size:17px;font-weight:bold;margin-top:8px}.product{border:1px solid #ddd;border-radius:15px;padding:16px;margin-top:13px}
.product-name{font-size:23px;font-weight:bold;margin-bottom:8px}.info{font-size:17px;margin-top:8px}.actions{display:flex;gap:8px}.actions a{flex:1}
.stat{text-align:center;padding:20px;border-radius:15px;background:#eef2ff;margin-bottom:12px}.stat-number{font-size:27px;font-weight:bold}
.empty{text-align:center;padding:25px;color:#777;font-size:18px}.warning{background:#fff7ed;border:1px solid #fed7aa;padding:15px;border-radius:13px;margin-top:10px}
.back{display:block;text-align:center;margin:20px;color:#2563eb;text-decoration:none;font-size:18px}
.invoice-title{text-align:center;font-size:28px;font-weight:bold;margin-bottom:20px}.invoice-line{border-bottom:1px dashed #aaa;padding:12px 0;font-size:18px}
.invoice-total{font-size:24px;font-weight:bold;text-align:center;margin-top:20px}.print-btn{background:#111827;color:#fff;border:0;border-radius:14px;padding:16px;width:100%;font-size:18px;margin-top:20px}
@media print{body{background:#fff}.no-print{display:none!important}.invoice{box-shadow:none}}
"""

PAGE = """<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{{ title }}</title><style>{{ style|safe }}</style></head><body>{{ body|safe }}</body></html>"""

def page(title, body, **ctx):
    return render_template_string(PAGE, title=title, style=STYLE, body=render_template_string(body, **ctx))

@app.route("/")
def home():
    d=load_data()
    stock=sum(sum(p["colors"].values()) for p in d["products"])
    revenue=sum(s.get("total",0) for s in d["sales"])
    body="""<div class="header"><h1>🛍️ إدارة المتجر</h1><p>نظام إدارة المنتجات والمبيعات</p></div>
    <div class="container"><div class="card" style="text-align:center;background:#fff7ed;border:1px solid #fed7aa">
    <strong>🎁 نسخة تجريبية لمدة 3 أيام</strong><br>
    {% if trial_days == 1 %}متبقي أقل من يوم{% else %}متبقي {{ trial_days }} أيام{% endif %}
    </div></div>
    <div class="container"><div class="card"><h2>لوحة التحكم</h2><div class="grid">
    <a class="btn" href="/products">📦<br>المنتجات</a><a class="btn green" href="/sales">🛒<br>المبيعات</a>
    <a class="btn" href="/statistics">📊<br>الإحصائيات</a><a class="btn" href="/search">🔎<br>البحث</a>
    <a class="btn red" href="/low-stock">⚠️<br>المخزون المنخفض</a><a class="btn gray" href="/add-product">➕<br>إضافة منتج</a>
    </div></div><div class="card"><h2>📊 ملخص المتجر</h2>
    <div class="stat"><div class="stat-number">{{ pc }}</div>عدد المنتجات</div>
    <div class="stat"><div class="stat-number">{{ stock }}</div>إجمالي القطع في المخزون</div>
    <div class="stat"><div class="stat-number">{{ "%.0f"|format(revenue) }} DA</div>إجمالي المبيعات</div>
    </div></div>"""
    active, trial_days = trial_status()
    return page("إدارة المتجر",body,pc=len(d["products"]),stock=stock,revenue=revenue,trial_days=trial_days)

@app.route("/products")
def products():
    d=load_data()
    body="""<div class="header"><h1>📦 المنتجات</h1></div><div class="container"><div class="card">
    <a class="btn green" href="/add-product">➕ إضافة منتج جديد</a>
    {% if products %}{% for p in products %}<div class="product"><div class="product-name">{{ p.name }}</div>
    <div class="info">💰 السعر: {{ "%.0f"|format(p.price) }} DA</div><div class="info">📦 المخزون:</div>
    {% for c,q in p.colors.items() %}<div class="info">• {{ c }} : {{ q }} قطعة</div>{% endfor %}
    <div class="actions"><a class="btn orange" href="/edit-product/{{ loop.index0 }}">✏️ تعديل</a>
    <a class="btn red" href="/delete-product/{{ loop.index0 }}" onclick="return confirm('هل أنت متأكد من حذف هذا المنتج؟')">🗑️ حذف</a></div></div>{% endfor %}
    {% else %}<div class="empty">لا توجد منتجات حتى الآن.</div>{% endif %}</div></div><a class="back" href="/">← العودة للرئيسية</a>"""
    return page("المنتجات",body,products=d["products"])

@app.route("/add-product",methods=["GET","POST"])
def add_product():
    if request.method=="POST":
        d=load_data()
        name=request.form.get("name","").strip()
        colors=[x.strip() for x in request.form.get("colors","").split(",") if x.strip()]
        qs=[x.strip() for x in request.form.get("quantities","").split(",")]
        try: price=float(request.form.get("price","").replace("DA","").replace("da","").strip())
        except: price=0
        stock={}
        for i,c in enumerate(colors):
            try:q=int(qs[i])
            except:q=0
            stock[c]=q
        if name and colors and price>0:
            d["products"].append({"name":name,"colors":stock,"price":price});save_data(d)
        return redirect("/products")
    body="""<div class="header"><h1>➕ إضافة منتج</h1></div><div class="container"><div class="card"><form method="POST">
    <label>اسم المنتج</label><input name="name" value="Sac" placeholder="مثال: Sac" required>
    <label>الألوان</label><input name="colors" value="Beige, Noir" placeholder="Beige, Noir" required>
    <label>السعر بالدينار</label><input type="number" name="price" value="2500" placeholder="2500" required>
    <label>الكميات حسب ترتيب الألوان</label><input name="quantities" value="10, 10" placeholder="10, 10" required>
    <button class="btn green" type="submit">✅ حفظ المنتج</button></form></div></div><a class="back" href="/products">← العودة للمنتجات</a>"""
    return page("إضافة منتج",body)

@app.route("/edit-product/<int:i>",methods=["GET","POST"])
def edit_product(i):
    d=load_data()
    if not 0<=i<len(d["products"]): return redirect("/products")
    p=d["products"][i]
    if request.method=="POST":
        p["name"]=request.form.get("name","").strip()
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
    <label>الألوان</label><input name="colors" value="{{ p.colors.keys()|join(', ') }}" required>
    <label>السعر</label><input type="number" name="price" value="{{ p.price }}" required>
    <label>الكميات</label><input name="quantities" value="{{ p.colors.values()|join(', ') }}" required>
    <button class="btn green">💾 حفظ التعديلات</button></form></div></div><a class="back" href="/products">← العودة</a>"""
    return page("تعديل المنتج",body,p=p)

@app.route("/delete-product/<int:i>")
def delete_product(i):
    d=load_data()
    if 0<=i<len(d["products"]): del d["products"][i];save_data(d)
    return redirect("/products")

@app.route("/sales",methods=["GET","POST"])
def sales():
    d=load_data()
    if request.method=="POST":
        try: pi=int(request.form["product"]); qty=int(request.form["quantity"]); color_input=request.form["color"].strip()
        except:return redirect("/sales")
        if 0<=pi<len(d["products"]) and qty>0:
                p = d["products"][pi]
    color_input_clean = color_input.strip().lower()
    color = next(
        (c for c in p["colors"] if c.strip().lower() == color_input_clean), None
    )
    if color is not None and qty <= p["colors"][color]:

    
                p["colors"][color]-=qty; inv=d["invoice_number"]; total=qty*p["price"]; now=datetime.now()
                d["sales"].append({"invoice":inv,"product":p["name"],"color":color,"quantity":qty,"price":p["price"],"total":total,"date":now.strftime("%Y-%m-%d"),"time":now.strftime("%H:%M")})
                d["invoice_number"]+=1;save_data(d);return redirect(f"/invoice/{inv}")
        return redirect("/sales")
    body="""<div class="header"><h1>🛒 المبيعات</h1></div><div class="container"><div class="card"><h2>تسجيل عملية بيع</h2>
    {% if products %}<form method="POST"><label>المنتج</label><select name="product">{% for p in products %}<option value="{{ loop.index0 }}">{{ p.name }}</option>{% endfor %}</select>
    <label>اللون</label><input name="color" placeholder="beige" required><label>الكمية</label><input type="number" name="quantity" min="1" required>
    <button class="btn green">✅ تسجيل البيع وإنشاء الفاتورة</button></form>{% else %}<div class="empty">لا توجد منتجات للبيع.</div>{% endif %}</div>
    <div class="card"><h2>آخر المبيعات</h2>{% for s in sales %}<div class="product"><div class="product-name">🧾 فاتورة #{{ "%05d"|format(s.invoice) }}</div>
    <div class="info">المنتج: {{ s.product }}</div><div class="info">اللون: {{ s.color }}</div><div class="info">الكمية: {{ s.quantity }}</div>
    <div class="info">الإجمالي: {{ "%.0f"|format(s.total) }} DA</div><div class="info">{{ s.date }} — {{ s.time }}</div>
    <a class="btn" href="/invoice/{{ s.invoice }}">🧾 عرض الفاتورة</a></div>{% else %}<div class="empty">لا توجد مبيعات حتى الآن.</div>{% endfor %}</div></div><a class="back" href="/">← العودة</a>"""
    return page("المبيعات",body,products=d["products"],sales=list(reversed(d["sales"]))[:10])

@app.route("/invoice/<int:n>")
def invoice(n):
    d=load_data();s=next((x for x in d["sales"] if x.get("invoice")==n),None)
    if not s:return redirect("/sales")
    body="""<div class="container"><div class="invoice"><div class="invoice-title">🧾 الفاتورة</div>
    <div class="invoice-line">رقم الفاتورة: <strong>{{ "%05d"|format(s.invoice) }}</strong></div>
    <div class="invoice-line">المنتج: <strong>{{ s.product }}</strong></div><div class="invoice-line">اللون: <strong>{{ s.color }}</strong></div>
    <div class="invoice-line">الكمية: <strong>{{ s.quantity }}</strong></div><div class="invoice-line">سعر القطعة: <strong>{{ "%.0f"|format(s.price) }} DA</strong></div>
    <div class="invoice-total">الإجمالي:<br>{{ "%.0f"|format(s.total) }} DA</div><div class="invoice-line">التاريخ: {{ s.date }}<br>الوقت: {{ s.time }}</div>
    <div style="text-align:center;margin-top:25px;font-size:18px">شكراً لزيارتكم ❤️</div>
    <button class="print-btn no-print" onclick="window.print()">🖨️ طباعة / حفظ الفاتورة</button><a class="btn no-print" href="/sales">← العودة للمبيعات</a>
    </div></div>"""
    return page("الفاتورة",body,s=s)

@app.route("/statistics")
def statistics():
    d=load_data();stock=sum(sum(p["colors"].values()) for p in d["products"]);sold=sum(s["quantity"] for s in d["sales"]);rev=sum(s["total"] for s in d["sales"])
    body="""<div class="header"><h1>📊 الإحصائيات</h1></div><div class="container"><div class="card">
    <div class="stat"><div class="stat-number">{{ pc }}</div>عدد المنتجات</div><div class="stat"><div class="stat-number">{{ stock }}</div>القطع الموجودة</div>
    <div class="stat"><div class="stat-number">{{ sold }}</div>القطع المباعة</div><div class="stat"><div class="stat-number">{{ "%.0f"|format(rev) }} DA</div>إجمالي المبيعات</div>
    </div></div><a class="back" href="/">← العودة للرئيسية</a>"""
    return page("الإحصائيات",body,pc=len(d["products"]),stock=stock,sold=sold,rev=rev)

@app.route("/search")
def search():
    q=request.args.get("q","").strip().lower();d=load_data();results=[p for p in d["products"] if q in p["name"].lower()]
    body="""<div class="header"><h1>🔎 البحث</h1></div><div class="container"><div class="card"><form><input name="q" placeholder="اكتب اسم المنتج..." value="{{ q }}"><button class="btn">🔎 بحث</button></form></div>
    <div class="card">{% for p in results %}<div class="product"><div class="product-name">{{ p.name }}</div><div class="info">السعر: {{ "%.0f"|format(p.price) }} DA</div></div>
    {% else %}<div class="empty">{% if q %}لم يتم العثور على المنتج.{% else %}اكتب اسم المنتج للبحث.{% endif %}</div>{% endfor %}</div></div><a class="back" href="/">← العودة</a>"""
    return page("البحث",body,q=q,results=results)

@app.route("/low-stock")
def low_stock():
    d=load_data();low=[(p["name"],c,q) for p in d["products"] for c,q in p["colors"].items() if q<=3]
    body="""<div class="header"><h1>⚠️ المخزون المنخفض</h1></div><div class="container"><div class="card">
    {% for name,color,q in low %}<div class="warning"><strong>{{ name }}</strong><br>اللون: {{ color }}<br>المتبقي: {{ q }} قطعة</div>
    {% else %}<div class="empty">✅ لا توجد منتجات ذات مخزون منخفض.</div>{% endfor %}</div></div><a class="back" href="/">← العودة</a>"""
    return page("المخزون المنخفض",body,low=low)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
