package com.example.demo;

public class EmailValidator {

    private static final String EMAIL_PATTERN =
        "^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$";

    private int validationCount;

    public EmailValidator() {
        this.validationCount = 0;
    }


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
