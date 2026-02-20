package com.fashionstore.inventory;

import java.util.*;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * ClothingInventoryManager - A "God Class" managing ALL aspects of a clothing store.
 * 
 * PROBLEMS WITH THIS CLASS:
 * 1. Too many responsibilities (Inventory, Pricing, Categories, Seasons, Sizes, Reports)
 * 2. 350+ lines of code
 * 3. 45+ methods
 * 4. Low cohesion (LCOM > 0.7)
 * 5. High coupling with multiple domains
 * 
 * This class SHOULD be decomposed into:
 * - ClothingCategoryManager (men/women/children categories)
 * - SeasonalCollectionManager (summer/winter/spring/fall)
 * - SizeInventoryManager (size tracking and availability)
 * - PricingEngine (discounts, promotions, pricing rules)
 * - InventoryReporter (statistics, reports, analytics)
 */
public class ClothingInventoryManager {
    
    // ========== INVENTORY FIELDS ==========
    private Map<String, ClothingItem> inventory;
    private List<String> itemIds;
    private int totalItemCount;
    private LocalDate lastInventoryUpdate;
    
    // ========== CATEGORY FIELDS (Men/Women/Children) ==========
    private List<ClothingItem> menCollection;
    private List<ClothingItem> womenCollection;
    private List<ClothingItem> childrenCollection;
    private Map<String, String> categoryMapping;
    private String[] validCategories = {"MEN", "WOMEN", "CHILDREN", "UNISEX"};
    
    // ========== SEASONAL FIELDS (Summer/Winter/Sport) ==========
    private List<ClothingItem> summerCollection;
    private List<ClothingItem> winterCollection;
    private List<ClothingItem> springCollection;
    private List<ClothingItem> fallCollection;
    private List<ClothingItem> sportCollection;
    private String currentSeason;
    private Map<String, Double> seasonalDiscounts;
    
    // ========== SIZE FIELDS ==========
    private Map<String, Integer> sizeInventory; // Size -> Count
    private String[] validSizes = {"XS", "S", "M", "L", "XL", "XXL", "XXXL"};
    private Map<String, List<String>> sizeAvailability;
    private int lowStockThreshold;
    
    // ========== COLOR FIELDS ==========
    private Map<String, List<ClothingItem>> colorIndex;
    private String[] popularColors = {"BLACK", "WHITE", "BLUE", "RED", "GREEN", "GRAY"};
    private Map<String, Integer> colorSalesCount;
    
    // ========== PRICING FIELDS ==========
    private BigDecimal taxRate;
    private Map<String, BigDecimal> categoryPriceMultipliers;
    private Map<String, BigDecimal> promotionalDiscounts;
    private BigDecimal minimumProfitMargin;
    private List<String> clearanceItems;
    
    // ========== REPORTING FIELDS ==========
    private List<SalesRecord> salesHistory;
    private Map<String, Integer> dailySalesCount;
    private BigDecimal totalRevenue;
    private LocalDate reportingPeriodStart;
    
    // ========== CONSTRUCTOR ==========
    public ClothingInventoryManager() {
        this.inventory = new HashMap<>();
        this.itemIds = new ArrayList<>();
        this.menCollection = new ArrayList<>();
        this.womenCollection = new ArrayList<>();
        this.childrenCollection = new ArrayList<>();
        this.summerCollection = new ArrayList<>();
        this.winterCollection = new ArrayList<>();
        this.sportCollection = new ArrayList<>();
        this.sizeInventory = new HashMap<>();
        this.colorIndex = new HashMap<>();
        this.salesHistory = new ArrayList<>();
        this.taxRate = new BigDecimal("0.08");
        this.lowStockThreshold = 5;
        this.totalRevenue = BigDecimal.ZERO;
        initializeSeasonalDiscounts();
        initializeCategoryMultipliers();
    }
    
    // ========== INVENTORY MANAGEMENT METHODS ==========
    
    public void addItem(ClothingItem item) {
        String id = generateItemId(item);
        inventory.put(id, item);
        itemIds.add(id);
        totalItemCount++;
        lastInventoryUpdate = LocalDate.now();
        categorizeItem(item);
        indexByColor(item);
        updateSizeInventory(item, 1);
    }
    
