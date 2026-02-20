package com.example.demo;

import java.util.*;
import java.io.*;
import java.text.*;
import java.net.*;
import java.sql.*;

/**
 * CRITICAL SEVERITY EXAMPLE
 * 
 * Massive God Class that urgently needs decomposition.
 * Handles way too many responsibilities.
 * 
 * Metrics:
 * - LOC: ~1200 lines (CRITICAL: >1000)
 * - NOM: 52 methods (CRITICAL: >40)
 * - WMC: 145 complexity (CRITICAL: >100)
 * - CBO: 22 dependencies (CRITICAL: >20)
 * - LCOM: 0.92 (CRITICAL: >0.9) - almost no cohesion
 * 
 * Expected Result: CRITICAL priority, URGENT refactoring required
 */
public class EnterpriseResourcePlanner {

    // User Management Fields
    private Map<String, User> users;
    private Map<String, String> passwords;
    private Map<String, List<String>> userRoles;
    private Map<String, Date> lastLogin;
    private Set<String> activeSession;
    private String adminEmail;
    
    // Customer Management Fields
    private Map<String, Customer> customers;
    private Map<String, List<String>> customerOrders;
    private Map<String, Double> customerBalances;
    private Map<String, String> customerNotes;
    
    // Product Management Fields
    private Map<String, Product> products;
    private Map<String, Integer> inventory;
    private Map<String, Double> prices;
    private Map<String, String> productDescriptions;
    private List<String> categories;
    private Map<String, List<String>> productsByCategory;
    
    // Order Management Fields
    private Map<String, Order> orders;
    private Queue<String> pendingOrders;
    private Map<String, String> orderStatuses;
    private Map<String, Double> orderTotals;
    private Map<String, Date> deliveryDates;
    
    // Supplier Management Fields
    private Map<String, Supplier> suppliers;
    private Map<String, List<String>> supplierProducts;
    private Map<String, Double> supplierPayments;
    private List<PurchaseOrder> purchaseOrders;
    
    // Invoice Management Fields
    private Map<String, Invoice> invoices;
    private Map<String, Boolean> invoicesPaid;
    private Map<String, Date> invoiceDueDates;
    private double totalOutstanding;
    
    // Payment Processing Fields
    private Map<String, PaymentMethod> paymentMethods;
    private List<Transaction> transactions;
    private Map<String, List<String>> customerTransactions;
    
    // Shipping Management Fields
    private Map<String, ShippingInfo> shippingInfo;
    private Map<String, String> trackingNumbers;
    private Map<String, String> carriers;
    
    // Reporting Fields
    private Map<String, Integer> salesByProduct;
    private Map<String, Double> revenueByMonth;
    private List<String> reportCache;
    
    // Email/Notification Fields
    private String smtpServer;
    private int smtpPort;
    private Queue<EmailMessage> emailQueue;
    private List<String> notificationHistory;
    
    // System Configuration
    private Properties systemConfig;
    private String dbConnectionString;
    private Connection dbConnection;
    private boolean autoBackupEnabled;
    private int sessionTimeout;
    
    public EnterpriseResourcePlanner() {
        // Initialize ALL the maps and lists (30+ collections!)
        this.users = new HashMap<>();
        this.passwords = new HashMap<>();
        this.userRoles = new HashMap<>();
        this.lastLogin = new HashMap<>();
        this.activeSession = new HashSet<>();
        this.customers = new HashMap<>();
        this.customerOrders = new HashMap<>();
        this.customerBalances = new HashMap<>();
        this.customerNotes = new HashMap<>();
        this.products = new HashMap<>();
        this.inventory = new HashMap<>();
        this.prices = new HashMap<>();
        this.productDescriptions = new HashMap<>();
        this.categories = new ArrayList<>();
        this.productsByCategory = new HashMap<>();
        this.orders = new HashMap<>();
        this.pendingOrders = new LinkedList<>();
        this.orderStatuses = new HashMap<>();
        this.orderTotals = new HashMap<>();
        this.deliveryDates = new HashMap<>();
        this.suppliers = new HashMap<>();
        this.supplierProducts = new HashMap<>();
        this.supplierPayments = new HashMap<>();
        this.purchaseOrders = new ArrayList<>();
        this.invoices = new HashMap<>();
        this.invoicesPaid = new HashMap<>();
        this.invoiceDueDates = new HashMap<>();
        this.paymentMethods = new HashMap<>();
        this.transactions = new ArrayList<>();
        this.customerTransactions = new HashMap<>();
        this.shippingInfo = new HashMap<>();
        this.trackingNumbers = new HashMap<>();
        this.carriers = new HashMap<>();
        this.salesByProduct = new HashMap<>();
        this.revenueByMonth = new HashMap<>();
        this.reportCache = new ArrayList<>();
        this.emailQueue = new LinkedList<>();
        this.notificationHistory = new ArrayList<>();
        this.systemConfig = new Properties();
        this.totalOutstanding = 0.0;
        this.autoBackupEnabled = true;
        this.sessionTimeout = 3600;
    }
    
