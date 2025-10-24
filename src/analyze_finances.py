#!/usr/bin/env python3
"""
Daily Financial Summary Agent - Main Script
Analyzes bank transaction CSV files using Claude AI and generates financial insights.
"""

import logging
import pandas as pd
import sys
from pathlib import Path
from anthropic import Anthropic
from datetime import datetime
from typing import Dict, Any, Tuple

from config import config
from utils import CSVValidator, DataFormatter, ReportGenerator, DataValidationError


class CreditBalanceError(Exception):
    """Raised when Anthropic account has insufficient credits."""
    pass


class AuthenticationError(Exception):
    """Raised when API key is invalid or expired."""
    pass


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    pass


class FinanceAgent:
    """Main finance analysis agent using Claude AI."""
    
    def __init__(self):
        """Initialize the finance agent with Claude client."""
        self.logger = logging.getLogger(__name__)
        self.client = Anthropic(api_key=config.anthropic_api_key)
        self.validator = CSVValidator()
        self.formatter = DataFormatter()
        self.report_generator = ReportGenerator()
        self.logger.info("Finance Agent initialized successfully")
    
    def load_transactions(self, file_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Load and validate transaction data from CSV file."""
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Transaction file not found: {file_path}")
            
            # Read CSV with pandas
            df = pd.read_csv(file_path)
            self.logger.info(f"Loaded {len(df)} transactions from {file_path}")
            
            # Validate CSV structure and quality
            validation_results = self.validator.validate_csv_structure(df)
            
            # Log validation warnings
            for warning in validation_results.get('warnings', []):
                self.logger.warning(warning)
            
            # Raise errors if validation failed
            if not validation_results['is_valid']:
                error_msg = '; '.join(validation_results['errors'])
                raise DataValidationError(f"CSV validation failed: {error_msg}")
            
            # Clean and validate the data
            df_clean = self.validator.clean_and_validate_data(df)
            
            # Prepare file info for reporting
            file_info = {
                'filename': file_path.name,
                'transaction_count': len(df_clean),
                'date_range': self._get_date_range(df_clean),
                'validation_results': validation_results
            }
            
            self.logger.info(f"Successfully processed {len(df_clean)} valid transactions")
            return df_clean, file_info
            
        except Exception as e:
            self.logger.error(f"Error loading transactions: {e}")
            raise
    
    def _get_date_range(self, df: pd.DataFrame) -> str:
        """Get formatted date range from transaction data."""
        if df.empty or 'Date' not in df.columns:
            return "Unknown"
        
        min_date = df['Date'].min()
        max_date = df['Date'].max()
        
        return DataFormatter.format_date_range(min_date, max_date)
    
    def format_transactions_for_analysis(self, df: pd.DataFrame) -> str:
        """Format transaction data for Claude analysis."""
        # Sort by date (most recent first)
        df_sorted = df.sort_values('Date', ascending=False)
        
        # Create formatted string for Claude
        transactions_text = "TRANSACTION DATA:\n"
        transactions_text += "Date | Description | Amount | Type\n"
        transactions_text += "-" * 50 + "\n"
        
        for _, row in df_sorted.iterrows():
            date_str = row['Date'].strftime('%Y-%m-%d')
            amount_str = f"${row['Amount']:.2f}"
            transactions_text += f"{date_str} | {row['Description']} | {amount_str} | {row['Type']}\n"
        
        # Add summary statistics
        total_spent = df[df['Amount'] < 0]['Amount'].sum()
        total_income = df[df['Amount'] > 0]['Amount'].sum()
        net_flow = total_income + total_spent  # total_spent is negative
        transaction_count = len(df)
        
        transactions_text += f"\nSUMMARY STATISTICS:\n"
        transactions_text += f"Total Transactions: {transaction_count}\n"
        transactions_text += f"Total Income: ${total_income:.2f}\n"
        transactions_text += f"Total Spent: ${abs(total_spent):.2f}\n"
        transactions_text += f"Net Cash Flow: ${net_flow:.2f}\n"
        
        return transactions_text
    
    def get_financial_analysis_prompt(self) -> str:
        """Get the system prompt for financial analysis."""
        return """You are a personal finance advisor AI assistant specializing in transaction analysis.

Your responsibilities:
1. Analyze bank transaction data from CSV files
2. Categorize each transaction accurately (groceries, dining, transportation, shopping, entertainment, bills, etc.)
3. Calculate total spending per category
4. Identify spending patterns and trends
5. Spot unusual or large transactions that need attention
6. Provide encouraging but realistic financial insights
7. Generate specific, actionable recommendations

Analysis Format:
- Spending Breakdown (by category with percentages)
- Top 3 Categories (with amounts and insights)
- Notable Transactions (large or unusual purchases)
- Daily Insights (3 observations about spending patterns)
- Action Items (3 specific ways to save money)
- Financial Health Score (1-10 with explanation)

Tone: Encouraging, practical, and focused on actionable improvements.

Please analyze the following transaction data and provide a comprehensive financial summary:"""
    
    def analyze_with_claude(self, transactions_text: str) -> str:
        """Send transaction data to Claude for analysis."""
        try:
            system_prompt = self.get_financial_analysis_prompt()
            
            self.logger.info("Sending transaction data to Claude for analysis...")
            
            response = self.client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=2000,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": transactions_text}
                ]
            )
            
            analysis = response.content[0].text
            self.logger.info("Received analysis from Claude")
            return analysis
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error getting Claude analysis: {e}")
            
            # Handle specific API errors with helpful messages
            if "credit balance is too low" in error_msg:
                raise CreditBalanceError("Insufficient credits in your Anthropic account")
            elif "authentication_error" in error_msg:
                raise AuthenticationError("Invalid or expired API key")
            elif "rate_limit" in error_msg:
                raise RateLimitError("API rate limit exceeded")
            else:
                raise
    
    def generate_basic_analysis(self, breakdown: Dict[str, Any]) -> str:
        """Generate basic analysis without Claude API when credits are insufficient."""
        summary = breakdown.get('summary', {})
        categories = breakdown.get('categories', {})
        
        analysis = "## Basic Financial Analysis (Generated Locally)\n\n"
        
        # Summary
        analysis += f"**Total Income:** ${summary.get('total_income', 0):,.2f}\n"
        analysis += f"**Total Spent:** ${summary.get('total_spent', 0):,.2f}\n"
        analysis += f"**Net Cash Flow:** ${summary.get('net_flow', 0):,.2f}\n\n"
        
        # Top categories
        if categories:
            analysis += "### Top Spending Categories:\n"
            for i, (category, data) in enumerate(list(categories.items())[:3], 1):
                analysis += f"{i}. **{category}**: ${data['total']:,.2f} ({data['percentage']:.1f}% of spending)\n"
            
            analysis += "\n### Observations:\n"
            if summary.get('net_flow', 0) > 0:
                analysis += "✅ Positive cash flow - you're saving money!\n"
            else:
                analysis += "⚠️ Negative cash flow - spending exceeds income\n"
            
            top_category = list(categories.keys())[0] if categories else "Unknown"
            analysis += f"💰 Largest expense category: {top_category}\n"
            analysis += f"📊 Tracked {summary.get('transaction_count', 0)} transactions\n"
        
        analysis += "\n*Note: This is a basic analysis. Add credits to your Anthropic account for AI-powered insights and recommendations.*"
        
        return analysis
    
    def run_analysis(self, use_sample_data: bool = False, save_report: bool = True, fallback_on_error: bool = True) -> Dict[str, Any]:
        """Run the complete financial analysis workflow."""
        try:
            # Determine which file to use
            if use_sample_data or not config.transactions_file.exists():
                file_path = config.sample_transactions_file
                self.logger.info("Using sample transaction data")
            else:
                file_path = config.transactions_file
                self.logger.info("Using user transaction data")
            
            # Load and process transactions
            df, file_info = self.load_transactions(file_path)
            transactions_text = self.format_transactions_for_analysis(df)
            
            # Calculate spending breakdown
            breakdown = DataFormatter.calculate_spending_breakdown(df)
            
            # Try to get Claude analysis
            analysis = None
            try:
                analysis = self.analyze_with_claude(transactions_text)
            except (CreditBalanceError, AuthenticationError, RateLimitError) as api_error:
                if fallback_on_error:
                    self.logger.warning(f"Claude API unavailable ({api_error}), generating basic analysis")
                    analysis = self.generate_basic_analysis(breakdown)
                else:
                    raise api_error
            
            # Generate and save report if requested
            report_path = None
            if save_report:
                report_content = self.report_generator.generate_report(
                    analysis, breakdown, file_info
                )
                report_path = self.report_generator.save_report(
                    report_content, config.reports_dir
                )
            
            return {
                'analysis': analysis,
                'breakdown': breakdown,
                'file_info': file_info,
                'report_path': report_path,
                'used_fallback': analysis and "Basic Financial Analysis" in analysis
            }
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            raise


def main():
    """Main entry point for the finance agent."""
    print("🏦 Daily Financial Summary Agent")
    print("=" * 50)
    
    try:
        # Initialize the agent
        agent = FinanceAgent()
        
        # Run analysis
        print("📊 Analyzing your financial transactions...")
        results = agent.run_analysis(use_sample_data=True, save_report=True, fallback_on_error=True)
        
        # Display results
        print("\n" + "=" * 50)
        if results.get('used_fallback'):
            print("📊 BASIC FINANCIAL ANALYSIS REPORT")
            print("(Add credits for AI-powered insights)")
        else:
            print("🤖 AI FINANCIAL ANALYSIS REPORT")
        print("=" * 50)
        print(results['analysis'])
        print("\n" + "=" * 50)
        
        # Show summary statistics
        summary = results['breakdown']['summary']
        print(f"📈 Summary: {DataFormatter.format_currency(summary['total_income'])} income, "
              f"{DataFormatter.format_currency(summary['total_spent'])} spent, "
              f"{DataFormatter.format_currency(summary['net_flow'])} net flow")
        
        # Show report save location
        if results['report_path']:
            print(f"📄 Report saved: {results['report_path']}")
        
        # Show credit message if using fallback
        if results.get('used_fallback'):
            print("\n💡 To get AI-powered insights:")
            print("   1. Add credits: https://console.anthropic.com/settings/billing")
            print("   2. Run analysis again for personalized recommendations")
        
        print("✅ Analysis complete!")
        
    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}")
        print("💡 Make sure your transaction CSV file exists in the data/ directory")
        sys.exit(1)
        
    except CreditBalanceError as e:
        print(f"\n💳 Credit Balance Error: {e}")
        print("💡 Steps to fix:")
        print("   1. Go to: https://console.anthropic.com/settings/billing")
        print("   2. Add credits to your account ($5 minimum)")
        print("   3. Run the analysis again")
        print(f"   💰 Estimated cost per analysis: ~$0.05")
        sys.exit(1)
        
    except AuthenticationError as e:
        print(f"\n🔑 Authentication Error: {e}")
        print("💡 Steps to fix:")
        print("   1. Check your API key at: https://console.anthropic.com/")
        print("   2. Update your .env file with the correct key")
        print("   3. Make sure the key starts with 'sk-ant-api03-'")
        sys.exit(1)
        
    except RateLimitError as e:
        print(f"\n⏰ Rate Limit Error: {e}")
        print("💡 Please wait a few minutes and try again")
        sys.exit(1)
        
    except DataValidationError as e:
        print(f"\n📊 Data Validation Error: {e}")
        print("💡 Check your CSV file format and required columns")
        sys.exit(1)
        
    except ValueError as e:
        print(f"\n❌ Data Error: {e}")
        print("💡 Check your CSV file format and required columns")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print("💡 Check your configuration and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()