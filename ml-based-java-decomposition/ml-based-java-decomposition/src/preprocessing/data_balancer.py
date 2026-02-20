#!/usr/bin/env python3
"""
Data Balancer for Code Smell Detection

Implements SMOTE and other balancing techniques.
Based on Rao et al. (2023) - SMOTE improves severity detection.

Author: Research Implementation
Version: 1.0
"""

import logging
from typing import Tuple, Optional, Dict

import numpy as np

try:
    from imblearn.over_sampling import SMOTE, ADASYN, RandomOverSampler
    from imblearn.combine import SMOTETomek
    IMBLEARN_AVAILABLE = True
except ImportError:
    IMBLEARN_AVAILABLE = False


class DataBalancer:
    """Data balancing using SMOTE (Rao et al. 2023)."""
    
    METHODS = ['smote', 'adasyn', 'smote_tomek', 'random_over', 'none']
    
    def __init__(self, method: str = 'smote', config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.method = method if method in self.METHODS else 'smote'
        self.sampler = None
        
        cfg = self.config.get('preprocessing', {}).get('balancing', {})
        self.k_neighbors = cfg.get('k_neighbors', 5)
        self.random_state = cfg.get('random_state', 42)
        
        self._init_sampler()
    
    def _init_sampler(self):
        if not IMBLEARN_AVAILABLE:
            self.logger.warning("imbalanced-learn not available")
            return
        
        if self.method == 'smote':
            self.sampler = SMOTE(k_neighbors=min(self.k_neighbors, 5), 
                                random_state=self.random_state)
        elif self.method == 'adasyn':
            self.sampler = ADASYN(n_neighbors=min(self.k_neighbors, 5),
                                 random_state=self.random_state)
        elif self.method == 'smote_tomek':
            self.sampler = SMOTETomek(random_state=self.random_state)
        elif self.method == 'random_over':
            self.sampler = RandomOverSampler(random_state=self.random_state)
    
    def balance(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Balance dataset using SMOTE."""
        unique, counts = np.unique(y, return_counts=True)
        self.logger.info(f"Original distribution: {dict(zip(unique, counts))}")
        
        if self.sampler is None or self.method == 'none':
            return X, y
        
        try:
            # Adjust k_neighbors if needed
            min_samples = min(counts)
            if min_samples < self.k_neighbors and self.method == 'smote':
                k = max(1, min_samples - 1)
                self.sampler = SMOTE(k_neighbors=k, random_state=self.random_state)
            
            X_bal, y_bal = self.sampler.fit_resample(X, y)
            
            unique, counts = np.unique(y_bal, return_counts=True)
            self.logger.info(f"Balanced distribution: {dict(zip(unique, counts))}")
            self.logger.info(f"Samples: {len(y)} → {len(y_bal)}")
            
            return X_bal, y_bal
        except Exception as e:
            self.logger.error(f"Balancing error: {e}")
            return X, y
    
    def get_imbalance_ratio(self, y: np.ndarray) -> float:
        """Calculate imbalance ratio."""
        _, counts = np.unique(y, return_counts=True)
        return float(max(counts) / min(counts)) if len(counts) > 1 else 1.0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    np.random.seed(42)
    X = np.random.randn(327, 8)
    y = np.array([0]*280 + [1]*47)
    
    balancer = DataBalancer(method='smote')
    X_bal, y_bal = balancer.balance(X, y)
    print(f"Ratio: {balancer.get_imbalance_ratio(y):.2f} → {balancer.get_imbalance_ratio(y_bal):.2f}")
