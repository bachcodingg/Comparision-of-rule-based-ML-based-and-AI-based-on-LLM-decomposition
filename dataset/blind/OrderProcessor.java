package com.example.demo;

import java.util.*;

public class OrderProcessor {

    private List<Order> orders;
    private Map<String, Double> discounts;
    private double taxRate;
    private String currency;
    private Date lastProcessed;
    private int orderCount;
    private double totalRevenue;

    public OrderProcessor() {
        this.orders = new ArrayList<>();
        this.discounts = new HashMap<>();
        this.taxRate = 0.10;
        this.currency = "USD";
        this.orderCount = 0;
        this.totalRevenue = 0.0;
    }

    /**
     * Add new order
     * Complexity: 3
     */
    public boolean addOrder(Order order) {
        if (order == null) {
            return false;
        }

        if (validateOrder(order)) {
            orders.add(order);
            orderCount++;
            return true;
        }

        return false;
    }

    /**
     * Process single order
     * Complexity: 4
     */
    public boolean processOrder(String orderId) {
        Order order = findOrder(orderId);

        if (order == null) {
            return false;
        }

        if (order.isProcessed()) {
            return false;
        }

        double amount = calculateOrderTotal(order);
        order.setTotal(amount);
        order.setProcessed(true);
        totalRevenue += amount;

        return true;
    }

    /**
     * Find order by ID
     * Complexity: 2
     */
    private Order findOrder(String orderId) {
        for (Order order : orders) {
            if (order.getId().equals(orderId)) {
                return order;
            }
        }
        return null;
    }

    /**
     * Validate order
     * Complexity: 3
     */
    private boolean validateOrder(Order order) {
        if (order.getItems() == null || order.getItems().isEmpty()) {
            return false;
        }

        if (order.getCustomerId() == null) {
            return false;
        }

        return order.getId() != null;
    }

    /**
     * Remove order
     * Complexity: 3
     */
    public boolean removeOrder(String orderId) {
        Order order = findOrder(orderId);

        if (order == null) {
            return false;
        }

        if (order.isProcessed()) {
            return false;
        }

        orders.remove(order);
        orderCount--;
        return true;
    }

    /**
     * Calculate order total
     * Complexity: 5
     */
    public double calculateOrderTotal(Order order) {
        double subtotal = 0.0;

        for (OrderItem item : order.getItems()) {
            subtotal += item.getPrice() * item.getQuantity();
        }

        double discount = getDiscount(order.getCustomerId());
        double afterDiscount = subtotal * (1 - discount);

        double tax = afterDiscount * taxRate;

        return afterDiscount + tax;
    }

    /**
     * Get customer discount
     * Complexity: 2
     */
    private double getDiscount(String customerId) {
        if (discounts.containsKey(customerId)) {
            return discounts.get(customerId);
        }
        return 0.0;
    }

    /**
     * Apply discount
     * Complexity: 3
     */
    public void applyDiscount(String customerId, double discountRate) {
        if (discountRate < 0 || discountRate > 1) {
            throw new IllegalArgumentException("Discount must be between 0 and 1");
        }

        if (customerId != null) {
            discounts.put(customerId, discountRate);
        }
    }

    /**
     * Calculate tax
     * Complexity: 2
     */
    public double calculateTax(double amount) {
        if (amount < 0) {
            return 0;
        }
        return amount * taxRate;
    }

    /**
     * Set tax rate
     * Complexity: 3
     */
    public void setTaxRate(double rate) {
        if (rate < 0 || rate > 0.5) {
            throw new IllegalArgumentException("Invalid tax rate");
        }

        this.taxRate = rate;
    }

    /**
     * Get total revenue
     * Complexity: 1
     */
    public double getTotalRevenue() {
        return totalRevenue;
    }

    /**
     * Get order count
     * Complexity: 1
     */
    public int getOrderCount() {
        return orderCount;
    }

    /**
     * Get average order value
     * Complexity: 2
     */
    public double getAverageOrderValue() {
        if (orderCount == 0) {
            return 0.0;
        }
        return totalRevenue / orderCount;
    }

    /**
     * Get pending orders
     * Complexity: 3
     */
    public List<Order> getPendingOrders() {
        List<Order> pending = new ArrayList<>();

        for (Order order : orders) {
            if (!order.isProcessed()) {
                pending.add(order);
            }
        }

        return pending;
    }

    /**
     * Generate summary report
     * Complexity: 5
     */
    public String generateReport() {
        StringBuilder report = new StringBuilder();
        report.append("Order Processing Summary\n");
        report.append("=======================\n");
        report.append("Total Orders: ").append(orderCount).append("\n");
        report.append("Total Revenue: ").append(currency).append(" ").append(totalRevenue).append("\n");

        if (orderCount > 0) {
            report.append("Average Order: ").append(currency).append(" ")
                  .append(String.format("%.2f", getAverageOrderValue())).append("\n");
        }

        int pending = getPendingOrders().size();
        report.append("Pending Orders: ").append(pending).append("\n");

        return report.toString();
    }
}

// Supporting classes
class Order {
    private String id;
    private String customerId;
    private List<OrderItem> items;
    private double total;
    private boolean processed;

    public String getId() { return id; }
    public String getCustomerId() { return customerId; }
    public List<OrderItem> getItems() { return items; }
    public double getTotal() { return total; }
    public boolean isProcessed() { return processed; }
    public void setTotal(double total) { this.total = total; }
    public void setProcessed(boolean processed) { this.processed = processed; }
}

class OrderItem {
    private String productId;
    private double price;
    private int quantity;

    public double getPrice() { return price; }
    public int getQuantity() { return quantity; }
}