    public void removeItem(String itemId) {
        ClothingItem item = inventory.remove(itemId);
        if (item != null) {
            itemIds.remove(itemId);
            totalItemCount--;
            removeFromCategory(item);
            updateSizeInventory(item, -1);
        }
    }
    
    public ClothingItem getItem(String itemId) {
        return inventory.get(itemId);
    }
    
    public List<ClothingItem> getAllItems() {
        return new ArrayList<>(inventory.values());
    }
    
    public int getTotalItemCount() {
        return totalItemCount;
    }
    
    private String generateItemId(ClothingItem item) {
        return item.getCategory() + "-" + item.getType() + "-" + System.currentTimeMillis();
    }
    
    // ========== CATEGORY MANAGEMENT METHODS (Men/Women/Children) ==========
    
    public void categorizeItem(ClothingItem item) {
        String category = item.getCategory().toUpperCase();
        switch (category) {
            case "MEN":
                menCollection.add(item);
                break;
            case "WOMEN":
                womenCollection.add(item);
                break;
            case "CHILDREN":
                childrenCollection.add(item);
                break;
            default:
                // Add to all collections if unisex
                menCollection.add(item);
                womenCollection.add(item);
        }
        categoryMapping.put(item.getId(), category);
    }
    
    public List<ClothingItem> getMenCollection() {
        return new ArrayList<>(menCollection);
    }
    
    public List<ClothingItem> getWomenCollection() {
        return new ArrayList<>(womenCollection);
    }
    
    public List<ClothingItem> getChildrenCollection() {
        return new ArrayList<>(childrenCollection);
    }
    
    public void removeFromCategory(ClothingItem item) {
        menCollection.remove(item);
        womenCollection.remove(item);
        childrenCollection.remove(item);
    }
    
    public boolean isValidCategory(String category) {
        for (String valid : validCategories) {
            if (valid.equalsIgnoreCase(category)) return true;
        }
        return false;
    }
    
    public Map<String, Integer> getCategoryCounts() {
        Map<String, Integer> counts = new HashMap<>();
        counts.put("MEN", menCollection.size());
        counts.put("WOMEN", womenCollection.size());
        counts.put("CHILDREN", childrenCollection.size());
        return counts;
    }
    
    // ========== SEASONAL COLLECTION METHODS (Summer/Winter/Sport) ==========
    
    public void assignToSeason(ClothingItem item, String season) {
        season = season.toUpperCase();
        switch (season) {
            case "SUMMER":
                summerCollection.add(item);
                break;
            case "WINTER":
                winterCollection.add(item);
                break;
            case "SPRING":
                springCollection.add(item);
                break;
            case "FALL":
                fallCollection.add(item);
                break;
            case "SPORT":
                sportCollection.add(item);
                break;
        }
    }
    
    public List<ClothingItem> getSummerCollection() {
        return new ArrayList<>(summerCollection);
    }
    
    public List<ClothingItem> getWinterCollection() {
        return new ArrayList<>(winterCollection);
    }
    
    public List<ClothingItem> getSportCollection() {
        return new ArrayList<>(sportCollection);
    }
    
    public void setCurrentSeason(String season) {
        this.currentSeason = season.toUpperCase();
    }
    
    public List<ClothingItem> getCurrentSeasonItems() {
        switch (currentSeason) {
            case "SUMMER": return getSummerCollection();
            case "WINTER": return getWinterCollection();
            case "SPRING": return new ArrayList<>(springCollection);
            case "FALL": return new ArrayList<>(fallCollection);
            default: return getAllItems();
        }
    }
    
    private void initializeSeasonalDiscounts() {
        seasonalDiscounts = new HashMap<>();
        seasonalDiscounts.put("SUMMER", 0.0);
        seasonalDiscounts.put("WINTER", 0.0);
        seasonalDiscounts.put("SPRING", 0.10);
        seasonalDiscounts.put("FALL", 0.10);
        seasonalDiscounts.put("CLEARANCE", 0.50);
    }
    
    public double getSeasonalDiscount(String season) {
        return seasonalDiscounts.getOrDefault(season.toUpperCase(), 0.0);
    }
    
    // ========== SIZE MANAGEMENT METHODS ==========
    
    public void updateSizeInventory(ClothingItem item, int delta) {
        String size = item.getSize();
        int current = sizeInventory.getOrDefault(size, 0);
        sizeInventory.put(size, current + delta);
    }
    
