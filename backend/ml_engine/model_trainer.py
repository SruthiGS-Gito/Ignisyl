"""
Model Training Pipeline for IGNISYL
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional
import json
import pandas as pd
import numpy as np

# Get project root (IGNISYL folder)
current_dir = os.path.dirname(os.path.abspath(__file__))  # ml_engine
backend_dir = os.path.dirname(current_dir)                 # backend
project_root = os.path.dirname(backend_dir)                # IGNISYL

# Add project root to path so we can import config
sys.path.insert(0, project_root)

# NOW we can import from config folder at root level
from config.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelTrainingPipeline:
    """Complete pipeline for training IGNISYL ML models"""
    
    def __init__(self, data_path: Optional[str] = None, model_path: Optional[str] = None):
        self.data_path = data_path or os.path.join(settings.DATA_PATH, "synthetic")
        self.model_path = model_path or settings.MODEL_PATH
        self.training_results = {}
        
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(self.model_path, exist_ok=True)
        
        logger.info("="*60)
        logger.info("Training Pipeline Initialized")
        logger.info("="*60)
        logger.info(f"Data: {self.data_path}")
        logger.info(f"Models: {self.model_path}")
    
    def generate_training_data(self, num_users=50, num_days=30, use_real_data=True, real_data_ratio=0.3):
        logger.info("\n" + "="*60)
        logger.info("Step 1: Generating Training Data")
        logger.info("="*60)
        
        try:
            # Add backend to path for these imports
            sys.path.insert(0, backend_dir)
            
            from ml_engine.data_generator import BehavioralDataGenerator
            from ml_engine.real_data_loader import RealWorldDataLoader
            
            logger.info("📊 Generating synthetic data...")
            generator = BehavioralDataGenerator(num_users, num_days)
            normal, anomalous = generator.generate_complete_dataset()
            synthetic_df = pd.DataFrame(normal + anomalous)
            
            logger.info(f"   ✅ Generated {len(synthetic_df):,} synthetic activities")
            
            if use_real_data:
                logger.info("\n📥 Loading real-world data...")
                real_loader = RealWorldDataLoader(os.path.join(project_root, "data", "real_world"))
                final_df = real_loader.combine_with_synthetic(synthetic_df, real_data_ratio)
            else:
                final_df = synthetic_df
                logger.info("   Using only synthetic data")
            
            output = os.path.join(self.data_path, "combined_activities.csv")
            final_df.to_csv(output, index=False)
            
            self.training_results['data_generation'] = {
                'status': 'success',
                'total': len(final_df),
                'features': len(final_df.columns),
                'normal': int((~final_df['is_suspicious']).sum()),
                'suspicious': int(final_df['is_suspicious'].sum())
            }
            
            logger.info(f"\n✅ Saved: {output}")
            logger.info(f"   Total: {len(final_df):,} records")
            logger.info(f"   Features: {len(final_df.columns)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def train_anomaly_detector(self):
        logger.info("\n" + "="*60)
        logger.info("Step 2: Training Anomaly Detector")
        logger.info("="*60)
        
        try:
            sys.path.insert(0, backend_dir)
            from ml_engine.anomaly_detector import BehavioralAnomalyDetector
            
            detector = BehavioralAnomalyDetector()
            detector.train_models(self.data_path)
            detector.save_models(self.model_path)
            
            self.training_results['anomaly_detector'] = {
                'status': 'success',
                'models': list(detector.models.keys())
            }
            
            logger.info("✅ Anomaly detector trained")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def train_hybrid_detector(self):
        logger.info("\n" + "="*60)
        logger.info("Step 3: Training Hybrid Detector")
        logger.info("="*60)
        
        try:
            sys.path.insert(0, backend_dir)
            from ml_engine.hybrid_detector import AdvancedHybridDetector
            
            data_file = os.path.join(self.data_path, "combined_activities.csv")
            df = pd.read_csv(data_file)
            
            # Prepare features
            features = ['hour', 'day_of_week', 'file_size', 'network_bytes', 'is_weekend', 'is_business_hours']
            
            for col in features:
                if col not in df.columns:
                    df[col] = 0 if col in ['file_size', 'network_bytes'] else False
            
            X = df[features].fillna(0).values
            y = df['is_suspicious'].astype(int).values if 'is_suspicious' in df.columns else None
            
            detector = AdvancedHybridDetector()
            detector.fit(X, y)
            
            self.training_results['hybrid_detector'] = {'status': 'success'}
            logger.info("✅ Hybrid detector trained")
            return True
            
        except Exception as e:
            logger.error(f"⚠️ Hybrid training failed: {e}")
            return False
    
    def validate_models(self):
        logger.info("\n" + "="*60)
        logger.info("Step 4: Validating Models")
        logger.info("="*60)
        
        try:
            sys.path.insert(0, backend_dir)
            from ml_engine.anomaly_detector import BehavioralAnomalyDetector
            
            detector = BehavioralAnomalyDetector()
            if not detector.load_models(self.model_path):
                logger.warning("Could not load models for validation")
                return False
            
            data_file = os.path.join(self.data_path, "combined_activities.csv")
            df = pd.read_csv(data_file)
            
            test_sample = df.sample(n=min(100, len(df)), random_state=42)
            
            results = []
            for _, row in test_sample.iterrows():
                try:
                    result = detector.predict_single_activity(row.to_dict())
                    results.append(result['risk_score'])
                except:
                    pass
            
            if results:
                avg_risk = np.mean(results)
                self.training_results['validation'] = {
                    'status': 'success',
                    'samples': len(results),
                    'avg_risk': float(avg_risk)
                }
                logger.info(f"✅ Validated {len(results)} samples (avg risk: {avg_risk:.2f})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"⚠️ Validation failed: {e}")
            return False
    
    def save_report(self):
        try:
            report_file = os.path.join(self.model_path, "training_report.json")
            report = {
                'date': datetime.now().isoformat(),
                'results': self.training_results
            }
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📄 Report: {report_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return False
    
    def run_complete_pipeline(self, num_users=50, num_days=30, use_real_data=True):
        logger.info("\n" + "="*70)
        logger.info("IGNISYL ML TRAINING PIPELINE")
        logger.info("="*70)
        
        start = datetime.now()
        
        # Run pipeline steps
        if not self.generate_training_data(num_users, num_days, use_real_data):
            logger.error("Pipeline failed at data generation")
            return False
        
        if not self.train_anomaly_detector():
            logger.error("Pipeline failed at anomaly detector training")
            return False
        
        # Optional steps
        self.train_hybrid_detector()
        self.validate_models()
        self.save_report()
        
        duration = (datetime.now() - start).total_seconds()
        
        logger.info("\n" + "="*70)
        logger.info("✅ TRAINING COMPLETE")
        logger.info("="*70)
        logger.info(f"⏱️  Time: {duration:.2f} seconds")
        logger.info(f"📁 Models: {self.model_path}")
        logger.info("="*70 + "\n")
        
        return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train IGNISYL ML models')
    parser.add_argument('--users', type=int, default=50, help='Number of users')
    parser.add_argument('--days', type=int, default=30, help='Days of activity')
    parser.add_argument('--no-real-data', action='store_true', help='Skip real-world data')
    
    args = parser.parse_args()
    
    pipeline = ModelTrainingPipeline()
    success = pipeline.run_complete_pipeline(
        num_users=args.users,
        num_days=args.days,
        use_real_data=not args.no_real_data
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()