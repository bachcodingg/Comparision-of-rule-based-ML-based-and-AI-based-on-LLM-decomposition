#!/usr/bin/env python3
"""
Feature Selector for Code Smell Detection

Implements Chi-square and PCA feature selection.
Based on Dewangan et al. (2023) - Chi-square best for code smell.

Author: Research Implementation
Version: 1.0
"""

import logging
from typing import List, Optional, Dict

import numpy as np
from sklearn.feature_selection import SelectKBest, chi2, mutual_info_classif
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler


class FeatureSelector:
    """Feature selection using Chi-square or PCA."""
    
    METHODS = ['chi_square', 'pca', 'mutual_info', 'none']
    
    def __init__(self, method: str = 'chi_square', config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.method = method if method in self.METHODS else 'chi_square'
        
        cfg = self.config.get('preprocessing', {}).get('feature_selection', {})
        self.n_features = cfg.get('n_features', 10)
        
        self.selector = None
        self.scaler = MinMaxScaler()
        self.feature_names = None
        self.selected_features = None
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray, 
            feature_names: List[str] = None) -> 'FeatureSelector':
        """Fit selector to data."""
        self.feature_names = feature_names or [f'f{i}' for i in range(X.shape[1])]
        
        X_scaled = self.scaler.fit_transform(X)
        if self.method == 'chi_square':
            X_scaled = np.abs(X_scaled)
        
        k = min(self.n_features, X.shape[1])
        
        if self.method == 'chi_square':
            self.selector = SelectKBest(chi2, k=k)
            self.selector.fit(X_scaled, y)
            mask = self.selector.get_support()
            self.selected_features = [n for n, m in zip(self.feature_names, mask) if m]
            
        elif self.method == 'pca':
            self.selector = PCA(n_components=k)
            self.selector.fit(X_scaled)
            self.selected_features = self.feature_names
            var = sum(self.selector.explained_variance_ratio_)
            self.logger.info(f"PCA variance: {var:.4f}")
            
        elif self.method == 'mutual_info':
            self.selector = SelectKBest(
                lambda X, y: mutual_info_classif(X, y, random_state=42), k=k)
            self.selector.fit(X_scaled, y)
            mask = self.selector.get_support()
            self.selected_features = [n for n, m in zip(self.feature_names, mask) if m]
        else:
            self.selected_features = self.feature_names
        
        self.is_fitted = True
        self.logger.info(f"Selected {len(self.selected_features)} features using {self.method}")
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform data using fitted selector."""
        if not self.is_fitted:
            raise RuntimeError("Selector not fitted")
        
        X_scaled = self.scaler.transform(X)
        if self.method == 'chi_square':
            X_scaled = np.abs(X_scaled)
        
        if self.method == 'none' or self.selector is None:
            return X_scaled
        
        return self.selector.transform(X_scaled)
    
    def fit_transform(self, X: np.ndarray, y: np.ndarray,
                     feature_names: List[str] = None) -> np.ndarray:
        """Fit and transform."""
        self.fit(X, y, feature_names)
        return self.transform(X)
    
    def get_feature_scores(self) -> Dict[str, float]:
        """Get feature scores."""
        if not self.is_fitted or self.method in ['pca', 'none']:
            return {}
        
        if hasattr(self.selector, 'scores_'):
            return {self.feature_names[i]: float(self.selector.scores_[i])
                   for i in range(len(self.feature_names))}
        return {}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    np.random.seed(42)
    X = np.random.randn(500, 15)
    y = np.random.randint(0, 4, 500)
    
    selector = FeatureSelector(method='chi_square')
    X_sel = selector.fit_transform(X, y)
    print(f"Shape: {X.shape} → {X_sel.shape}")
    print(f"Selected: {selector.selected_features}")
