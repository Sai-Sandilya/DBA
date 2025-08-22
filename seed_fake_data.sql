-- Optional: set your database
-- USE your_database_name;

-- Allow deeper recursive CTEs (default is 1000)
SET SESSION cte_max_recursion_depth = 5000;

CREATE TABLE IF NOT EXISTS fake_users (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  phone VARCHAR(20) NOT NULL,
  address_line VARCHAR(120) NOT NULL,
  city VARCHAR(60) NOT NULL,
  state VARCHAR(60) NOT NULL,
  zip_code VARCHAR(10) NOT NULL,
  created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS fake_orders (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  order_number VARCHAR(20) NOT NULL UNIQUE,
  product_name VARCHAR(100) NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  status ENUM('pending','processing','shipped','delivered','cancelled') NOT NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  notes VARCHAR(255) NULL,
  CONSTRAINT fk_fake_orders_user FOREIGN KEY (user_id) REFERENCES fake_users(id)
);

WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 5000
)
INSERT INTO fake_users
(first_name, last_name, email, phone, address_line, city, state, zip_code, created_at)
SELECT
  ELT(1 + (n % 10), 'Alice','Bob','Carol','Dave','Eve','Frank','Grace','Heidi','Ivan','Judy') AS first_name,
  ELT(1 + (n % 10), 'Smith','Johnson','Williams','Brown','Jones','Miller','Davis','Garcia','Rodriguez','Wilson') AS last_name,
  CONCAT(
    LOWER(ELT(1 + (n % 10), 'Alice','Bob','Carol','Dave','Eve','Frank','Grace','Heidi','Ivan','Judy')),
    '.',
    LOWER(ELT(1 + (n % 10), 'Smith','Johnson','Williams','Brown','Jones','Miller','Davis','Garcia','Rodriguez','Wilson')),
    n, '@example.com'
  ) AS email,
  CONCAT('+1-',
         LPAD(FLOOR(RAND(n) * 900) + 100, 3, '0'), '-',
         LPAD(FLOOR(RAND(n*2) * 900) + 100, 3, '0'), '-',
         LPAD(FLOOR(RAND(n*3) * 9000) + 1000, 4, '0')) AS phone,
  CONCAT(FLOOR(RAND(n*4) * 9999) + 1, ' ',
         ELT(1 + (n % 5), 'Oak','Pine','Maple','Cedar','Elm'), ' St') AS address_line,
  ELT(1 + (n % 10), 'New York','Los Angeles','Chicago','Houston','Phoenix','Philadelphia','San Antonio','San Diego','Dallas','San Jose') AS city,
  ELT(1 + (n % 10), 'NY','CA','IL','TX','AZ','PA','TX','CA','TX','CA') AS state,
  LPAD(FLOOR(RAND(n*5) * 99999), 5, '0') AS zip_code,
  DATE_ADD(
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND(n*6) * 365) DAY),
    INTERVAL FLOOR(RAND(n*7) * 24) HOUR
  ) AS created_at
FROM seq;

WITH RECURSIVE seq2(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq2 WHERE n < 5000
)
INSERT INTO fake_orders
(user_id, order_number, product_name, quantity, unit_price, status, created_at, updated_at, notes)
SELECT
  FLOOR(RAND(n) * 5000) + 1 AS user_id,
  CONCAT('ORD-', LPAD(n, 8, '0')) AS order_number,
  ELT(1 + (n % 10), 'Keyboard','Mouse','Monitor','Laptop','Headphones','Webcam','Desk','Chair','USB Hub','Microphone') AS product_name,
  FLOOR(RAND(n*2) * 5) + 1 AS quantity,
  ROUND(RAND(n*3) * 490 + 10, 2) AS unit_price,
  ELT(1 + (n % 5), 'pending','processing','shipped','delivered','cancelled') AS status,
  DATE_ADD(
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND(n*4) * 365) DAY),
    INTERVAL FLOOR(RAND(n*5) * 24) HOUR
  ) AS created_at,
  DATE_ADD(
    DATE_ADD(
      DATE_SUB(NOW(), INTERVAL FLOOR(RAND(n*4) * 365) DAY),
      INTERVAL FLOOR(RAND(n*5) * 24) HOUR
    ),
    INTERVAL FLOOR(RAND(n*6) * 72) HOUR
  ) AS updated_at,
  CONCAT('Note ', n) AS notes
FROM seq2;


