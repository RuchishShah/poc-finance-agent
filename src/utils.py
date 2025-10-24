#!/usr/bin/env python3
"""
Utility functions for Daily Financial Summary Agent
Handles CSV validation, data processing, formatting, and report generation.
"""

import logging
import pandas as pd
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal, InvalidOperation


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class CSVValidator:
    """Validates and processes CSV transaction data."""
    
    REQUIRED_COLUMNS = ['Date', 'Description', 'Amount', 'Type']
    OPTIONAL_COLUMNS = ['Category', 'Account', 'Balance']
    VALID_TYPES = ['Debit', 'Credit', 'debit', 'credit']
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_csv_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate CSV structure and return validation results."""
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'column_info': {},
            'data_quality': {}
        }
        
        # Check required columns
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            validation_results['is_valid'] = False
            validation_results['errors'].append(f"Missing required columns: {missing_columns}")
        
        # Check for extra columns
        extra_columns = [col for col in df.columns if col not in self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS]
        if extra_columns:
            validation_results['warnings'].append(f"Unknown columns found: {extra_columns}")
        
        # Validate data types and content
        if validation_results['is_valid']:
            validation_results.update(self._validate_data_quality(df))
        
        return validation_results
    
    def _validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate data quality and content."""
        quality_info = {
            'data_quality': {
                'total_rows': len(df),
                'valid_rows': 0,
                'date_errors': 0,
                'amount_errors': 0,
                'type_errors': 0,
                'duplicate_count': 0
            },
            'errors': [],
            'warnings': []
        }
        
        # Check for duplicates
        duplicates = df.duplicated().sum()
        quality_info['data_quality']['duplicate_count'] = duplicates
        if duplicates > 0:
            quality_info['warnings'].append(f"Found {duplicates} duplicate transactions")
        
        # Validate dates
        date_errors = 0
        for idx, date_val in df['Date'].items():
            if pd.isna(date_val) or str(date_val).strip() == '':
                date_errors += 1
        
        quality_info['data_quality']['date_errors'] = date_errors
        if date_errors > 0:
            quality_info['warnings'].append(f"Found {date_errors} invalid/missing dates")
        
        # Validate amounts
        amount_errors = 0
        for idx, amount_val in df['Amount'].items():
            if pd.isna(amount_val):
                amount_errors += 1
                continue
            try:
                float(str(amount_val).replace('$', '').replace(',', ''))
            except (ValueError, TypeError):
                amount_errors += 1
        
        quality_info['data_quality']['amount_errors'] = amount_errors
        if amount_errors > 0:
            quality_info['warnings'].append(f"Found {amount_errors} invalid amounts")
        
        # Validate transaction types
        type_errors = 0
        if 'Type' in df.columns:
            invalid_types = df[~df['Type'].isin(self.VALID_TYPES)]
            type_errors = len(invalid_types)
            if type_errors > 0:
                unique_invalid = invalid_types['Type'].unique()
                quality_info['warnings'].append(f"Found {type_errors} invalid transaction types: {list(unique_invalid)}")
        
        quality_info['data_quality']['type_errors'] = type_errors
        quality_info['data_quality']['valid_rows'] = len(df) - max(date_errors, amount_errors, type_errors)
        
        return quality_info
    
    def clean_and_validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate transaction data."""
        df_clean = df.copy()
        
        # Clean and convert dates
        df_clean['Date'] = self._parse_dates(df_clean['Date'])
        
        # Clean and convert amounts
        df_clean['Amount'] = self._parse_amounts(df_clean['Amount'])
        
        # Standardize transaction types
        df_clean['Type'] = self._standardize_types(df_clean['Type'])
        
        # Remove rows with critical missing data
        df_clean = df_clean.dropna(subset=['Date', 'Amount'])
        
        # Remove duplicates
        df_clean = df_clean.drop_duplicates()
        
        self.logger.info(f"Data cleaning complete: {len(df)} -> {len(df_clean)} valid transactions")
        
        return df_clean
    
    def _parse_dates(self, date_series: pd.Series) -> pd.Series:
        """Parse dates with multiple format support."""
        def parse_date(date_val):
            if pd.isna(date_val):
                return pd.NaT
            
            date_str = str(date_val).strip()
            
            # Try common date formats
            formats = [
                '%Y-%m-%d',           # 2025-10-24
                '%m/%d/%Y',           # 10/24/2025
                '%m-%d-%Y',           # 10-24-2025
                '%d/%m/%Y',           # 24/10/2025
                '%Y/%m/%d',           # 2025/10/24
                '%m/%d/%y',           # 10/24/25
                '%Y-%m-%d %H:%M:%S',  # 2025-10-24 14:30:00
            ]
            
            for fmt in formats:
                try:
                    return pd.to_datetime(date_str, format=fmt)
                except (ValueError, TypeError):
                    continue
            
            # Try pandas' automatic parsing as fallback
            try:
                return pd.to_datetime(date_str)
            except:
                return pd.NaT
        
        return date_series.apply(parse_date)
    
    def _parse_amounts(self, amount_series: pd.Series) -> pd.Series:
        """Parse and clean amount values."""
        def clean_amount(amount_val):
            if pd.isna(amount_val):
                return None
            
            # Convert to string and clean
            amount_str = str(amount_val).strip()
            
            # Remove currency symbols and commas
            amount_str = re.sub(r'[$,€£¥]', '', amount_str)
            
            # Handle parentheses (accounting format for negative)
            if amount_str.startswith('(') and amount_str.endswith(')'):
                amount_str = '-' + amount_str[1:-1]
            
            try:
                return float(amount_str)
            except (ValueError, TypeError):
                return None
        
        return amount_series.apply(clean_amount)
    
    def _standardize_types(self, type_series: pd.Series) -> pd.Series:
        """Standardize transaction type values."""
        def standardize_type(type_val):
            if pd.isna(type_val):
                return 'Unknown'
            
            type_str = str(type_val).strip().lower()
            
            if type_str in ['debit', 'withdrawal', 'expense', 'out', '-']:
                return 'Debit'
            elif type_str in ['credit', 'deposit', 'income', 'in', '+']:
                return 'Credit'
            else:
                return 'Unknown'
        
        return type_series.apply(standardize_type)


class DataFormatter:
    """Formats financial data for display and analysis."""
    
    @staticmethod
    def format_currency(amount: float, currency_symbol: str = '$') -> str:
        """Format amount as currency."""
        if pd.isna(amount):
            return f"{currency_symbol}0.00"
        
        return f"{currency_symbol}{abs(amount):,.2f}"
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """Format value as percentage."""
        if pd.isna(value):
            return "0.0%"
        
        return f"{value:.{decimal_places}f}%"
    
    @staticmethod
    def format_date_range(start_date: datetime, end_date: datetime) -> str:
        """Format date range for display."""
        if start_date == end_date:
            return start_date.strftime('%B %d, %Y')
        else:
            return f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"
    
    @staticmethod
    def calculate_spending_breakdown(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate spending breakdown by category and type."""
        # Separate income and expenses
        expenses = df[df['Amount'] < 0].copy()
        income = df[df['Amount'] > 0].copy()
        
        # Calculate totals
        total_spent = abs(expenses['Amount'].sum()) if not expenses.empty else 0
        total_income = income['Amount'].sum() if not income.empty else 0
        
        # Basic categorization by description keywords
        categories = DataFormatter._categorize_transactions(expenses)
        
        breakdown = {
            'summary': {
                'total_income': total_income,
                'total_spent': total_spent,
                'net_flow': total_income - total_spent,
                'transaction_count': len(df)
            },
            'categories': categories,
            'by_type': {
                'income_count': len(income),
                'expense_count': len(expenses)
            }
        }
        
        return breakdown
    
    @staticmethod
    def _categorize_transactions(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Categorize transactions based on description keywords."""
        if df.empty:
            return {}
        
        # Category mapping
        category_keywords = {
            'Groceries': ['grocery', 'whole foods', 'trader joe', 'costco', 'safeway', 'kroger', 'walmart', 'food'],
            'Dining': ['restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonald', 'burger', 'pizza', 'chipotle', 'uber eats', 'doordash'],
            'Transportation': ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'parking', 'metro', 'bus', 'train'],
            'Bills': ['electric', 'gas bill', 'water', 'internet', 'phone', 'cable', 'insurance', 'rent', 'mortgage'],
            'Shopping': ['amazon', 'target', 'mall', 'store', 'shopping', 'clothing', 'retail'],
            'Entertainment': ['netflix', 'spotify', 'movie', 'theater', 'game', 'entertainment', 'subscription'],
            'Healthcare': ['pharmacy', 'doctor', 'medical', 'health', 'cvs', 'walgreen'],
            'Other': []
        }
        
        categories = {}
        df_copy = df.copy()
        df_copy['Category'] = 'Other'
        
        # Categorize based on description
        for category, keywords in category_keywords.items():
            if category == 'Other':
                continue
                
            mask = df_copy['Description'].str.lower().str.contains('|'.join(keywords), na=False)
            df_copy.loc[mask, 'Category'] = category
        
        # Calculate category totals
        for category in category_keywords.keys():
            category_data = df_copy[df_copy['Category'] == category]
            if not category_data.empty:
                total = abs(category_data['Amount'].sum())
                count = len(category_data)
                avg = total / count if count > 0 else 0
                
                categories[category] = {
                    'total': total,
                    'count': count,
                    'average': avg,
                    'percentage': 0  # Will be calculated later
                }
        
        # Calculate percentages
        total_spending = sum(cat['total'] for cat in categories.values())
        if total_spending > 0:
            for category in categories:
                categories[category]['percentage'] = (categories[category]['total'] / total_spending) * 100
        
        # Sort by total spending
        categories = dict(sorted(categories.items(), key=lambda x: x[1]['total'], reverse=True))
        
        return categories


class ReportGenerator:
    """Generates markdown financial reports."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, analysis: str, breakdown: Dict[str, Any], 
                       file_info: Dict[str, Any]) -> str:
        """Generate complete markdown report."""
        timestamp = datetime.now()
        
        report = self._generate_header(timestamp, file_info)
        report += self._generate_summary_section(breakdown)
        report += self._generate_analysis_section(analysis)
        report += self._generate_breakdown_section(breakdown)
        report += self._generate_footer(timestamp)
        
        return report
    
    def _generate_header(self, timestamp: datetime, file_info: Dict[str, Any]) -> str:
        """Generate report header with metadata."""
        return f"""# 💰 Daily Financial Summary Report

**Generated:** {timestamp.strftime('%B %d, %Y at %I:%M %p')}  
**Data Source:** {file_info.get('filename', 'Unknown')}  
**Transactions:** {file_info.get('transaction_count', 0)}  
**Date Range:** {file_info.get('date_range', 'Unknown')}  

---

"""
    
    def _generate_summary_section(self, breakdown: Dict[str, Any]) -> str:
        """Generate executive summary section."""
        summary = breakdown.get('summary', {})
        
        return f"""## 📊 Executive Summary

| Metric | Amount |
|--------|--------|
| **Total Income** | {DataFormatter.format_currency(summary.get('total_income', 0))} |
| **Total Spent** | {DataFormatter.format_currency(summary.get('total_spent', 0))} |
| **Net Cash Flow** | {DataFormatter.format_currency(summary.get('net_flow', 0))} |
| **Transactions** | {summary.get('transaction_count', 0)} |

---

"""
    
    def _generate_analysis_section(self, analysis: str) -> str:
        """Generate Claude analysis section."""
        return f"""## 🤖 AI Financial Analysis

{analysis}

---

"""
    
    def _generate_breakdown_section(self, breakdown: Dict[str, Any]) -> str:
        """Generate detailed spending breakdown."""
        categories = breakdown.get('categories', {})
        
        section = "## 📈 Spending Breakdown by Category\n\n"
        
        if not categories:
            section += "*No categorized spending found.*\n\n"
            return section
        
        section += "| Category | Amount | Transactions | Average | Percentage |\n"
        section += "|----------|--------|--------------|---------|------------|\n"
        
        for category, data in categories.items():
            section += f"| **{category}** | {DataFormatter.format_currency(data['total'])} | {data['count']} | {DataFormatter.format_currency(data['average'])} | {DataFormatter.format_percentage(data['percentage'])} |\n"
        
        section += "\n---\n\n"
        
        return section
    
    def _generate_footer(self, timestamp: datetime) -> str:
        """Generate report footer."""
        return f"""## 📝 Report Information

- **Report Generated:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- **Analysis Engine:** Claude AI (Anthropic)
- **Agent Version:** Daily Financial Summary Agent v2.0

---

*This report was automatically generated by the Daily Financial Summary Agent. Please review all recommendations and verify calculations before making financial decisions.*
"""
    
    def save_report(self, report_content: str, reports_dir: Path) -> Path:
        """Save report to file with timestamp."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"financial_analysis_{timestamp}.md"
        file_path = reports_dir / filename
        
        try:
            # Ensure reports directory exists
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Write report to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"Report saved successfully: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            raise