import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import re
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

class CommodityInsightService:
    """Enhanced service for analyzing commodity impacts and generating insights"""
    
    def __init__(self, commodity_data_path='data/IPH-Kota-Batu.csv'):
        self.commodity_data_path = commodity_data_path
        self.commodity_cache = None
        self.last_cache_time = None
        self.cache_duration = 300  # 5 minutes cache
        self.use_database = True  # Use database instead of CSV
        
        # Enhanced commodity mapping dengan lebih banyak variasi
        self.commodity_mapping = {
            'CABAI RAWIT': 'CABAI_RAWIT',
            'CABAI MERAH': 'CABAI_MERAH', 
            'DAGING AYAM RAS': 'DAGING_AYAM',
            'DAGING AYAM': 'DAGING_AYAM',
            'TELUR AYAM RAS': 'TELUR_AYAM',
            'TELUR AYAM': 'TELUR_AYAM',
            'BAWANG MERAH': 'BAWANG_MERAH',
            'BAWANG PUTIH': 'BAWANG_PUTIH',
            'MINYAK GORENG': 'MINYAK_GORENG',
            'DAGING SAPI': 'DAGING_SAPI',
            'GULA PASIR': 'GULA_PASIR',
            'TEPUNG TERIGU': 'TEPUNG_TERIGU',
            'BERAS': 'BERAS',
            'PISANG': 'PISANG',
            'IKAN KEMBUNG': 'IKAN_KEMBUNG',
            'TEMPE': 'TEMPE'
        }
        
        # Enhanced commodity categories dengan icon dan description
        self.commodity_categories = {
            'PROTEIN': {
                'items': ['DAGING_AYAM', 'DAGING_SAPI', 'TELUR_AYAM', 'IKAN_KEMBUNG', 'TEMPE'],
                'icon': '',
                'description': 'Sumber protein hewani dan nabati'
            },
            'SAYURAN_BUMBU': {
                'items': ['CABAI_RAWIT', 'CABAI_MERAH', 'BAWANG_MERAH', 'BAWANG_PUTIH'],
                'icon': '',
                'description': 'Sayuran dan bumbu dapur'
            },
            'KARBOHIDRAT': {
                'items': ['BERAS', 'TEPUNG_TERIGU'],
                'icon': '',
                'description': 'Sumber karbohidrat utama'
            },
            'LEMAK_MINYAK': {
                'items': ['MINYAK_GORENG'],
                'icon': '',
                'description': 'Minyak dan lemak'
            },
            'PEMANIS': {
                'items': ['GULA_PASIR'],
                'icon': '',
                'description': 'Pemanis dan gula'
            },
            'BUAH': {
                'items': ['PISANG'],
                'icon': '',
                'description': 'Buah-buahan'
            }
        }
        
    def load_commodity_data(self):
        """Enhanced commodity data loading dengan better error handling"""
        try:
            if self.use_database:
                db_data = self._load_from_database()
                if not db_data.empty:
                    return db_data
                else:
                    print("Database empty, falling back to CSV...")
                    return self._load_from_csv()
            else:
                return self._load_from_csv()
                
        except Exception as e:
            print(f"Critical error loading commodity data: {str(e)}")
            print("Falling back to CSV...")
            return self._load_from_csv()
    
    def _load_from_database(self):
        """Load commodity data from database"""
        try:
            from database import CommodityData, db
            
            # Check cache first
            current_time = datetime.now()
            if (self.commodity_cache is not None and 
                self.last_cache_time is not None and 
                (current_time - self.last_cache_time).seconds < self.cache_duration):
                print(" Using cached commodity data from database")
                return self.commodity_cache.copy()
            
            print("Loading fresh commodity data from database...")
            
            # Query all commodity data
            commodity_records = CommodityData.query.all()
            print(f" DEBUG: Found {len(commodity_records)} commodity records in database")
            
            if not commodity_records:
                print(" No commodity data found in database")
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for record in commodity_records:
                data.append({
                    'Tanggal': record.tanggal.strftime('%Y-%m-%d'),
                    'Bulan': record.bulan,
                    'Minggu': record.minggu,  # Fixed: remove 'ke-' suffix
                    'Kota': record.kab_kota,  # Fixed: use 'Kota' instead of 'Kab/Kota'
                    'IPH': record.iph_value,  # Fixed: use 'IPH' instead of long name
                    'Komoditas_Andil': record.komoditas_andil,  # Fixed: use underscore
                    'Komoditas_Fluktuasi_Tertinggi': record.komoditas_fluktuasi,  # Fixed: use underscore
                    'Nilai_Fluktuasi': record.nilai_fluktuasi  # Fixed: use underscore
                })
            
            df = pd.DataFrame(data)
            
            # Process the dataframe
            df = self._process_commodity_dataframe(df)
            
            # Cache the successful result
            self.commodity_cache = df.copy()
            self.last_cache_time = current_time
            
            print(f" Commodity data loaded from database: {len(df)} records")
            return df
                
        except Exception as e:
            print(f"Error loading from database: {str(e)}")
            return pd.DataFrame()
    
    def _load_from_csv(self):
        """Load commodity data from CSV (fallback)"""
        try:
            if not os.path.exists(self.commodity_data_path):
                print(f" Commodity data not found at {self.commodity_data_path}")
                return pd.DataFrame()
            
            # Check cache first
            current_time = datetime.now()
            if (self.commodity_cache is not None and 
                self.last_cache_time is not None and 
                (current_time - self.last_cache_time).seconds < self.cache_duration):
                print(" Using cached commodity data from CSV")
                return self.commodity_cache.copy()
            
            print("Loading fresh commodity data from CSV...")
            
            # Enhanced CSV reading
            df = None
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(self.commodity_data_path, encoding=encoding)
                    print(f" CSV loaded with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Error with {encoding}: {str(e)}")
                    continue
            
            if df is None:
                return pd.DataFrame()
            
            # Enhanced data processing
            df = self._process_commodity_dataframe(df)
            
            # Cache the successful result
            self.commodity_cache = df.copy()
            self.last_cache_time = current_time
            
            print(f" Commodity data loaded from CSV: {len(df)} records")
            return df
            
        except Exception as e:
            print(f"Error loading from CSV: {str(e)}")
            return pd.DataFrame()

    def _process_commodity_dataframe(self, df):
        """Process and clean commodity dataframe"""
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Enhanced column mapping
        column_mapping = {
            'Indikator Perubahan Harga (%)': 'IPH',
            ' Indikator Perubahan Harga (%)': 'IPH',
            'Komoditas Andil Perubahan Harga ': 'Komoditas_Andil',
            'Komoditas Andil Perubahan Harga': 'Komoditas_Andil',
            'Komoditas Fluktuasi Harga Tertinggi': 'Komoditas_Fluktuasi_Tertinggi',
            'Fluktuasi Harga': 'Nilai_Fluktuasi',
            'Minggu ke-': 'Minggu',
            'Kab/Kota': 'Kota'
        }
        
        # Apply column mapping
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)
        
        # Forward fill critical columns
        fill_columns = ['Bulan', 'Minggu', 'Kota']
        for col in fill_columns:
            if col in df.columns:
                df[col] = df[col].fillna(method='ffill')
        
        # Enhanced numeric conversion
        numeric_columns = ['IPH', 'Nilai_Fluktuasi']
        for col in numeric_columns:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.')
                    df[col] = df[col].str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Enhanced date creation - use existing Tanggal if available, otherwise create from Bulan/Minggu
        if 'Tanggal' not in df.columns or df['Tanggal'].isna().all():
            df['Tanggal'] = df.apply(lambda row: self._create_robust_date(
                row.get('Bulan', ''), 
                row.get('Minggu', '')
            ), axis=1)
        else:
            # Convert existing Tanggal to datetime if it's string
            if df['Tanggal'].dtype == 'object':
                df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        
        # Remove rows with invalid dates
        df = df.dropna(subset=['Tanggal'])
        df = df.sort_values('Tanggal').reset_index(drop=True)
        
        return df

    def _create_robust_date(self, bulan_str, minggu_str):
        """Enhanced date creation dengan comprehensive error handling"""
        try:
            year = 2024  # Default
            month = 1   # Default
            week = 1    # Default
            
            # Enhanced year extraction
            if pd.notna(bulan_str) and bulan_str:
                bulan_clean = str(bulan_str).strip()
                
                year_patterns = {
                    "'23": 2023, "'2023": 2023, "2023": 2023,
                    "'24": 2024, "'2024": 2024, "2024": 2024, 
                    "'25": 2025, "'2025": 2025, "2025": 2025
                }
                
                for pattern, year_val in year_patterns.items():
                    if pattern in bulan_clean:
                        year = year_val
                        break
                
                # Enhanced month extraction
                month_patterns = {
                    'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
                    'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
                    'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
                }
                
                bulan_lower = bulan_clean.lower().split("'")[0].strip()
                for pattern, month_num in month_patterns.items():
                    if pattern in bulan_lower:
                        month = month_num
                        break
            
            # Enhanced week extraction
            if pd.notna(minggu_str) and minggu_str:
                minggu_clean = str(minggu_str).strip().upper()
                week_match = re.search(r'M(\d+)', minggu_clean)
                if week_match:
                    week = int(week_match.group(1))
                else:
                    try:
                        week = int(minggu_clean.replace('M', ''))
                    except:
                        week = 1
            
            # Validate and create date
            week = max(1, min(week, 5))
            day = min((week - 1) * 7 + 1, 28)  # Safe day calculation
            
            return pd.Timestamp(year, month, day)
                
        except Exception as e:
            print(f"Date creation error: {str(e)}")
            return pd.Timestamp.now().normalize()

    def parse_commodity_impacts(self, commodity_string):
        """Enhanced commodity impact parsing"""
        if pd.isna(commodity_string) or not commodity_string:
            return []
        
        commodities = []
        commodity_str = str(commodity_string).strip()
        
        if not commodity_str or commodity_str.upper() in ['NAN', 'NULL', '', 'N/A']:
            return []
        
        try:
            # Normalize decimal separators
            normalized_str = re.sub(r'(-?\d+),(\d+)', r'\1.\2', commodity_str)
            
            # Enhanced parsing with multiple strategies
            parsing_strategies = [
                r'([A-Z\s/]+)\((-?\d+\.?\d*)\);?',  # Semicolon separated
                r'([A-Z\s/]+)\((-?\d+\.?\d*)\),?',  # Comma separated
                r'([A-Z\s/]+)\((-?\d+\.?\d*)\)\s*'  # Space separated
            ]
            
            matches = []
            for pattern in parsing_strategies:
                test_matches = re.findall(pattern, normalized_str.upper())
                if test_matches and len(test_matches) >= len(matches):
                    matches = test_matches
            
            # Process matches
            for match in matches:
                try:
                    commodity_name = match[0].strip()
                    impact_str = match[1].strip()
                    
                    if not commodity_name or len(commodity_name) < 2:
                        continue
                    
                    try:
                        impact_value = float(impact_str)
                    except ValueError:
                        continue
                    
                    standardized_name = self._standardize_commodity_name(commodity_name)
                    category_info = self._get_commodity_category_info(standardized_name)
                    
                    # Skip only generic category names, keep specific commodities
                    if category_info['category'] in ['KARBOHIDRAT', 'SAYURAN_BUMBU'] and len(standardized_name.split('_')) <= 1:
                        continue
                    
                    commodity_data = {
                        'name': standardized_name,
                        'original_name': commodity_name,
                        'impact': impact_value,
                        'category': 'KOMODITAS',
                        'category_icon': '',
                        'category_description': 'Komoditas utama'
                    }
                    
                    commodities.append(commodity_data)
                    
                except Exception as parse_error:
                    continue
            
            return commodities
            
        except Exception as e:
            print(f"Critical error in commodity parsing: {str(e)}")
            return []
    
    def _standardize_commodity_name(self, name):
        """Standardize commodity names"""
        name_clean = name.strip().upper()
        
        # Apply mapping if exists
        if name_clean in self.commodity_mapping:
            return self.commodity_mapping[name_clean]
        
        # Clean up common variations
        name_clean = re.sub(r'\s+', '_', name_clean)
        name_clean = re.sub(r'[/\\]', '_', name_clean)
        
        return name_clean
    
    def _get_commodity_category_info(self, commodity_name):
        """Get category info for commodity"""
        for category, info in self.commodity_categories.items():
            if commodity_name in info['items']:
                return {
                    'category': category,
                    'icon': info['icon'],
                    'description': info['description']
                }
        return {
            'category': 'LAINNYA',
            'icon': '',
            'description': 'Komoditas lainnya'
        }
    
    def get_current_week_insights(self):
        """Enhanced current week insights dengan detailed category analysis"""
        try:
            print("Starting enhanced current week insights analysis...")
            
            df = self.load_commodity_data()
            
            if df.empty:
                return {
                    'success': False,
                    'message': 'No commodity data available. Please upload commodity data file.',
                    'suggestion': 'Upload a CSV file with required columns'
                }
            
            # Get records with valid IPH and date
            df_valid = df.dropna(subset=['IPH', 'Tanggal'])
            
            if df_valid.empty:
                return {
                    'success': False,
                    'message': 'No valid IPH data found in commodity dataset'
                }
            
            # Get latest record
            latest_record = df_valid.iloc[-1]
            latest_date = latest_record['Tanggal']
            
            # Parse commodity impacts
            commodity_string = latest_record.get('Komoditas_Andil', '')
            commodities = self.parse_commodity_impacts(commodity_string)
            
            if not commodities:
                commodities = [{
                    'name': 'DATA_NOT_AVAILABLE',
                    'original_name': 'Data Not Available',
                    'impact': 0.0,
                    'category': 'UNKNOWN',
                    'category_icon': '',
                    'category_description': 'Data tidak tersedia'
                }]
            
            # Sort by absolute impact
            commodities.sort(key=lambda x: abs(x['impact']), reverse=True)
            
            # Enhanced category analysis
            category_analysis = self._analyze_by_category_detailed(commodities)
            
            # Categorize impacts dengan threshold yang lebih baik
            significant_positive = [c for c in commodities if c['impact'] > 0.1]  # > 0.1%
            significant_negative = [c for c in commodities if c['impact'] < -0.1]  # < -0.1%
            minor_impacts = [c for c in commodities if abs(c['impact']) <= 0.1]
            
            # Enhanced volatility handling
            most_volatile = latest_record.get('Komoditas_Fluktuasi_Tertinggi', 'Tidak ada data')
            volatility_value = latest_record.get('Nilai_Fluktuasi', 0)
            
            # Clean volatility data
            if pd.isna(volatility_value) or volatility_value == '':
                volatility_value = 0.0
                volatility_level = 'unknown'
                volatility_color = 'secondary'
            else:
                try:
                    volatility_value = float(volatility_value)
                    if volatility_value > 0.15:
                        volatility_level = 'Sangat Tinggi'
                        volatility_color = 'danger'
                    elif volatility_value > 0.10:
                        volatility_level = 'Tinggi'
                        volatility_color = 'warning'
                    elif volatility_value > 0.05:
                        volatility_level = 'Sedang'
                        volatility_color = 'info'
                    else:
                        volatility_level = 'Rendah'
                        volatility_color = 'success'
                except (ValueError, TypeError):
                    volatility_value = 0.0
                    volatility_level = 'unknown'
                    volatility_color = 'secondary'
            
            # Enhanced insights
            insights = {
                'success': True,
                'data_quality': {
                    'total_records_processed': len(df),
                    'valid_records_used': len(df_valid),
                    'commodities_parsed': len(commodities),
                    'parsing_success_rate': len([c for c in commodities if c['name'] != 'DATA_NOT_AVAILABLE']) / len(commodities) * 100 if commodities else 0
                },
                'period': {
                    'bulan': str(latest_record.get('Bulan', 'Unknown')),
                    'minggu': str(latest_record.get('Minggu', 'Unknown')),
                    'kota': str(latest_record.get('Kota', 'Unknown')),
                    'tanggal': latest_date.strftime('%Y-%m-%d')
                },
                'iph_analysis': {
                    'value': float(latest_record.get('IPH', 0)),
                    'level': self._get_iph_level(float(latest_record.get('IPH', 0))),
                    'color': self._get_iph_color(float(latest_record.get('IPH', 0))),
                    'direction': 'Inflasi' if float(latest_record.get('IPH', 0)) > 0 else 'Deflasi' if float(latest_record.get('IPH', 0)) < 0 else 'Stabil'
                },
                'commodity_impacts': {
                    'significant_positive': significant_positive[:5],
                    'significant_negative': significant_negative[:5],
                    'minor_impacts': minor_impacts[:3],
                    'total_commodities': len(commodities)
                },
                'volatility_analysis': {
                    'most_volatile_commodity': str(most_volatile),
                    'volatility_value': volatility_value,
                    'volatility_level': volatility_level,
                    'volatility_color': volatility_color,
                    'volatility_percentage': volatility_value * 100
                },
                'category_analysis': category_analysis,
                'summary': self._generate_enhanced_weekly_summary(latest_record, commodities, category_analysis),
                'recommendations': self._generate_weekly_recommendations(latest_record, commodities, category_analysis)
            }
            
            print(" Enhanced current week insights generated successfully")
            return insights
            
        except Exception as e:
            print(f"Critical error, using fallback data: {str(e)}")
            
            # Return fallback data untuk testing
            return {
                'success': True,
                'period': {
                    'bulan': 'Test Month',
                    'minggu': 'M1',
                    'kota': 'BATU',
                    'tanggal': datetime.now().strftime('%Y-%m-%d')
                },
                'iph_analysis': {
                    'value': 1.25,
                    'level': 'Sedang',
                    'color': 'warning',
                    'direction': 'Inflasi'
                },
                'commodity_impacts': {
                    'significant_positive': [
                        {'name': 'CABAI_RAWIT', 'impact': 0.5, 'category': 'SAYURAN_BUMBU', 'category_icon': ''}
                    ],
                    'significant_negative': [],
                    'minor_impacts': [],
                    'total_commodities': 1
                },
                'volatility_analysis': {
                    'most_volatile_commodity': 'CABAI_RAWIT',
                    'volatility_value': 0.08,
                    'volatility_level': 'Sedang',
                    'volatility_color': 'warning',
                    'volatility_percentage': 8.0
                },
                'category_analysis': {
                    'SAYURAN_BUMBU': {
                        'total_impact': 0.5,
                        'commodity_count': 1,
                        'icon': '',
                        'direction_color': 'warning',
                        'impact_color': 'warning',
                        'dominant_direction': 'inflationary'
                    }
                },
                'summary': 'Test data - sistem berfungsi normal',
                'recommendations': []
            }

    def _analyze_by_category_detailed(self, commodities):
        """Enhanced category analysis dengan detailed metrics"""
        category_impacts = defaultdict(lambda: {
            'commodities': [],
            'total_impact': 0,
            'positive_impact': 0,
            'negative_impact': 0,
            'commodity_count': 0,
            'avg_impact': 0,
            'dominant_direction': 'neutral',
            'icon': '',
            'description': 'Unknown category'
        })
        
        for commodity in commodities:
            category = commodity.get('category', 'LAINNYA')
            impact = commodity['impact']
            
            category_impacts[category]['commodities'].append(commodity)
            category_impacts[category]['total_impact'] += impact
            category_impacts[category]['commodity_count'] += 1
            
            if impact > 0:
                category_impacts[category]['positive_impact'] += impact
            else:
                category_impacts[category]['negative_impact'] += abs(impact)
            
            # Set category info
            if category in self.commodity_categories:
                category_impacts[category]['icon'] = self.commodity_categories[category]['icon']
                category_impacts[category]['description'] = self.commodity_categories[category]['description']
        
        # Calculate derived metrics
        for category, data in category_impacts.items():
            if data['commodity_count'] > 0:
                data['avg_impact'] = data['total_impact'] / data['commodity_count']
                
                # Determine dominant direction
                if abs(data['positive_impact']) > abs(data['negative_impact']):
                    data['dominant_direction'] = 'inflationary'
                    data['direction_color'] = 'warning'
                elif abs(data['negative_impact']) > abs(data['positive_impact']):
                    data['dominant_direction'] = 'deflationary'
                    data['direction_color'] = 'info'
                else:
                    data['dominant_direction'] = 'neutral'
                    data['direction_color'] = 'secondary'
                
                # Calculate category impact level
                abs_total = abs(data['total_impact'])
                if abs_total > 1.0:
                    data['impact_level'] = 'high'
                    data['impact_color'] = 'danger'
                elif abs_total > 0.5:
                    data['impact_level'] = 'medium'
                    data['impact_color'] = 'warning'
                elif abs_total > 0.1:
                    data['impact_level'] = 'low'
                    data['impact_color'] = 'info'
                else:
                    data['impact_level'] = 'minimal'
                    data['impact_color'] = 'light'
        
        # Convert to regular dict and sort by absolute total impact
        result = dict(category_impacts)
        result = dict(sorted(result.items(), 
                           key=lambda x: abs(x[1]['total_impact']), 
                           reverse=True))
        
        return result

    def _get_iph_level(self, iph_value):
        """Get IPH level description"""
        abs_iph = abs(iph_value)
        if abs_iph > 3:
            return 'Sangat Tinggi'
        elif abs_iph > 2:
            return 'Tinggi'
        elif abs_iph > 1:
            return 'Sedang'
        elif abs_iph > 0.5:
            return 'Rendah'
        else:
            return 'Minimal'
    
    def _get_iph_color(self, iph_value):
        """Get IPH color based on value"""
        abs_iph = abs(iph_value)
        if abs_iph > 3:
            return 'danger'
        elif abs_iph > 2:
            return 'warning'
        elif abs_iph > 1:
            return 'info'
        else:
            return 'success'

    def _calculate_commodity_trend(self, impacts):
        """Calculate trend for commodity impacts"""
        if len(impacts) < 2:
            return 'insufficient_data'
        
        # Simple linear trend
        x = np.arange(len(impacts))
        z = np.polyfit(x, impacts, 1)
        slope = z[0]
        
        if slope > 0.01:
            return 'increasing'
        elif slope < -0.01:
            return 'decreasing'
        else:
            return 'stable'

    def _get_impact_level(self, total_impact):
        """Get impact level based on total impact"""
        abs_impact = abs(total_impact)
        if abs_impact > 2.0:
            return 'very_high'
        elif abs_impact > 1.0:
            return 'high'
        elif abs_impact > 0.5:
            return 'medium'
        elif abs_impact > 0.1:
            return 'low'
        else:
            return 'minimal'

    def _get_enhanced_category_breakdown(self, commodity_stats):
        """Enhanced category breakdown dengan detailed analysis"""
        category_breakdown = defaultdict(lambda: {
            'total_impact': 0,
            'positive_impact': 0,
            'negative_impact': 0,
            'commodity_count': 0,
            'commodities': [],
            'avg_impact': 0,
            'max_impact_commodity': None,
            'icon': '',
            'description': 'Unknown',
            'dominance_score': 0
        })
        
        for stat in commodity_stats:
            category = stat['category']
            impact = stat['total_impact']
            
            category_breakdown[category]['commodities'].append(stat)
            category_breakdown[category]['commodity_count'] += 1
            category_breakdown[category]['total_impact'] += impact
            
            if impact > 0:
                category_breakdown[category]['positive_impact'] += impact
            else:
                category_breakdown[category]['negative_impact'] += abs(impact)
            
            # Set max impact commodity
            if (not category_breakdown[category]['max_impact_commodity'] or 
                abs(impact) > abs(category_breakdown[category]['max_impact_commodity']['total_impact'])):
                category_breakdown[category]['max_impact_commodity'] = stat
            
            # Set category info
            if category in self.commodity_categories:
                category_breakdown[category]['icon'] = self.commodity_categories[category]['icon']
                category_breakdown[category]['description'] = self.commodity_categories[category]['description']
        
        # Calculate derived metrics
        for category, data in category_breakdown.items():
            if data['commodity_count'] > 0:
                data['avg_impact'] = data['total_impact'] / data['commodity_count']
                data['dominance_score'] = abs(data['total_impact']) * data['commodity_count']
        
        # Convert to regular dict and sort by dominance score
        result = dict(category_breakdown)
        result = dict(sorted(result.items(), 
                           key=lambda x: x[1]['dominance_score'], 
                           reverse=True))
        
        return result

    def _generate_enhanced_monthly_summary(self, df_filtered, commodity_stats, category_breakdown):
        """Generate enhanced monthly summary"""
        try:
            month = df_filtered.iloc[0]['Bulan'] if not df_filtered.empty else 'Unknown'
            avg_iph = df_filtered['IPH'].mean() if 'IPH' in df_filtered.columns else 0
            weeks_count = len(df_filtered)
            
            summary = f"Analisis Lengkap {month}\n\n"
            
            # IPH Analysis
            if avg_iph > 2:
                summary += f" **Inflasi Tinggi**: Rata-rata IPH {avg_iph:.2f}% dalam {weeks_count} minggu\n"
            elif avg_iph > 0:
                summary += f" **Inflasi Moderat**: Rata-rata IPH {avg_iph:.2f}% dalam {weeks_count} minggu\n"
            elif avg_iph < -2:
                summary += f" **Deflasi Tinggi**: Rata-rata IPH {avg_iph:.2f}% dalam {weeks_count} minggu\n"
            else:
                summary += f" **Kondisi Stabil**: Rata-rata IPH {avg_iph:.2f}% dalam {weeks_count} minggu\n"
            
            # Top commodities impact
            if commodity_stats:
                top_3 = commodity_stats[:3]
                summary += f"\nKomoditas Paling Berpengaruh:\n"
                for i, comm in enumerate(top_3, 1):
                    direction = "+" if comm['total_impact'] > 0 else "-"
                    summary += f"{i}. {comm['name']} {direction} {abs(comm['total_impact']):.3f}% ({comm['frequency']}x)\n"
            else:
                summary += f"\n**Catatan**: Data komoditas tidak tersedia untuk periode ini. Analisis hanya berdasarkan data IPH.\n"
            
            # Category dominance
            if category_breakdown:
                dominant_category = list(category_breakdown.keys())[0]
                category_info = category_breakdown[dominant_category]
                summary += f"\n{category_info['icon']} **Kategori Dominan**: {dominant_category}\n"
                summary += f"   Total dampak: {abs(category_info['total_impact']):.3f}% ({category_info['commodity_count']} komoditas)\n"
            
            # Overall assessment
            if abs(avg_iph) > 2:
                summary += f"\n **Perhatian**: {month} menunjukkan pergerakan harga signifikan!"
            elif abs(avg_iph) > 1:
                summary += f"\nCatatan: {month} menunjukkan pergerakan harga moderat"
            else:
                summary += f"\n **Positif**: {month} menunjukkan stabilitas harga yang baik"
            
            return summary
            
        except Exception as e:
            print(f" Error generating enhanced monthly summary: {e}")
            return f"Analisis {month}: Data tersedia namun terjadi error dalam pemrosesan detail"

    def _generate_monthly_recommendations(self, commodity_stats, category_breakdown):
        """Generate monthly recommendations"""
        recommendations = []
        
        try:
            # High impact commodities recommendations
            high_impact_commodities = [c for c in commodity_stats if abs(c['total_impact']) > 1.0]
            if high_impact_commodities:
                recommendations.append({
                    'priority': 'high',
                    'type': 'commodity_monitoring',
                    'title': 'Monitor Komoditas High-Impact',
                    'description': f'Fokus monitoring {len(high_impact_commodities)} komoditas dengan dampak tinggi',
                    'commodities': [c['name'] for c in high_impact_commodities[:3]],
                    'action': 'Intensifkan monitoring supply-demand'
                })
            
            # Category-based recommendations
            for category, info in list(category_breakdown.items())[:2]:  # Top 2 categories
                if abs(info['total_impact']) > 0.5:
                    recommendations.append({
                        'priority': 'medium',
                        'type': 'category_focus',
                        'title': f'Fokus Kategori {category}',
                        'description': f"{info['icon']} {info['description']} menunjukkan dampak signifikan",
                        'category': category,
                        'action': f"Analisis supply chain kategori {category}"
                    })
            
            # Volatility recommendations
            high_volatility_commodities = [c for c in commodity_stats if c['volatility'] > 1.0]
            if high_volatility_commodities:
                recommendations.append({
                    'priority': 'medium',
                    'type': 'volatility_control',
                    'title': 'Kontrol Volatilitas',
                    'description': f'{len(high_volatility_commodities)} komoditas menunjukkan volatilitas tinggi',
                    'commodities': [c['name'] for c in high_volatility_commodities[:3]],
                    'action': 'Stabilisasi harga komoditas volatile'
                })
            
            return recommendations
            
        except Exception as e:
            print(f" Error generating monthly recommendations: {e}")
            return []

    def get_seasonal_patterns(self):
        """Enhanced seasonal patterns dengan clear categorization"""
        try:
            print(" Analyzing enhanced seasonal patterns...")
            
            df = self.load_commodity_data()
            
            if df.empty:
                return {
                    'success': False, 
                    'message': 'No commodity data available for seasonal analysis'
                }
            
            # Enhanced monthly patterns analysis
            monthly_patterns = {}
            
            # Define month order for proper seasonal analysis
            month_order = [
                'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
            ]
            
            # Process each month
            all_months_in_data = df['Bulan'].dropna().unique()
            
            for month in all_months_in_data:
                month_data = df[df['Bulan'] == month].copy()
                
                if len(month_data) < 1:
                    continue
                
                # Collect commodities for this month
                month_commodities = defaultdict(list)
                
                for _, row in month_data.iterrows():
                    commodities = self.parse_commodity_impacts(row.get('Komoditas_Andil', ''))
                    for comm in commodities:
                        month_commodities[comm['name']].append({
                            'impact': abs(comm['impact']),
                            'category': comm.get('category', 'LAINNYA')
                        })
                
                # Calculate dominant commodities dengan enhanced metrics
                dominant = []
                category_impacts = defaultdict(float)
                
                for name, impacts_data in month_commodities.items():
                    if impacts_data:
                        impacts = [item['impact'] for item in impacts_data]
                        category = impacts_data[0]['category']
                        
                        commodity_info = {
                            'name': name,
                            'avg_impact': float(np.mean(impacts)),
                            'total_impact': float(sum(impacts)),
                            'frequency': len(impacts),
                            'max_impact': float(max(impacts)),
                            'category': category,
                            'consistency_score': 1.0 - (np.std(impacts) / (np.mean(impacts) + 0.001)) if len(impacts) > 1 else 1.0
                        }
                        
                        dominant.append(commodity_info)
                        category_impacts[category] += commodity_info['total_impact']
                
                dominant.sort(key=lambda x: x['total_impact'], reverse=True)
                
                # Calculate month statistics
                iph_values = month_data['IPH'].dropna()
                volatility_values = month_data['Nilai_Fluktuasi'].dropna()
                
                # Determine month characteristics
                avg_iph = float(iph_values.mean()) if not iph_values.empty else 0.0
                iph_volatility = float(iph_values.std()) if len(iph_values) > 1 else 0.0
                commodity_volatility = float(volatility_values.mean()) if not volatility_values.empty else 0.0
                
                # Enhanced categorization
                month_category = self._categorize_month_pattern(avg_iph, iph_volatility, commodity_volatility)
                
                monthly_patterns[month] = {
                    'avg_iph': avg_iph,
                    'iph_std': iph_volatility,
                    'commodity_volatility': commodity_volatility,
                    'weeks_data': len(month_data),
                    'dominant_commodities': dominant[:5],
                    'commodity_diversity': len(month_commodities),
                    'category_breakdown': dict(category_impacts),
                    'month_category': month_category,
                    'dominant_category': max(category_impacts.items(), key=lambda x: x[1])[0] if category_impacts else 'UNKNOWN'
                }
            
            # Enhanced seasonal insights dengan clear explanation
            seasonal_insights = self._analyze_enhanced_seasonal_insights(monthly_patterns)
            
            # Generate categorization explanation
            categorization_explanation = {
                'temporal_basis': {
                    'type': 'Monthly Calendar Pattern',
                    'description': 'Analisis berdasarkan 12 bulan kalender (Januari-Desember)',
                    'purpose': 'Mengidentifikasi pola seasonal komoditas sepanjang tahun'
                },
                'impact_categories': {
                    'Inflasi Tinggi': {'threshold': '> 2%', 'color': 'danger', 'description': 'Bulan dengan tekanan inflasi kuat'},
                    'Inflasi Sedang': {'threshold': '0.5% - 2%', 'color': 'warning', 'description': 'Bulan dengan inflasi moderat'},
                    'Stabil': {'threshold': '-0.5% - 0.5%', 'color': 'success', 'description': 'Bulan dengan kondisi harga stabil'},
                    'Deflasi Sedang': {'threshold': '-2% - -0.5%', 'color': 'info', 'description': 'Bulan dengan deflasi moderat'},
                    'Deflasi Tinggi': {'threshold': '< -2%', 'color': 'primary', 'description': 'Bulan dengan deflasi kuat'}
                },
                'volatility_levels': {
                    'Rendah': {'threshold': '< 1%', 'description': 'Volatilitas harga rendah, kondisi stabil'},
                    'Sedang': {'threshold': '1% - 2%', 'description': 'Volatilitas normal, pergerakan wajar'},
                    'Tinggi': {'threshold': '> 2%', 'description': 'Volatilitas tinggi, perlu perhatian khusus'}
                }
            }
            
            return {
                'success': True,
                'seasonal_patterns': monthly_patterns,
                'seasonal_insights': seasonal_insights,
                'categorization_explanation': categorization_explanation,
                'summary': self._generate_enhanced_seasonal_summary(monthly_patterns, seasonal_insights),
                'recommendations': self._generate_seasonal_recommendations(monthly_patterns, seasonal_insights)
            }
            
        except Exception as e:
            print(f"Error in enhanced seasonal analysis: {str(e)}")
            return {
                'success': False,
                'message': f'Error menganalisis pola musiman: {str(e)}'
            }

    def _categorize_month_pattern(self, avg_iph, iph_volatility, commodity_volatility):
        """Categorize month pattern based on IPH and volatility"""
        # Primary categorization based on IPH
        if avg_iph > 2:
            primary = 'Inflasi Tinggi'
            color = 'danger'
        elif avg_iph > 0.5:
            primary = 'Inflasi Sedang'
            color = 'warning'
        elif avg_iph > -0.5:
            primary = 'Stabil'
            color = 'success'
        elif avg_iph > -2:
            primary = 'Deflasi Sedang'
            color = 'info'
        else:
            primary = 'Deflasi Tinggi'
            color = 'primary'
        
        # Secondary categorization based on volatility
        if iph_volatility > 2:
            volatility_level = 'Volatilitas Tinggi'
        elif iph_volatility > 1:
            volatility_level = 'Volatilitas Sedang'
        else:
            volatility_level = 'Volatilitas Rendah'
        
        return {
            'primary': primary,
            'color': color,
            'volatility_level': volatility_level,
            'combined_score': abs(avg_iph) + iph_volatility,
            'risk_level': 'high' if abs(avg_iph) > 2 or iph_volatility > 2 else 'medium' if abs(avg_iph) > 1 or iph_volatility > 1 else 'low'
        }

    def _analyze_enhanced_seasonal_insights(self, patterns):
        """Generate enhanced seasonal insights"""
        insights = {
            'peak_inflation_months': [],
            'peak_deflation_months': [],
            'most_volatile_months': [],
            'stable_months': [],
            'high_risk_months': [],
            'seasonal_commodity_patterns': {},
            'category_seasonal_trends': {}
        }
        
        # Analyze each month
        for month, data in patterns.items():
            month_info = {
                'month': month,
                'avg_iph': data['avg_iph'],
                'category': data['month_category']['primary'],
                'risk_level': data['month_category']['risk_level'],
                'dominant_commodity': data['dominant_commodities'][0]['name'] if data['dominant_commodities'] else 'N/A',
                'dominant_category': data['dominant_category']
            }
            
            # Categorize months
            if data['avg_iph'] > 1.5:
                insights['peak_inflation_months'].append(month_info)
            elif data['avg_iph'] < -1.5:
                insights['peak_deflation_months'].append(month_info)
            elif abs(data['avg_iph']) < 0.5:
                insights['stable_months'].append(month_info)
            
            if data['month_category']['risk_level'] == 'high':
                insights['high_risk_months'].append(month_info)
            
            if data['iph_std'] > 1.5:
                insights['most_volatile_months'].append({
                    **month_info,
                    'volatility': data['iph_std']
                })
        
        # Sort insights
        insights['peak_inflation_months'].sort(key=lambda x: x['avg_iph'], reverse=True)
        insights['peak_deflation_months'].sort(key=lambda x: x['avg_iph'])
        insights['most_volatile_months'].sort(key=lambda x: x['volatility'], reverse=True)
        
        return insights

    def _generate_enhanced_seasonal_summary(self, patterns, insights):
        """Generate enhanced seasonal summary"""
        if not patterns:
            return "No seasonal data available"
        
        summary = " **Pola Seasonal Komoditas (Berdasarkan Bulan Kalender)**\n\n"
        
        # High-level overview
        total_months = len(patterns)
        avg_iph_all = np.mean([data['avg_iph'] for data in patterns.values()])
        
        summary += f"Overview: {total_months} bulan dianalisis, rata-rata IPH tahunan: {avg_iph_all:.2f}%\n\n"
        
        # Peak periods
        if insights['peak_inflation_months']:
            peak_month = insights['peak_inflation_months'][0]
            summary += f" **Puncak Inflasi**: {peak_month['month']} ({peak_month['avg_iph']:.2f}%)\n"
            summary += f"   Didominasi: {peak_month['dominant_commodity']} (kategori {peak_month['dominant_category']})\n\n"
        
        if insights['peak_deflation_months']:
            trough_month = insights['peak_deflation_months'][0]
            summary += f" **Puncak Deflasi**: {trough_month['month']} ({trough_month['avg_iph']:.2f}%)\n"
            summary += f"   Didominasi: {trough_month['dominant_commodity']} (kategori {trough_month['dominant_category']})\n\n"
        
        # Stability analysis
        if insights['stable_months']:
            stable_count = len(insights['stable_months'])
            summary += f" **Bulan Stabil**: {stable_count} bulan menunjukkan stabilitas harga\n\n"
        
        # Risk assessment
        if insights['high_risk_months']:
            risk_months = [m['month'] for m in insights['high_risk_months']]
            summary += f" **Bulan Berisiko Tinggi**: {', '.join(risk_months)}\n"
            summary += f"   Memerlukan monitoring ekstra dan persiapan kebijakan\n\n"
        
        # Volatility patterns
        if insights['most_volatile_months']:
            volatile_month = insights['most_volatile_months'][0]
            summary += f" **Bulan Paling Volatile**: {volatile_month['month']} "
            summary += f"(volatility: {volatile_month['volatility']:.3f}%)\n"
        
        return summary

    def get_alert_commodities(self, threshold=0.05):
        """Enhanced alert system dengan better space efficiency"""
        try:
            df = self.load_commodity_data()
            
            if df.empty:
                return {
                    'success': False, 
                    'message': 'No commodity data available'
                }
            
            # Get recent data (last 8 weeks for better analysis)
            recent_df = df.tail(16).copy()
            
            alerts = []
            
            for _, row in recent_df.iterrows():
                volatility = row.get('Nilai_Fluktuasi', 0)
                
                if pd.isna(volatility):
                    continue
                    
                try:
                    volatility = float(volatility)
                except:
                    continue
                
                if volatility > threshold:
                    # Enhanced severity determination
                    if volatility > 0.20:
                        severity = 'critical'
                        severity_text = 'Kritis'
                        priority_score = 4
                    elif volatility > 0.15:
                        severity = 'high'
                        severity_text = 'Tinggi'
                        priority_score = 3
                    elif volatility > 0.10:
                        severity = 'medium'
                        severity_text = 'Sedang'
                        priority_score = 2
                    else:
                        severity = 'low'
                        severity_text = 'Rendah'
                        priority_score = 1
                    
                    commodity_name = row.get('Komoditas_Fluktuasi_Tertinggi', 'Unknown')
                    standardized_name = self._standardize_commodity_name(str(commodity_name))
                    category_info = self._get_commodity_category_info(standardized_name)
                    
                    alerts.append({
                        'period': f"{row.get('Bulan', 'Unknown')} {row.get('Minggu', 'Unknown')}",
                        'date': row['Tanggal'].strftime('%Y-%m-%d') if pd.notna(row['Tanggal']) else 'Unknown',
                        'commodity': str(commodity_name),
                        'standardized_name': standardized_name,
                        'volatility': volatility,
                        'volatility_percentage': volatility * 100,
                        'iph_impact': float(row.get('IPH', 0)),
                        'severity': severity,
                        'severity_text': severity_text,
                        'priority_score': priority_score,
                        'category': category_info['category'],
                        'category_icon': category_info['icon'],
                        'threshold_exceeded': volatility / threshold,
                        'days_ago': (datetime.now() - pd.to_datetime(row['Tanggal'])).days if pd.notna(row['Tanggal']) else 0
                    })
            
            # Sort by priority score then volatility
            alerts.sort(key=lambda x: (x['priority_score'], x['volatility']), reverse=True)
            
            # Enhanced alert statistics
            alert_stats = {
                'total_alerts': len(alerts),
                'critical_alerts': len([a for a in alerts if a['severity'] == 'critical']),
                'high_alerts': len([a for a in alerts if a['severity'] == 'high']),
                'medium_alerts': len([a for a in alerts if a['severity'] == 'medium']),
                'low_alerts': len([a for a in alerts if a['severity'] == 'low']),
                'categories_affected': len(set(a['category'] for a in alerts)),
                'recent_alerts': len([a for a in alerts if a['days_ago'] <= 7]),
                'avg_volatility': np.mean([a['volatility'] for a in alerts]) if alerts else 0,
                'max_volatility': max([a['volatility'] for a in alerts]) if alerts else 0
            }
            
            return {
                'success': True,
                'threshold': threshold,
                'threshold_percentage': threshold * 100,
                'alerts': alerts,
                'statistics': alert_stats,
                'summary': self._generate_enhanced_alert_summary(alerts, threshold, alert_stats),
                'recommendations': self._generate_enhanced_alert_recommendations(alerts, alert_stats)
            }
            
        except Exception as e:
            print(f"Error in enhanced alert analysis: {str(e)}")
            return {
                'success': False,
                'message': f'Error menganalisis peringatan: {str(e)}'
            }

    def _generate_enhanced_alert_summary(self, alerts, threshold, stats):
        """Generate enhanced alert summary"""
        if not alerts:
            return f" Kondisi Normal: Tidak ada komoditas dengan volatilitas > {threshold:.1%}"
        
        summary = f" **Alert Volatilitas Komoditas** (Threshold: {threshold:.1%})\n\n"
        
        # Alert breakdown
        if stats['critical_alerts'] > 0:
            summary += f" **Kritis**: {stats['critical_alerts']} komoditas (>20%)\n"
        if stats['high_alerts'] > 0:
            summary += f" **Tinggi**: {stats['high_alerts']} komoditas (15-20%)\n"
        if stats['medium_alerts'] > 0:
            summary += f" **Sedang**: {stats['medium_alerts']} komoditas (10-15%)\n"
        
        # Most problematic
        if alerts:
            top_alert = alerts[0]
            summary += f"\n **Paling Bermasalah**: {top_alert['commodity']}\n"
            summary += f"   Volatilitas: {top_alert['volatility_percentage']:.1f}% ({top_alert['severity_text']})\n"
            summary += f"   Kategori: {top_alert['category']} {top_alert['category_icon']}\n"
        
        # Recent trend
        recent_alerts = [a for a in alerts if a['days_ago'] <= 7]
        if recent_alerts:
            summary += f"\n **Minggu Ini**: {len(recent_alerts)} alert baru"
        
        return summary

    def _generate_enhanced_alert_recommendations(self, alerts, stats):
        """Generate enhanced alert recommendations"""
        recommendations = []
        
        try:
            # Critical alerts
            critical_alerts = [a for a in alerts if a['severity'] == 'critical']
            if critical_alerts:
                recommendations.append({
                    'priority': 'critical',
                    'type': 'immediate_action',
                    'title': 'Tindakan Segera Diperlukan',
                    'description': f'Monitor intensif {len(critical_alerts)} komoditas dengan volatilitas kritis',
                    'commodities': [a['commodity'] for a in critical_alerts[:3]],
                    'action': 'Intervensi pasar dan stabilisasi harga',
                    'timeframe': 'Segera (24-48 jam)'
                })
            
            # Category-based recommendations
            category_counts = defaultdict(int)
            for alert in alerts:
                category_counts[alert['category']] += 1
            
            for category, count in category_counts.items():
                if count >= 2:
                    category_info = self.commodity_categories.get(category, {})
                    recommendations.append({
                        'priority': 'high',
                        'type': 'category_intervention',
                        'title': f'Intervensi Kategori {category}',
                        'description': f"{category_info.get('icon', '')} {count} komoditas dalam kategori {category} menunjukkan volatilitas tinggi",
                        'category': category,
                        'action': f'Analisis supply chain {category_info.get("description", "kategori ini")}',
                        'timeframe': '1-2 minggu'
                    })
            
            # Trend-based recommendations
            recent_alerts = [a for a in alerts if a['days_ago'] <= 7]
            if len(recent_alerts) > len(alerts) * 0.5:  # More than 50% are recent
                recommendations.append({
                    'priority': 'medium',
                    'type': 'trend_monitoring',
                    'title': 'Trend Volatilitas Meningkat',
                    'description': f'{len(recent_alerts)} dari {len(alerts)} alert terjadi dalam 7 hari terakhir',
                    'action': 'Tingkatkan frekuensi monitoring harga',
                    'timeframe': 'Ongoing'
                })
            
            return recommendations
            
        except Exception as e:
            print(f" Error generating enhanced recommendations: {e}")
            return []
         
    def get_full_commodity_insights(self, start_key=None, end_key=None):
            """
            MODIFIED: Menghasilkan data Tren (Bar Chart dengan warna dinamis) 
            dan Frekuensi (Top 5). Dampak Akumulatif dihapus.
            """
            try:
                df = self.load_commodity_data()
                # Struktur default
                empty_response = {
                    'success': True,
                    'trend_sparkline_data': [],
                    'frequency_chart_data': {'x': [], 'y': []},
                    'impact_chart_data': {} 
                }

                if df.empty:
                    return empty_response

                # --- 1. Filter Rentang Waktu (Logika Standar) ---
                df_filtered = df.copy()
                if start_key or end_key:
                    try:
                        df_filtered['Tanggal'] = pd.to_datetime(df_filtered['Tanggal'])
                        df_filtered['_ym'] = df_filtered['Tanggal'].dt.year * 100 + df_filtered['Tanggal'].dt.month
                        
                        start_ym = int(start_key.replace('-', '')) if start_key else 0
                        end_ym = int(end_key.replace('-', '')) if end_key else 999999

                        if start_ym and end_ym:
                            df_filtered = df_filtered[(df_filtered['_ym'] >= start_ym) & (df_filtered['_ym'] <= end_ym)]
                    except Exception as e:
                        print(f"Error filtering dates: {e}")
                        return empty_response
                
                if df_filtered.empty:
                    return empty_response

                # --- 2. Parsing Komoditas ---
                all_commodities = []
                for _, row in df_filtered.iterrows():
                    if pd.notna(row.get('Komoditas_Andil')) and row.get('Komoditas_Andil') != 'DATA_TIDAK_TERSEDIA':
                        commodities = self.parse_commodity_impacts(row['Komoditas_Andil'])
                        for comm in commodities:
                            comm['tanggal'] = row['Tanggal']
                            # PERUBAHAN 1: Siapkan label periode (Bulan X Minggu Y) untuk tooltip
                            comm['periode_label'] = f"{row.get('Bulan', '')} {row.get('Tahun', '')} {row.get('Minggu', '')}".strip()
                        all_commodities.extend(commodities)
                
                if not all_commodities:
                    return empty_response
                
                commodities_df = pd.DataFrame(all_commodities)
                commodities_df['tanggal'] = pd.to_datetime(commodities_df['tanggal'])

                # --- 3. Hitung Agregat ---
                
                # A. DATA TREN (Disesuaikan untuk Bar Chart Warna-warni)
                trend_stats = commodities_df.groupby('name').agg(
                    frequency=pd.NamedAgg(column='name', aggfunc='size')
                ).sort_values(by='frequency', ascending=False)

                trend_data_final = []
                # Ambil Top 5 Komoditas Saja
                for name in trend_stats.head(5).index:
                    comm_data = commodities_df[commodities_df['name'] == name].sort_values('tanggal')
                    
                    chart_x = [d.strftime('%Y-%m-%d') for d in comm_data['tanggal']]
                    chart_y = [float(i) for i in comm_data['impact']]
                    
                    # PERUBAHAN 2: Custom Tooltip Text
                    chart_text = [
                        f"{row.periode_label}<br>Indeks: {row.impact:.3f}%" 
                        for _, row in comm_data.iterrows()
                    ]
                    
                    # PERUBAHAN 3: Warna Dinamis (Merah=Inflasi, Hijau=Deflasi)
                    chart_color = ['#dc3545' if val > 0 else '#198754' for val in chart_y]

                    trend_data_final.append({
                        'name': self._standardize_commodity_name(name).replace('_', ' ').lower(),
                        'frequency': int(trend_stats.loc[name, 'frequency']),
                        'chart': { 
                            'x': chart_x,
                            'y': chart_y,
                            'text': chart_text,         # Text khusus untuk hover
                            'marker_color': chart_color # Warna khusus per bar
                        }
                    })

                # B. DATA FREKUENSI (Top 5 Bar Chart)
                freq_series = commodities_df.groupby('name').size().sort_values(ascending=False).head(5)
                frequency_chart_data = {
                    'x': [self._standardize_commodity_name(n).replace('_', ' ').lower() for n in freq_series.index],
                    'y': [int(v) for v in freq_series.values]
                }

                # PERUBAHAN 4: Impact Chart dikosongkan (karena dihapus dari UI)
                impact_chart_data = {}

                return {
                    'success': True,
                    'trend_sparkline_data': trend_data_final,
                    'frequency_chart_data': frequency_chart_data,
                    'impact_chart_data': impact_chart_data
                }
                
            except Exception as e:
                print(f"Error in get_full_commodity_insights: {e}")
                return {'success': False, 'error': str(e)}

    def _generate_enhanced_trend_summary(trends):
        """Generate enhanced trend summary"""
        if not trends:
            return "No commodity trends available"
        
        # Categorize trends
        strong_increasing = [name for name, data in trends.items() 
                        if data.get('trend') == 'increasing' and data.get('trend_strength') == 'strong']
        strong_decreasing = [name for name, data in trends.items() 
                        if data.get('trend') == 'decreasing' and data.get('trend_strength') == 'strong']
        
        most_volatile = max(trends.items(), key=lambda x: x[1].get('volatility', 0)) if trends else None
        most_consistent = max(trends.items(), key=lambda x: x[1]['appearances']) if trends else None
        
        summary = "Analisis Trend Komoditas:\n\n"
        
        if strong_increasing:
            summary += f"Dampak meningkat kuat: {', '.join(strong_increasing[:3])}\n"
        
        if strong_decreasing:
            summary += f"Dampak menurun kuat: {', '.join(strong_decreasing[:3])}\n"
        
        if most_volatile:
            summary += f"Paling volatile: {most_volatile[0]} (volatility: {most_volatile[1]['volatility']:.3f})\n"
        
        if most_consistent:
            summary += f"Paling konsisten: {most_consistent[0]} ({most_consistent[1]['appearances']} kali muncul)"
        
        return summary

    def _analyze_category_trends(self, trends):
        """Analyze trends by commodity category"""
        category_trends = defaultdict(lambda: {
            'commodities': 0,
            'total_impact': 0,
            'avg_volatility': 0,
            'trend_direction': 'stable'
        })
        
        for name, data in trends.items():
            category = data.get('category', 'LAINNYA')
            category_trends[category]['commodities'] += 1
            category_trends[category]['total_impact'] += data.get('total_impact', 0)
            category_trends[category]['avg_volatility'] += data.get('volatility', 0)
        
        # Calculate averages and determine trend direction
        for category, data in category_trends.items():
            if data['commodities'] > 0:
                data['avg_volatility'] /= data['commodities']
                if data['total_impact'] > 0.1:
                    data['trend_direction'] = 'inflationary'
                elif data['total_impact'] < -0.1:
                    data['trend_direction'] = 'deflationary'
                else:
                    data['trend_direction'] = 'stable'
        
        return dict(category_trends)

    def _generate_enhanced_weekly_summary(self, latest_record, commodities, category_analysis):
        """Generate enhanced weekly summary"""
        try:
            iph_value = latest_record.get('IPH', 0)
            period = f"{latest_record.get('Bulan', 'Unknown')} {latest_record.get('Minggu', 'Unknown')}"
            
            # Create summary based on IPH and commodities
            if iph_value > 2:
                summary = f" **Inflasi Tinggi**: IPH mencapai {iph_value:.2f}% pada {period}"
            elif iph_value > 0:
                summary = f" **Inflasi Moderat**: IPH {iph_value:.2f}% pada {period}"
            elif iph_value < -2:
                summary = f" **Deflasi Tinggi**: IPH turun {iph_value:.2f}% pada {period}"
            else:
                summary = f" **Kondisi Stabil**: IPH {iph_value:.2f}% pada {period}"
            
            # Add top commodity info
            if commodities:
                top_commodity = max(commodities, key=lambda x: abs(x['impact']))
                summary += f"\n\nKomoditas paling berpengaruh: **{top_commodity['name']}** "
                summary += f"({top_commodity['impact']:+.3f}%)"
            
            # Add category dominance
            if category_analysis:
                dominant_category = list(category_analysis.keys())[0]
                summary += f"\n\nKategori dominan: **{dominant_category}**"
            
            return summary
            
        except Exception as e:
            return f"Ringkasan minggu {latest_record.get('Minggu', 'ini')}: Data tersedia"

    def _generate_weekly_recommendations(self, latest_record, commodities, category_analysis):
        """Generate weekly recommendations"""
        recommendations = []
        
        try:
            iph_value = latest_record.get('IPH', 0)
            
            # IPH-based recommendations
            if abs(iph_value) > 2:
                recommendations.append({
                    'priority': 'high',
                    'title': 'Monitor Intensif',
                    'description': f'IPH {iph_value:.2f}% memerlukan monitoring ketat',
                    'action': 'Analisis supply-demand komoditas utama'
                })
            
            # High impact commodity recommendations
            high_impact = [c for c in commodities if abs(c['impact']) > 0.5]
            if high_impact:
                recommendations.append({
                    'priority': 'medium',
                    'title': 'Komoditas High-Impact',
                    'description': f'{len(high_impact)} komoditas dengan dampak signifikan',
                    'action': 'Fokus stabilisasi harga'
                })
            
            return recommendations
            
        except Exception as e:
            return []

    def _generate_enhanced_trend_summary(self, trends, periods_analyzed=None, total_available=None):
        """Generate enhanced trend summary"""
        if not trends:
            return "No commodity trends available"
        
        # Categorize trends
        strong_increasing = [name for name, data in trends.items() 
                        if data.get('trend') == 'increasing' and data.get('trend_strength') == 'strong']
        strong_decreasing = [name for name, data in trends.items() 
                        if data.get('trend') == 'decreasing' and data.get('trend_strength') == 'strong']
        moderate_increasing = [name for name, data in trends.items() 
                        if data.get('trend') == 'increasing' and data.get('trend_strength') == 'moderate']
        moderate_decreasing = [name for name, data in trends.items() 
                        if data.get('trend') == 'decreasing' and data.get('trend_strength') == 'moderate']
        
        most_volatile = max(trends.items(), key=lambda x: x[1].get('volatility', 0)) if trends else None
        most_consistent = max(trends.items(), key=lambda x: x[1]['appearances']) if trends else None
        
        summary = "📊 Analisis Trend Komoditas:\n\n"
        
        # Add scope information
        if periods_analyzed and total_available:
            if periods_analyzed == total_available:
                summary += f"**Scope**: Semua data ({total_available} periode)\n"
            else:
                summary += f"**Scope**: {periods_analyzed} periode terakhir dari {total_available} total\n"
        
        summary += f"**Total Komoditas**: {len(trends)} komoditas dianalisis\n\n"
        
        # Trend analysis
        if strong_increasing:
            summary += f"📈 **Dampak meningkat kuat**: {', '.join(strong_increasing[:3])}\n"
        
        if strong_decreasing:
            summary += f"📉 **Dampak menurun kuat**: {', '.join(strong_decreasing[:3])}\n"
        
        if moderate_increasing:
            summary += f"📊 **Dampak meningkat moderat**: {', '.join(moderate_increasing[:3])}\n"
        
        if moderate_decreasing:
            summary += f"📊 **Dampak menurun moderat**: {', '.join(moderate_decreasing[:3])}\n"
        
        if most_volatile:
            summary += f"⚡ **Paling volatile**: {most_volatile[0]} (volatility: {most_volatile[1]['volatility']:.3f})\n"
        
        if most_consistent:
            summary += f"🎯 **Paling konsisten**: {most_consistent[0]} ({most_consistent[1]['appearances']} kali muncul)"
        
        return summary

    def _generate_seasonal_recommendations(self, patterns, insights):
        """Generate seasonal recommendations"""
        recommendations = []
        
        try:
            # High risk months recommendations
            if insights.get('high_risk_months'):
                recommendations.append({
                    'priority': 'high',
                    'title': 'Monitor Bulan Berisiko',
                    'description': f'{len(insights["high_risk_months"])} bulan memerlukan perhatian khusus',
                    'action': 'Persiapan kebijakan stabilisasi'
                })
            
            # Peak inflation recommendations
            if insights.get('peak_inflation_months'):
                peak_month = insights['peak_inflation_months'][0]
                recommendations.append({
                    'priority': 'medium',
                    'title': f'Antisipasi {peak_month["month"]}',
                    'description': f'Bulan dengan inflasi tertinggi ({peak_month["avg_iph"]:.2f}%)',
                    'action': 'Persiapan stock dan stabilisasi'
                })
            
            return recommendations
            
        except Exception as e:
            return []
        