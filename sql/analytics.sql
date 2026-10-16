-- All values in this project are synthetic and generated for education.

-- Monthly event count, synthetic ticket sales, and derived synthetic revenue.
SELECT month_label,
       COUNT(*) AS event_count,
       SUM(tickets_sold) AS tickets_sold,
       ROUND(SUM(revenue), 2) AS synthetic_revenue
FROM events
GROUP BY month_label
ORDER BY month_label;

-- Compare event activity and occupancy by city.
SELECT city,
       COUNT(*) AS event_count,
       ROUND(AVG(occupancy_rate) * 100, 1) AS average_occupancy_percent
FROM events
GROUP BY city
ORDER BY event_count DESC;

-- Explore event and ticket totals by genre.
SELECT genre,
       COUNT(*) AS event_count,
       SUM(tickets_sold) AS tickets_sold
FROM events
GROUP BY genre
ORDER BY event_count DESC;