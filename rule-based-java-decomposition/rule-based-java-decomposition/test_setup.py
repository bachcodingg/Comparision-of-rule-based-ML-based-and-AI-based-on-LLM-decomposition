#!/usr/bin/env python3
"""
Test Setup Script

Verifies the installation and creates sample data for testing.
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("⚠ Warning: Python 3.9+ recommended")
    return True


def check_dependencies():
    """Check required dependencies."""
    deps = ["pandas", "numpy", "yaml"]
    missing = []
    
    for dep in deps:
        try:
            __import__(dep if dep != "yaml" else "yaml")
            print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep} - not installed")
            missing.append(dep)
    
    return len(missing) == 0


def check_directories():
    """Create necessary directories."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/sample",
        "results/charts",
        "results/reports",
        "logs"
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {d}")
    
    return True


def check_config():
    """Check config file exists."""
    config_path = Path("config.yaml")
    if config_path.exists():
        print("✓ config.yaml found")
        return True
    else:
        print("✗ config.yaml not found")
        return False


def check_pmd():
    """Check if PMD is available."""
    import subprocess
    try:
        result = subprocess.run(
            ["pmd", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✓ PMD installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("⚠ PMD not found (optional - fallback analysis available)")
    except Exception as e:
        print(f"⚠ PMD check failed: {e}")
    return False


def create_sample_java():
    """Create sample Java file for testing."""
    sample_dir = Path("data/sample")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    sample_code = '''package com.example.sample;

import java.util.*;
import java.io.*;

/**
 * Sample large class for testing decomposition detection.
 * This class intentionally has too many responsibilities.
 */
public class LargeClassExample {
    
    // Too many fields
    private String name;
    private int id;
    private List<String> items;
    private Map<String, Object> config;
    private boolean active;
    private Date createdAt;
    private Date updatedAt;
    private String description;
    private int counter;
    private double score;
    
    // Constructor
    public LargeClassExample(String name, int id) {
        this.name = name;
        this.id = id;
        this.items = new ArrayList<>();
        this.config = new HashMap<>();
        this.active = true;
        this.createdAt = new Date();
    }
    
    // User management methods
    public void createUser(String username) {
        // Complex logic
        if (username != null && !username.isEmpty()) {
            System.out.println("Creating user: " + username);
        }
    }
    
    public void updateUser(String username, Map<String, String> data) {
        // More complex logic
        for (Map.Entry<String, String> entry : data.entrySet()) {
            System.out.println("Updating: " + entry.getKey());
        }
    }
    
    public void deleteUser(String username) {
        System.out.println("Deleting user: " + username);
    }
    
    // Order management methods
    public void createOrder(int orderId) {
        System.out.println("Creating order: " + orderId);
    }
    
    public void updateOrder(int orderId, String status) {
        System.out.println("Updating order " + orderId + " to " + status);
    }
    
    public void cancelOrder(int orderId) {
        System.out.println("Cancelling order: " + orderId);
    }
    
    // Payment methods
    public void processPayment(double amount) {
        if (amount > 0) {
            System.out.println("Processing payment: $" + amount);
        }
    }
    
    public void refundPayment(double amount) {
        System.out.println("Refunding: $" + amount);
    }
    
    // Notification methods
    public void sendEmail(String to, String subject) {
        System.out.println("Sending email to " + to);
    }
    
    public void sendSMS(String phone, String message) {
        System.out.println("Sending SMS to " + phone);
    }
    
    public void sendPushNotification(String deviceId) {
        System.out.println("Sending push to " + deviceId);
    }
    
    // Report methods
    public void generateReport(String type) {
        switch(type) {
            case "daily":
                generateDailyReport();
                break;
            case "weekly":
                generateWeeklyReport();
                break;
            case "monthly":
                generateMonthlyReport();
                break;
        }
    }
    
    private void generateDailyReport() {
        System.out.println("Generating daily report");
    }
    
    private void generateWeeklyReport() {
        System.out.println("Generating weekly report");
    }
    
    private void generateMonthlyReport() {
        System.out.println("Generating monthly report");
    }
    
    // Utility methods
    public String formatDate(Date date) {
        return date != null ? date.toString() : "";
    }
    
    public boolean validateInput(String input) {
        return input != null && !input.trim().isEmpty();
    }
    
    public int calculateTotal(List<Integer> values) {
        int total = 0;
        for (int v : values) {
            total += v;
        }
        return total;
    }
    
    // Getters and setters
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public int getId() { return id; }
    public void setId(int id) { this.id = id; }
    public List<String> getItems() { return items; }
    public void setItems(List<String> items) { this.items = items; }
    public boolean isActive() { return active; }
    public void setActive(boolean active) { this.active = active; }
}
'''
    
    sample_file = sample_dir / "LargeClassExample.java"
    sample_file.write_text(sample_code)
    print(f"✓ Created sample Java file: {sample_file}")
    
    return True


def main():
    """Run all setup checks."""
    print("=" * 50)
    print("Rule-Based Java Decomposition - Setup Check")
    print("=" * 50)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Configuration", check_config),
        ("PMD (optional)", check_pmd),
        ("Sample Data", create_sample_java),
    ]
    
    results = []
    for name, check in checks:
        print(f"\n{name}:")
        print("-" * 30)
        results.append(check())
    
    print()
    print("=" * 50)
    if all(results[:-1]):  # Ignore PMD result (optional)
        print("✓ Setup complete! Ready to run analysis.")
        print()
        print("Next steps:")
        print("  1. python run_pipeline.py --all")
        print("  2. Open results/reports/ for HTML report")
    else:
        print("⚠ Some checks failed. Please resolve issues above.")
    print("=" * 50)


if __name__ == "__main__":
    main()
