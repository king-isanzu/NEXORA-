CREATE DATABASE IF NOT EXISTS nexora
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE nexora;


CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(160) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL UNIQUE,

    password_hash VARCHAR(255) NOT NULL,
    address TEXT,
    role VARCHAR(30) NOT NULL DEFAULT 'customer',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


CREATE TABLE businesses (
    id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(160) NOT NULL,
    category VARCHAR(80) NOT NULL,
    phone VARCHAR(30),

    address TEXT,

    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,

    business_id INT NOT NULL,

    name VARCHAR(160) NOT NULL,
    description TEXT,

    price DECIMAL(12, 2) NOT NULL,
    image_url VARCHAR(500),

    stock INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_products_business
        FOREIGN KEY (business_id)
        REFERENCES businesses(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    total_amount DECIMAL(12, 2) NOT NULL,

    payment_method VARCHAR(80) NOT NULL,

    status VARCHAR(40) DEFAULT 'pending',

    delivery_address TEXT,

    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_orders_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,

    order_id INT NOT NULL,
    product_id INT NOT NULL,

    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(12, 2) NOT NULL,

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE RESTRICT
) ENGINE=InnoDB;


CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    business_id INT NULL,

    service_type VARCHAR(80) NOT NULL,

    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,

    notes TEXT,

    status VARCHAR(40) DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_bookings_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_bookings_business
        FOREIGN KEY (business_id)
        REFERENCES businesses(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;


CREATE TABLE addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    label VARCHAR(80),
    address_text TEXT NOT NULL,

    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_addresses_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE delivery_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    pickup_address TEXT NOT NULL,
    delivery_address TEXT NOT NULL,

    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),

    delivery_fee DECIMAL(12, 2) DEFAULT 0,

    status VARCHAR(40) DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_delivery_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,

    order_id INT NOT NULL,

    provider VARCHAR(80) NOT NULL,
    method VARCHAR(80) NOT NULL,

    amount DECIMAL(12, 2) NOT NULL,

    transaction_reference VARCHAR(160),

    status VARCHAR(40) DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_id)
        REFERENCES orders(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    business_id INT NOT NULL,

    rating INT NOT NULL,
    comment TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_review_rating
        CHECK (rating BETWEEN 1 AND 5),

    CONSTRAINT fk_reviews_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_reviews_business
        FOREIGN KEY (business_id)
        REFERENCES businesses(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE INDEX idx_business_category
    ON businesses(category);

CREATE INDEX idx_products_business
    ON products(business_id);

CREATE INDEX idx_orders_user
    ON orders(user_id);

CREATE INDEX idx_orders_status
    ON orders(status);

CREATE INDEX idx_bookings_date
    ON bookings(booking_date);

CREATE INDEX idx_delivery_status
    ON delivery_orders(status);


-- NEXORA creates the demo user automatically on backend startup.
-- Demo login: demo@nexora.co.tz / Demo@12345
