# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
# 明文存储密码，直接对比，无需哈希
from flask_login import (
    LoginManager, login_user, login_required, logout_user, current_user, UserMixin
)
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 请换成随机字符串

# 订单状态映射：数据库中存英文，界面显示中文
STATUS_MAP = {
    'created': '已创建',
    'paid': '已支付',
    'shipped': '已发货',
    'completed': '已完成',
    'canceled': '已取消'
}

@app.context_processor
def inject_status_map():
    """在所有模板中注入 status_map"""
    return dict(status_map=STATUS_MAP)

# ====================
#  配置 MySQL 连接
# ====================
db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',            # 请改为你的 MySQL 用户
    'password': '20041224cbW',
    'database': 'bookstore',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


def get_db_connection():
    return pymysql.connect(**db_config)


# ====================
#  Flask-Login 配置
# ====================
login_manager = LoginManager()
login_manager.login_view = 'login'  # 未登录时重定向到 login 路由
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, data):
        self.id = data['id']
        self.username = data['username']
        self.is_admin = data['is_admin']

    @staticmethod
    def get_by_username(username):
        """根据用户名查询 User 记录，返回 User 对象或 None"""
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM users WHERE username=%s"
            cursor.execute(sql, (username,))
            row = cursor.fetchone()
        conn.close()
        if row:
            return User(row)
        return None

    @staticmethod
    def get_by_id(user_id):
        """根据 id 查询 User 记录，返回 User 对象或 None"""
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM users WHERE id=%s"
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
        conn.close()
        if row:
            return User(row)
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


# ====================
#  辅助函数
# ====================
def query_all_books(keyword=None):
    """
    查询所有图书，可根据关键字（书名、作者）模糊查询
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        if keyword:
            like_kw = f"%{keyword}%"
            sql = """
                SELECT b.id, b.title, b.author, b.price, b.stock, c.name AS category
                FROM books b
                LEFT JOIN categories c ON b.category_id=c.id
                WHERE b.title LIKE %s OR b.author LIKE %s
                ORDER BY b.title;
            """
            cursor.execute(sql, (like_kw, like_kw))
        else:
            sql = """
                SELECT b.id, b.title, b.author, b.price, b.stock, c.name AS category
                FROM books b
                LEFT JOIN categories c ON b.category_id=c.id
                ORDER BY b.title;
            """
            cursor.execute(sql)
        results = cursor.fetchall()
    conn.close()
    return results


def get_book_by_id(book_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = "SELECT * FROM books WHERE id=%s"
        cursor.execute(sql, (book_id,))
        row = cursor.fetchone()
    conn.close()
    return row


def get_cart_items(user_id):
    """
    获取某用户购物车所有条目
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = """
            SELECT ci.id AS cart_id, b.id AS book_id, b.title, b.price, ci.quantity
            FROM cart_items ci
            JOIN books b ON ci.book_id = b.id
            WHERE ci.user_id=%s;
        """
        cursor.execute(sql, (user_id,))
        items = cursor.fetchall()
    conn.close()
    return items


def calculate_cart_total(user_id):
    """
    计算购物车总金额
    """
    items = get_cart_items(user_id)
    total = sum(item['price'] * item['quantity'] for item in items)
    return total


# ====================
#  前端商城管理子系统
# ====================

