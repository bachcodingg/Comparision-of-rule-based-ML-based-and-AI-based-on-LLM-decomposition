package com.example.demo;

/**
 * LOW SEVERITY EXAMPLE
 * 
 * Simple utility class with minimal complexity.
 * Metrics:
 * - LOC: ~80 lines (LOW: < 200)
 * - NOM: 5 methods (LOW: < 10)
 * - WMC: 12 complexity (LOW: < 30)
 * - CBO: 2 dependencies (LOW: < 5)
 * - LCOM: 0.2 (LOW: < 0.4) - good cohesion
 * 
 * Expected Result: LOW priority, no refactoring needed
 */
public class EmailValidator {

    private static final String EMAIL_PATTERN = 
        "^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$";
    
    private int validationCount;
    
    public EmailValidator() {
        this.validationCount = 0;
    }
    
    /**
     * Validates email format
     * Complexity: 3 (if statements)
     */
    public boolean isValid(String email) {
        if (email == null || email.trim().isEmpty()) {
            return false;
        }
        
        if (!email.contains("@")) {
            return false;
        }
        
        if (email.matches(EMAIL_PATTERN)) {
            validationCount++;
            return true;
        }
        
        return false;
    }
    
    /**
     * Validates domain part of email
     * Complexity: 2
     */
    public boolean hasValidDomain(String email) {
        if (!isValid(email)) {
            return false;
        }
        
        String domain = email.substring(email.indexOf("@") + 1);
        return domain.contains(".");
    }
    
    /**
     * Checks if email is from allowed domain
     * Complexity: 3
     */
    public boolean isFromAllowedDomain(String email, String[] allowedDomains) {
        if (!isValid(email)) {
            return false;
        }
        
        String domain = email.substring(email.indexOf("@") + 1);
        
        for (String allowed : allowedDomains) {
            if (domain.equalsIgnoreCase(allowed)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * Gets validation count
     * Complexity: 1
     */
    public int getValidationCount() {
        return validationCount;
    }
    
    /**
     * Resets validation counter
     * Complexity: 1
     */
    public void resetCount() {
        this.validationCount = 0;
    }
}

/**
 * METRICS SUMMARY:
 * ================
 * LOC: 80 lines (LOW)
 * NOM: 5 methods (LOW)
 * WMC: 10 complexity (LOW)
 * CBO: 2 (String, Arrays) (LOW)
 * LCOM: 0.2 (LOW - methods work together)
 * 
 * SEVERITY LEVELS:
 * LOC:  80 → LOW (1)
 * NOM:  5 → LOW (1)
 * WMC: 10 → LOW (1)
 * CBO:  2 → LOW (1)
 * LCOM: 0.2 → LOW (1)
 * 
 * PRIORITY SCORE:
 * = (1 × 0.25) + (1 × 0.15) + (1 × 0.25) + (1 × 0.20) + (1 × 0.15)
 * = 0.25 + 0.15 + 0.25 + 0.20 + 0.15
 * = 1.00 (LOW PRIORITY)
 * 
 * Result: ✅ No refactoring needed
 */
