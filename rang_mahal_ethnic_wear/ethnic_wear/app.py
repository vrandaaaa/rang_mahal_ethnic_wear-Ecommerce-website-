"""
Rang Mahal — Women's Ethnic Wear E-Commerce
Flask + SQLite (pure sqlite3, no ORM needed)
Run:  python app.py   then open  http://localhost:5000
Admin login:  admin@ethnicwear.com / admin123
"""

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, g)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os, json, uuid, sqlite3

# ─── App ─────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY']     = 'rang-mahal-secret-key-2024'
app.config['DATABASE']       = os.path.join(os.path.dirname(__file__), 'instance', 'rang_mahal.db')
app.config['UPLOAD_FOLDER']  = os.path.join('static', 'images', 'uploads')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ─── Jinja filter ─────────────────────────────────────────────────────────────
@app.template_filter('from_json')
def from_json_f(v):
    try: return json.loads(v) if v else []
    except: return []

@app.template_filter('fmtdate')
def fmtdate_f(v):
    """Format sqlite datetime string for display"""
    if not v: return ''
    try:
        from datetime import datetime
        dt = datetime.strptime(str(v)[:19], '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%d %b %Y')
    except:
        return str(v)[:10]

# ─── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def q(sql, args=(), one=False, commit=False):
    db = get_db()
    cur = db.execute(sql, args)
    if commit:
        db.commit()
        return cur.lastrowid
    return (cur.fetchone() if one else cur.fetchall())

def dictrow(row):  return dict(row) if row else None
def dictrows(rows): return [dict(r) for r in rows] if rows else []

# ─── Product helpers ──────────────────────────────────────────────────────────
def enrich(p):
    if not p: return None
    p = dict(p)
    p['images_list'] = _jlist(p.get('images'))
    p['sizes_list']  = _jlist(p.get('sizes'))
    p['colors_list'] = _jlist(p.get('colors'))
    row = q("SELECT AVG(rating) as a, COUNT(*) as c FROM reviews WHERE product_id=?", (p['id'],), one=True)
    p['avg_rating']   = round(row['a'] or 0, 1)
    p['review_count'] = row['c'] or 0
    return p

def _jlist(v):
    try: return json.loads(v) if v else []
    except: return []

# ─── Auth decorators ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*a, **kw)
    return wrapped

def admin_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        if not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*a, **kw)
    return wrapped

def allowed(fn):
    return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_EXT

# ─── Context processor ────────────────────────────────────────────────────────
@app.context_processor
def globals():
    cart  = session.get('cart', {})
    cc    = sum(i['quantity'] for i in cart.values())
    wc    = 0
    if 'user_id' in session:
        row = q("SELECT COUNT(*) c FROM wishlist WHERE user_id=?", (session['user_id'],), one=True)
        wc  = row['c'] if row else 0
    return dict(cart_count=cc, wishlist_count=wc)

# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def home():
    featured     = [enrich(p) for p in dictrows(q("SELECT * FROM products WHERE is_featured=1 AND is_active=1 ORDER BY created_at DESC LIMIT 8"))]
    new_arrivals = [enrich(p) for p in dictrows(q("SELECT * FROM products WHERE is_active=1 ORDER BY created_at DESC LIMIT 8"))]
    categories   = ['Kurti','Suit','Sharara','Lehenga','Saree','Anarkali']
    return render_template('home.html', featured=featured, new_arrivals=new_arrivals, categories=categories)

