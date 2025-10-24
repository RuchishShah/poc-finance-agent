# Daily Financial Summary Agent - Project Guide

## Project Overview
Build a local Python-based financial analysis agent using Claude Agent SDK that analyzes bank transaction CSV files and generates personalized daily financial summaries.

## Project Goals
- Learn Claude Agent SDK fundamentals
- Create a practical daily-use financial tool
- Keep costs minimal ($5-15/month)
- Run completely locally with Docker
- Generate actionable financial insights

## Technical Requirements

### Core Technologies
- **Language**: Python 3.10+
- **Main Framework**: Claude Agent SDK (Python)
- **Data Processing**: pandas
- **Containerization**: Docker
- **Dependencies**: asyncio, datetime

### System Requirements
- Docker Desktop installed
- Claude API key from console.anthropic.com
- Ability to export bank transactions as CSV

## Project Structure

```
finance-agent/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── src/
│   ├── __init__.py
│   ├── analyze_finances.py    # Main agent script
│   ├── config.py               # Configuration management
│   └── utils.py                # Helper functions
├── data/
│   ├── transactions.csv        # User's bank data (gitignored)
│   └── sample_transactions.csv # Example data
├── reports/
│   └── .gitkeep                # Generated reports go here
└── tests/
    ├── __init__.py
    └── test_analyze.py
```

## Implementation Phases

### Phase 1: Docker Setup & Project Initialization
**Objective**: Create a containerized Python environment

**Tasks**:
1. Create project directory structure
2. Write Dockerfile with Python 3.10+ base image
3. Create docker-compose.yml for easy management
4. Write requirements.txt with dependencies:
   - claude-agent-sdk
   - pandas
   - python-dotenv
5. Create .env.example for API key template
6. Create .gitignore to exclude sensitive files
7. Test Docker build and container startup

**Acceptance Criteria**:
- Docker container builds successfully
- Can run `docker-compose up` without errors
- Python environment is accessible inside container

### Phase 2: Basic Agent Implementation
**Objective**: Create a working Claude agent that can read and analyze CSV files

**Tasks**:
1. Create `src/config.py`:
   - Load environment variables
   - Validate API key presence
   - Set up logging configuration

2. Create `src/analyze_finances.py`:
   - Import Claude Agent SDK
   - Configure ClaudeAgentOptions with financial advisor system prompt
   - Implement CSV reading with pandas
   - Create basic query to Claude for transaction analysis
   - Handle responses and print to console

3. Create system prompt that instructs Claude to:
   - Categorize transactions (groceries, dining, transport, etc.)
   - Calculate spending by category
   - Identify top 3 spending categories
   - Spot unusual/large transactions
   - Provide 3 actionable money-saving insights
   - Rate financial health (1-10 scale)

**System Prompt Template**:
```
You are a personal finance advisor AI assistant specializing in transaction analysis.

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
```

**Acceptance Criteria**:
- Script successfully reads CSV file
- Claude agent analyzes transactions and returns structured insights
- Output is formatted and readable
- Error handling for missing files or API issues

### Phase 3: Data Processing & Report Generation
**Objective**: Add data validation and save reports to files

**Tasks**:
1. Create `src/utils.py`:
   - CSV validation function (check required columns)
   - Date parsing and formatting utilities
   - Amount formatting (currency)
   - Report template generator

2. Enhance `analyze_finances.py`:
   - Add data validation before analysis
   - Implement error handling for malformed CSV
   - Generate markdown reports with timestamp
   - Save reports to `reports/` directory
   - Add summary statistics (total spent, transaction count)

3. Create sample CSV template in `data/sample_transactions.csv`:
```csv
Date,Description,Amount,Type
2025-10-20,Starbucks Coffee,-5.50,Debit
2025-10-20,Salary Deposit,3500.00,Credit
2025-10-21,Uber Ride,-18.75,Debit
2025-10-21,Amazon Purchase,-89.99,Debit
2025-10-22,Whole Foods,-156.43,Debit
2025-10-23,Netflix Subscription,-15.99,Debit
2025-10-23,Restaurant Dinner,-85.50,Debit
2025-10-24,Gas Station,-45.00,Debit
```

**Acceptance Criteria**:
- CSV validation works correctly
- Reports are saved with proper timestamps
- Markdown formatting is clean and readable
- Sample data analysis runs successfully

### Phase 4: Enhanced Features
**Objective**: Add advanced analysis capabilities

