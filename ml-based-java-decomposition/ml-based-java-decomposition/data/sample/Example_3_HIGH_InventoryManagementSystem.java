package com.example.demo;

import java.util.*;
import java.io.*;
import java.text.*;

/**
 * HIGH SEVERITY EXAMPLE
 * 
 * Large class with significant complexity.
 * Should be refactored when time permits.
 * 
 * Metrics:
 * - LOC: ~700 lines (HIGH: 501-1000)
 * - NOM: 28 methods (HIGH: 21-40)
 * - WMC: 85 complexity (HIGH: 61-100)
 * - CBO: 15 dependencies (HIGH: 11-20)
 * - LCOM: 0.75 (HIGH: 0.71-0.9) - low cohesion
 * 
 * Expected Result: HIGH priority, refactor when possible
 */
public class InventoryManagementSystem {

    // Product data
    private Map<String, Product> products;
    private Map<String, Integer> stock;
    private Map<String, Double> prices;
    private List<String> categories;
    
    // Supplier data
    private Map<String, Supplier> suppliers;
    private Map<String, List<String>> supplierProducts;
    
    // Order data
    private List<PurchaseOrder> purchaseOrders;
    private Queue<String> pendingOrders;
    private Map<String, Date> deliveryDates;
    
    // Reporting data
    private Map<String, Integer> salesHistory;
    private List<Transaction> transactions;
    private double totalRevenue;
    private Date lastReportDate;
    
    // System settings
    private double lowStockThreshold;
    private String warehouseLocation;
    private boolean autoReorderEnabled;
    
    public InventoryManagementSystem() {
        this.products = new HashMap<>();
        this.stock = new HashMap<>();
        this.prices = new HashMap<>();
        this.categories = new ArrayList<>();
        this.suppliers = new HashMap<>();
        this.supplierProducts = new HashMap<>();
        this.purchaseOrders = new ArrayList<>();
        this.pendingOrders = new LinkedList<>();
        this.deliveryDates = new HashMap<>();
        this.salesHistory = new HashMap<>();
        this.transactions = new ArrayList<>();
        this.totalRevenue = 0.0;
        this.lowStockThreshold = 10.0;
        this.autoReorderEnabled = true;
    }
    
    // ===== PRODUCT MANAGEMENT (8 methods, complexity 28) =====
    
    /**
     * Add product - Complexity: 4
     */
    public boolean addProduct(Product product) {
        if (product == null || product.getId() == null) {
            return false;
        }
        
        if (products.containsKey(product.getId())) {
            return false;
        }
        
        products.put(product.getId(), product);
        stock.put(product.getId(), 0);
        prices.put(product.getId(), product.getPrice());
        
        if (!categories.contains(product.getCategory())) {
            categories.add(product.getCategory());
        }
        
        return true;
    }
    
    /**
     * Update product - Complexity: 5
     */
    public boolean updateProduct(String productId, Product updatedProduct) {
        if (!products.containsKey(productId)) {
            return false;
        }
        
        if (updatedProduct == null) {
            return false;
        }
        
        products.put(productId, updatedProduct);
        
        if (updatedProduct.getPrice() != prices.get(productId)) {
            prices.put(productId, updatedProduct.getPrice());
            logPriceChange(productId, prices.get(productId), updatedProduct.getPrice());
        }
        
        return true;
    }
    
    /**
     * Delete product - Complexity: 3
     */
    public boolean deleteProduct(String productId) {
        if (!products.containsKey(productId)) {
            return false;
        }
        
        products.remove(productId);
        stock.remove(productId);
        prices.remove(productId);
        
        return true;
    }
    
    /**
     * Search products - Complexity: 4
     */
    public List<Product> searchProducts(String keyword) {
        List<Product> results = new ArrayList<>();
        
        if (keyword == null || keyword.trim().isEmpty()) {
            return results;
        }
        
        for (Product product : products.values()) {
            if (product.getName().toLowerCase().contains(keyword.toLowerCase()) ||
                product.getCategory().toLowerCase().contains(keyword.toLowerCase())) {
                results.add(product);
            }
        }
        
        return results;
    }
    
    /**
     * Get products by category - Complexity: 3
     */
    public List<Product> getProductsByCategory(String category) {
        List<Product> results = new ArrayList<>();
        
        for (Product product : products.values()) {
            if (product.getCategory().equals(category)) {
                results.add(product);
            }
        }
        
        return results;
    }
    
