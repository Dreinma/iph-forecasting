import pandas as pd
import numpy as np
import os
import shutil
import calendar
import logging
from datetime import datetime, timedelta, date
from database import db, IPHData, CommodityData
from sqlalchemy import func, and_, or_
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class DataHandler:
    """Enhanced handler for data operations with database support"""
    
    def __init__(self, backup_path='data/backups/'):
        self.backup_path = backup_path
        os.makedirs(self.backup_path, exist_ok=True)
        
        logger.debug(f"DataHandler initialized (backup: {self.backup_path})")
    
    def _anchor_date(self, d: date) -> date:
        """Normalize a given date to nearest weekly anchor (1, 8, 15, 22, 29) within same month."""
        try:
            year, month, day = d.year, d.month, d.day
            max_day = calendar.monthrange(year, month)[1]
            anchors = [x for x in (1, 8, 15, 22, 29) if x <= max_day]
            target = min(anchors, key=lambda a: (abs(a - day), a))
            return date(year, month, target)
        except Exception:
            return d
    
    def load_historical_data(self):
        """Load historical data from database"""
        try:
            logger.debug("Loading historical data from database")

            # Query all IPH data ordered by date
            query = IPHData.query.order_by(IPHData.tanggal).all()

            if not query:
                logger.warning("No records found in database")
                return pd.DataFrame()

            # Convert to DataFrame with fields known to exist in schema
            data = []
            for i, record in enumerate(query):
                try:
                    periode = None
                    if record.bulan or record.minggu:
                        periode = f"{record.bulan or ''} {record.minggu or ''}".strip()
                    
                    row = {
                        'Tanggal': record.tanggal,
                        'Indikator_Harga': record.indikator_harga,
                        'Periode': periode,
                        'Bulan': getattr(record, 'bulan', None),
                        'Minggu': getattr(record, 'minggu', None),
                        'Tahun': getattr(record, 'tahun', None),
                        'Data_Source': getattr(record, 'data_source', None),
                        'Last_Updated': getattr(record, 'updated_at', None)
                    }
                    data.append(row)
                        
                except Exception as row_error:
                    logger.warning(f"Error processing record {i}: {str(row_error)}")
                    continue
            
            df = pd.DataFrame(data)

            # Ensure proper data types
            df['Tanggal'] = pd.to_datetime(df['Tanggal'])
            df['Indikator_Harga'] = pd.to_numeric(df['Indikator_Harga'], errors='coerce')
            
            logger.info(f"Loaded {len(df)} records | "
                       f"Date: {df['Tanggal'].min().strftime('%Y-%m-%d')} to {df['Tanggal'].max().strftime('%Y-%m-%d')} | "
                       f"IPH: {df['Indikator_Harga'].min():.2f} to {df['Indikator_Harga'].max():.2f}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}", exc_info=True)
            return pd.DataFrame()
    
    def validate_new_data(self, df):
        """Validate new data format and content (same as before)"""
        if df.empty:
            raise ValueError("Data is empty")
        
        original_size = len(df)
        
        # Check for completely empty rows
        empty_rows = df.isnull().all(axis=1).sum()
        if empty_rows > 0:
            logger.debug(f"Removing {empty_rows} empty rows")
            df = df.dropna(how='all')
        
        # Map common column variations to standard names
        column_mapping = {
            'Indikator Perubahan Harga (%)': 'Indikator_Harga',
            ' Indikator Perubahan Harga (%)': 'Indikator_Harga',
            'Indikator_Perubahan_Harga': 'Indikator_Harga',
            'IPH': 'Indikator_Harga',
            'Date': 'Tanggal',
            'date': 'Tanggal',
            'Tanggal ': 'Tanggal',
            ' Tanggal': 'Tanggal'
        }
        
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
                logger.debug(f"Renamed column: {old_name} -> {new_name}")
        
        # Special handling for IPH Kota Batu format
        if 'Tanggal' not in df.columns and 'Bulan' in df.columns and 'Minggu ke-' in df.columns:
            logger.debug("Creating Tanggal column from Bulan and Minggu")
            df = self._create_date_from_bulan_minggu(df)
        
        # Check required columns
        required_columns = ['Tanggal', 'Indikator_Harga']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            available_cols = list(df.columns)
            raise ValueError(f"Missing required columns: {missing_cols}. Available: {available_cols}")
        
        # Validate and convert date column
        try:
            original_dates = len(df)
            df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
            invalid_dates = df['Tanggal'].isna().sum()
            
            if invalid_dates > 0:
                logger.debug(f"Removed {invalid_dates} invalid dates")
                df = df.dropna(subset=['Tanggal'])
                
            if df.empty:
                raise ValueError("No valid dates found")
                
        except Exception as e:
            raise ValueError(f"Error processing dates: {str(e)}")
        
        # Validate and convert numeric column
        try:
            original_values = len(df)
            df['Indikator_Harga'] = pd.to_numeric(df['Indikator_Harga'], errors='coerce')
            invalid_values = df['Indikator_Harga'].isna().sum()
            
            if invalid_values > 0:
                logger.debug(f"Removed {invalid_values} invalid numeric values")
                df = df.dropna(subset=['Indikator_Harga'])
                
            if df.empty:
                raise ValueError("No valid numeric values found")
                
        except Exception as e:
            raise ValueError(f"Error processing numeric values: {str(e)}")
        
        # Check for reasonable value ranges
        iph_values = df['Indikator_Harga']
        extreme_values = ((iph_values < -50) | (iph_values > 50)).sum()
        
        if extreme_values > 0:
            logger.warning(f"{extreme_values} extreme IPH values detected (>50% or <-50%)")
            
        # Sort by date
        df = df.sort_values('Tanggal').reset_index(drop=True)
        
        # Summary log
        logger.info(f"Validated: {len(df)}/{original_size} records | "
                   f"IPH: {iph_values.min():.2f}% to {iph_values.max():.2f}% | "
                   f"Date: {df['Tanggal'].min().strftime('%Y-%m-%d')} to {df['Tanggal'].max().strftime('%Y-%m-%d')}")
        
        return df

    def merge_and_save_data(self, new_data_df):
        """ Merge new data with database and save - FIXED DUPLICATE DETECTION"""
        # Validate new data
        validated_df = self.validate_new_data(new_data_df.copy())
        
        # Create backup of current database state
        backup_info = self.backup_database_to_csv()
        
        try:
            # Get existing data count
            existing_count = IPHData.query.count()
            logger.debug(f"Existing records: {existing_count}")
            
            # Process and insert new records
            new_records = 0
            updated_records = 0
            duplicate_dates = []
            
            # FIX: Use session.no_autoflush() to prevent premature flush
            with db.session.no_autoflush:
                for _, row in validated_df.iterrows():
                    date_value = row['Tanggal'].date()
                    # Normalize to weekly anchor (1, 8, 15, 22, 29)
                    anchored = self._anchor_date(date_value)
                    if anchored != date_value:
                        logger.debug(f"Normalized date {date_value} -> {anchored}")
                        date_value = anchored
                    bulan_val = str(row['Bulan']) if 'Bulan' in row and pd.notna(row['Bulan']) else None
                    minggu_val = str(row['Minggu']) if 'Minggu' in row and pd.notna(row['Minggu']) else None
                    kab_kota_val = str(row['Kab/Kota']) if 'Kab/Kota' in row and pd.notna(row['Kab/Kota']) else 'BATU'

                    # FIX: Check by TANGGAL (unique key), not bulan+minggu
                    existing_record = IPHData.query.filter_by(tanggal=date_value).first()

                    if existing_record:
                        # Update existing record
                        logger.debug(f"Updating existing record: {date_value}")
                        existing_record.indikator_harga = float(row['Indikator_Harga'])
                        existing_record.updated_at = datetime.utcnow()
                        
                        # Update optional fields if provided
                        if bulan_val:
                            existing_record.bulan = bulan_val
                        if minggu_val:
                            existing_record.minggu = minggu_val
                        if 'Tahun' in row and pd.notna(row['Tahun']):
                            existing_record.tahun = int(row['Tahun'])
                        if kab_kota_val:
                            existing_record.kab_kota = kab_kota_val
                        
                        updated_records += 1
                        duplicate_dates.append(date_value)
                    else:
                        # Create new record
                        logger.debug(f"Adding new record: {date_value}")
                        
                        # Extract tahun from bulan if not provided
                        tahun_val = None
                        if 'Tahun' in row and pd.notna(row['Tahun']):
                            tahun_val = int(row['Tahun'])
                        elif bulan_val and "'" in bulan_val:
                            # Extract from format "Januari '24"
                            try:
                                tahun_part = bulan_val.split("'")[1].strip()
                                tahun_val = 2000 + int(tahun_part) if int(tahun_part) < 100 else int(tahun_part)
                            except:
                                tahun_val = date_value.year
                        else:
                            tahun_val = date_value.year
                        
                        # Calculate bulan_numerik
                        bulan_numerik = date_value.month
                        
                        new_record = IPHData(
                            tanggal=date_value,
                            indikator_harga=float(row['Indikator_Harga']),
                            bulan=bulan_val,
                            minggu=minggu_val,
                            tahun=tahun_val,
                            bulan_numerik=bulan_numerik,
                            kab_kota=kab_kota_val,
                            data_source='uploaded'
                        )
                        
                        db.session.add(new_record)
                        db.session.flush()  # Get the ID
                        
                        # Create CommodityData record if commodity data exists
                        if 'Komoditas Andil Perubahan Harga' in row and pd.notna(row['Komoditas Andil Perubahan Harga']):
                            commodity_record = CommodityData(
                                tanggal=date_value,
                                bulan=bulan_val,
                                minggu=minggu_val,
                                tahun=tahun_val,
                                kab_kota=kab_kota_val,
                                iph_id=new_record.id,
                                iph_value=float(row['Indikator_Harga']),
                                komoditas_andil=str(row['Komoditas Andil Perubahan Harga']),
                                komoditas_fluktuasi=str(row['Komoditas Fluktuasi Harga Tertinggi']) if 'Komoditas Fluktuasi Harga Tertinggi' in row and pd.notna(row['Komoditas Fluktuasi Harga Tertinggi']) else None,
                                nilai_fluktuasi=float(row['Fluktuasi Harga']) if 'Fluktuasi Harga' in row and pd.notna(row['Fluktuasi Harga']) else 0.0
                            )
                            db.session.add(commodity_record)
                        
                        new_records += 1
            
            # Commit all changes at once
            db.session.commit()
            logger.debug("Database changes committed")
            
            # Get final count
            final_count = IPHData.query.count()
            
            merge_info = {
                'existing_records': existing_count,
                'new_records': new_records,
                'updated_records': updated_records,
                'total_records': final_count,
                'duplicates_removed': updated_records,
                'date_overlap': len(duplicate_dates) > 0,
                'overlap_count': len(duplicate_dates),
                'backup_created': backup_info is not None
            }
            
            logger.info(f"Data merged: {existing_count} existing + {new_records} new + {updated_records} updated = {final_count} total")
            
            # Return combined data as DataFrame
            combined_df = self.load_historical_data()
            
            return combined_df, merge_info
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Merge error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Attempt to restore from backup if available
            if backup_info:
                logger.warning("Database rollback executed")
            
            raise Exception(f"Database merge failed: {str(e)}")

    def backup_database_to_csv(self):
        """ Backup database to CSV file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"db_backup_{timestamp}.csv"
            backup_filepath = os.path.join(self.backup_path, backup_filename)
            
            # Load all data from database
            df = self.load_historical_data()
            
            if df.empty:
                logger.debug("No data to backup")
                return None
            
            # Save to CSV
            df.to_csv(backup_filepath, index=False)
            
            # Create info file
            info_filepath = backup_filepath.replace('.csv', '_info.txt')
            with open(info_filepath, 'w') as f:
                f.write(f"Database backup created: {datetime.now().isoformat()}\n")
                f.write(f"Records backed up: {len(df)}\n")
                f.write(f"Date range: {df['Tanggal'].min()} to {df['Tanggal'].max()}\n")
            
            logger.debug(f"Database backed up to {backup_filename}")
            return backup_filepath
            
        except Exception as e:
            logger.warning(f"Backup failed: {str(e)}")
            return None
    
    def get_data_summary(self):
        """ Get comprehensive summary from database"""
        try:
            # Get basic counts
            total_records = IPHData.query.count()
            
            if total_records == 0:
                return {
                    'total_records': 0,
                    'date_range': None,
                    'latest_value': None,
                    'statistics': {},
                    'data_quality': {},
                    'database_info': {}
                }
            
            # Get date range
            date_stats = db.session.query(
                func.min(IPHData.tanggal).label('min_date'),
                func.max(IPHData.tanggal).label('max_date')
            ).first()
            
            # Get latest value
            latest_record = IPHData.query.order_by(IPHData.tanggal.desc()).first()
            
            # Load data for statistics
            df = self.load_historical_data()
            iph_values = df['Indikator_Harga']
            
            # Calculate statistics
            Q1 = iph_values.quantile(0.25)
            Q3 = iph_values.quantile(0.75)
            IQR = Q3 - Q1
            outliers = iph_values[(iph_values < Q1 - 1.5*IQR) | (iph_values > Q3 + 1.5*IQR)]
            
            # Calculate completeness
            missing_values = df.isnull().sum().sum()
            total_cells = len(df) * len(df.columns)
            completeness = (1 - missing_values / total_cells) * 100 if total_cells > 0 else 0
            
            summary = {
                'total_records': int(total_records),
                'date_range': {
                    'start': date_stats.min_date.strftime('%Y-%m-%d'),
                    'end': date_stats.max_date.strftime('%Y-%m-%d'),
                    'days_span': int((date_stats.max_date - date_stats.min_date).days)
                },
                'latest_value': float(latest_record.indikator_harga),
                'statistics': {
                    'mean': float(iph_values.mean()),
                    'std': float(iph_values.std()),
                    'min': float(iph_values.min()),
                    'max': float(iph_values.max()),
                    'median': float(iph_values.median()),
                    'q1': float(Q1),
                    'q3': float(Q3)
                },
                'data_quality': {
                    'completeness_percent': float(completeness),
                    'missing_values': int(missing_values),
                    'outliers_count': int(len(outliers)),
                    'outliers_percent': float(len(outliers) / len(df) * 100)
                },
                'database_info': {
                    'storage_type': 'SQLite Database',
                    'last_updated': latest_record.updated_at.isoformat() if latest_record.updated_at else None
                },
                'columns': list(df.columns),
                'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting data summary: {str(e)}")
            return {
                'total_records': 0,
                'error': str(e)
            }
    
    def get_recent_backups(self, limit=10):
        """Get list of recent backup files"""
        if not os.path.exists(self.backup_path):
            return []
        
        backup_files = []
        for file in os.listdir(self.backup_path):
            if file.startswith('db_backup_') and file.endswith('.csv'):
                filepath = os.path.join(self.backup_path, file)
                stat = os.stat(filepath)
                
                backup_files.append({
                    'filename': file,
                    'filepath': filepath,
                    'size_mb': stat.st_size / (1024 * 1024),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Sort by creation time (newest first)
        backup_files.sort(key=lambda x: x['created'], reverse=True)
        
        return backup_files[:limit]
    
    def _create_date_from_bulan_minggu(self, df):
        """Create Tanggal column from Bulan and Minggu ke- columns (same as before)"""
        
        def extract_year_from_bulan(bulan_str):
            if pd.isna(bulan_str):
                return 2024
            
            bulan_str = str(bulan_str).strip()
            if "'24" in bulan_str:
                return 2024
            elif "'25" in bulan_str:
                return 2025
            elif "'23" in bulan_str:
                return 2023
            else:
                return 2024
        
        def extract_month_from_bulan(bulan_str):
            month_map = {
                'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
                'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
                'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
            }
            
            if pd.isna(bulan_str):
                return 1
            
            bulan_str = str(bulan_str).strip().lower()
            bulan_clean = bulan_str.split("'")[0].strip()
            
            for nama_bulan, nomor_bulan in month_map.items():
                if nama_bulan in bulan_clean:
                    return nomor_bulan
            return 1
        
        def extract_week_from_minggu(minggu_str):
            if pd.isna(minggu_str):
                return 1
            
            minggu_str = str(minggu_str).strip().upper()
            if minggu_str.startswith('M'):
                week_num = minggu_str.replace('M', '')
            else:
                week_num = minggu_str
            
            try:
                return int(week_num)
            except:
                return 1
        
        def create_date(year, month, week):
            try:
                day = (week - 1) * 7 + 1
                
                if month == 2:
                    max_day = 29 if year % 4 == 0 else 28
                elif month in [4, 6, 9, 11]:
                    max_day = 30
                else:
                    max_day = 31
                
                if day > max_day:
                    day = max_day
                
                return pd.Timestamp(year, month, day)
            except:
                return pd.Timestamp(year, month, 1)
        
        df['Year'] = df['Bulan'].apply(extract_year_from_bulan)
        df['Month'] = df['Bulan'].apply(extract_month_from_bulan)
        df['Week'] = df['Minggu ke-'].apply(extract_week_from_minggu)
        
        df['Tanggal'] = df.apply(lambda row: create_date(row['Year'], row['Month'], row['Week']), axis=1)
        
        df = df.drop(['Year', 'Month', 'Week'], axis=1)
        
        logger.debug("Created Tanggal column from Bulan and Minggu")
        
        return df
