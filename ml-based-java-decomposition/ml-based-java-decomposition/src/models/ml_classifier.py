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
from sklearn.decomposition import PCA
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

try:
    from imblearn.over_sampling import SMOTE
    IMBLEARN_AVAILABLE = True
except ImportError:
    IMBLEARN_AVAILABLE = False

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

warnings.filterwarnings('ignore')

# Model inputs, in order. 'cyclomatic' was removed: the extractor computed it as
# the same number as WMC, while the generator sampled it independently, so the
# model was trained on a feature that behaved differently on real files.
FEATURES = ['loc', 'sloc', 'wmc', 'cbo', 'lcom', 'nom', 'noa']


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
    f1_macro: float = 0.0
    
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
    
    def __init__(self, config: Optional[Dict] = None,
                 use_smote: bool = False, use_pca: bool = False):
        """
        Args:
            config: Parsed config.yaml.
            use_smote: Oversample the training split with SMOTE (k=5).
                The synthetic data is generated with equal class sizes, so
                this only changes the model when the classes are imbalanced.
            use_pca: Standardise the features and keep the principal
                components that explain 95% of the variance. Models then no
                longer see the raw metrics, so per-metric feature importance
                is not available in this mode.

        Both default to False, which is the configuration that produced the
        committed results.
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.use_smote = use_smote
        self.use_pca = use_pca
        self.models = {}
        self.ensemble_model = None
        self.feature_names = None
        self.is_trained = False
        self._init_models()
        if self.use_pca:
            self.models = {
                name: make_pipeline(StandardScaler(), PCA(n_components=0.95), model)
                for name, model in self.models.items()
            }
    
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

        # Cross-validation runs on the training split only. It previously ran
        # on all data, so the held-out split was also used for model scoring.
        X_cv, y_cv = X_train, y_train

        if self.use_smote:
            if not IMBLEARN_AVAILABLE:
                raise RuntimeError("use_smote=True requires imbalanced-learn")
            # Resample the training split only, so the held-out split stays
            # untouched. Cross-validation below uses the training split as it
            # was before resampling.
            before = np.bincount(y_train)
            X_train, y_train = SMOTE(k_neighbors=5, random_state=42).fit_resample(X_train, y_train)
            self.logger.info(f"SMOTE: class counts {before.tolist()} -> "
                             f"{np.bincount(y_train).tolist()}")

        performances = {}
        
        for name, model in self.models.items():
            self.logger.info(f"Training {name}...")
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            cv_scores = cross_val_score(model, X_cv, y_cv, cv=5, scoring='f1_weighted')
            
            perf = ModelPerformance(
                model_name=name,
                accuracy=round(accuracy_score(y_test, y_pred), 4),
                precision=round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                recall=round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                f1_score=round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                cv_mean=round(np.mean(cv_scores), 4),
                cv_std=round(np.std(cv_scores), 4),
                f1_macro=round(f1_score(y_test, y_pred, average='macro', zero_division=0), 4)
            )
            performances[name] = perf
        
        # Create ensemble
        estimators = [(n, m) for n, m in self.models.items() if n != 'svm']
        if len(estimators) >= 2:
            self.ensemble_model = VotingClassifier(estimators=estimators, voting='soft')
            self.ensemble_model.fit(X_train, y_train)
            
            y_pred = self.ensemble_model.predict(X_test)
            cv_scores = cross_val_score(self.ensemble_model, X_cv, y_cv, cv=5, scoring='f1_weighted')
            
            performances['ensemble'] = ModelPerformance(
                model_name='ensemble',
                accuracy=round(accuracy_score(y_test, y_pred), 4),
                precision=round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                recall=round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                f1_score=round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                cv_mean=round(np.mean(cv_scores), 4),
                cv_std=round(np.std(cv_scores), 4),
                f1_macro=round(f1_score(y_test, y_pred, average='macro', zero_division=0), 4)
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
        feature_order = self.feature_names or FEATURES
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
        if self.use_pca:
            # Importances would refer to principal components, not metrics.
            return {}
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
                'trained': self.is_trained,
                'use_smote': self.use_smote,
                'use_pca': self.use_pca
            }, f)
    
    def load_model(self, path: str):
        """Load model from disk."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.models = data['models']
        self.ensemble_model = data['ensemble']
        self.feature_names = data['features']
        self.is_trained = data['trained']
        self.use_smote = data.get('use_smote', False)
        self.use_pca = data.get('use_pca', False)


def generate_synthetic_training_data(n_samples: int = 2000,
                                     random_state: int = 42,
                                     class_proportions: Optional[List[float]] = None
                                     ) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic training data from hand-chosen metric ranges.

    Every sample is drawn from the range box of one severity level and labelled
    with that level. The label is therefore a function of the generator, not of
    any real code: accuracy measured on data from this function shows that a
    model can recover the ranges below, and nothing about detecting God Classes
    in real projects.

    The ranges are placed around the severity thresholds used by the rule-based
    pipeline (cut-offs in the style of Dewangan et al. 2023 and Gupta & Chauhan
    2022) with roughly 15-20% overlap between adjacent levels. They were chosen
    by the author and adjusted during development while the six sample classes
    were being classified; they are not fitted to a labelled dataset.

    Args:
        n_samples: total number of samples.
        random_state: seed for numpy's global generator.
        class_proportions: share of NONE, MINOR, MAJOR, CRITICAL samples.
            Default is equal shares. Pass e.g. [0.60, 0.25, 0.10, 0.05] to
            create the class imbalance that SMOTE is meant to correct.
    """
    np.random.seed(random_state)
    if class_proportions is None:
        class_proportions = [0.25, 0.25, 0.25, 0.25]
    if len(class_proportions) != 4 or abs(sum(class_proportions) - 1.0) > 1e-6:
        raise ValueError("class_proportions must be four shares that sum to 1")
    class_counts = [int(round(n_samples * share)) for share in class_proportions]

    ranges = {
        0: {'loc': (30, 220), 'sloc': (25, 200), 'wmc': (3, 35),
            'cbo': (0, 6), 'lcom': (0.0, 0.35), 'nom': (2, 12), 'noa': (0, 6)},
        1: {'loc': (180, 550), 'sloc': (160, 500), 'wmc': (25, 70),
            'cbo': (4, 12), 'lcom': (0.25, 0.55), 'nom': (8, 24), 'noa': (4, 12)},
        2: {'loc': (450, 1100), 'sloc': (400, 1000), 'wmc': (55, 120),
            'cbo': (9, 25), 'lcom': (0.45, 0.75), 'nom': (18, 48), 'noa': (8, 24)},
        3: {'loc': (900, 2500), 'sloc': (800, 2200), 'wmc': (90, 250),
            'cbo': (18, 50), 'lcom': (0.65, 1.0), 'nom': (35, 100), 'noa': (18, 50)}
    }

    features, labels = [], []
    for severity, r in ranges.items():
        for _ in range(class_counts[severity]):
            sample = []
            for feat in FEATURES:
                low, high = r[feat]
                mid = (low + high) / 2
                std = (high - low) / 4  # about 95% of draws fall inside the range
                val = np.clip(np.random.normal(mid, std), low, high)
                sample.append(float(val) if feat == 'lcom' else int(val))

            # SLOC cannot exceed LOC
            if sample[1] > sample[0]:
                sample[1] = int(sample[0] * 0.85)

            features.append(sample)
            labels.append(severity)

    idx = np.random.permutation(len(features))
    return np.array(features)[idx], np.array(labels)[idx]