    public int getSizeCount(String size) {
        return sizeInventory.getOrDefault(size.toUpperCase(), 0);
    }
    
    public boolean isSizeAvailable(String itemId, String size) {
        List<String> available = sizeAvailability.get(itemId);
        return available != null && available.contains(size.toUpperCase());
    }
    
    public List<String> getAvailableSizes(String itemId) {
        return sizeAvailability.getOrDefault(itemId, new ArrayList<>());
    }
    
    public boolean isValidSize(String size) {
        for (String valid : validSizes) {
            if (valid.equalsIgnoreCase(size)) return true;
        }
        return false;
    }
    
    public List<String> getLowStockSizes() {
        List<String> lowStock = new ArrayList<>();
        for (Map.Entry<String, Integer> entry : sizeInventory.entrySet()) {
            if (entry.getValue() < lowStockThreshold) {
                lowStock.add(entry.getKey());
            }
        }
        return lowStock;
    }
    
    public void setLowStockThreshold(int threshold) {
        this.lowStockThreshold = threshold;
    }
    
    // ========== COLOR MANAGEMENT METHODS ==========
    
    public void indexByColor(ClothingItem item) {
        String color = item.getColor().toUpperCase();
        colorIndex.computeIfAbsent(color, k -> new ArrayList<>()).add(item);
    }
    
    public List<ClothingItem> getItemsByColor(String color) {
        return colorIndex.getOrDefault(color.toUpperCase(), new ArrayList<>());
    }
    
    public String[] getPopularColors() {
        return popularColors.clone();
    }
    
    public void recordColorSale(String color) {
        color = color.toUpperCase();
        colorSalesCount.put(color, colorSalesCount.getOrDefault(color, 0) + 1);
    }
    
    public String getMostPopularColor() {
        return colorSalesCount.entrySet().stream()
            .max(Map.Entry.comparingByValue())
            .map(Map.Entry::getKey)
            .orElse("UNKNOWN");
    }
    
    // ========== PRICING METHODS ==========
    
    public BigDecimal calculatePrice(ClothingItem item) {
        BigDecimal basePrice = item.getBasePrice();
        BigDecimal categoryMultiplier = categoryPriceMultipliers.getOrDefault(
            item.getCategory(), BigDecimal.ONE);
        BigDecimal adjustedPrice = basePrice.multiply(categoryMultiplier);
        
        // Apply seasonal discount
        double seasonDiscount = getSeasonalDiscount(currentSeason);
        if (seasonDiscount > 0) {
            adjustedPrice = adjustedPrice.multiply(
                BigDecimal.valueOf(1 - seasonDiscount));
        }
        
        // Apply promotional discount if exists
        BigDecimal promoDiscount = promotionalDiscounts.get(item.getId());
        if (promoDiscount != null) {
            adjustedPrice = adjustedPrice.subtract(promoDiscount);
        }
        
        return adjustedPrice;
    }
    
    public BigDecimal calculatePriceWithTax(ClothingItem item) {
        BigDecimal price = calculatePrice(item);
        return price.add(price.multiply(taxRate));
    }
    
    public void setPromotionalDiscount(String itemId, BigDecimal discount) {
        promotionalDiscounts.put(itemId, discount);
    }
    
    public void addToClearance(String itemId) {
        clearanceItems.add(itemId);
        setPromotionalDiscount(itemId, 
            inventory.get(itemId).getBasePrice().multiply(BigDecimal.valueOf(0.5)));
    }
    
    public boolean isOnClearance(String itemId) {
        return clearanceItems.contains(itemId);
    }
    
    private void initializeCategoryMultipliers() {
        categoryPriceMultipliers = new HashMap<>();
        categoryPriceMultipliers.put("MEN", new BigDecimal("1.0"));
        categoryPriceMultipliers.put("WOMEN", new BigDecimal("1.1"));
        categoryPriceMultipliers.put("CHILDREN", new BigDecimal("0.8"));
        categoryPriceMultipliers.put("SPORT", new BigDecimal("1.2"));
    }
    
    public void setTaxRate(BigDecimal rate) {
        this.taxRate = rate;
    }
    
    // ========== REPORTING & ANALYTICS METHODS ==========
    
