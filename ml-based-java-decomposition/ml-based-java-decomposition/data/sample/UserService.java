package com.example.demo;

import java.util.*;
import java.io.*;

/**
 * UserService - Example of a God Class that needs decomposition.
 * 
 * This class violates the Single Responsibility Principle by handling:
 * 1. User authentication
 * 2. User profile management
 * 3. Email notifications
 * 4. Data validation
 * 
 * This is a demonstration file for rule-based decomposition.
 */
public class UserService {

    // Authentication fields
    private String authToken;
    private Date tokenExpiry;
    private int loginAttempts;
    private boolean isLocked;
    
    // Profile fields
    private String username;
    private String email;
    private String firstName;
    private String lastName;
    private Date birthDate;
    private String address;
    
    // Email fields
    private String smtpServer;
    private int smtpPort;
    private String emailTemplate;
    private List<String> pendingEmails;
    
    // Validation fields
    private List<String> validationErrors;
    private Map<String, String> validationRules;
    
    // Constructor
    public UserService() {
        this.pendingEmails = new ArrayList<>();
        this.validationErrors = new ArrayList<>();
        this.validationRules = new HashMap<>();
        this.loginAttempts = 0;
        this.isLocked = false;
    }
    
    // ===== AUTHENTICATION METHODS =====
    
    public boolean authenticate(String username, String password) {
        if (isLocked) {
            return false;
        }
        
        loginAttempts++;
        
        if (loginAttempts > 5) {
            lockAccount();
            return false;
        }
        
        // Simulate authentication
        if (validateCredentials(username, password)) {
            generateToken();
            loginAttempts = 0;
            return true;
        }
        
        return false;
    }
    
    private boolean validateCredentials(String username, String password) {
        // Simplified validation
        return username != null && password != null && password.length() >= 8;
    }
    
    private void generateToken() {
        this.authToken = UUID.randomUUID().toString();
        Calendar cal = Calendar.getInstance();
        cal.add(Calendar.HOUR, 24);
        this.tokenExpiry = cal.getTime();
    }
    
    public boolean isTokenValid() {
        if (authToken == null || tokenExpiry == null) {
            return false;
        }
        return new Date().before(tokenExpiry);
    }
    
    public void logout() {
        this.authToken = null;
        this.tokenExpiry = null;
    }
    
    private void lockAccount() {
        this.isLocked = true;
    }
    
    public void unlockAccount() {
        this.isLocked = false;
        this.loginAttempts = 0;
    }
    
    public String getAuthToken() {
        return authToken;
    }
    
    // ===== PROFILE METHODS =====
    
    public void setUsername(String username) {
        this.username = username;
    }
    
    public String getUsername() {
        return username;
    }
    
    public void setEmail(String email) {
        this.email = email;
    }
    
