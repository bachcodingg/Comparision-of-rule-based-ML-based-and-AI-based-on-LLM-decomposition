#!/usr/bin/env python3
"""
ML-Based Code Smell Classifier.
Based on Rao et al. (2023), Dewangan et al. (2023).

Models: Random Forest, XGBoost, Gradient Boosting, Ensemble
"""

import pickle
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

import numpy as np
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
)
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

warnings.filterwarnings('ignore')


@dataclass
class ClassificationResult:
    """Classification result for a file."""
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


@dataclass 
class ModelPerformance:
    """Model performance metrics."""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    cv_mean: float
    cv_std: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SeverityClassifier:
    """4-level severity classifier (Dewangan et al. 2023)."""
    
    SEVERITY_LEVELS = ['NONE', 'MINOR', 'MAJOR', 'CRITICAL']
    SEVERITY_MAP = {0: 'NONE', 1: 'MINOR', 2: 'MAJOR', 3: 'CRITICAL'}
    RECOMMENDATIONS = {
        'NONE': "No action required. Class is well-designed.",
        'MINOR': "Monitor for growth. Consider refactoring if metrics increase.",
        'MAJOR': "Schedule refactoring. This class shows signs of becoming a God Class.",
        'CRITICAL': "URGENT: Immediate decomposition required. This is a severe God Class."
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.ensemble_model = None
        self.feature_names = None
        self.is_trained = False
        self._init_models()
    
    def _init_models(self):
        """Initialize ML models."""
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=100, max_depth=15, class_weight='balanced', 
            random_state=42, n_jobs=-1
        )
        
        if XGBOOST_AVAILABLE:
            self.models['xgboost'] = XGBClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.1,
                random_state=42, use_label_encoder=False, 
                eval_metric='mlogloss', verbosity=0
            )
        
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
        )
        
        self.models['svm'] = SVC(
            kernel='rbf', probability=True, class_weight='balanced', random_state=42
        )
    
    def train(self, X: np.ndarray, y: np.ndarray, 
              feature_names: Optional[List[str]] = None) -> Dict[str, ModelPerformance]:
        """Train all models."""
        self.feature_names = feature_names
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        
        performances = {}
        
        for name, model in self.models.items():
            self.logger.info(f"Training {name}...")
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            cv_scores = cross_val_score(model, X, y, cv=5, scoring='f1_weighted')
            
            perf = ModelPerformance(
                model_name=name,
                accuracy=round(accuracy_score(y_test, y_pred), 4),
                precision=round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                recall=round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                f1_score=round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                cv_mean=round(np.mean(cv_scores), 4),
                cv_std=round(np.std(cv_scores), 4)
            )
            performances[name] = perf
        
        # Create ensemble
        estimators = [(n, m) for n, m in self.models.items() if n != 'svm']
        if len(estimators) >= 2:
            self.ensemble_model = VotingClassifier(estimators=estimators, voting='soft')
            self.ensemble_model.fit(X_train, y_train)
            
            y_pred = self.ensemble_model.predict(X_test)
            cv_scores = cross_val_score(self.ensemble_model, X, y, cv=5, scoring='f1_weighted')
            
            performances['ensemble'] = ModelPerformance(
                model_name='ensemble',
                accuracy=round(accuracy_score(y_test, y_pred), 4),
                precision=round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                recall=round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                f1_score=round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                cv_mean=round(np.mean(cv_scores), 4),
                cv_std=round(np.std(cv_scores), 4)
            )
        
        self.is_trained = True
        return performances
    
    def predict(self, X: np.ndarray, model_name: str = 'ensemble') -> np.ndarray:
        """Predict severity levels."""
        if model_name == 'ensemble' and self.ensemble_model:
            return self.ensemble_model.predict(X)
        elif model_name in self.models:
            return self.models[model_name].predict(X)
        return self.models['random_forest'].predict(X)
    
    def predict_proba(self, X: np.ndarray, model_name: str = 'ensemble') -> np.ndarray:
        """Predict probabilities."""
        if model_name == 'ensemble' and self.ensemble_model:
            return self.ensemble_model.predict_proba(X)
        elif model_name in self.models:
            return self.models[model_name].predict_proba(X)
        return self.models['random_forest'].predict_proba(X)
    
    def classify_file(self, metrics: Dict, model_name: str = 'ensemble') -> ClassificationResult:
        """Classify a single file."""
        feature_order = self.feature_names or ['loc', 'sloc', 'wmc', 'cyclomatic', 
                                                'cbo', 'lcom', 'nom', 'noa']
        features = [metrics.get(f, 0) for f in feature_order]
        X = np.array(features).reshape(1, -1)
        
        pred = self.predict(X, model_name)[0]
        proba = self.predict_proba(X, model_name)[0]
        
        severity = self.SEVERITY_MAP.get(int(pred), 'UNKNOWN')
        confidence = float(max(proba)) * 100
        
        prob_dict = {}
        for i, level in enumerate(self.SEVERITY_LEVELS):
            if i < len(proba):
                prob_dict[level] = round(float(proba[i]) * 100, 2)
        
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
        if model_name not in self.models or not self.feature_names:
            return {}
        model = self.models[model_name]
        if hasattr(model, 'feature_importances_'):
            return dict(sorted(
                zip(self.feature_names, model.feature_importances_),
                key=lambda x: x[1], reverse=True
            ))
        return {}
    
    def save_model(self, path: str):
        """Save model to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'models': self.models,
                'ensemble': self.ensemble_model,
                'features': self.feature_names,
                'trained': self.is_trained
            }, f)
    
    def load_model(self, path: str):
        """Load model from disk."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.models = data['models']
        self.ensemble_model = data['ensemble']
        self.feature_names = data['features']
        self.is_trained = data['trained']


def generate_synthetic_training_data(n_samples: int = 2000, 
                                     random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic training data based on empirical distributions.
    
    Ranges include realistic overlap between severity levels (~15-20%) to prevent
    overfitting on perfectly separable data. Gaussian noise is added to simulate
    real-world metric variation.
    
    Based on threshold distributions from:
    - Dewangan et al. (2023) severity thresholds
    - Rao et al. (2023) empirical distributions
    - Gupta & Chauhan (2022) Java-specific ranges
    """
    np.random.seed(random_state)
    samples_per_class = n_samples // 4
    
    # Severity ranges with ~15-20% overlap between adjacent levels
    # This prevents the model from learning perfectly separable boundaries
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
    feature_order = ['loc', 'sloc', 'wmc', 'cyclomatic', 'cbo', 'lcom', 'nom', 'noa']
    
    for severity, r in ranges.items():
        for _ in range(samples_per_class):
            sample = []
            for feat in feature_order:
                low, high = r[feat]
                if feat == 'lcom':
                    # Use beta distribution for LCOM (bounded 0-1)
                    mid = (low + high) / 2
                    val = np.clip(np.random.normal(mid, (high - low) / 4), low, high)
                else:
                    # Use normal distribution centered in range with noise
                    mid = (low + high) / 2
                    std = (high - low) / 4  # ~95% within range
                    val = int(np.clip(np.random.normal(mid, std), low, high))
                sample.append(val)
            
            # Ensure sloc <= loc
            if sample[1] > sample[0]:
                sample[1] = int(sample[0] * 0.85)
            
            features.append(sample)
            labels.append(severity)
    
    idx = np.random.permutation(len(features))
    return np.array(features)[idx], np.array(labels)[idx]
