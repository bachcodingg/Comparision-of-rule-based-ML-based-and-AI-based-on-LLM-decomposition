#!/usr/bin/env python3
"""
Severity Classifier for God Class Detection

4-level severity classification based on Dewangan et al. (2023).
Uses ensemble of XGBoost, Random Forest, and Gradient Boosting.

Research Foundation:
- Dewangan et al. (2023): 99.12% accuracy with XGBoost + Chi-square
- Rao et al. (2023): 99% accuracy with RF + PCA + SMOTE
- Singh et al. (2024): 99.21% with EMBBC ensemble

Author: Research Implementation
Version: 1.0
"""

import logging
import pickle
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    VotingClassifier
)
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

warnings.filterwarnings('ignore')


@dataclass
class ClassificationResult:
    """Result of severity classification."""
    class_name: str
    file_path: str
    predicted_severity: str
    severity_score: int
    confidence: float
    probabilities: Dict[str, float]
    is_god_class: bool
    recommendation: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SeverityClassifier:
    """
    4-level severity classifier for God Class detection.
    
    Levels (Dewangan et al. 2023):
    - NONE (0): No code smell
    - MINOR (1): Low severity
    - MAJOR (2): Medium severity  
    - CRITICAL (3): High severity
    """
    
    SEVERITY_LEVELS = ['NONE', 'MINOR', 'MAJOR', 'CRITICAL']
    SEVERITY_MAP = {0: 'NONE', 1: 'MINOR', 2: 'MAJOR', 3: 'CRITICAL'}
    
    RECOMMENDATIONS = {
        'NONE': "No action required. Class is well-designed.",
        'MINOR': "Monitor for growth. Consider refactoring if metrics increase.",
        'MAJOR': "Schedule refactoring. This class shows signs of becoming a God Class.",
        'CRITICAL': "URGENT: Immediate decomposition required. Severe God Class detected."
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.ensemble = None
        self.feature_names = None
        self.is_trained = False
        
        self._init_models()
    
    def _init_models(self):
        """Initialize ML models based on research."""
        mc = self.config.get('models', {})
        
        # XGBoost - Best single model (Dewangan et al. 2023)
        if XGBOOST_AVAILABLE:
            xgb_cfg = mc.get('xgboost', {})
            self.models['xgboost'] = XGBClassifier(
                n_estimators=xgb_cfg.get('n_estimators', 100),
                max_depth=xgb_cfg.get('max_depth', 6),
                learning_rate=xgb_cfg.get('learning_rate', 0.1),
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss',
                verbosity=0
            )
        
        # Random Forest (Rao et al. 2023)
        rf_cfg = mc.get('random_forest', {})
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=rf_cfg.get('n_estimators', 100),
            max_depth=rf_cfg.get('max_depth', 15),
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        
        # Gradient Boosting
        gb_cfg = mc.get('gradient_boosting', {})
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=gb_cfg.get('n_estimators', 100),
            max_depth=gb_cfg.get('max_depth', 5),
            learning_rate=gb_cfg.get('learning_rate', 0.1),
            random_state=42
        )
        
        self.logger.info(f"Initialized {len(self.models)} ML models")
    
    def train(self, X: np.ndarray, y: np.ndarray, 
              feature_names: List[str] = None) -> Dict:
        """Train all models."""
        import time
        
        self.logger.info("Starting model training...")
        self.feature_names = feature_names
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        
        performances = {}
        
        # Train each model
        for name, model in self.models.items():
            self.logger.info(f"Training {name}...")
            start = time.time()
            
            model.fit(X_train, y_train)
            train_time = time.time() - start
            
            y_pred = model.predict(X_test)
            
            performances[name] = {
                'accuracy': round(accuracy_score(y_test, y_pred), 4),
                'precision': round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                'recall': round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                'f1_score': round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                'cv_scores': cross_val_score(model, X, y, cv=10, scoring='f1_weighted').tolist(),
                'train_time': round(train_time, 2)
            }
            
            cv_mean = np.mean(performances[name]['cv_scores'])
            self.logger.info(f"  {name}: Accuracy={performances[name]['accuracy']:.4f}, CV={cv_mean:.4f}")
        
        # Create ensemble (Singh et al. 2024 - EMBBC)
        self._create_ensemble(X_train, y_train)
        
        if self.ensemble:
            y_pred = self.ensemble.predict(X_test)
            performances['ensemble'] = {
                'accuracy': round(accuracy_score(y_test, y_pred), 4),
                'precision': round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                'recall': round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                'f1_score': round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                'cv_scores': cross_val_score(self.ensemble, X, y, cv=10, scoring='f1_weighted').tolist(),
            }
            self.logger.info(f"  ensemble: Accuracy={performances['ensemble']['accuracy']:.4f}")
        
        self.is_trained = True
        return performances
    
    def _create_ensemble(self, X_train, y_train):
        """Create voting ensemble."""
        estimators = [(n, m) for n, m in self.models.items()]
        if len(estimators) >= 2:
            self.ensemble = VotingClassifier(
                estimators=estimators,
                voting='soft',
                weights=[0.4, 0.35, 0.25][:len(estimators)]
            )
            self.ensemble.fit(X_train, y_train)
    
    def predict(self, X: np.ndarray, model_name: str = 'ensemble') -> np.ndarray:
        """Predict severity levels."""
        if not self.is_trained:
            raise RuntimeError("Model not trained")
        
        if model_name == 'ensemble' and self.ensemble:
            return self.ensemble.predict(X)
        elif model_name in self.models:
            return self.models[model_name].predict(X)
        return self.models['random_forest'].predict(X)
    
    def predict_proba(self, X: np.ndarray, model_name: str = 'ensemble') -> np.ndarray:
        """Predict probabilities."""
        if not self.is_trained:
            raise RuntimeError("Model not trained")
        
        if model_name == 'ensemble' and self.ensemble:
            return self.ensemble.predict_proba(X)
        elif model_name in self.models:
            return self.models[model_name].predict_proba(X)
        return self.models['random_forest'].predict_proba(X)
    
    def classify_file(self, metrics: Dict, model_name: str = 'ensemble') -> ClassificationResult:
        """Classify a single file."""
        if not self.is_trained:
            raise RuntimeError("Model not trained")
        
        features = [metrics.get(f, 0) for f in (self.feature_names or 
                   ['loc', 'sloc', 'wmc', 'cyclomatic', 'cbo', 'lcom', 'nom', 'noa'])]
        X = np.array(features).reshape(1, -1)
        
        pred = self.predict(X, model_name)[0]
        proba = self.predict_proba(X, model_name)[0]
        
        severity = self.SEVERITY_MAP.get(int(pred), 'UNKNOWN')
        confidence = float(max(proba)) * 100
        
        prob_dict = {self.SEVERITY_LEVELS[i]: round(float(proba[i]) * 100, 2) 
                    for i in range(min(len(proba), len(self.SEVERITY_LEVELS)))}
        
        return ClassificationResult(
            class_name=metrics.get('class_name', 'Unknown'),
            file_path=metrics.get('file_path', ''),
            predicted_severity=severity,
            severity_score=int(pred),
            confidence=round(confidence, 2),
            probabilities=prob_dict,
            is_god_class=int(pred) >= 2,
            recommendation=self.RECOMMENDATIONS[severity]
        )
    
    def get_feature_importance(self, model_name: str = 'random_forest') -> Dict[str, float]:
        """Get feature importance."""
        if not self.is_trained or not self.feature_names:
            return {}
        
        if model_name in self.models:
            model = self.models[model_name]
            if hasattr(model, 'feature_importances_'):
                imp = {self.feature_names[i]: float(model.feature_importances_[i])
                      for i in range(len(self.feature_names))}
                return dict(sorted(imp.items(), key=lambda x: x[1], reverse=True))
        return {}
    
    def save_model(self, path: str):
        """Save trained models."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            'models': self.models,
            'ensemble': self.ensemble,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        self.logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load trained models."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.models = data['models']
        self.ensemble = data['ensemble']
        self.feature_names = data['feature_names']
        self.is_trained = data['is_trained']
        self.logger.info(f"Model loaded from {path}")


def generate_training_data(n_samples: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data based on research thresholds.
    Based on Dewangan et al. (2023) severity thresholds.
    
    Ranges include realistic overlap between severity levels (~15-20%) to prevent
    overfitting on perfectly separable data. Gaussian noise is added to simulate
    real-world metric variation.
    """
    np.random.seed(42)
    per_class = n_samples // 4
    
    # Severity ranges with ~15-20% overlap between adjacent levels
    ranges = {
        0: {'loc': (30, 220), 'sloc': (25, 200), 'wmc': (3, 35), 'cyclomatic': (3, 25),
            'cbo': (0, 6), 'lcom': (0.0, 0.35), 'nom': (2, 12), 'noa': (0, 6)},
        1: {'loc': (180, 550), 'sloc': (160, 500), 'wmc': (25, 70), 'cyclomatic': (18, 50),
            'cbo': (4, 12), 'lcom': (0.25, 0.55), 'nom': (8, 24), 'noa': (4, 12)},
        2: {'loc': (450, 1100), 'sloc': (400, 1000), 'wmc': (55, 120), 'cyclomatic': (35, 95),
            'cbo': (9, 25), 'lcom': (0.45, 0.75), 'nom': (18, 48), 'noa': (8, 24)},
        3: {'loc': (900, 2500), 'sloc': (800, 2200), 'wmc': (90, 250), 'cyclomatic': (70, 200),
            'cbo': (18, 50), 'lcom': (0.65, 1.0), 'nom': (35, 100), 'noa': (18, 50)}
    }
    
    features, labels = [], []
    feat_names = ['loc', 'sloc', 'wmc', 'cyclomatic', 'cbo', 'lcom', 'nom', 'noa']
    
    for sev, r in ranges.items():
        for _ in range(per_class):
            sample = []
            for f in feat_names:
                lo, hi = r[f]
                if f == 'lcom':
                    mid = (lo + hi) / 2
                    val = np.clip(np.random.normal(mid, (hi - lo) / 4), lo, hi)
                else:
                    mid = (lo + hi) / 2
                    std = (hi - lo) / 4
                    val = int(np.clip(np.random.normal(mid, std), lo, hi))
                sample.append(val)
            
            # Ensure sloc <= loc
            if sample[1] > sample[0]:
                sample[1] = int(sample[0] * 0.85)
            
            features.append(sample)
            labels.append(sev)
    
    idx = np.random.permutation(len(features))
    return np.array(features)[idx], np.array(labels)[idx]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    X, y = generate_training_data(2000)
    feat_names = ['loc', 'sloc', 'wmc', 'cyclomatic', 'cbo', 'lcom', 'nom', 'noa']
    
    classifier = SeverityClassifier()
    performances = classifier.train(X, y, feat_names)
    
    print("\n" + "="*60)
    print("MODEL PERFORMANCE")
    print("="*60)
    for name, perf in performances.items():
        print(f"{name}: Accuracy={perf['accuracy']:.4f}, F1={perf['f1_score']:.4f}")
