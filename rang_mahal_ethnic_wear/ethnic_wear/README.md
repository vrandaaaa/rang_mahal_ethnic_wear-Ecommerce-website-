# 🌸 Rang Mahal — Women's Ethnic Wear E-Commerce

A complete, production-ready e-commerce website for women's ethnic fashion built with **Flask + SQLite**.

---

## 📁 Project Structure

```
ethnic_wear/
├── app.py                          # Main Flask application (all routes + DB logic)
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── instance/
│   └── rang_mahal.db               # SQLite database (auto-created on first run)
├── static/
│   ├── css/
│   │   ├── style.css               # Main storefront styles
│   │   └── admin.css               # Admin panel styles
│   ├── js/
│   │   └── main.js                 # Frontend interactivity
│   └── images/
│       ├── placeholder.svg         # Default product image
│       └── uploads/                # Uploaded product images (auto-created)
└── templates/
    ├── base.html                   # Base layout (navbar, footer, flash messages)
    ├── home.html                   # Homepage (hero, featured, new arrivals)
    ├── products.html               # Product listing with filters & search
    ├── product_detail.html         # Single product page (gallery, reviews)
    ├── cart.html                   # Shopping cart
    ├── checkout.html               # Checkout with mock payment
    ├── order_success.html          # Order confirmation page
    ├── my_orders.html              # User order history
    ├── wishlist.html               # User wishlist
    ├── login.html                  # Login page
    ├── signup.html                 # Registration page
    ├── contact.html                # Contact page
    └── admin/
        ├── base_admin.html         # Admin layout (sidebar navigation)
        ├── dashboard.html          # Admin dashboard (stats + recent orders)
        ├── products.html           # Admin product list
        ├── add_product.html        # Add new product form
        ├── edit_product.html       # Edit product form
        ├── orders.html             # All orders management
        └── contacts.html           # Contact form submissions
```

---

## ⚙️ Setup & Running Locally

### Prerequisites
- Python 3.8 or higher
- pip

### 1. Install Dependencies

```bash
pip install flask werkzeug
```

> **Note:** No other packages needed — the app uses Python's built-in `sqlite3`.

### 2. Run the App

```bash
cd ethnic_wear
python app.py
```

You'll see:
```
✅ Rang Mahal DB initialised.

🌸 Rang Mahal starting on http://localhost:5000
   Admin login: admin@ethnicwear.com / admin123
```

### 3. Open in Browser

```
http://localhost:5000
```

---

## 🔐 Default Login Credentials

| Role  | Email                    | Password   |
|-------|--------------------------|------------|
| Admin | admin@ethnicwear.com     | admin123   |
| User  | Create via /signup       | your choice|

---

## ✨ Features

### Storefront
| Feature | Details |
|---|---|
| **Homepage** | Hero banner, featured products, new arrivals, category strip, trust badges |
| **Product Listing** | Grid view, filters (category/price/size/color), search, sort, pagination |
| **Product Detail** | Image gallery, size/color selector, quantity control, add to cart |
| **Cart** | Add/remove/update quantity, subtotal, free shipping threshold |
| **Checkout** | Address form, 3 payment methods (card/UPI/COD), mock payment simulation |
| **Order Success** | Confirmation with order number |
| **My Orders** | Full order history with status |
| **Wishlist** | Save/remove products, move to cart |
| **Reviews** | Star ratings (1–5) + text comments per product |
| **Contact Page** | Phone, email, Instagram, WhatsApp + contact form |

### Admin Panel (`/admin`)
| Feature | Details |
|---|---|
| **Dashboard** | Total products, orders, users, revenue + recent orders table |
| **Products** | List all, add, edit, soft-delete, toggle featured/active |
| **Image Upload** | Multi-image upload with preview |
| **Orders** | View all orders with items, update status (pending → shipped → delivered) |
| **Messages** | View all contact form submissions |

### Security
- Passwords hashed with Werkzeug `generate_password_hash`
- Session-based authentication
- `@login_required` and `@admin_required` decorators
- Admin routes fully protected

---

## 🗄️ Database Schema

```sql
users         -- id, name, email, password (hashed), phone, address, is_admin
products      -- id, name, description, price, original_price, category,
              --   sizes (JSON), colors (JSON), images (JSON), stock,
              --   is_featured, is_active
orders        -- id, order_number, user_id, items (JSON), total_amount,
              --   status, payment_status, payment_method,
              --   full_name, phone, address, city, state, pincode
reviews       -- id, product_id, user_id, rating (1-5), comment
wishlist      -- id, user_id, product_id
contacts      -- id, name, email, message
```

---

## 💳 Mock Payment

The checkout page includes a **payment simulator**:
- Select **✓ Success** → order is placed, stock reduced, cart cleared
- Select **✗ Failure** → shows payment failed message, order NOT created

This simulates real payment gateway responses without any external API.

---

## 🖼️ Adding Real Product Images

1. Go to **Admin → Edit Product**
2. Upload images (PNG/JPG/WEBP, max 16MB each)
3. Images are saved to `static/images/uploads/`

Or drop images directly into `static/images/products/` and reference them as:
```
/static/images/products/your-image.jpg
```

---

## 🎨 Design

- **Font:** Cormorant Garamond (headings) + Jost (body)
- **Colors:** Deep Burgundy · Rose · Ivory · Warm Gold
- **Responsive:** Mobile-first, works on all screen sizes
- **Theme:** Refined luxury editorial — inspired by Indian heritage

---

## 📦 Categories

Kurti · Suit · Sharara · Lehenga · Saree · Anarkali

---

## 📞 Contact Info (shown on /contact)

- **Phone:** +91 98765 43210
- **Email:** care@rangmahal.com
- **Instagram:** @rangmahal.official
- **WhatsApp:** +91 98765 43210

*(Update these in `templates/contact.html` and `templates/base.html`)*