    // ===== USER MANAGEMENT (10 methods, complexity 35) =====
    
    /**
     * Register new user - Complexity: 5
     */
    public boolean registerUser(String username, String password, String email) {
        if (username == null || password == null || email == null) {
            return false;
        }
        
        if (users.containsKey(username)) {
            return false;
        }
        
        if (password.length() < 8) {
            return false;
        }
        
        User user = new User(username, email);
        users.put(username, user);
        passwords.put(username, hashPassword(password));
        userRoles.put(username, new ArrayList<>());
        
        sendWelcomeEmail(email, username);
        
        return true;
    }
    
    /**
     * User login - Complexity: 6
     */
    public boolean login(String username, String password) {
        if (!users.containsKey(username)) {
            return false;
        }
        
        if (!passwords.get(username).equals(hashPassword(password))) {
            return false;
        }
        
        String sessionId = UUID.randomUUID().toString();
        activeSession.add(sessionId);
        lastLogin.put(username, new Date());
        
        logUserActivity(username, "LOGIN");
        
        if (isAdmin(username)) {
            sendAdminNotification(username + " logged in");
        }
        
        return true;
    }
    
    /**
     * User logout - Complexity: 3
     */
    public void logout(String sessionId) {
        if (activeSession.contains(sessionId)) {
            activeSession.remove(sessionId);
            logUserActivity(getUserBySession(sessionId), "LOGOUT");
        }
    }
    
    /**
     * Change password - Complexity: 4
     */
    public boolean changePassword(String username, String oldPassword, String newPassword) {
        if (!users.containsKey(username)) {
            return false;
        }
        
        if (!passwords.get(username).equals(hashPassword(oldPassword))) {
            return false;
        }
        
        if (newPassword.length() < 8) {
            return false;
        }
        
        passwords.put(username, hashPassword(newPassword));
        sendPasswordChangeEmail(users.get(username).getEmail());
        
        return true;
    }
    
    /**
     * Assign role - Complexity: 3
     */
    public boolean assignRole(String username, String role) {
        if (!users.containsKey(username)) {
            return false;
        }
        
        List<String> roles = userRoles.get(username);
        if (!roles.contains(role)) {
            roles.add(role);
            return true;
        }
        
        return false;
    }
    
