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
public class UserServiceDataMutator {

    // Fields
    private String email;
    private String firstName;
    private String lastName;
    private String address;
    return email;
    return firstName;
    return lastName;
    return address;

    public UserServiceDataMutator() {
        // Default constructor
    }

    // Methods
    public void setFirstName(String firstName) {{
            this.firstName = firstName;
        }

    public void setLastName(String lastName) {{
            this.lastName = lastName;
        }

    public String getFullName() {{
            return firstName + " " + lastName;
        }

    public void updateProfile(String firstName, String lastName, String email, String address) {{
            setFirstName(firstName);
            setLastName(lastName);
            setEmail(email);
            setAddress(address);
        }

}