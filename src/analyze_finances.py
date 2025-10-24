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

from config import config


class FinanceAgent:
    """Main finance analysis agent using Claude AI."""
    
    def __init__(self):
        """Initialize the finance agent with Claude client."""
        self.logger = logging.getLogger(__name__)
        self.client = Anthropic(api_key=config.anthropic_api_key)
        self.logger.info("Finance Agent initialized successfully")
    
    def load_transactions(self, file_path: Path) -> pd.DataFrame:
        """Load and validate transaction data from CSV file."""
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Transaction file not found: {file_path}")
            
            # Read CSV with pandas
            df = pd.read_csv(file_path)
            self.logger.info(f"Loaded {len(df)} transactions from {file_path}")
            
            # Validate required columns
            required_columns = ['Date', 'Description', 'Amount', 'Type']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Convert date column
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Ensure Amount is numeric
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            
            # Remove rows with invalid data
            df = df.dropna(subset=['Amount'])
            
            self.logger.info(f"Successfully validated {len(df)} transactions")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading transactions: {e}")
            raise
    
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
                model="claude-3-5-sonnet-20241022",
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
            self.logger.error(f"Error getting Claude analysis: {e}")
            raise
    
    def run_analysis(self, use_sample_data: bool = False) -> str:
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
            df = self.load_transactions(file_path)
            transactions_text = self.format_transactions_for_analysis(df)
            
            # Get Claude analysis
            analysis = self.analyze_with_claude(transactions_text)
            
            return analysis
            
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
        analysis = agent.run_analysis(use_sample_data=True)
        
        # Display results
        print("\n" + "=" * 50)
        print("💰 FINANCIAL ANALYSIS REPORT")
        print("=" * 50)
        print(analysis)
        print("\n" + "=" * 50)
        print("✅ Analysis complete!")
        
    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}")
        print("💡 Make sure your transaction CSV file exists in the data/ directory")
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