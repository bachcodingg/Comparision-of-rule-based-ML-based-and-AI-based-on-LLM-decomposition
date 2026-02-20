package com.fashionstore.inventory;

import java.util.*;

/**
 * ClothingInventoryCategoryManagement - Category Management
 * 
 * Extracted from ClothingInventoryManager using rule-based decomposition.
 * 
 * Extraction Reason: Methods share access to fields: womenCollection, childrenCollection, menCollection, size
 * 
 * @see ClothingInventoryManager
 */
public class ClothingInventoryCategoryManagement {

    // Extracted fields
    private List<ClothingItem> menCollection;
    private List<ClothingItem> womenCollection;
    private List<ClothingItem> childrenCollection;
    private String size;

    // Constructor
    public ClothingInventoryCategoryManagement() {
        // Initialize fields
    }

    // Extracted methods
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

    public Map<String, Integer> getCategoryCounts() {
        Map<String, Integer> counts = new HashMap<>();
        counts.put("MEN", menCollection.size());
        counts.put("WOMEN", womenCollection.size());
        counts.put("CHILDREN", childrenCollection.size());
        return counts;
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

}