    /**
     * Get low stock products - Complexity: 3
     */
    public List<Product> getLowStockProducts() {
        List<Product> lowStock = new ArrayList<>();
        
        for (Map.Entry<String, Integer> entry : stock.entrySet()) {
            if (entry.getValue() < lowStockThreshold) {
                lowStock.add(products.get(entry.getKey()));
            }
        }
        
        return lowStock;
    }
    
    /**
     * Update price - Complexity: 3
     */
    public void updatePrice(String productId, double newPrice) {
        if (prices.containsKey(productId)) {
            double oldPrice = prices.get(productId);
            prices.put(productId, newPrice);
            logPriceChange(productId, oldPrice, newPrice);
        }
    }
    
    /**
     * Log price change - Complexity: 3
     */
    private void logPriceChange(String productId, double oldPrice, double newPrice) {
        Transaction trans = new Transaction();
        trans.setType("PRICE_CHANGE");
        trans.setProductId(productId);
        trans.setOldValue(oldPrice);
        trans.setNewValue(newPrice);
        trans.setTimestamp(new Date());
        transactions.add(trans);
    }
    
    // ===== STOCK MANAGEMENT (7 methods, complexity 24) =====
    
    /**
     * Add stock - Complexity: 4
     */
    public boolean addStock(String productId, int quantity) {
        if (!stock.containsKey(productId)) {
            return false;
        }
        
        if (quantity <= 0) {
            return false;
        }
        
        int currentStock = stock.get(productId);
        stock.put(productId, currentStock + quantity);
        
        logStockChange(productId, currentStock, currentStock + quantity);
        
        return true;
    }
    
    /**
     * Remove stock - Complexity: 5
     */
    public boolean removeStock(String productId, int quantity) {
        if (!stock.containsKey(productId)) {
            return false;
        }
        
        if (quantity <= 0) {
            return false;
        }
        
        int currentStock = stock.get(productId);
        
        if (currentStock < quantity) {
            return false;
        }
        
        stock.put(productId, currentStock - quantity);
        logStockChange(productId, currentStock, currentStock - quantity);
        
        if (autoReorderEnabled && (currentStock - quantity) < lowStockThreshold) {
            triggerAutoReorder(productId);
        }
        
        return true;
    }
    
    /**
     * Get stock level - Complexity: 2
     */
    public int getStock(String productId) {
        return stock.getOrDefault(productId, 0);
    }
    
    /**
     * Set stock level - Complexity: 3
     */
    public void setStock(String productId, int quantity) {
        if (stock.containsKey(productId)) {
            int oldStock = stock.get(productId);
            stock.put(productId, quantity);
            logStockChange(productId, oldStock, quantity);
        }
    }
    
    /**
     * Check availability - Complexity: 3
     */
    public boolean isAvailable(String productId, int requestedQuantity) {
        if (!stock.containsKey(productId)) {
            return false;
        }
        
        return stock.get(productId) >= requestedQuantity;
    }
    
    /**
     * Log stock change - Complexity: 3
     */
    private void logStockChange(String productId, int oldStock, int newStock) {
        Transaction trans = new Transaction();
        trans.setType("STOCK_CHANGE");
        trans.setProductId(productId);
        trans.setOldValue(oldStock);
        trans.setNewValue(newStock);
        trans.setTimestamp(new Date());
        transactions.add(trans);
    }
    
    /**
     * Trigger auto reorder - Complexity: 4
     */
    private void triggerAutoReorder(String productId) {
        if (!products.containsKey(productId)) {
            return;
        }
        
        Product product = products.get(productId);
        String supplierId = findBestSupplier(productId);
        
        if (supplierId != null) {
            createPurchaseOrder(productId, supplierId, 50);
        }
    }
    
    // ===== SUPPLIER MANAGEMENT (5 methods, complexity 17) =====
    
    /**
     * Add supplier - Complexity: 3
     */
    public boolean addSupplier(Supplier supplier) {
        if (supplier == null || supplier.getId() == null) {
            return false;
        }
        
        suppliers.put(supplier.getId(), supplier);
        supplierProducts.put(supplier.getId(), new ArrayList<>());
        
        return true;
    }
    