**Tasks**:
1. Implement spending trend detection:
   - Compare current week vs previous weeks (if historical data exists)
   - Calculate percentage changes
   - Identify spending spikes

2. Add category insights:
   - Average spending per category
   - Percentage of income (if income transactions present)
   - Category-specific recommendations

3. Implement budget tracking (optional):
   - Allow user to set category budgets in config
   - Show budget vs actual spending
   - Alert when over budget

4. Add recurring transaction detection:
   - Identify subscriptions
   - Calculate monthly recurring costs
   - Suggest subscription optimization

**Acceptance Criteria**:
- Trend analysis provides meaningful insights
- Category budgets work correctly (if implemented)
- Subscription detection identifies recurring charges

### Phase 5: Docker Optimization & Documentation
**Objective**: Optimize for easy daily use

**Tasks**:
1. Optimize Docker setup:
   - Add volume mounting for data and reports
   - Create convenient shell script for daily runs
   - Minimize image size
   - Add health checks

2. Write comprehensive README.md:
   - Installation instructions
   - How to get API key
   - How to export bank CSV
   - How to run daily analysis
   - Example output
   - Troubleshooting section
   - Cost estimation

3. Create shell scripts:
   - `run_analysis.sh` (Mac/Linux)
   - `run_analysis.bat` (Windows)
   - Scripts should handle Docker compose and cleanup

4. Add example outputs to documentation

**Acceptance Criteria**:
- One-command execution works smoothly
- Documentation is clear and beginner-friendly
- Scripts handle errors gracefully

## CSV Format Requirements

### Required Columns
- `Date`: Transaction date (YYYY-MM-DD or MM/DD/YYYY)
- `Description`: Merchant or transaction description
- `Amount`: Transaction amount (negative for expenses, positive for income)
- `Type`: "Debit" or "Credit"

### Optional Columns
- `Category`: Pre-categorized (if available)
- `Account`: Account name (for multi-account tracking)
- `Balance`: Account balance after transaction

### Data Preparation Notes
- Most banks allow CSV export from online banking
- Some banks may use different column names (handle this)
- Amount may be in different formats ($-50.00 vs -50.00)
- Date formats vary by bank and region

## Docker Configuration Details

### Dockerfile Structure
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required by Claude SDK)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/

# Create necessary directories
RUN mkdir -p /app/data /app/reports

CMD ["python", "src/analyze_finances.py"]
```

### docker-compose.yml Structure
```yaml
version: '3.8'

services:
  finance-agent:
    build: .
    container_name: finance-agent
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./data:/app/data
      - ./reports:/app/reports
      - ./src:/app/src
    command: python src/analyze_finances.py
