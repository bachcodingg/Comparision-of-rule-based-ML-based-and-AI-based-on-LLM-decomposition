package com.fashionstore.inventory;

import java.util.*;

/**
 * ClothingInventoryColorManagement - Color Management
 * 
 * Extracted from ClothingInventoryManager using rule-based decomposition.
 * 
 * Extraction Reason: Methods share access to fields: color, colorSalesCount, colorIndex
 * 
 * @see ClothingInventoryManager
 */
public class ClothingInventoryColorManagement {

    // Extracted fields
    private Map<String, List<ClothingItem>> colorIndex;
    private Map<String, Integer> colorSalesCount;
    private String color;

    // Constructor
    public ClothingInventoryColorManagement() {
        // Initialize fields
    }

    // Extracted methods
    public void indexByColor(ClothingItem item) {
        String color = item.getColor().toUpperCase();
        colorIndex.computeIfAbsent(color, k -> new ArrayList<>()).add(item);
    }

    public List<ClothingItem> getItemsByColor(String color) {
        return colorIndex.getOrDefault(color.toUpperCase(), new ArrayList<>());
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

}