@app.route('/products')
def products():
    page     = request.args.get('page', 1, type=int)
    per_page = 12
    category = request.args.get('category','')
    search   = request.args.get('search','')
    min_p    = request.args.get('min_price', 0, type=float)
    max_p    = request.args.get('max_price', 999999, type=float)
    size_f   = request.args.get('size','')
    color_f  = request.args.get('color','')
    sort     = request.args.get('sort','newest')

    where, args = ["is_active=1"], []
    if category: where.append("category=?");         args.append(category)
    if search:   where.append("(name LIKE ? OR description LIKE ?)"); args += [f'%{search}%']*2
    if min_p:    where.append("price>=?");           args.append(min_p)
    if max_p < 999999: where.append("price<=?");    args.append(max_p)
    if size_f:   where.append("sizes LIKE ?");       args.append(f'%{size_f}%')
    if color_f:  where.append("colors LIKE ?");      args.append(f'%{color_f}%')

    order_map = {"newest":"created_at DESC","price_asc":"price ASC","price_desc":"price DESC"}
    order_sql = order_map.get(sort, "created_at DESC")
    base      = f"FROM products WHERE {' AND '.join(where)}"
    total     = q(f"SELECT COUNT(*) c {base}", args, one=True)['c']
    offset    = (page-1)*per_page
    rows      = [enrich(p) for p in dictrows(q(f"SELECT * {base} ORDER BY {order_sql} LIMIT ? OFFSET ?", args+[per_page,offset]))]

    pages = max(1, (total+per_page-1)//per_page)
    pag   = dict(product_list=rows, total=total, page=page, pages=pages,
                 has_prev=page>1, has_next=page<pages,
                 prev_num=page-1, next_num=page+1,
                 iter_pages=lambda: range(1, pages+1))

    cats   = ['Kurti','Suit','Sharara','Lehenga','Saree','Anarkali']
    sizes  = ['XS','S','M','L','XL','XXL','Free Size']
    colors = ['Red','Pink','Blue','Green','Yellow','Orange','Purple','White','Black','Gold','Maroon','Teal']
    return render_template('products.html', products=pag,
        categories=cats, sizes=sizes, colors=colors,
        selected_category=category, search=search,
        min_price=min_p, max_price=max_p,
        selected_size=size_f, selected_color=color_f, sort=sort)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = enrich(q("SELECT * FROM products WHERE id=?", (product_id,), one=True))
    if not product: return redirect(url_for('products'))
    reviews = dictrows(q(
        "SELECT r.*, u.name user_name FROM reviews r JOIN users u ON r.user_id=u.id WHERE r.product_id=? ORDER BY r.created_at DESC",
        (product_id,)))
    related = [enrich(p) for p in dictrows(q(
        "SELECT * FROM products WHERE category=? AND id!=? AND is_active=1 LIMIT 4",
        (product['category'], product_id)))]
    in_wishlist = False
    if 'user_id' in session:
        in_wishlist = bool(q("SELECT id FROM wishlist WHERE user_id=? AND product_id=?",
                             (session['user_id'], product_id), one=True))
    return render_template('product_detail.html', product=product,
                           reviews=reviews, related=related, in_wishlist=in_wishlist)

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.route('/signup', methods=['GET','POST'])
def signup():
    if 'user_id' in session: return redirect(url_for('home'))
    if request.method == 'POST':
        name, email = request.form.get('name','').strip(), request.form.get('email','').strip().lower()
        pwd, cpwd   = request.form.get('password',''), request.form.get('confirm_password','')
        if not all([name,email,pwd]):   flash('All fields required.','danger'); return render_template('signup.html')
        if pwd != cpwd:                 flash('Passwords do not match.','danger'); return render_template('signup.html')
        if len(pwd) < 6:               flash('Password min 6 characters.','danger'); return render_template('signup.html')
        if q("SELECT id FROM users WHERE email=?", (email,), one=True):
            flash('Email already registered.','warning'); return redirect(url_for('login'))
        q("INSERT INTO users (name,email,password) VALUES (?,?,?)",
          (name, email, generate_password_hash(pwd)), commit=True)
        flash(f'Welcome {name}! Please login.','success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session: return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        pwd   = request.form.get('password','')
        user  = q("SELECT * FROM users WHERE email=?", (email,), one=True)
        if user and check_password_hash(user['password'], pwd):
            session.update({'user_id':user['id'], 'user_name':user['name'], 'is_admin':bool(user['is_admin'])})
            flash(f'Welcome back, {user["name"]}! 🌸','success')
            return redirect(request.args.get('next') or url_for('home'))
        flash('Invalid email or password.','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); flash('Logged out.','info'); return redirect(url_for('home'))

# ── Cart ──────────────────────────────────────────────────────────────────────
@app.route('/cart')
def cart():
    cart_data = session.get('cart',{})
    items, total = [], 0
    for key, item in cart_data.items():
        p = enrich(q("SELECT * FROM products WHERE id=?", (item['product_id'],), one=True))
        if p:
            sub = p['price']*item['quantity']
            items.append({'key':key,'product':p,'size':item.get('size',''),
                          'color':item.get('color',''),'quantity':item['quantity'],'subtotal':sub})
            total += sub
    return render_template('cart.html', items=items, total=total)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    qty = request.form.get('quantity', 1, type=int)
    size, color = request.form.get('size',''), request.form.get('color','')
    p = q("SELECT * FROM products WHERE id=?", (product_id,), one=True)
    if not p: flash('Product not found.','danger'); return redirect(url_for('products'))
    if p['stock'] < qty:
        flash('Not enough stock.','warning'); return redirect(request.referrer or url_for('products'))
    cart = session.get('cart',{})
    key  = f"{product_id}_{size}_{color}"
    if key in cart: cart[key]['quantity'] += qty
    else: cart[key] = {'product_id':product_id,'quantity':qty,'size':size,'color':color}
    session['cart'] = cart; session.modified = True
    flash(f'"{p["name"]}" added to cart! 🛍️','success')
    return redirect(request.referrer or url_for('cart'))

@app.route('/cart/update', methods=['POST'])
def update_cart():
    key = request.form.get('key')
    qty = request.form.get('quantity', type=int)
    cart = session.get('cart',{})
    if key in cart:
        if qty is not None and qty <= 0: del cart[key]; flash('Item removed.','info')
        elif qty: cart[key]['quantity'] = qty
    session['cart'] = cart; session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart/remove/<key>')
def remove_from_cart(key):
    cart = session.get('cart',{})
    if key in cart:
        del cart[key]; session['cart']=cart; session.modified=True
        flash('Item removed.','info')
    return redirect(url_for('cart'))

# ── Checkout ──────────────────────────────────────────────────────────────────
@app.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    cart_data = session.get('cart',{})
    if not cart_data: flash('Cart is empty.','warning'); return redirect(url_for('cart'))
    items, total = [], 0
    for key, item in cart_data.items():
        p = enrich(q("SELECT * FROM products WHERE id=?", (item['product_id'],), one=True))
        if p:
            sub = p['price']*item['quantity']
            items.append({'product':p,'size':item.get('size',''),'color':item.get('color',''),'quantity':item['quantity'],'subtotal':sub})
            total += sub
    user = dictrow(q("SELECT * FROM users WHERE id=?", (session['user_id'],), one=True))
    if request.method == 'POST':
        if request.form.get('simulate','success') == 'failure':
            flash('Payment failed. Please try again.','danger')
            return render_template('checkout.html', items=items, total=total, user=user)
        order_items = [{'product_id':i['product']['id'],'name':i['product']['name'],
                        'price':i['product']['price'],'quantity':i['quantity'],
                        'size':i['size'],'color':i['color']} for i in items]
        onum = f"EW{uuid.uuid4().hex[:8].upper()}"
        oid  = q("""INSERT INTO orders
            (order_number,user_id,items,total_amount,status,payment_status,payment_method,
             full_name,phone,address,city,state,pincode) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (onum, session['user_id'], json.dumps(order_items), total,
             'confirmed','paid', request.form.get('payment_method','card'),
             request.form.get('full_name'), request.form.get('phone'),
             request.form.get('address'), request.form.get('city'),
             request.form.get('state'), request.form.get('pincode')), commit=True)
        for i in items:
            q("UPDATE products SET stock=MAX(0,stock-?) WHERE id=?",
              (i['quantity'], i['product']['id']), commit=True)
        session.pop('cart', None)
        flash(f'🎉 Order placed! #{onum}','success')
        return redirect(url_for('order_success', order_id=oid))
    return render_template('checkout.html', items=items, total=total, user=user)

@app.route('/order/success/<int:order_id>')
@login_required
def order_success(order_id):
    order = dictrow(q("SELECT * FROM orders WHERE id=?", (order_id,), one=True))
    if not order: return redirect(url_for("my_orders"))
    return render_template('order_success.html', order=order)

@app.route('/my-orders')
@login_required
def my_orders():
    orders = dictrows(q("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (session['user_id'],)))
    return render_template('my_orders.html', orders=orders)

# ── Reviews ───────────────────────────────────────────────────────────────────
@app.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    if q("SELECT id FROM reviews WHERE product_id=? AND user_id=?", (product_id, session['user_id']), one=True):
        flash('Already reviewed.','warning'); return redirect(url_for('product_detail', product_id=product_id))
    rating = request.form.get('rating', type=int)
    if not rating or not 1 <= rating <= 5:
        flash('Invalid rating.','danger'); return redirect(url_for('product_detail', product_id=product_id))
    q("INSERT INTO reviews (product_id,user_id,rating,comment) VALUES (?,?,?,?)",
      (product_id, session['user_id'], rating, request.form.get('comment','').strip()), commit=True)
    flash('Review submitted! ⭐','success')
    return redirect(url_for('product_detail', product_id=product_id))

# ── Wishlist ──────────────────────────────────────────────────────────────────
@app.route('/wishlist')
@login_required
def wishlist():
    rows = dictrows(q(
        "SELECT w.id wid, p.* FROM wishlist w JOIN products p ON w.product_id=p.id WHERE w.user_id=? ORDER BY w.created_at DESC",
        (session['user_id'],)))
    items = [{'product': enrich(r)} for r in rows]
    return render_template('wishlist.html', items=items)

@app.route('/wishlist/toggle/<int:product_id>')
@login_required
def toggle_wishlist(product_id):
    if q("SELECT id FROM wishlist WHERE user_id=? AND product_id=?", (session['user_id'], product_id), one=True):
        q("DELETE FROM wishlist WHERE user_id=? AND product_id=?", (session['user_id'], product_id), commit=True)
        flash('Removed from wishlist.','info')
    else:
        q("INSERT INTO wishlist (user_id,product_id) VALUES (?,?)", (session['user_id'], product_id), commit=True)
        flash('Added to wishlist! 💖','success')
    return redirect(request.referrer or url_for('wishlist'))

# ── Contact ───────────────────────────────────────────────────────────────────
@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        q("INSERT INTO contacts (name,email,message) VALUES (?,?,?)",
          (request.form.get('name','').strip(), request.form.get('email','').strip(),
           request.form.get('message','').strip()), commit=True)
        flash("Message sent! We'll be in touch. 🌸",'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin')
@admin_required
def admin_dashboard():
    total_products = q("SELECT COUNT(*) c FROM products WHERE is_active=1", one=True)['c']
    total_orders   = q("SELECT COUNT(*) c FROM orders", one=True)['c']
    total_users    = q("SELECT COUNT(*) c FROM users", one=True)['c']
    rev            = q("SELECT SUM(total_amount) s FROM orders WHERE payment_status='paid'", one=True)
    total_revenue  = rev['s'] or 0
    recent_orders  = dictrows(q(
        "SELECT o.*, u.name user_name FROM orders o JOIN users u ON o.user_id=u.id ORDER BY o.created_at DESC LIMIT 10"))
    return render_template('admin/dashboard.html',
        total_products=total_products, total_orders=total_orders,
        total_users=total_users, total_revenue=total_revenue, recent_orders=recent_orders)

@app.route('/admin/products')
@admin_required
def admin_products():
    prods = [enrich(p) for p in dictrows(q("SELECT * FROM products ORDER BY created_at DESC"))]
    return render_template('admin/products.html', products=prods)

@app.route('/admin/products/add', methods=['GET','POST'])
@admin_required
def admin_add_product():
    cats   = ['Kurti','Suit','Sharara','Lehenga','Saree','Anarkali']
    sizes  = ['XS','S','M','L','XL','XXL','Free Size']
    colors = ['Red','Pink','Blue','Green','Yellow','Orange','Purple','White','Black','Gold','Maroon','Teal']
    if request.method == 'POST':
        imgs = []
        for f in request.files.getlist('images'):
            if f and allowed(f.filename):
                fn = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                imgs.append(f"/static/images/uploads/{fn}")
        q("""INSERT INTO products (name,description,price,original_price,category,sizes,colors,images,stock,is_featured)
          VALUES (?,?,?,?,?,?,?,?,?,?)""",
          (request.form.get('name'), request.form.get('description'),
           float(request.form.get('price',0) or 0),
           float(request.form.get('original_price',0) or 0) or None,
           request.form.get('category'),
           json.dumps(request.form.getlist('sizes')),
           json.dumps(request.form.getlist('colors')),
           json.dumps(imgs),
           int(request.form.get('stock',0) or 0),
           1 if request.form.get('is_featured') else 0), commit=True)
        flash('Product added!','success')
        return redirect(url_for('admin_products'))
    return render_template('admin/add_product.html', categories=cats, sizes=sizes, colors=colors)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET','POST'])
@admin_required
def admin_edit_product(product_id):
    product = enrich(q("SELECT * FROM products WHERE id=?", (product_id,), one=True))
    if not product: return redirect(url_for('admin_products'))
    cats   = ['Kurti','Suit','Sharara','Lehenga','Saree','Anarkali']
    sizes  = ['XS','S','M','L','XL','XXL','Free Size']
    colors = ['Red','Pink','Blue','Green','Yellow','Orange','Purple','White','Black','Gold','Maroon','Teal']
    if request.method == 'POST':
        existing = product['images_list'][:]
        for f in request.files.getlist('images'):
            if f and allowed(f.filename):
                fn = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                existing.append(f"/static/images/uploads/{fn}")
        q("""UPDATE products SET name=?,description=?,price=?,original_price=?,
          category=?,sizes=?,colors=?,images=?,stock=?,is_featured=?,is_active=? WHERE id=?""",
          (request.form.get('name'), request.form.get('description'),
           float(request.form.get('price',0) or 0),
           float(request.form.get('original_price',0) or 0) or None,
           request.form.get('category'),
           json.dumps(request.form.getlist('sizes')),
           json.dumps(request.form.getlist('colors')),
           json.dumps(existing),
           int(request.form.get('stock',0) or 0),
           1 if request.form.get('is_featured') else 0,
           1 if request.form.get('is_active') else 0, product_id), commit=True)
        flash('Product updated!','success')
        return redirect(url_for('admin_products'))
    return render_template('admin/edit_product.html', product=product,
        categories=cats, sizes=sizes, colors=colors)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    q("UPDATE products SET is_active=0 WHERE id=?", (product_id,), commit=True)
    flash('Product removed.','info')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    orders = dictrows(q(
        "SELECT o.*, u.name user_name FROM orders o JOIN users u ON o.user_id=u.id ORDER BY o.created_at DESC"))
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/update/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order(order_id):
    q("UPDATE orders SET status=? WHERE id=?", (request.form.get('status'), order_id), commit=True)
    flash('Order updated.','success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/contacts')
@admin_required
def admin_contacts():
    contacts = dictrows(q("SELECT * FROM contacts ORDER BY created_at DESC"))
    return render_template('admin/contacts.html', contacts=contacts)

# ══════════════════════════════════════════════════════════════════════════════
# DB INIT & SEED
# ══════════════════════════════════════════════════════════════════════════════

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
    phone TEXT, address TEXT, is_admin INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, description TEXT,
    price REAL NOT NULL, original_price REAL,
    category TEXT NOT NULL, sizes TEXT, colors TEXT, images TEXT,
    stock INTEGER DEFAULT 0, is_featured INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL, user_id INTEGER NOT NULL,
    items TEXT NOT NULL, total_amount REAL NOT NULL,
    status TEXT DEFAULT 'pending', payment_status TEXT DEFAULT 'pending',
    payment_method TEXT, full_name TEXT, phone TEXT, address TEXT,
    city TEXT, state TEXT, pincode TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL, comment TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, email TEXT NOT NULL, message TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

SEED_PRODUCTS = [
    ("Floral Print Straight Kurti",
     "Beautiful floral print kurti in breathable cotton fabric. Perfect for daily wear and casual outings. Features a mandarin collar and three-quarter sleeves.",
     899, 1299, "Kurti", '["S","M","L","XL","XXL"]', '["Pink","Blue","Yellow"]',
     '["/static/images/placeholder.svg"]', 50, 1),
    ("Embroidered Palazzo Suit Set",
     "Elegant embroidered suit set with palazzo pants. Comes with matching dupatta. Ideal for festive occasions and family gatherings.",
     2499, 3499, "Suit", '["S","M","L","XL"]', '["Maroon","Green","Blue"]',
     '["/static/images/placeholder.svg"]', 30, 1),
    ("Designer Sharara Set",
     "Stunning designer sharara set with heavy embroidery. Perfect for weddings, receptions, and festive celebrations.",
     4999, 6999, "Sharara", '["S","M","L","XL"]', '["Gold","Red","Purple"]',
     '["/static/images/placeholder.svg"]', 20, 1),
    ("Bridal Lehenga Choli",
     "Exquisite bridal lehenga with intricate zari work and mirror embellishments. Heavy silk fabric gives it a royal look.",
     12999, 18999, "Lehenga", '["XS","S","M","L","XL"]', '["Red","Maroon","Pink"]',
     '["/static/images/placeholder.svg"]', 15, 1),
    ("Chanderi Silk Saree",
     "Pure Chanderi silk saree with delicate zari border. Lightweight and easy to drape. Unstitched blouse piece included.",
     3299, 4500, "Saree", '["Free Size"]', '["Teal","Purple","Gold"]',
     '["/static/images/placeholder.svg"]', 25, 1),
    ("Lucknowi Chikankari Anarkali",
     "Authentic Lucknowi chikankari embroidered anarkali suit. Hand-embroidered floral patterns on soft georgette.",
     3799, 5200, "Anarkali", '["S","M","L","XL"]', '["White","Pink","Peach"]',
     '["/static/images/placeholder.svg"]', 35, 1),
    ("Ajrakh Print Cotton Kurti",
     "Traditional Ajrakh block print cotton kurti. Eco-friendly natural dyes. Great for casual and office wear.",
     749, 999, "Kurti", '["S","M","L","XL","XXL"]', '["Blue","Red","Black"]',
     '["/static/images/placeholder.svg"]', 60, 0),
    ("Patiala Salwar Suit",
     "Vibrant Patiala salwar suit with heavy phulkari embroidery. Loose pants offer great comfort.",
     1899, 2599, "Suit", '["S","M","L","XL"]', '["Orange","Yellow","Pink"]',
     '["/static/images/placeholder.svg"]', 40, 0),
    ("Mirror Work Lehenga",
     "Stunning mirror work lehenga perfect for Navratri and festive occasions. Vibrant colors with traditional craft.",
     5999, 8500, "Lehenga", '["S","M","L","XL"]', '["Red","Green","Blue"]',
     '["/static/images/placeholder.svg"]', 22, 1),
    ("Bandhani Silk Saree",
     "Beautiful Bandhani tie-dye silk saree from Rajasthan. Every piece is unique with its hand-tied pattern.",
     2799, 3800, "Saree", '["Free Size"]', '["Red","Yellow","Pink"]',
     '["/static/images/placeholder.svg"]', 18, 0),
]

def init_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.executescript(SCHEMA)
    # Admin
    if not db.execute("SELECT id FROM users WHERE email='admin@ethnicwear.com'").fetchone():
        db.execute("INSERT INTO users (name,email,password,is_admin) VALUES (?,?,?,1)",
                   ('Admin', 'admin@ethnicwear.com', generate_password_hash('admin123')))
    # Sample products
    for p in SEED_PRODUCTS:
        if not db.execute("SELECT id FROM products WHERE name=?", (p[0],)).fetchone():
            db.execute("""INSERT INTO products
                (name,description,price,original_price,category,sizes,colors,images,stock,is_featured)
                VALUES (?,?,?,?,?,?,?,?,?,?)""", p)
    db.commit(); db.close()
    print("✅ Rang Mahal DB initialised.")

# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print("\n🌸 Rang Mahal starting on http://localhost:5000")
    print("   Admin login: admin@ethnicwear.com / admin123\n")
    app.run(debug=True, port=5000)