@app.route('/')
def index():
    """
    首页：显示最近上架的几本图书（示例）
    """
    books = query_all_books()
    return render_template('search.html', books=books)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册：
      GET：渲染注册表单
      POST：保存用户并重定向到登录页面
    """
    if request.method == 'POST':
        username = request.form.get('username').strip()
        raw_pwd = request.form.get('password').strip()
        email = request.form.get('email').strip()
        # 检查用户名/邮箱是否已存在
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username=%s OR email=%s", (username, email))
            exists = cursor.fetchone()
            if exists:
                flash('用户名或邮箱已被占用，请更换后重试。', 'danger')
                return redirect(url_for('register'))
            # 直接保存明文密码（仅限教学示例，生产环境请使用哈希）
            pwd_hash = raw_pwd
            sql = """
                INSERT INTO users (username, password_hash, email)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (username, pwd_hash, email))
            conn.commit()
        conn.close()
        flash('注册成功，请使用新账号登录。', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录
    """
    if request.method == 'POST':
        username = request.form.get('username').strip()
        raw_pwd = request.form.get('password').strip()
        # 查询用户
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user_row = cursor.fetchone()
        conn.close()
        if not user_row:
            flash('用户名不存在。', 'danger')
            return redirect(url_for('login'))

        # 验证密码（明文比对）
        if user_row['password_hash'] != raw_pwd:
            flash('密码错误。', 'danger')
            return redirect(url_for('login'))

        user = User(user_row)
        login_user(user)

        flash('登录成功！', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已退出登录。', 'info')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    用户可修改个人信息（full_name、phone、address）
    """
    if request.method == 'POST':
        full_name = request.form.get('full_name').strip()
        phone = request.form.get('phone').strip()
        address = request.form.get('address').strip()
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                UPDATE users
                SET full_name=%s, phone=%s, address=%s, updated_at=%s
                WHERE id=%s
            """
            cursor.execute(sql, (full_name, phone, address, datetime.now(), current_user.id))
            conn.commit()
        conn.close()
        flash('个人信息已更新。', 'success')
        return redirect(url_for('profile'))

    # GET 时渲染表单，显示当前用户信息
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT username, email, full_name, phone, address FROM users WHERE id=%s", (current_user.id,))
        user_info = cursor.fetchone()
    conn.close()
    return render_template('profile.html', user=user_info)


@app.route('/search', methods=['GET', 'POST'])
def search():
    """
    查询图书：输入关键字，展示结果
    """
    keyword = request.form.get('keyword', '').strip() if request.method == 'POST' else request.args.get('keyword', '').strip()
    books = query_all_books(keyword) if keyword else query_all_books()
    return render_template('book_list.html', books=books, keyword=keyword)


@app.route('/book/<int:book_id>')
def book_detail(book_id):
    """
    查看单本图书的详细信息
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = """
            SELECT b.*, c.name AS category
            FROM books b
            LEFT JOIN categories c ON b.category_id = c.id
            WHERE b.id = %s
        """
        cursor.execute(sql, (book_id,))
        book = cursor.fetchone()
    conn.close()
    
    if not book:
        flash('未找到该图书信息。', 'warning')
        return redirect(url_for('search'))
    return render_template('book_detail.html', book=book)


@app.route('/add_to_cart/<int:book_id>', methods=['POST'])
@login_required
def add_to_cart(book_id):
    """
    将指定图书添加到购物车（若已存在则数量 +1）
    """
    # Ensure the quantity is a valid positive integer
    qty_raw = request.form.get('quantity', '1')
    try:
        quantity = int(qty_raw)
        if quantity < 1:
            raise ValueError
    except (TypeError, ValueError):
        flash('无效的数量。', 'danger')
        return redirect(url_for('view_cart'))
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # 检查该用户购物车中是否已有此书
        cursor.execute("SELECT id, quantity FROM cart_items WHERE user_id=%s AND book_id=%s", (current_user.id, book_id))
        row = cursor.fetchone()
        if row:
            new_qty = row['quantity'] + quantity
            cursor.execute("UPDATE cart_items SET quantity=%s WHERE id=%s", (new_qty, row['id']))
        else:
            cursor.execute("INSERT INTO cart_items (user_id, book_id, quantity) VALUES (%s, %s, %s)",
                           (current_user.id, book_id, quantity))
        conn.commit()
    conn.close()
    flash('已添加到购物车。', 'success')
    return redirect(url_for('view_cart'))


@app.route('/cart')
@login_required
def view_cart():
    """
    查看购物车：列出所有商品和数量，以及总价
    """
    items = get_cart_items(current_user.id)
    total = calculate_cart_total(current_user.id)
    return render_template('cart.html', items=items, total=total)


@app.route('/update_cart/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    """
    修改购物车中某个条目的数量（或删除：quantity=0）
    """
    new_qty = int(request.form.get('quantity', 1))
    conn = get_db_connection()
    with conn.cursor() as cursor:
        if new_qty <= 0:
            cursor.execute("DELETE FROM cart_items WHERE id=%s AND user_id=%s", (cart_id, current_user.id))
        else:
            cursor.execute("UPDATE cart_items SET quantity=%s WHERE id=%s AND user_id=%s",
                           (new_qty, cart_id, current_user.id))
        conn.commit()
    conn.close()
    flash('购物车已更新。', 'info')
    return redirect(url_for('view_cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """
    下单/提交订单：
      GET：显示收货地址、购物车商品、总价
      POST：创建订单、订单明细、清空购物车
    """
    if request.method == 'POST':
        # 获取地址和电话（允许用户下单时改写或使用个人资料中的信息）
        shipping_address = request.form.get('address', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        
        if not shipping_address or not contact_phone:
            flash('请填写收货地址和联系电话。', 'warning')
            return redirect(url_for('checkout'))
            
        # 计算总金额
        total = calculate_cart_total(current_user.id)
        if total <= 0:
            flash('购物车为空，无法下单。', 'warning')
            return redirect(url_for('view_cart'))

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 1) 插入 orders 表
                sql_order = """
                    INSERT INTO orders 
                    (user_id, total_amount, status, shipping_address, contact_phone, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                order_status = 'created'  # 使用变量存储状态值
                try:
                    cursor.execute(sql_order, (
                        current_user.id, 
                        total, 
                        order_status,  # 使用变量
                        shipping_address, 
                        contact_phone, 
                        datetime.now()
                    ))
                    order_id = cursor.lastrowid
                except Exception as e:
                    print(f"订单创建失败: {str(e)}")  # 添加调试信息
                    raise

                # 2) 插入 order_items 表，并减少库存
                items = get_cart_items(current_user.id)
                for item in items:
                    unit_price = item['price']
                    qty = item['quantity']
                    subtotal = unit_price * qty
                    # 插入 order_items
                    sql_item = """
                        INSERT INTO order_items (order_id, book_id, quantity, unit_price, subtotal)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_item, (order_id, item['book_id'], qty, unit_price, subtotal))

                    # 更新库存：books.stock -= quantity
                    sql_update_stock = "UPDATE books SET stock = stock - %s WHERE id = %s AND stock >= %s"
                    cursor.execute(sql_update_stock, (qty, item['book_id'], qty))

                # 3) 清空当前用户购物车
                cursor.execute("DELETE FROM cart_items WHERE user_id=%s", (current_user.id,))
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"下单失败: {str(e)}")  # 添加调试信息
            flash(f'下单失败：{str(e)}', 'danger')
            return redirect(url_for('view_cart'))
        finally:
            conn.close()

        flash('订单提交成功，请付款以完成订单。', 'success')
        return redirect(url_for('order_status', order_id=order_id))

    # GET 方法：显示微信地址、联系电话（从用户表中读取）
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT address, phone FROM users WHERE id=%s", (current_user.id,))
        usr = cursor.fetchone()
    conn.close()

    items = get_cart_items(current_user.id)
    total = calculate_cart_total(current_user.id)
    return render_template('checkout.html', items=items, total=total, user_info=usr)


@app.route('/order_status/<int:order_id>')
@login_required
def order_status(order_id):
    """
    查看某个订单的状态及明细
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # 获取订单信息
        cursor.execute("SELECT * FROM orders WHERE id=%s AND user_id=%s", (order_id, current_user.id))
        order = cursor.fetchone()
        # 获取订单明细
        cursor.execute("""
            SELECT oi.book_id, b.title, oi.quantity, oi.unit_price, oi.subtotal
            FROM order_items oi
            JOIN books b ON oi.book_id = b.id
            WHERE oi.order_id=%s
        """, (order_id,))
        items = cursor.fetchall()
    conn.close()
    if not order:
        flash('未找到该订单或无权限查看。', 'warning')
        return redirect(url_for('index'))

    return render_template('order_status.html', order=order, items=items)


# ====================
#  后台（Admin）管理子系统
# ====================

def admin_required(func):
    """
    装饰器：仅管理员可访问
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.is_admin != 1:
            flash('只有管理员才能访问该页面。', 'danger')
            return redirect(url_for('login'))
        return func(*args, **kwargs)

    return wrapper


@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """
    后台首页：显示一些简单统计，例如总用户数、总订单数、总销售额等
    """
    conn = get_db_connection()
    stats = {}
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM users")
        stats['user_count'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) AS cnt FROM books")
        stats['book_count'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) AS cnt FROM orders")
        stats['order_count'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT IFNULL(SUM(total_amount), 0) AS total_sales FROM orders WHERE status='completed'")
        stats['total_sales'] = cursor.fetchone()['total_sales']
    conn.close()
    return render_template('admin/dashboard.html', stats=stats)


# ---- 图书信息管理 ----

@app.route('/admin/books')
@login_required
@admin_required
def admin_book_list():
    """
    后台"图书列表"页：罗列所有图书
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT b.id, b.title, b.author, b.price, b.stock, c.name AS category
            FROM books b
            LEFT JOIN categories c ON b.category_id=c.id
            ORDER BY b.id DESC
        """)
        books = cursor.fetchall()
    conn.close()
    return render_template('admin/book_list.html', books=books)


@app.route('/admin/book/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_book_create():
    """
    后台"新增图书"页
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # 获取所有分类，供下拉框使用
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        categories = cursor.fetchall()

    if request.method == 'POST':
        title = request.form.get('title').strip()
        author = request.form.get('author').strip()
        publisher = request.form.get('publisher').strip()
        publish_date = request.form.get('publish_date') or None
        price = float(request.form.get('price') or 0)
        stock = int(request.form.get('stock') or 0)
        category_id = int(request.form.get('category_id'))
        description = request.form.get('description').strip()
        # （可选）处理封面图片上传，此处简化
        cover_image = request.form.get('cover_image').strip()

        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO books
                  (title, author, publisher, publish_date, price, stock, category_id, description, cover_image, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                title, author, publisher, publish_date, price, stock, category_id,
                description, cover_image, datetime.now()
            ))
            conn.commit()
        conn.close()
        flash('图书已新增。', 'success')
        return redirect(url_for('admin_book_list'))

    return render_template('admin/book_form.html', categories=categories, action='create', book=None)


@app.route('/admin/book/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_book_edit(book_id):
    """
    后台"编辑图书"页
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # 获取图书当前信息
        cursor.execute("SELECT * FROM books WHERE id=%s", (book_id,))
        book = cursor.fetchone()
        if not book:
            conn.close()
            flash('未找到该图书。', 'warning')
            return redirect(url_for('admin_book_list'))
        # 获取所有分类
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        categories = cursor.fetchall()
    conn.close()

    if request.method == 'POST':
        title = request.form.get('title').strip()
        author = request.form.get('author').strip()
        publisher = request.form.get('publisher').strip()
        publish_date = request.form.get('publish_date') or None
        price = float(request.form.get('price') or 0)
        stock = int(request.form.get('stock') or 0)
        category_id = int(request.form.get('category_id'))
        description = request.form.get('description').strip()
        cover_image = request.form.get('cover_image').strip()
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                UPDATE books
                SET title=%s, author=%s, publisher=%s, publish_date=%s,
                    price=%s, stock=%s, category_id=%s, description=%s,
                    cover_image=%s, updated_at=%s
                WHERE id=%s
            """
            cursor.execute(sql, (
                title, author, publisher, publish_date, price, stock,
                category_id, description, cover_image, datetime.now(), book_id
            ))
            conn.commit()
        conn.close()
        flash('图书信息已更新。', 'success')
        return redirect(url_for('admin_book_list'))

    return render_template('admin/book_form.html', categories=categories, action='edit', book=book)


@app.route('/admin/book/delete/<int:book_id>', methods=['POST'])
@login_required
@admin_required
def admin_book_delete(book_id):
    """
    后台"删除图书"操作
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM books WHERE id=%s", (book_id,))
        conn.commit()
    conn.close()
    flash('图书已删除。', 'info')
    return redirect(url_for('admin_book_list'))


# ---- 会员信息管理 ----

@app.route('/admin/users')
@login_required
@admin_required
def admin_user_list():
    """
    后台"会员列表"页：可以查看所有会员状态，并支持修改/删除等操作
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, username, email, full_name, phone, address, is_admin, created_at FROM users ORDER BY id DESC")
        users = cursor.fetchall()
    conn.close()
    return render_template('admin/user_list.html', users=users)


@app.route('/admin/user/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    """
    后台切换会员是否为管理员
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # 查询当前 is_admin 值
        cursor.execute("SELECT is_admin FROM users WHERE id=%s", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            flash('未找到该会员。', 'warning')
            return redirect(url_for('admin_user_list'))
        new_flag = 0 if row['is_admin'] == 1 else 1
        cursor.execute("UPDATE users SET is_admin=%s WHERE id=%s", (new_flag, user_id))
        conn.commit()
    conn.close()
    flash('管理员权限已切换。', 'success')
    return redirect(url_for('admin_user_list'))


@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_user_delete(user_id):
    """
    后台删除会员
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
    conn.close()
    flash('会员已删除。', 'info')
    return redirect(url_for('admin_user_list'))


# ---- 订单管理 ----

@app.route('/admin/orders')
@login_required
@admin_required
def admin_order_list():
    """
    后台"订单列表"页：可查看订单状态、修改配送状态、删除订单等
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT o.id, u.username, o.total_amount, o.status, o.created_at
            FROM orders o
            JOIN users u ON o.user_id=u.id
            ORDER BY o.created_at DESC
        """)
        orders = cursor.fetchall()
    conn.close()
    return render_template('admin/order_list.html', orders=orders)


@app.route('/admin/order/detail/<int:order_id>')
@login_required
@admin_required
def admin_order_detail(order_id):
    """
    后台查看订单明细
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
        order = cursor.fetchone()
        cursor.execute("""
            SELECT oi.book_id, b.title, oi.quantity, oi.unit_price, oi.subtotal
            FROM order_items oi
            JOIN books b ON oi.book_id=b.id
            WHERE oi.order_id=%s
        """, (order_id,))
        items = cursor.fetchall()
    conn.close()
    return render_template('admin/order_detail.html', order=order, items=items)


@app.route('/admin/order/update_status/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def admin_order_update_status(order_id):
    """
    后台修改订单状态
    """
    new_status = request.form.get('status')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 如果订单状态改为已取消，需要返还库存
            if new_status == 'canceled':
                # 1. 获取订单中的所有商品
                cursor.execute("""
                    SELECT book_id, quantity 
                    FROM order_items 
                    WHERE order_id = %s
                """, (order_id,))
                items = cursor.fetchall()
                
                # 2. 返还库存
                for item in items:
                    cursor.execute("""
                        UPDATE books 
                        SET stock = stock + %s 
                        WHERE id = %s
                    """, (item['quantity'], item['book_id']))
            
            # 3. 更新订单状态
            cursor.execute("""
                UPDATE orders 
                SET status = %s, 
                    updated_at = %s 
                WHERE id = %s
            """, (new_status, datetime.now(), order_id))
            
            conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f'更新订单状态失败：{str(e)}', 'danger')
    finally:
        conn.close()
        
    flash('订单状态已更新。', 'success')
    return redirect(url_for('admin_order_list'))


# ---- 统计模块 ----

@app.route('/admin/stats')
@login_required
@admin_required
def admin_stats():
    """
    后台"统计报表"页：可以做销售统计、库存统计、会员统计等
     这里以 "各分类销量" 举例
    """
    conn = get_db_connection()
    stats = {}
    with conn.cursor() as cursor:
        # 各分类已完成订单总销售额
        cursor.execute("""
            SELECT 
                c.name AS category,
                IFNULL(SUM(oi.subtotal), 0) AS sales
            FROM categories c
            LEFT JOIN books b ON c.id = b.category_id
            LEFT JOIN order_items oi ON b.id = oi.book_id
            LEFT JOIN orders o ON oi.order_id = o.id
            WHERE o.status = 'completed' OR o.status IS NULL
            GROUP BY c.id, c.name
            ORDER BY sales DESC;
        """)
        stats['category_sales'] = cursor.fetchall()

        # 库存不足（stock<=5）的图书列表
        cursor.execute("""
            SELECT id, title, stock
            FROM books
            WHERE stock <= 5
            ORDER BY stock ASC;
        """)
        stats['low_stock'] = cursor.fetchall()
    conn.close()
    return render_template('admin/stats.html', stats=stats)


# ====================
#  启动服务
# ====================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
