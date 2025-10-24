# Daily Financial Summary Agent

A local Python-based financial analysis agent using Claude API that analyzes bank transaction CSV files and generates personalized daily financial summaries.

## Quick Start

### Prerequisites
- Docker Desktop installed
- Claude API key from [console.anthropic.com](https://console.anthropic.com/)

### Setup
1. Clone/download this project
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Add your Claude API key to `.env`:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

### Usage
1. Export your bank transactions as CSV and save as `data/transactions.csv`
2. Run the analysis:
   ```bash
   docker-compose up
   ```
3. View the generated report in the `reports/` directory

## CSV Format Requirements

Your CSV file should contain these columns:
- `Date`: Transaction date (YYYY-MM-DD or MM/DD/YYYY)
- `Description`: Merchant or transaction description  
- `Amount`: Transaction amount (negative for expenses, positive for income)
- `Type`: "Debit" or "Credit"

## Project Structure
```
finance-agent/
├── src/            # Source code
├── data/           # Transaction CSV files (gitignored)
├── reports/        # Generated reports (gitignored)
├── tests/          # Test files
├── Dockerfile      # Container configuration
└── docker-compose.yml
```

## Development

### Building
```bash
docker-compose build
```

### Testing
```bash
docker-compose run finance-agent python -m pytest tests/
```

## Cost Estimate
- ~$0.05 per analysis
- Monthly cost: $1.50 (daily use) or $0.30 (weekly use)

## Next Steps
- Phase 2: Implement basic agent functionality
- Phase 3: Add report generation
- Phase 4: Enhanced analysis features