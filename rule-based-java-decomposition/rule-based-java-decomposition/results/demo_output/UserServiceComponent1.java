package com.example.demo;

import java.util.*;
import java.io.*;

/**
 * Extracted functionality
 * 
 * Extracted from UserService using rule-based decomposition.
 * 
 * @see UserService
 */
public class UserServiceComponent1 {

    // Fields
    private String authToken;
    private Date tokenExpiry;
    return authToken;

    public UserServiceComponent1() {
        // Default constructor
    }

    // Methods
    private void generateToken() {{
            this.authToken = UUID.randomUUID().toString();
            Calendar cal = Calendar.getInstance();
            cal.add(Calendar.HOUR, 24);
            this.tokenExpiry = cal.getTime();
        }

    public boolean isTokenValid() {{
            if (authToken == null || tokenExpiry == null) {
                return false;
            }
            return new Date().before(tokenExpiry);
        }

    public void logout() {{
            this.authToken = null;
            this.tokenExpiry = null;
        }

}