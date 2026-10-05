-- Task 3: sql/reports.sql

USE mamaearth_analytics;

-- ============================================================
-- (a) Order totals                                    
-- Output:
-- total_orders | total_revenue | avg_order_value
-- 180          | 99860.20      | 554.78
-- ============================================================
SELECT COUNT(*) AS total_orders,
       ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100)), 2) AS total_revenue,
       ROUND(AVG(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100)), 2) AS avg_order_value
FROM orders o
JOIN products p ON o.product_id = p.product_id;

-- ============================================================
-- (b) COUNT(*) vs COUNT(column)                       
-- Output:
-- total_rows | rated_rows | unrated_diff
-- 180        | 165        | 15
-- ============================================================
SELECT COUNT(*)                 AS total_rows,
       COUNT(rating)            AS rated_rows,
       COUNT(*) - COUNT(rating) AS unrated_diff
FROM orders;

-- ============================================================
-- (c) LEFT JOIN zero-match + NOT IN cross-check       
-- Output (both queries): C045 | Vihaan
-- ============================================================
-- (c1) LEFT JOIN approach
SELECT c.customer_id, c.name
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0;

-- (c2) Independent NOT IN confirmation
SELECT customer_id, name
FROM customers
WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM orders);

-- ============================================================
-- (d) GROUP BY + HAVING: return rate by city          
-- Output:
-- city      | total_orders | returned_orders | return_rate_pct
-- Jaipur    | 19           | 8               | 42.1
-- Lucknow   | 49           | 15              | 30.6
-- Bangalore | 33           | 8               | 24.2
-- ============================================================
SELECT c.city,
       COUNT(*)                                AS total_orders,
       SUM(o.returned)                         AS returned_orders,
       ROUND(100.0 * SUM(o.returned) / COUNT(*), 1) AS return_rate_pct
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;

-- ============================================================
-- (e) Ranking with ORDER BY + LIMIT/OFFSET            
-- Tie-break on customer_id ASC: without it, customers with equal
-- total_spend can swap places between runs, which makes LIMIT/OFFSET
-- pages inconsistent and non-reproducible.
-- Output (top 5):
-- C043 Reyansh 12920.00 | C026 Isha 8371.60 | C008 Meera 4564.60
-- C011 Arjun   4111.00  | C042 Sanya 3785.00
-- ============================================================
-- (e1) Top 5
SELECT c.customer_id, c.name,
       ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100)), 2) AS total_spend
FROM orders o
JOIN products  p ON o.product_id  = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;

-- (e2) Ranks 3-5 (must equal last three rows of e1)
-- Output: C008 Meera 4564.60 | C011 Arjun 4111.00 | C042 Sanya 3785.00
SELECT c.customer_id, c.name,
       ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100)), 2) AS total_spend
FROM orders o
JOIN products  p ON o.product_id  = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;

-- ============================================================
-- (f) Three-table JOIN, revenue by category           
-- Output:
-- Haircare     | 54 | 44956.10
-- Skincare     | 60 | 27346.00
-- Babycare     | 30 | 16805.00
-- PersonalCare | 36 | 10753.10
-- ============================================================
SELECT p.category,
       COUNT(*) AS order_count,
       ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100)), 2) AS category_revenue
FROM orders o
JOIN products  p ON o.product_id  = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- ============================================================
-- (g) LIKE pattern match                              
-- Output: 10 rows (Aarav, Aditi, Ananya, Arjun, Aryan,
--         Anika, Aditya, Aisha, Aria, Ayaan)
-- ============================================================
SELECT customer_id, name
FROM customers
WHERE name LIKE 'A%';

-- ============================================================
-- (h) DISTINCT                                        
-- Output: Ad, Organic, Referral, Social (4 rows)
-- ============================================================
SELECT DISTINCT acquisition_source
FROM customers
ORDER BY acquisition_source;

-- ============================================================
-- (i) ALTER TABLE + UPDATE with CASE                 
-- Output: Gold | 28, Silver | 17
-- ============================================================
-- Note: re-running this block fails at ALTER once the column exists.
-- Re-run schema.sql + seed_data.sql first for a clean state.
ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);

SET SQL_SAFE_UPDATES = 0;   -- MySQL Workbench blocks UPDATE without WHERE
UPDATE customers
SET loyalty_tier = CASE WHEN city_tier = 1 THEN 'Gold' ELSE 'Silver' END;
SET SQL_SAFE_UPDATES = 1;

SELECT loyalty_tier, COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier;