```

## Usage Instructions

### Daily Workflow
1. Download bank statement CSV (weekly or monthly)
2. Save as `data/transactions.csv`
3. Run: `docker-compose up`
4. Review generated report in `reports/` directory
5. Take action on recommendations!

### First-Time Setup
1. Clone/create project directory
2. Copy `.env.example` to `.env`
3. Add Claude API key to `.env`
4. Build Docker image: `docker-compose build`
5. Add sample data: Copy bank CSV to `data/transactions.csv`
6. Run first analysis: `docker-compose up`

## Testing Strategy

### Manual Testing Checklist
- [ ] Docker builds successfully
- [ ] Container runs without errors
- [ ] Sample CSV analysis completes
- [ ] Report is generated with proper format
- [ ] Large CSV files (1000+ transactions) process correctly
- [ ] Invalid CSV is handled gracefully
- [ ] Missing API key shows clear error message

### Test Cases to Implement (Optional)
1. Test valid CSV parsing
2. Test invalid CSV handling
3. Test report generation
4. Test spending categorization accuracy
5. Test large file performance

## Error Handling

### Common Errors to Handle
1. **Missing API Key**: Show setup instructions
2. **Invalid CSV Format**: Explain required columns
3. **API Rate Limits**: Implement exponential backoff
4. **File Not Found**: Check data directory
5. **Docker Issues**: Verify Docker is running
6. **Insufficient Credits**: Show billing link

### Error Messages Should Include
- Clear explanation of what went wrong
- Specific steps to fix the issue
- Relevant documentation links

## Cost Optimization

### Estimated Costs
- Claude API: ~$0.05 per analysis
- Daily usage (30 days): ~$1.50/month
- With weekly use: ~$0.30/month

### Tips to Minimize Costs
1. Batch weekly instead of daily
2. Use Claude Haiku for simple categorization (cheaper)
3. Cache repeated queries
4. Limit transaction history length
5. Use local categorization rules when possible

## Security Considerations

### Sensitive Data Protection
1. Never commit `.env` file
2. Add `data/*.csv` to `.gitignore`
3. Don't share reports with account numbers
4. Keep Docker container logs clean of sensitive data
5. Rotate API keys periodically

### Best Practices
- Use environment variables for all secrets
- Don't hardcode API keys
- Review what data is sent to Claude API
- Consider encrypting local CSV files
- Use read-only volume mounts where possible

## Future Enhancement Ideas

### Short-term (Easy Additions)
1. Email reports automatically
2. Add spending visualizations (charts)
3. Multi-month trend analysis
4. Budget goal tracking
5. Export to Google Sheets

### Medium-term (More Complex)
1. Web UI dashboard
2. Multiple bank account support
3. Investment portfolio tracking
4. Bill payment reminders
5. Tax optimization insights

### Long-term (Advanced)
1. Automatic bank API integration
2. Real-time transaction monitoring
3. Predictive spending forecasts
4. Mobile app
5. Family/household shared budgets

## Troubleshooting Guide

### Issue: Docker build fails
- Check Docker Desktop is running
- Verify Docker version is recent
- Try `docker-compose build --no-cache`

### Issue: API key not recognized
- Verify `.env` file exists and contains key
- Check for extra spaces in API key
- Ensure API key is valid at console.anthropic.com

### Issue: CSV not found
- Verify file is in `data/` directory
- Check filename is exactly `transactions.csv`
- Ensure volume mounting is correct in docker-compose

### Issue: Analysis is slow
- Large CSV files take longer
- Check internet connection
- Consider reducing transaction count

### Issue: Categorization is inaccurate
- Improve system prompt with examples
- Add category rules in code
- Provide feedback to improve over time

## Success Metrics

### You'll know it's working when:
- ✅ Analysis completes in under 60 seconds
- ✅ Categories are 80%+ accurate
- ✅ Insights are actionable and specific
- ✅ Reports are easy to read
- ✅ You actually use it regularly!
- ✅ You identify real saving opportunities
- ✅ Your financial awareness improves

## Learning Objectives

By completing this project, you will learn:
1. How to use Claude Agent SDK
2. Docker containerization basics
3. Python async programming
4. CSV data processing with pandas
5. AI prompt engineering
6. System design for local tools
7. Financial data analysis fundamentals

## Important Notes

### About Claude Agent SDK
- Requires ANTHROPIC_API_KEY environment variable
- Supports streaming responses
- Allows file operations (Read, Write)
- Can execute bash commands (use cautiously)
- Has built-in context management

### About Financial Data
- Never share raw bank data with others
- Review Claude's data usage policy
- Consider anonymizing data for testing
- Keep backups of important reports
- Verify calculations manually initially

## Getting Help

### Resources
- Claude Agent SDK Docs: https://docs.claude.com/en/api/agent-sdk/overview
- Python Docs: https://docs.python.org/3/
- Pandas Docs: https://pandas.pydata.org/docs/
- Docker Docs: https://docs.docker.com/

### When Stuck
1. Check error messages carefully
2. Review this CLAUDE.md file
3. Test with sample data first
4. Verify environment setup
5. Check Claude Code suggestions
6. Search for specific error messages

## Project Timeline

### Week 1: Foundation
- Days 1-2: Docker setup and project structure
- Days 3-4: Basic agent implementation
- Days 5-7: CSV processing and initial testing

### Week 2: Enhancement & Polish
- Days 8-10: Report generation and enhanced features
- Days 11-12: Testing with real data
- Days 13-14: Documentation and optimization

## Final Deliverables

By the end of this project, you should have:
1. ✅ Working Docker container
2. ✅ Python script that analyzes transactions
3. ✅ Sample CSV template
4. ✅ Generated financial reports
5. ✅ Complete documentation
6. ✅ Shell scripts for easy execution
7. ✅ Understanding of Claude Agent SDK

## Remember
- Start simple, add complexity gradually
- Test with sample data first
- Focus on getting it working before optimizing
- Document as you go
- Have fun learning! 🚀

## Next Steps
1. Create the project directory structure
2. Set up Docker configuration
3. Implement basic agent
4. Test with sample data
5. Refine and enhance
6. Start using daily!

---

*This CLAUDE.md file should guide Claude Code to help you build the complete project step-by-step. Start with Phase 1 and work through each phase sequentially.*
