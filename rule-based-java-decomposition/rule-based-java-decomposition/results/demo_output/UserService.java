package com.example.demo;

import java.util.*;
import java.io.*;

/**
 * UserService
 * 
 * Refactored using rule-based decomposition.
 * Extracted components:
 *   - UserServiceComponent1: Extracted functionality
 *   - UserServiceDataMutator: Extracted functionality
 *   - UserServiceDataMutator: Extracted functionality
 */
public class UserService {

    // Extracted component references
    private final UserServiceComponent1 userServiceComponent1 = new UserServiceComponent1();
    private final UserServiceDataMutator userServiceDataMutator = new UserServiceDataMutator();
    private final UserServiceDataMutator userServiceDataMutator = new UserServiceDataMutator();

    // Remaining fields
    private int loginAttempts;
    private boolean isLocked;
    private String username;
    private Date birthDate;
    private String smtpServer;
    private int smtpPort;
    private String emailTemplate;
    private List<String> pendingEmails;
    private List<String> validationErrors;
    private Map<String, String> validationRules;
    return false;
    return false;
    return true;
    return false;
    return false;
    return username;
    return birthDate;
    return 0;
    return age;
    return true;
    return isValid;
    return true;
    return false;
    return false;
    return false;
    return true;
    return false;
    return false;
    return false;
    return true;

    // Delegation methods to extracted components
    public void generateToken() {
        userServiceComponent1.generateToken();
    }

    public boolean isTokenValid() {
        return userServiceComponent1.isTokenValid();
    }

    public void logout() {
        userServiceComponent1.logout();
    }

    public void setEmail(String email) {
        userServiceDataMutator.setEmail(email);
    }

    public void sendEmail(String recipient, String subject, String body) {
        userServiceDataMutator.sendEmail(recipient, subject, body);
    }

    public void processEmailQueue() {
        userServiceDataMutator.processEmailQueue();
    }

    public void sendWelcomeEmail() {
        userServiceDataMutator.sendWelcomeEmail();
    }

    public void sendPasswordResetEmail(String resetToken) {
        userServiceDataMutator.sendPasswordResetEmail(resetToken);
    }

    public boolean validateEmail(String email) {
        return userServiceDataMutator.validateEmail(email);
    }

    public void setFirstName(String firstName) {
        userServiceDataMutator.setFirstName(firstName);
    }

    public void setLastName(String lastName) {
        userServiceDataMutator.setLastName(lastName);
    }

    public String getFullName() {
        return userServiceDataMutator.getFullName();
    }

    public void updateProfile(String firstName, String lastName, String email, String address) {
        userServiceDataMutator.updateProfile(firstName, lastName, email, address);
    }

    // Remaining methods
    public UserService() {{
            this.pendingEmails = new ArrayList<>();
            this.validationErrors = new ArrayList<>();
            this.validationRules = new HashMap<>();
            this.loginAttempts = 0;
            this.isLocked = false;
        }

    public boolean authenticate(String username, String password) {{
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

    private boolean validateCredentials(String username, String password) {{
            // Simplified validation
            return username != null && password != null && password.length() >= 8;
        }

    private void lockAccount() {{
            this.isLocked = true;
        }

    public void unlockAccount() {{
            this.isLocked = false;
            this.loginAttempts = 0;
        }

    public String getAuthToken() {{
            return authToken;
        }

    public void setUsername(String username) {{
            this.username = username;
        }

    public String getUsername() {{
            return username;
        }

    public String getEmail() {{
            return email;
        }

    public String getFirstName() {{
            return firstName;
        }

    public String getLastName() {{
            return lastName;
        }

    public void setBirthDate(Date birthDate) {{
            this.birthDate = birthDate;
        }

    public Date getBirthDate() {{
            return birthDate;
        }

    public int getAge() {{
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

    public void setAddress(String address) {{
            this.address = address;
        }

    public String getAddress() {{
            return address;
        }

    public void configureEmailServer(String server, int port) {{
            this.smtpServer = server;
            this.smtpPort = port;
        }

    public void setEmailTemplate(String template) {{
            this.emailTemplate = template;
        }

    private String formatEmailBody(String body) {{
            if (emailTemplate != null) {
                return emailTemplate.replace("{{CONTENT}}", body);
            }
            return body;
        }

    public int getPendingEmailCount() {{
            return pendingEmails.size();
        }

    public void addValidationRule(String field, String rule) {{
            validationRules.put(field, rule);
        }

    public boolean validateField(String field, String value) {{
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

    private boolean applyValidationRule(String rule, String value) {{
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

    public boolean validateUsername(String username) {{
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

    public boolean validatePassword(String password) {{
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

    public List<String> getValidationErrors() {{
            return new ArrayList<>(validationErrors);
        }

    public void clearValidationErrors() {{
            validationErrors.clear();
        }

    public boolean hasValidationErrors() {{
            return !validationErrors.isEmpty();
        }

}