    /**
     * Link product to supplier - Complexity: 4
     */
    public boolean linkProductToSupplier(String productId, String supplierId) {
        if (!products.containsKey(productId) || !suppliers.containsKey(supplierId)) {
            return false;
        }
        
        List<String> products = supplierProducts.get(supplierId);
        
        if (!products.contains(productId)) {
            products.add(productId);
            return true;
        }
        
        return false;
    }
    
    /**
     * Find best supplier - Complexity: 4
     */
    private String findBestSupplier(String productId) {
        String bestSupplier = null;
        double bestPrice = Double.MAX_VALUE;
        
        for (Map.Entry<String, List<String>> entry : supplierProducts.entrySet()) {
            if (entry.getValue().contains(productId)) {
                Supplier supplier = suppliers.get(entry.getKey());
                double price = supplier.getPrice(productId);
                
                if (price < bestPrice) {
                    bestPrice = price;
                    bestSupplier = entry.getKey();
                }
            }
        }
        
        return bestSupplier;
    }
    
    /**
     * Get supplier products - Complexity: 3
     */
    public List<String> getSupplierProducts(String supplierId) {
        if (!supplierProducts.containsKey(supplierId)) {
            return new ArrayList<>();
        }
        
        return new ArrayList<>(supplierProducts.get(supplierId));
    }
    
    /**
     * Remove supplier - Complexity: 3
     */
    public boolean removeSupplier(String supplierId) {
        if (!suppliers.containsKey(supplierId)) {
            return false;
        }
        
        suppliers.remove(supplierId);
        supplierProducts.remove(supplierId);
        
        return true;
    }
    
    // ===== ORDER MANAGEMENT (5 methods, complexity 20) =====
    
    /**
     * Create purchase order - Complexity: 5
     */
    public boolean createPurchaseOrder(String productId, String supplierId, int quantity) {
        if (!products.containsKey(productId) || !suppliers.containsKey(supplierId)) {
            return false;
        }
        
        if (quantity <= 0) {
            return false;
        }
        
        PurchaseOrder order = new PurchaseOrder();
        order.setId(UUID.randomUUID().toString());
        order.setProductId(productId);
        order.setSupplierId(supplierId);
        order.setQuantity(quantity);
        order.setOrderDate(new Date());
        order.setStatus("PENDING");
        
        purchaseOrders.add(order);
        pendingOrders.add(order.getId());
        
        return true;
    }
    
    /**
     * Process order - Complexity: 5
     */
    public boolean processOrder(String orderId) {
        PurchaseOrder order = findOrder(orderId);
        
        if (order == null) {
            return false;
        }
        
        if (!order.getStatus().equals("PENDING")) {
            return false;
        }
        
        order.setStatus("PROCESSING");
        
        Calendar cal = Calendar.getInstance();
        cal.add(Calendar.DAY_OF_MONTH, 7);
        deliveryDates.put(orderId, cal.getTime());
        
        return true;
    }
    
    /**
     * Complete order - Complexity: 4
     */
    public boolean completeOrder(String orderId) {
        PurchaseOrder order = findOrder(orderId);
        
        if (order == null || !order.getStatus().equals("PROCESSING")) {
            return false;
        }
        
        addStock(order.getProductId(), order.getQuantity());
        order.setStatus("COMPLETED");
        pendingOrders.remove(orderId);
        
        return true;
    }
    
    /**
     * Find order - Complexity: 3
     */
    private PurchaseOrder findOrder(String orderId) {
        for (PurchaseOrder order : purchaseOrders) {
            if (order.getId().equals(orderId)) {
                return order;
            }
        }
        return null;
    }
    
    /**
     * Get pending orders - Complexity: 3
     */
    public List<PurchaseOrder> getPendingOrders() {
        List<PurchaseOrder> pending = new ArrayList<>();
        
        for (PurchaseOrder order : purchaseOrders) {
            if (order.getStatus().equals("PENDING") || order.getStatus().equals("PROCESSING")) {
                pending.add(order);
            }
        }
        
        return pending;
    }
    
    // ===== REPORTING (3 methods, complexity 12) =====
    
