"""
Real-World Dataset Loader for IGNISYL (Production Version)
Loads complete KDD Cup 1999 dataset with maximum diversity
"""

import pandas as pd
import numpy as np
import os
import urllib.request
import gzip
import shutil
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealWorldDataLoader:
    """Load and preprocess real-world security datasets"""
    
    def __init__(self, data_dir: str = "./data/real_world"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"📁 Data directory: {os.path.abspath(data_dir)}")
        
    def download_kdd_cup_1999(self, use_full_dataset: bool = False) -> Optional[str]:
        """
        Download KDD Cup 1999 dataset
        
        Args:
            use_full_dataset: If True, downloads full dataset (75MB), else 10% sample
        """
        logger.info("="*60)
        logger.info("📥 KDD Cup 1999 Dataset Downloader")
        logger.info("="*60)
        
        if use_full_dataset:
            # Full dataset - 494,021 records (better for production)
            url = "http://kdd.ics.uci.edu/databases/kddcup99/kddcup.data.gz"
            gz_file = os.path.join(self.data_dir, "kddcup.data.gz")
            csv_file = os.path.join(self.data_dir, "kddcup.data.csv")
            logger.info("📦 Mode: FULL DATASET (494K records)")
        else:
            # 10% sample - 49,402 records (faster for testing)
            url = "http://kdd.ics.uci.edu/databases/kddcup99/kddcup.data_10_percent.gz"
            gz_file = os.path.join(self.data_dir, "kddcup.data_10_percent.gz")
            csv_file = os.path.join(self.data_dir, "kddcup.data_10_percent.csv")
            logger.info("📦 Mode: 10% SAMPLE (49K records)")
        
        # Check if already downloaded
        if os.path.exists(csv_file):
            logger.info("✅ Dataset already exists!")
            logger.info(f"   Location: {csv_file}")
            file_size = os.path.getsize(csv_file) / (1024 * 1024)  # MB
            logger.info(f"   Size: {file_size:.2f} MB")
            return csv_file
        
        try:
            # Download with progress
            logger.info(f"📡 Downloading from: {url}")
            logger.info("   This may take a few minutes...")
            
            def reporthook(blocknum, blocksize, totalsize):
                readsofar = blocknum * blocksize
                if totalsize > 0:
                    percent = readsofar * 100 / totalsize
                    s = f"\r   Progress: {percent:5.1f}% ({readsofar / (1024*1024):.1f}/{totalsize / (1024*1024):.1f} MB)"
                    print(s, end='', flush=True)
            
            urllib.request.urlretrieve(url, gz_file, reporthook)
            print()  # New line
            
            logger.info("✅ Download complete!")
            
            # Decompress
            logger.info("📦 Extracting...")
            with gzip.open(gz_file, 'rb') as f_in:
                with open(csv_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            os.remove(gz_file)
            
            logger.info("✅ Extraction complete!")
            logger.info(f"   Saved to: {csv_file}")
            
            return csv_file
            
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return None
    
    def load_kdd_cup_1999(self, sample_size: Optional[int] = None, 
                         balanced: bool = True) -> Optional[pd.DataFrame]:
        """
        Load KDD Cup 1999 dataset with balancing options
        
        Args:
            sample_size: Number of records to load (None = load all)
            balanced: If True, ensures 70-30 normal-attack ratio
        """
        logger.info("\n" + "="*60)
        logger.info("📊 Loading KDD Cup 1999 Dataset")
        logger.info("="*60)
        
        # Download if needed
        csv_file = self.download_kdd_cup_1999(use_full_dataset=False)
        
        if not csv_file or not os.path.exists(csv_file):
            logger.error("❌ Failed to load dataset")
            return None
        
        # Column names
        columns = [
            'duration', 'protocol_type', 'service', 'flag', 'src_bytes',
            'dst_bytes', 'land', 'wrong_fragment', 'urgent', 'hot',
            'num_failed_logins', 'logged_in', 'num_compromised', 'root_shell',
            'su_attempted', 'num_root', 'num_file_creations', 'num_shells',
            'num_access_files', 'num_outbound_cmds', 'is_host_login',
            'is_guest_login', 'count', 'srv_count', 'serror_rate',
            'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate',
            'same_srv_rate', 'diff_srv_rate', 'srv_diff_host_rate',
            'dst_host_count', 'dst_host_srv_count', 'dst_host_same_srv_rate',
            'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
            'dst_host_srv_diff_host_rate', 'dst_host_serror_rate',
            'dst_host_srv_serror_rate', 'dst_host_rerror_rate',
            'dst_host_srv_rerror_rate', 'attack_type'
        ]
        
        try:
            logger.info(f"📖 Reading dataset...")
            
            # Load full dataset or sample
            df = pd.read_csv(csv_file, names=columns, nrows=sample_size)
            df['attack_type'] = df['attack_type'].str.strip('.')
            
            # Create binary label
            df['is_attack'] = df['attack_type'] != 'normal'
            
            # Balance dataset if requested
            if balanced:
                logger.info("⚖️ Balancing dataset...")
                
                normal_df = df[df['is_attack'] == False]
                attack_df = df[df['is_attack'] == True]
                
                # Target: 70% normal, 30% attacks
                if sample_size:
                    normal_size = int(sample_size * 0.7)
                    attack_size = int(sample_size * 0.3)
                else:
                    # Use all attacks, sample normal to maintain 70-30 ratio
                    attack_size = len(attack_df)
                    normal_size = int(attack_size * (70/30))
                
                # Sample from each class
                normal_sample = normal_df.sample(n=min(normal_size, len(normal_df)), random_state=42)
                attack_sample = attack_df.sample(n=min(attack_size, len(attack_df)), random_state=42)
                
                # Combine
                df = pd.concat([normal_sample, attack_sample], ignore_index=True)
                df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # Shuffle
            
            # Statistics
            normal_count = (~df['is_attack']).sum()
            attack_count = df['is_attack'].sum()
            unique_attacks = df[df['is_attack']]['attack_type'].nunique()
            
            logger.info(f"✅ Loaded {len(df):,} records")
            logger.info(f"\n📈 Dataset Statistics:")
            logger.info(f"   Normal records: {normal_count:,} ({normal_count/len(df)*100:.1f}%)")
            logger.info(f"   Attack records: {attack_count:,} ({attack_count/len(df)*100:.1f}%)")
            logger.info(f"   Unique attacks: {unique_attacks}")
            
            # Show attack distribution
            logger.info(f"\n🎯 Top 10 Attack Types:")
            top_attacks = df[df['is_attack']]['attack_type'].value_counts().head(10)
            for i, (attack, count) in enumerate(top_attacks.items(), 1):
                logger.info(f"   {i:2}. {attack:20} {count:6,} ({count/attack_count*100:5.1f}%)")
            
            # Feature statistics
            logger.info(f"\n📊 Feature Statistics:")
            logger.info(f"   Total features: {len(columns)}")
            logger.info(f"   Numeric features: {df.select_dtypes(include=[np.number]).shape[1]}")
            logger.info(f"   Categorical features: {df.select_dtypes(include=['object']).shape[1]}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to load KDD dataset: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def transform_kdd_to_ignisyl(self, kdd_df: pd.DataFrame) -> pd.DataFrame:
        """Transform KDD Cup data to IGNISYL format with all features"""
        logger.info("\n🔄 Transforming to IGNISYL format...")
        
        activities = []
        
        # Attack type to activity type mapping
        attack_mapping = {
            'neptune': 'network_access', 'smurf': 'network_access', 'pod': 'network_access',
            'teardrop': 'network_access', 'land': 'network_access', 'back': 'network_access',
            'portsweep': 'system_command', 'ipsweep': 'system_command', 'nmap': 'system_command',
            'satan': 'system_command', 'buffer_overflow': 'privilege_escalation',
            'loadmodule': 'privilege_escalation', 'rootkit': 'privilege_escalation',
            'perl': 'privilege_escalation', 'warezclient': 'file_download',
            'warezmaster': 'file_upload', 'ftp_write': 'file_upload',
            'guess_passwd': 'login', 'spy': 'email_sent', 'phf': 'network_access',
            'multihop': 'network_access', 'imap': 'email_sent'
        }
        
        for idx, row in kdd_df.iterrows():
            attack_type = row['attack_type']
            is_attack = row.get('is_attack', attack_type != 'normal')
            
            # Determine activity type
            activity_type = attack_mapping.get(attack_type, 'network_access')
            
            # Set confidence scores
            if is_attack:
                confidence = np.random.uniform(0.7, 0.95)
            else:
                confidence = np.random.uniform(0.1, 0.3)
            
            # Create rich activity record with ALL features
            activity = {
                # Identity
                'user_id': f"user_{np.random.randint(1, 51):03d}",
                'username': f"user{np.random.randint(1, 51)}",
                'department': np.random.choice(['IT', 'Finance', 'HR', 'Sales', 'Marketing', 'Operations']),
                
                # Activity details
                'activity_type': activity_type,
                'timestamp': pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(0, 30)),
                
                # Network features (from KDD)
                'source_ip': f"192.168.{np.random.randint(1,10)}.{np.random.randint(1,255)}",
                'destination_ip': f"10.0.{np.random.randint(0,255)}.{np.random.randint(1,255)}",
                'protocol': str(row['protocol_type']),
                'service': str(row['service']),
                'flag': str(row['flag']),
                
                # Size features
                'src_bytes': int(row['src_bytes']),
                'dst_bytes': int(row['dst_bytes']),
                'bytes_transferred': int(row['src_bytes'] + row['dst_bytes']),
                'network_bytes': int(row['dst_bytes']),
                'file_size': int(row['src_bytes']),
                
                # Connection features
                'duration_seconds': int(row['duration']),
                'num_failed_logins': int(row['num_failed_logins']),
                'logged_in': bool(row['logged_in']),
                'count': int(row['count']),
                'srv_count': int(row['srv_count']),
                
                # Error rates
                'serror_rate': float(row['serror_rate']),
                'rerror_rate': float(row['rerror_rate']),
                
                # Same service rate
                'same_srv_rate': float(row['same_srv_rate']),
                'diff_srv_rate': float(row['diff_srv_rate']),
                
                # Host features
                'dst_host_count': int(row['dst_host_count']),
                'dst_host_srv_count': int(row['dst_host_srv_count']),
                
                # Labels
                'is_suspicious': is_attack,
                'confidence_score': confidence,
                'attack_type': attack_type,
                
                # Temporal features
                'hour': np.random.randint(0, 24),
                'day_of_week': np.random.randint(0, 7),
                'is_weekend': np.random.choice([True, False], p=[0.2, 0.8]),
                'is_business_hours': np.random.choice([True, False], p=[0.7, 0.3]),
                
                # Additional context
                'sensitive_data_accessed': is_attack and np.random.random() > 0.7,
                'root_shell': bool(row['root_shell']),
                'num_file_creations': int(row['num_file_creations']),
                'num_shells': int(row['num_shells']),
                'num_access_files': int(row['num_access_files'])
            }
            
            activities.append(activity)
        
        result_df = pd.DataFrame(activities)
        logger.info(f"✅ Transformed {len(result_df):,} activities with {len(result_df.columns)} features")
        
        return result_df
    
    def combine_with_synthetic(self, synthetic_df: pd.DataFrame, 
                               real_data_ratio: float = 0.3,
                               total_size: Optional[int] = None) -> pd.DataFrame:
        """
        Combine real KDD data with synthetic data
        
        Args:
            synthetic_df: Your synthetic data
            real_data_ratio: Percentage of real data (0.3 = 30%)
            total_size: Total desired size (None = use synthetic size)
        """
        logger.info("\n" + "="*60)
        logger.info("🔀 Combining Synthetic + Real-World Data")
        logger.info("="*60)
        
        # Determine total size
        if total_size is None:
            total_size = len(synthetic_df)
        
        # Calculate how much real data to load
        real_sample_size = int(total_size * real_data_ratio)
        synthetic_sample_size = total_size - real_sample_size
        
        logger.info(f"Target composition:")
        logger.info(f"   Total size: {total_size:,}")
        logger.info(f"   Synthetic: {synthetic_sample_size:,} ({(1-real_data_ratio)*100:.0f}%)")
        logger.info(f"   Real-world: {real_sample_size:,} ({real_data_ratio*100:.0f}%)")
        
        # Load balanced KDD data
        kdd_df = self.load_kdd_cup_1999(sample_size=real_sample_size, balanced=True)
        
        if kdd_df is None:
            logger.warning("⚠️ Using only synthetic data")
            return synthetic_df
        
        # Transform to IGNISYL format
        real_df = self.transform_kdd_to_ignisyl(kdd_df)
        
        # Sample from synthetic
        synthetic_sample = synthetic_df.sample(n=synthetic_sample_size, replace=False, random_state=42)
        
        # Combine and shuffle
        combined = pd.concat([synthetic_sample, real_df], ignore_index=True)
        combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Final statistics
        logger.info(f"\n📊 Final Dataset Composition:")
        logger.info(f"   {'─'*50}")
        logger.info(f"   Synthetic:  {len(synthetic_sample):8,} ({len(synthetic_sample)/len(combined)*100:5.1f}%)")
        logger.info(f"   Real-world: {len(real_df):8,} ({len(real_df)/len(combined)*100:5.1f}%)")
        logger.info(f"   {'─'*50}")
        logger.info(f"   Total:      {len(combined):8,} (100.0%)")
        logger.info(f"\n   Normal:     {(~combined['is_suspicious']).sum():8,} ({(~combined['is_suspicious']).sum()/len(combined)*100:.1f}%)")
        logger.info(f"   Suspicious: {combined['is_suspicious'].sum():8,} ({combined['is_suspicious'].sum()/len(combined)*100:.1f}%)")
        logger.info(f"\n   Total features: {len(combined.columns)}")
        
        return combined

def main():
    """Test with larger, balanced dataset"""
    print("\n" + "="*60)
    print("IGNISYL Real-World Data Loader - Production Test")
    print("="*60)
    
    loader = RealWorldDataLoader()
    
    # Load balanced dataset with more records
    kdd_df = loader.load_kdd_cup_1999(sample_size=10000, balanced=True)
    
    if kdd_df is not None:
        ignisyl_df = loader.transform_kdd_to_ignisyl(kdd_df)
        
        print("\n📋 Sample Transformed Data:")
        print(ignisyl_df[['user_id', 'activity_type', 'is_suspicious', 'attack_type', 'bytes_transferred']].head(10))
        
        print("\n✅ Production test completed successfully!")
        print(f"   Dataset size: {len(ignisyl_df):,} records")
        print(f"   Features: {len(ignisyl_df.columns)}")
    else:
        print("\n❌ Test failed")

if __name__ == "__main__":
    main()