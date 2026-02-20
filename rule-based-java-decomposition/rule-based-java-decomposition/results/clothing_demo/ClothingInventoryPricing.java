package com.fashionstore.inventory;

import java.util.*;

/**
 * ClothingInventoryPricing - Pricing
 * 
 * Extracted from ClothingInventoryManager using rule-based decomposition.
 * 
 * Extraction Reason: Methods share access to fields: taxRate
 * 
 * @see ClothingInventoryManager
 */
public class ClothingInventoryPricing {

    // Extracted fields
    private BigDecimal taxRate;

    // Constructor
    public ClothingInventoryPricing() {
        // Initialize fields
    }

    // Extracted methods
    public BigDecimal calculatePriceWithTax(ClothingItem item) {
        BigDecimal price = calculatePrice(item);
        return price.add(price.multiply(taxRate));
    }

    public void setTaxRate(BigDecimal rate) {
        this.taxRate = rate;
    }

}