    /**
     * Generate inventory report - Complexity: 5
     */
    public String generateInventoryReport() {
        StringBuilder report = new StringBuilder();
        report.append("Inventory Report\n");
        report.append("================\n\n");
        
        report.append("Total Products: ").append(products.size()).append("\n");
        report.append("Total Categories: ").append(categories.size()).append("\n");
        
        int totalStock = 0;
        for (int quantity : stock.values()) {
            totalStock += quantity;
        }
        report.append("Total Stock Units: ").append(totalStock).append("\n");
        
        List<Product> lowStock = getLowStockProducts();
        report.append("Low Stock Items: ").append(lowStock.size()).append("\n");
        
        return report.toString();
    }
    
    /**
     * Generate sales report - Complexity: 4
     */
    public String generateSalesReport() {
        StringBuilder report = new StringBuilder();
        report.append("Sales Report\n");
        report.append("============\n\n");
        
        report.append("Total Revenue: $").append(String.format("%.2f", totalRevenue)).append("\n");
        report.append("Total Transactions: ").append(transactions.size()).append("\n");
        
        int totalSales = 0;
        for (int quantity : salesHistory.values()) {
            totalSales += quantity;
        }
        report.append("Total Units Sold: ").append(totalSales).append("\n");
        
        return report.toString();
    }
    
    /**
     * Export data to file - Complexity: 3
     */
    public boolean exportToFile(String filename) {
        try (PrintWriter writer = new PrintWriter(new FileWriter(filename))) {
            writer.println(generateInventoryReport());
            writer.println("\n");
            writer.println(generateSalesReport());
            return true;
        } catch (IOException e) {
            return false;
        }
    }
}

// Supporting classes
class Product {
    private String id;
    private String name;
    private String category;
    private double price;
    
    public String getId() { return id; }
    public String getName() { return name; }
    public String getCategory() { return category; }
    public double getPrice() { return price; }
}

class Supplier {
    private String id;
    private String name;
    private Map<String, Double> prices;
    
    public String getId() { return id; }
    public double getPrice(String productId) { 
        return prices.getOrDefault(productId, 0.0); 
    }
}

class PurchaseOrder {
    private String id;
    private String productId;
    private String supplierId;
    private int quantity;
    private Date orderDate;
    private String status;
    
    public String getId() { return id; }
    public String getProductId() { return productId; }
    public String getSupplierId() { return supplierId; }
    public int getQuantity() { return quantity; }
    public String getStatus() { return status; }
    public void setId(String id) { this.id = id; }
    public void setProductId(String productId) { this.productId = productId; }
    public void setSupplierId(String supplierId) { this.supplierId = supplierId; }
    public void setQuantity(int quantity) { this.quantity = quantity; }
    public void setOrderDate(Date date) { this.orderDate = date; }
    public void setStatus(String status) { this.status = status; }
}

class Transaction {
    private String type;
    private String productId;
    private double oldValue;
    private double newValue;
    private Date timestamp;
    
    public void setType(String type) { this.type = type; }
    public void setProductId(String productId) { this.productId = productId; }
    public void setOldValue(double oldValue) { this.oldValue = oldValue; }
    public void setNewValue(double newValue) { this.newValue = newValue; }
    public void setTimestamp(Date timestamp) { this.timestamp = timestamp; }
}

/**
 * METRICS SUMMARY:
 * ================
 * LOC: 700 lines (HIGH)
 * NOM: 28 methods (HIGH)
 * WMC: 85 complexity (HIGH)
 * CBO: 15 (Map, List, Queue, Date, Calendar, UUID, FileWriter, PrintWriter, etc.) (HIGH)
 * LCOM: 0.75 (HIGH - weak cohesion, multiple responsibilities)
 * 
 * SEVERITY LEVELS:
 * LOC:  700 → HIGH (3)
 * NOM:  28 → HIGH (3)
 * WMC:  85 → HIGH (3)
 * CBO:  15 → HIGH (3)
 * LCOM: 0.75 → HIGH (3)
 * 
 * PRIORITY SCORE:
 * = (3 × 0.25) + (3 × 0.15) + (3 × 0.25) + (3 × 0.20) + (3 × 0.15)
 * = 0.75 + 0.45 + 0.75 + 0.60 + 0.45
 * = 3.00 (HIGH PRIORITY)
 * 
 * Result: 🟠 Refactor when time permits
 * 
 * Suggested decomposition:
 * 1. ProductManager - Product CRUD operations
 * 2. StockManager - Stock tracking and management
 * 3. SupplierManager - Supplier relationships
 * 4. OrderManager - Purchase order processing
 * 5. ReportGenerator - Reporting functionality
 */
