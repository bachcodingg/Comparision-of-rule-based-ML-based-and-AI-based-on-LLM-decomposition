package com.fashionstore.inventory;

import java.util.*;

/**
 * ClothingInventorySeasonalManagement - Seasonal Management
 * 
 * Extracted from ClothingInventoryManager using rule-based decomposition.
 * 
 * Extraction Reason: Methods share access to fields: season, seasonalDiscounts
 * 
 * @see ClothingInventoryManager
 */
public class ClothingInventorySeasonalManagement {

    // Extracted fields
    private Map<String, Double> seasonalDiscounts;
    private String season;

    // Constructor
    public ClothingInventorySeasonalManagement() {
        // Initialize fields
    }

    // Extracted methods
    public void setCurrentSeason(String season) {
        this.currentSeason = season.toUpperCase();
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

    public void setSeason(String season) {
        this.season = season;
    }

}
