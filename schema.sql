-- schema.sql

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS bookstore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bookstore;

-- 2. 创建"用户"表（会员信息）
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,                -- 会员ID
    username VARCHAR(50) NOT NULL UNIQUE,             -- 用户名（唯一）
    password_hash VARCHAR(255) NOT NULL,              -- 密码（存储哈希值）
    email VARCHAR(100) NOT NULL UNIQUE,               -- 邮箱（唯一）
    full_name VARCHAR(100) NULL,                      -- 真实姓名
    phone VARCHAR(20) NULL,                           -- 联系电话
    address VARCHAR(255) NULL,                        -- 收货地址
    is_admin TINYINT(1) NOT NULL DEFAULT 0,           -- 是否为管理员（0=普通会员，1=管理员）
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. 创建"图书分类"表
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,                -- 分类ID
    name VARCHAR(100) NOT NULL UNIQUE,                -- 分类名称
    description VARCHAR(255) NULL,                    -- 分类描述
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. 创建"图书"表
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,                 -- 图书ID
    title VARCHAR(200) NOT NULL,                       -- 书名
    author VARCHAR(100) NOT NULL,                      -- 作者
    publisher VARCHAR(100) NULL,                       -- 出版社
    publish_date DATE NULL,                            -- 出版日期
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,         -- 价格
    stock INT NOT NULL DEFAULT 0,                      -- 库存数量
    category_id INT NOT NULL,                          -- 分类ID（外键）
    description TEXT NULL,                             -- 图书简介
    cover_image VARCHAR(255) NULL,                     -- 封面图片URL或文件路径
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 5. 创建"购物车"表
-- 注意：这里假设每个用户有一个"临时购物车"，也可以改为每次下单临时存储
CREATE TABLE IF NOT EXISTS cart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,                               -- 会员ID
    book_id INT NOT NULL,                               -- 图书ID
    quantity INT NOT NULL DEFAULT 1,                    -- 数量
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_book (user_id, book_id),         -- 同一本书只存在一行，便于更新数量
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 6. 创建"订单"表
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,                  -- 订单ID
    user_id INT NOT NULL,                               -- 会员ID
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,   -- 订单总金额
    status ENUM('created','paid','shipped','completed','canceled') NOT NULL DEFAULT 'created',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    shipping_address VARCHAR(255) NOT NULL,             -- 收货地址（下单时拷贝用户地址）
    contact_phone VARCHAR(20) NOT NULL,                 -- 联系电话（下单时拷贝）
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 7. 创建"订单明细"表
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,                              -- 关联订单ID
    book_id INT NOT NULL,                               -- 关联图书ID
    quantity INT NOT NULL DEFAULT 1,                    -- 购买数量
    unit_price DECIMAL(10,2) NOT NULL,                  -- 下单时图书单价
    subtotal DECIMAL(12,2) NOT NULL,                    -- 小计 = unit_price * quantity
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 8. 创建"订单评价"表
CREATE TABLE IF NOT EXISTS order_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,                              -- 关联订单ID
    user_id INT NOT NULL,                               -- 评价用户ID
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5), -- 评分（1-5星）
    comment TEXT,                                       -- 评价内容
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY uk_order_user (order_id, user_id)        -- 每个订单每个用户只能评价一次
) ENGINE=InnoDB;

-- 9. 初始化一个管理员账号（使用明文密码）
INSERT INTO users (username, password_hash, email, full_name, is_admin)
VALUES ('admin', 'admin123', 'admin@example.com', '超级管理员', 1)
ON DUPLICATE KEY UPDATE password_hash = 'admin123';