    public String getEmail() {
        return email;
    }
    
    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }
    
    public String getFirstName() {
        return firstName;
    }
    
    public void setLastName(String lastName) {
        this.lastName = lastName;
    }
    
    public String getLastName() {
        return lastName;
    }
    
    public String getFullName() {
        return firstName + " " + lastName;
    }
    
    public void setBirthDate(Date birthDate) {
        this.birthDate = birthDate;
    }
    
    public Date getBirthDate() {
        return birthDate;
    }
    
    public int getAge() {
        if (birthDate == null) {
            return 0;
        }
        Calendar birth = Calendar.getInstance();
        birth.setTime(birthDate);
        Calendar today = Calendar.getInstance();
        int age = today.get(Calendar.YEAR) - birth.get(Calendar.YEAR);
        if (today.get(Calendar.DAY_OF_YEAR) < birth.get(Calendar.DAY_OF_YEAR)) {
            age--;
        }
        return age;
    }
    
    public void setAddress(String address) {
        this.address = address;
    }
    
    public String getAddress() {
        return address;
    }
    
    public void updateProfile(String firstName, String lastName, String email, String address) {
        setFirstName(firstName);
        setLastName(lastName);
        setEmail(email);
        setAddress(address);
    }
    
    // ===== EMAIL METHODS =====
    
    public void configureEmailServer(String server, int port) {
        this.smtpServer = server;
        this.smtpPort = port;
    }
    
    public void setEmailTemplate(String template) {
        this.emailTemplate = template;
    }
    
    public void sendEmail(String recipient, String subject, String body) {
        // Format email using template
        String formattedBody = formatEmailBody(body);
        
        // Add to pending queue
        String emailData = recipient + "|" + subject + "|" + formattedBody;
        pendingEmails.add(emailData);
        
        // Process email
        processEmailQueue();
    }
    
    private String formatEmailBody(String body) {
        if (emailTemplate != null) {
            return emailTemplate.replace("{{CONTENT}}", body);
        }
        return body;
    }
    
    private void processEmailQueue() {
        for (String emailData : pendingEmails) {
            String[] parts = emailData.split("\\|");
            if (parts.length == 3) {
                // Simulate sending
                System.out.println("Sending email to: " + parts[0]);
            }
        }
        pendingEmails.clear();
    }
    
    public void sendWelcomeEmail() {
        String subject = "Welcome to our service!";
        String body = "Hello " + getFullName() + ", welcome!";
        sendEmail(email, subject, body);
    }
    
    public void sendPasswordResetEmail(String resetToken) {
        String subject = "Password Reset Request";
        String body = "Click here to reset: http://example.com/reset?token=" + resetToken;
        sendEmail(email, subject, body);
    }
    
    public int getPendingEmailCount() {
        return pendingEmails.size();
    }
    
    // ===== VALIDATION METHODS =====
    
    public void addValidationRule(String field, String rule) {
        validationRules.put(field, rule);
    }
    
    public boolean validateField(String field, String value) {
        String rule = validationRules.get(field);
        if (rule == null) {
            return true;
        }
        
        boolean isValid = applyValidationRule(rule, value);
        if (!isValid) {
            validationErrors.add("Validation failed for field: " + field);
        }
        return isValid;
    }
    
    private boolean applyValidationRule(String rule, String value) {
        if (rule.equals("required")) {
            return value != null && !value.isEmpty();
        } else if (rule.equals("email")) {
            return validateEmail(value);
        } else if (rule.startsWith("minLength:")) {
            int minLen = Integer.parseInt(rule.split(":")[1]);
            return value != null && value.length() >= minLen;
        } else if (rule.startsWith("maxLength:")) {
            int maxLen = Integer.parseInt(rule.split(":")[1]);
            return value == null || value.length() <= maxLen;
        }
        return true;
    }
    
    public boolean validateEmail(String email) {
        if (email == null) {
            return false;
        }
        return email.contains("@") && email.contains(".");
    }
    
    public boolean validateUsername(String username) {
        if (username == null || username.length() < 3) {
            validationErrors.add("Username must be at least 3 characters");
            return false;
        }
        if (!username.matches("^[a-zA-Z0-9_]+$")) {
            validationErrors.add("Username can only contain letters, numbers, and underscores");
            return false;
        }
        return true;
    }
    
    public boolean validatePassword(String password) {
        if (password == null || password.length() < 8) {
            validationErrors.add("Password must be at least 8 characters");
            return false;
        }
        if (!password.matches(".*[A-Z].*")) {
            validationErrors.add("Password must contain uppercase letter");
            return false;
        }
        if (!password.matches(".*[0-9].*")) {
            validationErrors.add("Password must contain a number");
            return false;
        }
        return true;
    }
    
    public List<String> getValidationErrors() {
        return new ArrayList<>(validationErrors);
    }
    
    public void clearValidationErrors() {
        validationErrors.clear();
    }
    
    public boolean hasValidationErrors() {
        return !validationErrors.isEmpty();
    }
}