    /**
     * Check permission - Complexity: 4
     */
    public boolean hasPermission(String username, String permission) {
        if (!users.containsKey(username)) {
            return false;
        }
        
        List<String> roles = userRoles.get(username);
        
        for (String role : roles) {
            if (getRolePermissions(role).contains(permission)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * Hash password - Complexity: 2
     */
    private String hashPassword(String password) {
        return Integer.toString(password.hashCode());
    }
    
    /**
     * Check if admin - Complexity: 2
     */
    private boolean isAdmin(String username) {
        return userRoles.get(username).contains("ADMIN");
    }
    
    /**
     * Get user by session - Complexity: 3
     */
    private String getUserBySession(String sessionId) {
        // Simplified implementation
        return "user";
    }
    
    /**
     * Get role permissions - Complexity: 3
     */
    private List<String> getRolePermissions(String role) {
        List<String> permissions = new ArrayList<>();
        if (role.equals("ADMIN")) {
            permissions.add("ALL");
        }
        return permissions;
    }
    
    // ===== CUSTOMER MANAGEMENT (8 methods, complexity 28) =====
    
    /**
     * Add customer - Complexity: 4
     */
    public boolean addCustomer(Customer customer) {
        if (customer == null || customer.getId() == null) {
            return false;
        }
        
        if (customers.containsKey(customer.getId())) {
            return false;
        }
        
        customers.put(customer.getId(), customer);
        customerOrders.put(customer.getId(), new ArrayList<>());
        customerBalances.put(customer.getId(), 0.0);
        customerTransactions.put(customer.getId(), new ArrayList<>());
        
        sendWelcomeEmail(customer.getEmail(), customer.getName());
        
        return true;
    }
    
    /**
     * Update customer - Complexity: 3
     */
    public boolean updateCustomer(String customerId, Customer updated) {
        if (!customers.containsKey(customerId)) {
            return false;
        }
        
        customers.put(customerId, updated);
        logCustomerActivity(customerId, "UPDATE");
        
        return true;
    }
    
    /**
     * Get customer balance - Complexity: 2
     */
    public double getCustomerBalance(String customerId) {
        return customerBalances.getOrDefault(customerId, 0.0);
    }
    
    /**
     * Update customer balance - Complexity: 3
     */
    public void updateCustomerBalance(String customerId, double amount) {
        if (customers.containsKey(customerId)) {
            double current = customerBalances.get(customerId);
            customerBalances.put(customerId, current + amount);
            logCustomerActivity(customerId, "BALANCE_UPDATE");
        }
    }
    
    /**
     * Add customer note - Complexity: 3
     */
    public void addCustomerNote(String customerId, String note) {
        if (customers.containsKey(customerId)) {
            String existing = customerNotes.getOrDefault(customerId, "");
            customerNotes.put(customerId, existing + "\n" + new Date() + ": " + note);
        }
    }
    
    /**
     * Get customer orders - Complexity: 2
     */
    public List<String> getCustomerOrders(String customerId) {
        return customerOrders.getOrDefault(customerId, new ArrayList<>());
    }
    
    /**
     * Send customer notification - Complexity: 4
     */
    public void sendCustomerNotification(String customerId, String message) {
        if (customers.containsKey(customerId)) {
            Customer customer = customers.get(customerId);
            EmailMessage email = new EmailMessage();
            email.setTo(customer.getEmail());
            email.setSubject("Notification");
            email.setBody(message);
            emailQueue.add(email);
        }
    }
    
    /**
     * Log customer activity - Complexity: 3
     */
    private void logCustomerActivity(String customerId, String activity) {
        String log = new Date() + " - " + customerId + " - " + activity;
        notificationHistory.add(log);
    }
    
    // ===== PRODUCT MANAGEMENT (9 methods, complexity 31) =====
    
    /**
     * Add product - Complexity: 5
     */
    public boolean addProduct(Product product) {
        if (product == null || product.getId() == null) {
            return false;
        }
        
        if (products.containsKey(product.getId())) {
            return false;
        }
        
        products.put(product.getId(), product);
        inventory.put(product.getId(), 0);
        prices.put(product.getId(), product.getPrice());
        productDescriptions.put(product.getId(), product.getDescription());
        
        String category = product.getCategory();
        if (!categories.contains(category)) {
            categories.add(category);
            productsByCategory.put(category, new ArrayList<>());
        }
        productsByCategory.get(category).add(product.getId());
        
        return true;
    }
    
    /**
     * Update product - Complexity: 4
     */
    public boolean updateProduct(String productId, Product updated) {
        if (!products.containsKey(productId)) {
            return false;
        }
        
        double oldPrice = prices.get(productId);
        double newPrice = updated.getPrice();
        
        products.put(productId, updated);
        prices.put(productId, newPrice);
        productDescriptions.put(productId, updated.getDescription());
        
        if (oldPrice != newPrice) {
            notifyPriceChange(productId, oldPrice, newPrice);
        }
        
        return true;
    }
    
    /**
     * Delete product - Complexity: 4
     */
    public boolean deleteProduct(String productId) {
        if (!products.containsKey(productId)) {
            return false;
        }
        
        Product product = products.get(productId);
        String category = product.getCategory();
        
        products.remove(productId);
        inventory.remove(productId);
        prices.remove(productId);
        productDescriptions.remove(productId);
        
        if (productsByCategory.containsKey(category)) {
            productsByCategory.get(category).remove(productId);
        }
        
        return true;
    }
    
    /**
     * Search products - Complexity: 4
     */
    public List<Product> searchProducts(String keyword) {
        List<Product> results = new ArrayList<>();
        
        if (keyword == null || keyword.isEmpty()) {
            return results;
        }
        
        keyword = keyword.toLowerCase();
        
        for (Product product : products.values()) {
            if (product.getName().toLowerCase().contains(keyword) ||
                product.getDescription().toLowerCase().contains(keyword) ||
                product.getCategory().toLowerCase().contains(keyword)) {
                results.add(product);
            }
        }
        
        return results;
    }
    
    /**
     * Get products by category - Complexity: 2
     */
    public List<Product> getProductsByCategory(String category) {
        List<Product> results = new ArrayList<>();
        List<String> productIds = productsByCategory.getOrDefault(category, new ArrayList<>());
        
        for (String id : productIds) {
            results.add(products.get(id));
        }
        
        return results;
    }
    
    /**
     * Update inventory - Complexity: 3
     */
    public boolean updateInventory(String productId, int quantity) {
        if (!inventory.containsKey(productId)) {
            return false;
        }
        
        inventory.put(productId, inventory.get(productId) + quantity);
        
        if (inventory.get(productId) < 10) {
            triggerReorderAlert(productId);
        }
        
        return true;
    }
    
    /**
     * Check stock - Complexity: 3
     */
    public boolean isInStock(String productId, int requestedQty) {
        if (!inventory.containsKey(productId)) {
            return false;
        }
        
        return inventory.get(productId) >= requestedQty;
    }
    
    /**
     * Get low stock products - Complexity: 3
     */
    public List<Product> getLowStockProducts() {
        List<Product> lowStock = new ArrayList<>();
        
        for (Map.Entry<String, Integer> entry : inventory.entrySet()) {
            if (entry.getValue() < 10) {
                lowStock.add(products.get(entry.getKey()));
            }
        }
        
        return lowStock;
    }
    
    /**
     * Notify price change - Complexity: 3
     */
    private void notifyPriceChange(String productId, double oldPrice, double newPrice) {
        String message = "Price changed for " + products.get(productId).getName();
        notificationHistory.add(new Date() + ": " + message);
    }
    
    // ===== ORDER MANAGEMENT (10 methods, complexity 38) =====
    
    /**
     * Create order - Complexity: 6
     */
    public String createOrder(String customerId, List<OrderItem> items) {
        if (!customers.containsKey(customerId) || items == null || items.isEmpty()) {
            return null;
        }
        
        for (OrderItem item : items) {
            if (!isInStock(item.getProductId(), item.getQuantity())) {
                return null;
            }
        }
        
        String orderId = UUID.randomUUID().toString();
        Order order = new Order(orderId, customerId, items);
        orders.put(orderId, order);
        pendingOrders.add(orderId);
        orderStatuses.put(orderId, "PENDING");
        
        double total = calculateOrderTotal(orderId);
        orderTotals.put(orderId, total);
        
        customerOrders.get(customerId).add(orderId);
        
        for (OrderItem item : items) {
            updateInventory(item.getProductId(), -item.getQuantity());
        }
        
        sendOrderConfirmation(customerId, orderId);
        
        return orderId;
    }
    
    /**
     * Calculate order total - Complexity: 4
     */
    private double calculateOrderTotal(String orderId) {
        Order order = orders.get(orderId);
        double total = 0.0;
        
        for (OrderItem item : order.getItems()) {
            double price = prices.get(item.getProductId());
            total += price * item.getQuantity();
        }
        
        double tax = total * 0.10;
        return total + tax;
    }
    
    /**
     * Process order - Complexity: 5
     */
    public boolean processOrder(String orderId) {
        if (!orders.containsKey(orderId)) {
            return false;
        }
        
        if (!orderStatuses.get(orderId).equals("PENDING")) {
            return false;
        }
        
        orderStatuses.put(orderId, "PROCESSING");
        
        Calendar cal = Calendar.getInstance();
        cal.add(Calendar.DAY_OF_MONTH, 7);
        deliveryDates.put(orderId, cal.getTime());
        
        String customerId = orders.get(orderId).getCustomerId();
        sendOrderUpdate(customerId, orderId, "Your order is being processed");
        
        return true;
    }
    
    /**
     * Ship order - Complexity: 5
     */
    public boolean shipOrder(String orderId, String carrier, String trackingNum) {
        if (!orders.containsKey(orderId)) {
            return false;
        }
        
        if (!orderStatuses.get(orderId).equals("PROCESSING")) {
            return false;
        }
        
        orderStatuses.put(orderId, "SHIPPED");
        carriers.put(orderId, carrier);
        trackingNumbers.put(orderId, trackingNum);
        
        String customerId = orders.get(orderId).getCustomerId();
        sendShippingNotification(customerId, orderId, trackingNum);
        
        return true;
    }
    
    /**
     * Complete order - Complexity: 4
     */
    public boolean completeOrder(String orderId) {
        if (!orders.containsKey(orderId)) {
            return false;
        }
        
        orderStatuses.put(orderId, "COMPLETED");
        pendingOrders.remove(orderId);
        
        String customerId = orders.get(orderId).getCustomerId();
        updateCustomerBalance(customerId, -orderTotals.get(orderId));
        
        recordSale(orderId);
        
        return true;
    }
    
    /**
     * Cancel order - Complexity: 5
     */
    public boolean cancelOrder(String orderId) {
        if (!orders.containsKey(orderId)) {
            return false;
        }
        
        String status = orderStatuses.get(orderId);
        if (status.equals("SHIPPED") || status.equals("COMPLETED")) {
            return false;
        }
        
        Order order = orders.get(orderId);
        for (OrderItem item : order.getItems()) {
            updateInventory(item.getProductId(), item.getQuantity());
        }
        
        orderStatuses.put(orderId, "CANCELLED");
        
        String customerId = order.getCustomerId();
        sendOrderCancellation(customerId, orderId);
        
        return true;
    }
    
    /**
     * Get order status - Complexity: 2
     */
    public String getOrderStatus(String orderId) {
        return orderStatuses.getOrDefault(orderId, "UNKNOWN");
    }
    
    /**
     * Get tracking info - Complexity: 3
     */
    public String getTrackingInfo(String orderId) {
        if (!trackingNumbers.containsKey(orderId)) {
            return null;
        }
        
        String carrier = carriers.get(orderId);
        String tracking = trackingNumbers.get(orderId);
        
        return carrier + ": " + tracking;
    }
    
    /**
     * Record sale - Complexity: 3
     */
    private void recordSale(String orderId) {
        Order order = orders.get(orderId);
        
        for (OrderItem item : order.getItems()) {
            String productId = item.getProductId();
            int currentSales = salesByProduct.getOrDefault(productId, 0);
            salesByProduct.put(productId, currentSales + item.getQuantity());
        }
    }
    
    /**
     * Get pending orders - Complexity: 1
     */
    public Queue<String> getPendingOrders() {
        return new LinkedList<>(pendingOrders);
    }
    
    // ===== INVOICE MANAGEMENT (5 methods, complexity 18) =====
    
    /**
     * Generate invoice - Complexity: 5
     */
    public String generateInvoice(String orderId) {
        if (!orders.containsKey(orderId)) {
            return null;
        }
        
        String invoiceId = "INV-" + orderId;
        Invoice invoice = new Invoice();
        invoice.setId(invoiceId);
        invoice.setOrderId(orderId);
        invoice.setAmount(orderTotals.get(orderId));
        invoice.setDate(new Date());
        
        Calendar cal = Calendar.getInstance();
        cal.add(Calendar.DAY_OF_MONTH, 30);
        invoice.setDueDate(cal.getTime());
        
        invoices.put(invoiceId, invoice);
        invoicesPaid.put(invoiceId, false);
        invoiceDueDates.put(invoiceId, cal.getTime());
        totalOutstanding += invoice.getAmount();
        
        String customerId = orders.get(orderId).getCustomerId();
        sendInvoiceEmail(customerId, invoiceId);
        
        return invoiceId;
    }
    
    /**
     * Process payment - Complexity: 5
     */
    public boolean processPayment(String invoiceId, String paymentMethodId, double amount) {
        if (!invoices.containsKey(invoiceId)) {
            return false;
        }
        
        if (invoicesPaid.get(invoiceId)) {
            return false;
        }
        
        Invoice invoice = invoices.get(invoiceId);
        
        if (amount < invoice.getAmount()) {
            return false;
        }
        
        Transaction trans = new Transaction();
        trans.setInvoiceId(invoiceId);
        trans.setAmount(amount);
        trans.setDate(new Date());
        transactions.add(trans);
        
        invoicesPaid.put(invoiceId, true);
        totalOutstanding -= invoice.getAmount();
        
        String orderId = invoice.getOrderId();
        String customerId = orders.get(orderId).getCustomerId();
        sendPaymentConfirmation(customerId, invoiceId);
        
        return true;
    }
    
    /**
     * Check overdue invoices - Complexity: 4
     */
    public List<String> getOverdueInvoices() {
        List<String> overdue = new ArrayList<>();
        Date now = new Date();
        
        for (Map.Entry<String, Date> entry : invoiceDueDates.entrySet()) {
            String invoiceId = entry.getKey();
            
            if (!invoicesPaid.get(invoiceId) && entry.getValue().before(now)) {
                overdue.add(invoiceId);
            }
        }
        
        return overdue;
    }
    
    /**
     * Send payment reminder - Complexity: 3
     */
    public void sendPaymentReminder(String invoiceId) {
        if (invoices.containsKey(invoiceId) && !invoicesPaid.get(invoiceId)) {
            Invoice invoice = invoices.get(invoiceId);
            String orderId = invoice.getOrderId();
            String customerId = orders.get(orderId).getCustomerId();
            sendReminderEmail(customerId, invoiceId);
        }
    }
    
    /**
     * Get total outstanding - Complexity: 1
     */
    public double getTotalOutstanding() {
        return totalOutstanding;
    }
    
    // ===== EMAIL/NOTIFICATION (10 methods, complexity 25) =====
    
    private void sendWelcomeEmail(String email, String name) {
        EmailMessage msg = new EmailMessage();
        msg.setTo(email);
        msg.setSubject("Welcome!");
        msg.setBody("Welcome " + name);
        emailQueue.add(msg);
    }
    
    private void sendPasswordChangeEmail(String email) {
        EmailMessage msg = new EmailMessage();
        msg.setTo(email);
        msg.setSubject("Password Changed");
        msg.setBody("Your password was changed");
        emailQueue.add(msg);
    }
    
    private void sendOrderConfirmation(String customerId, String orderId) {
        Customer customer = customers.get(customerId);
        EmailMessage msg = new EmailMessage();
        msg.setTo(customer.getEmail());
        msg.setSubject("Order Confirmation");
        msg.setBody("Order " + orderId + " confirmed");
        emailQueue.add(msg);
    }
    
    private void sendOrderUpdate(String customerId, String orderId, String message) {
        Customer customer = customers.get(customerId);
        EmailMessage msg = new EmailMessage();
        msg.setTo(customer.getEmail());
        msg.setSubject("Order Update");
        msg.setBody(message);
        emailQueue.add(msg);
    }
    
    private void sendShippingNotification(String customerId, String orderId, String tracking) {
        Customer customer = customers.get(customerId);
        EmailMessage msg = new EmailMessage();
        msg.setTo(customer.getEmail());
        msg.setSubject("Order Shipped");
        msg.setBody("Tracking: " + tracking);
        emailQueue.add(msg);
    }
    
    private void sendOrderCancellation(String customerId, String orderId) {
        Customer customer = customers.get(customerId);
        EmailMessage msg = new EmailMessage();
        msg.setTo(customer.getEmail());
        msg.setSubject("Order Cancelled");
        msg.setBody("Order " + orderId + " cancelled");
        emailQueue.add(msg);
    }
    
    private void sendInvoiceEmail(String customerId, String invoiceId) {
        Customer customer = customers.get(customerId);
        EmailMessage msg = new EmailMessage();
        msg.setTo(customer.getEmail());
        msg.setSubject("Invoice");
        msg.setBody("Invoice " + invoiceId);
        emailQueue.add(msg);
    }
    
    private void sendPaymentConfirmation(String customerId, String invoiceId) {
        Customer customer = customers.get(customerId);
        EmailMessage msg = new EmailMessage();
        msg.setTo(customer.getEmail());
        msg.setSubject("Payment Confirmed");
        msg.setBody("Payment for " + invoiceId + " received");
        emailQueue.add(msg);
    }
    
    private void sendReminderEmail(String customerId, String invoiceId) {
        Customer customer = customers.get(customerId);
        EmailMessage msg = new EmailMessage();
        msg.setTo(customer.getEmail());
        msg.setSubject("Payment Reminder");
        msg.setBody("Invoice " + invoiceId + " is overdue");
        emailQueue.add(msg);
    }
    
    private void sendAdminNotification(String message) {
        EmailMessage msg = new EmailMessage();
        msg.setTo(adminEmail);
        msg.setSubject("Admin Alert");
        msg.setBody(message);
        emailQueue.add(msg);
    }
    
    private void triggerReorderAlert(String productId) {
        // Alert for low stock
    }
    
    private void logUserActivity(String username, String activity) {
        // Log activity
    }
}

// Supporting Classes (abbreviated)
class User {
    private String username;
    private String email;
    public User(String username, String email) {
        this.username = username;
        this.email = email;
    }
    public String getEmail() { return email; }
}

class Customer {
    private String id;
    private String name;
    private String email;
    public String getId() { return id; }
    public String getName() { return name; }
    public String getEmail() { return email; }
}

class Product {
    private String id;
    private String name;
    private String category;
    private String description;
    private double price;
    public String getId() { return id; }
    public String getName() { return name; }
    public String getCategory() { return category; }
    public String getDescription() { return description; }
    public double getPrice() { return price; }
}

class Order {
    private String id;
    private String customerId;
    private List<OrderItem> items;
    public Order(String id, String customerId, List<OrderItem> items) {
        this.id = id;
        this.customerId = customerId;
        this.items = items;
    }
    public String getId() { return id; }
    public String getCustomerId() { return customerId; }
    public List<OrderItem> getItems() { return items; }
}

class OrderItem {
    private String productId;
    private int quantity;
    public String getProductId() { return productId; }
    public int getQuantity() { return quantity; }
}

class Supplier {
    private String id;
    private String name;
    public String getId() { return id; }
}

class PurchaseOrder {}
class Invoice {
    private String id;
    private String orderId;
    private double amount;
    private Date date;
    private Date dueDate;
    public void setId(String id) { this.id = id; }
    public void setOrderId(String orderId) { this.orderId = orderId; }
    public void setAmount(double amount) { this.amount = amount; }
    public void setDate(Date date) { this.date = date; }
    public void setDueDate(Date dueDate) { this.dueDate = dueDate; }
    public String getOrderId() { return orderId; }
    public double getAmount() { return amount; }
}

class Transaction {
    private String invoiceId;
    private double amount;
    private Date date;
    public void setInvoiceId(String id) { this.invoiceId = id; }
    public void setAmount(double amount) { this.amount = amount; }
    public void setDate(Date date) { this.date = date; }
}

class PaymentMethod {}
class ShippingInfo {}
class EmailMessage {
    private String to;
    private String subject;
    private String body;
    public void setTo(String to) { this.to = to; }
    public void setSubject(String subject) { this.subject = subject; }
    public void setBody(String body) { this.body = body; }
}

/**
 * METRICS SUMMARY:
 * ================
 * LOC: 1200+ lines (CRITICAL)
 * NOM: 52 methods (CRITICAL)
 * WMC: 145 complexity (CRITICAL)
 * CBO: 22 (Map, List, Set, Queue, Date, Calendar, UUID, Properties, Connection, etc.) (CRITICAL)
 * LCOM: 0.92 (CRITICAL - almost no cohesion, completely unrelated methods)
 * 
 * SEVERITY LEVELS:
 * LOC:  1200 → CRITICAL (4)
 * NOM:  52 → CRITICAL (4)
 * WMC:  145 → CRITICAL (4)
 * CBO:  22 → CRITICAL (4)
 * LCOM: 0.92 → CRITICAL (4)
 * 
 * PRIORITY SCORE:
 * = (4 × 0.25) + (4 × 0.15) + (4 × 0.25) + (4 × 0.20) + (4 × 0.15)
 * = 1.00 + 0.60 + 1.00 + 0.80 + 0.60
 * = 4.00 (CRITICAL PRIORITY - MAXIMUM!)
 * 
 * Result: 🔴 URGENT REFACTORING REQUIRED!
 * 
 * This class does EVERYTHING:
 * - User management
 * - Customer management
 * - Product catalog
 * - Inventory tracking
 * - Order processing
 * - Invoicing
 * - Payment processing
 * - Shipping management
 * - Email notifications
 * - Reporting
 * 
 * Suggested decomposition into 10+ classes:
 * 1. UserManager
 * 2. CustomerManager
 * 3. ProductCatalog
 * 4. InventoryManager
 * 5. OrderProcessor
 * 6. InvoiceManager
 * 7. PaymentProcessor
 * 8. ShippingManager
 * 9. EmailService
 * 10. ReportGenerator
 * 
 * This is a textbook example of a God Class!
 */