    public void recordSale(ClothingItem item, int quantity, BigDecimal salePrice) {
        SalesRecord record = new SalesRecord(item.getId(), quantity, salePrice, LocalDate.now());
        salesHistory.add(record);
        totalRevenue = totalRevenue.add(salePrice.multiply(BigDecimal.valueOf(quantity)));
        updateDailySales(item.getId(), quantity);
        recordColorSale(item.getColor());
    }
    
    private void updateDailySales(String itemId, int quantity) {
        dailySalesCount.put(itemId, dailySalesCount.getOrDefault(itemId, 0) + quantity);
    }
    
    public BigDecimal getTotalRevenue() {
        return totalRevenue;
    }
    
    public int getTotalSalesCount() {
        return salesHistory.size();
    }
    
    public Map<String, Integer> getSalesByCategory() {
        Map<String, Integer> salesByCategory = new HashMap<>();
        for (SalesRecord record : salesHistory) {
            ClothingItem item = inventory.get(record.getItemId());
            if (item != null) {
                String category = item.getCategory();
                salesByCategory.put(category, 
                    salesByCategory.getOrDefault(category, 0) + record.getQuantity());
            }
        }
        return salesByCategory;
    }
    
    public List<ClothingItem> getTopSellingItems(int limit) {
        return dailySalesCount.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(limit)
            .map(e -> inventory.get(e.getKey()))
            .filter(Objects::nonNull)
            .collect(java.util.stream.Collectors.toList());
    }
    
    public String generateInventoryReport() {
        StringBuilder report = new StringBuilder();
        report.append("=== CLOTHING INVENTORY REPORT ===\n");
        report.append("Total Items: ").append(totalItemCount).append("\n");
        report.append("Men's Collection: ").append(menCollection.size()).append("\n");
        report.append("Women's Collection: ").append(womenCollection.size()).append("\n");
        report.append("Children's Collection: ").append(childrenCollection.size()).append("\n");
        report.append("Summer Items: ").append(summerCollection.size()).append("\n");
        report.append("Winter Items: ").append(winterCollection.size()).append("\n");
        report.append("Sport Items: ").append(sportCollection.size()).append("\n");
        report.append("Total Revenue: $").append(totalRevenue).append("\n");
        report.append("Low Stock Sizes: ").append(getLowStockSizes()).append("\n");
        return report.toString();
    }
    
    public String generateSalesReport() {
        StringBuilder report = new StringBuilder();
        report.append("=== SALES REPORT ===\n");
        report.append("Period Start: ").append(reportingPeriodStart).append("\n");
        report.append("Total Sales: ").append(getTotalSalesCount()).append("\n");
        report.append("Total Revenue: $").append(totalRevenue).append("\n");
        report.append("Sales by Category: ").append(getSalesByCategory()).append("\n");
        report.append("Most Popular Color: ").append(getMostPopularColor()).append("\n");
        return report.toString();
    }
    
    // ========== INNER CLASSES ==========
    
    public static class ClothingItem {
        private String id;
        private String name;
        private String category; // MEN, WOMEN, CHILDREN
        private String type;     // SHIRT, PANTS, DRESS, etc.
        private String size;
        private String color;
        private BigDecimal basePrice;
        private String season;
        
        public ClothingItem(String name, String category, String type, 
                           String size, String color, BigDecimal basePrice) {
            this.id = UUID.randomUUID().toString();
            this.name = name;
            this.category = category;
            this.type = type;
            this.size = size;
            this.color = color;
            this.basePrice = basePrice;
        }
        
        // Getters
        public String getId() { return id; }
        public String getName() { return name; }
        public String getCategory() { return category; }
        public String getType() { return type; }
        public String getSize() { return size; }
        public String getColor() { return color; }
        public BigDecimal getBasePrice() { return basePrice; }
        public String getSeason() { return season; }
        
        // Setters
        public void setSeason(String season) { this.season = season; }
    }
    
    public static class SalesRecord {
        private String itemId;
        private int quantity;
        private BigDecimal salePrice;
        private LocalDate saleDate;
        
        public SalesRecord(String itemId, int quantity, BigDecimal salePrice, LocalDate saleDate) {
            this.itemId = itemId;
            this.quantity = quantity;
            this.salePrice = salePrice;
            this.saleDate = saleDate;
        }
        
        public String getItemId() { return itemId; }
        public int getQuantity() { return quantity; }
        public BigDecimal getSalePrice() { return salePrice; }
        public LocalDate getSaleDate() { return saleDate; }
    }
}
