# Import necessary libraries for data handling, analysis, and visualization
import pandas as pd  # For DataFrame operations and Excel file reading
import numpy as np  # For numerical computations
import matplotlib.pyplot as plt  # For plotting time series and comparisons
import seaborn as sns  # For enhanced bar plot visualizations
from sklearn.linear_model import LinearRegression  # For forecasting ratios
import warnings
import os  # For file operations
import glob  # For file pattern matching
import yfinance as yf  # For fetching ESG data
import requests  # For currency conversion
warnings.filterwarnings('ignore')  # Suppress warnings for cleaner output

# Configure pandas to display floats with 2 decimal places for readability
pd.set_option('display.float_format', '{:.2f}'.format)

# Function to get EUR to USD exchange rates for specific years
def get_exchange_rates(years):
    exchange_rates = {}
    for year in years:
        try:
            # Using exchangerate-api.com (you'll need to replace with your API key)
            response = requests.get(f'https://api.exchangerate-api.com/v4/latest/EUR')
            if response.status_code == 200:
                # Get the EUR to USD rate
                rate = response.json()['rates']['USD']
                exchange_rates[year] = rate
            else:
                # Fallback to approximate rates if API fails
                fallback_rates = {2021: 1.18, 2022: 1.05, 2023: 1.08, 2024: 1.09}
                exchange_rates[year] = fallback_rates.get(year, 1.09)
        except:
            # Fallback to approximate rates if API fails
            fallback_rates = {2021: 1.18, 2022: 1.05, 2023: 1.08, 2024: 1.09}
            exchange_rates[year] = fallback_rates.get(year, 1.09)
    return exchange_rates

# Function to convert EUR to USD
def convert_eur_to_usd(df, exchange_rates):
    """Convert all values in DataFrame from EUR to USD using year-specific exchange rates"""
    converted_df = df.copy()
    for year in df.index.year:
        rate = exchange_rates.get(year)
        if rate:
            converted_df.loc[df.index.year == year] *= rate
    return converted_df

# Section 1: Data Loading
# Purpose: Load financial statement data from Excel files in working directory for Tesla, Ford, and Volkswagen
print("=== Loading Financial Statement Data ===")

# Define companies and years
companies = ['Tesla', 'Ford', 'Volkswagen']  # List of companies to analyze
years = [2021, 2022, 2023, 2024]  # Years covered by the data
dates = [pd.Timestamp(year, 12, 31) for year in years]  # Year-end dates for indexing

# Initialize dictionary to store financial data
# Structure: {company: {'income': DataFrame, 'balance': DataFrame, 'cashflow': DataFrame}}
financial_data = {company: {'income': None, 'balance': None, 'cashflow': None} for company in companies}

def find_financial_files():
    """
    Search for financial statement files in the working directory.
    Returns a dictionary mapping company and statement type to file paths.
    """
    file_map = {company: {'income': None, 'balance': None, 'cashflow': None} for company in companies}
    
    # Get all Excel files in the working directory
    excel_files = glob.glob("*.xlsx") + glob.glob("*.xls")
    
    for file in excel_files:
        file_lower = file.lower()
        # Determine which company the file belongs to
        for company in companies:
            if company.lower() in file_lower:
                # Determine which statement type it is
                if 'income' in file_lower or 'profit' in file_lower:
                    file_map[company]['income'] = file
                elif 'balance' in file_lower:
                    file_map[company]['balance'] = file
                elif 'cash' in file_lower or 'flow' in file_lower:
                    file_map[company]['cashflow'] = file
    
    return file_map

# Function to load and preprocess Excel data
def load_financial_data(company, file_type, filename):
    try:
        if filename is None:
            print(f"No {file_type} statement file found for {company}")
            return None
            
        # Read Excel file, setting 'Item' as the index
        df = pd.read_excel(filename, index_col='Item')
        # Drop TTM column if present
        if 'TTM' in df.columns:
            df = df.drop(columns=['TTM'])
        # Transpose to have years as rows and items as columns
        df = df.T
        # Convert index to datetime, ensuring year-end dates
        df.index = pd.to_datetime(df.index).map(lambda x: x.replace(month=12, day=31))
        # Filter for 2021–2024
        df = df.loc[df.index.isin(dates)]
        # Convert to numeric, coercing errors to NaN
        df = df.apply(pd.to_numeric, errors='coerce')
        return df
    except Exception as e:
        print(f"Error loading {file_type} for {company} from {filename}: {e}")
        return None

# Find financial files in working directory
print("Searching for financial statement files in working directory...")
file_map = find_financial_files()

# Load data for each company
for company in companies:
    print(f"\nLoading data for {company}:")
    for file_type in ['income', 'balance', 'cashflow']:
        filename = file_map[company][file_type]
        if filename:
            print(f"Found {file_type} statement: {filename}")
            financial_data[company][file_type] = load_financial_data(company, file_type, filename)
        else:
            print(f"Missing {file_type} statement file")

# Adjust Current Assets and Current Liabilities where missing
# Tesla and Ford: Approximate using Working Capital
for company in ['Tesla', 'Ford']:
    balance = financial_data[company]['balance']
    if 'Current Assets' not in balance.columns or 'Current Liabilities' not in balance.columns:
        # Assume Current Ratio ~1.5 (industry average) to estimate
        working_capital = balance.get('Working Capital', pd.Series(0, index=balance.index))
        # Estimate: Current Assets = Working Capital + Current Liabilities
        # Assume Current Liabilities = Working Capital / (Current Ratio - 1)
        assumed_ratio = 1.5
        current_liabilities = working_capital / (assumed_ratio - 1)
        current_assets = working_capital + current_liabilities
        balance['Current Assets'] = current_assets
        balance['Current Liabilities'] = current_liabilities
    financial_data[company]['balance'] = balance

# After loading data for each company, convert Volkswagen's data from EUR to USD
print("\nConverting Volkswagen's financial data from EUR to USD...")
exchange_rates = get_exchange_rates(years)
for statement_type in ['income', 'balance', 'cashflow']:
    if financial_data['Volkswagen'][statement_type] is not None:
        financial_data['Volkswagen'][statement_type] = convert_eur_to_usd(
            financial_data['Volkswagen'][statement_type],
            exchange_rates
        )

# Section 2: Financial Statement Analysis
# Purpose: Compute profitability, liquidity, and valuation ratios
print("\n=== Computing Financial Ratios ===")

# Initialize dictionary to store ratios
# Structure: {company: {'profitability': {ratio: Series}, 'liquidity': {ratio: Series}, 'valuation': {ratio: Series}}}
ratios = {company: {'profitability': {}, 'liquidity': {}, 'valuation': {}} for company in companies}

# Function to compute financial ratios for a company
def compute_ratios(company, income, balance):
    try:
        # Extract required financial items, with fallbacks for missing data
        revenue = income.get('Total Revenue', pd.Series(0, index=dates))  # Total revenue
        net_income = income.get('Net Income Common Stockholders', pd.Series(0, index=dates))  # Net income
        cogs = income.get('Cost of Revenue', pd.Series(0, index=dates))  # Cost of goods sold
        total_assets = balance.get('Total Assets', pd.Series(0, index=dates))  # Total assets
        total_liabilities = balance.get('Total Liabilities Net Minority Interest', pd.Series(0, index=dates))  # Total liabilities
        current_assets = balance.get('Current Assets', pd.Series(0, index=dates))  # Current assets
        current_liabilities = balance.get('Current Liabilities', pd.Series(0, index=dates))  # Current liabilities
        equity = balance.get('Common Stock Equity', pd.Series(0, index=dates))  # Shareholders' equity

        # Compute profitability ratios
        gross_margin = (revenue - cogs) / revenue * 100  # Gross Margin (%): (Revenue - COGS) / Revenue * 100
        net_margin = net_income / revenue * 100         # Net Margin (%): Net Income / Revenue * 100
        roa = net_income / total_assets * 100           # Return on Assets (%): Net Income / Total Assets * 100

        # Compute liquidity ratio
        current_ratio = current_assets / current_liabilities  # Current Ratio: Current Assets / Current Liabilities

        # Compute valuation ratio
        debt_to_equity = total_liabilities / equity     # Debt-to-Equity: Total Liabilities / Equity

        # Store ratios in dictionary
        ratios[company]['profitability'] = {
            'Gross Margin (%)': gross_margin,
            'Net Margin (%)': net_margin,
            'ROA (%)': roa
        }
        ratios[company]['liquidity'] = {
            'Current Ratio': current_ratio
        }
        ratios[company]['valuation'] = {
            'Debt-to-Equity': debt_to_equity
        }

        print(f"Ratios computed for {company}")
    except Exception as e:
        print(f"Error computing ratios for {company}: {e}")

# Compute ratios for each company
for company in companies:
    income = financial_data[company]['income']
    balance = financial_data[company]['balance']
    if income is not None and balance is not None:
        compute_ratios(company, income, balance)
    else:
        print(f"Skipping ratio computation for {company} due to missing data")

# Section 3: Visualization of Ratios
# Purpose: Plot time series trends of financial ratios
print("\n=== Plotting Financial Ratios ===")

# Function to plot a ratio's time series for all companies
def plot_ratio(ratio_name, ratio_type):
    plt.figure(figsize=(10, 6))  # Create a figure with specified size
    for company in companies:
        ratio_data = ratios[company][ratio_type].get(ratio_name, pd.Series(np.nan, index=dates))
        if not ratio_data.isna().all():
            plt.plot(years, ratio_data.values, marker='o', label=company)  # Plot with markers
    plt.title(f'{ratio_name} Trend (2021-2024)')  # Set title
    plt.xlabel('Year')  # Set x-axis label
    plt.ylabel(ratio_name)  # Set y-axis label
    plt.legend()  # Add legend
    plt.grid(True)  # Add grid
    plt.tight_layout()  # Adjust layout
    plt.show()  # Display plot

# Plot key ratios
plot_ratio('Gross Margin (%)', 'profitability')
plot_ratio('Net Margin (%)', 'profitability')
plot_ratio('ROA (%)', 'profitability')  # Add ROA time series plot
plot_ratio('Current Ratio', 'liquidity')
plot_ratio('Debt-to-Equity', 'valuation')

# Section 4: Comparative Bar Plots
# Purpose: Compare ratios across companies for 2024
print("\n=== Comparing Ratios Across Companies ===")

# Function to plot a bar comparison for a ratio in 2024
def plot_bar_comparison(ratio_name, ratio_type, year=2024):
    values = []  # Store ratio values for 2024
    valid_companies = []
    for company in companies:
        ratio_data = ratios[company][ratio_type].get(ratio_name, pd.Series(np.nan, index=dates))
        idx = dates[years.index(year)]
        value = ratio_data.loc[idx] if idx in ratio_data.index else np.nan
        if not np.isnan(value):
            values.append(value)
            valid_companies.append(company)
    if values:
        plt.figure(figsize=(8, 5))  # Create figure
        sns.barplot(x=valid_companies, y=values)  # Create bar plot
        plt.title(f'{ratio_name} Comparison in {year}')  # Set title
        plt.ylabel(ratio_name)  # Set y-axis label
        plt.tight_layout()  # Adjust layout
        plt.show()  # Display plot

# Plot comparisons
plot_bar_comparison('Net Margin (%)', 'profitability')
plot_bar_comparison('ROA (%)', 'profitability')  # Add ROA bar comparison
plot_bar_comparison('Current Ratio', 'liquidity')

# Section 5: Analysis and Conclusions
# Purpose: Analyze trends and draw conclusions
print("\n=== Financial Analysis Conclusions ===")

# Analyze trends for each ratio
for ratio_type in ['profitability', 'liquidity', 'valuation']:
    for ratio_name in ratios['Tesla'][ratio_type]:
        print(f"\nAnalyzing {ratio_name}:")
        for company in companies:
            ratio_data = ratios[company][ratio_type].get(ratio_name, pd.Series(np.nan, index=dates))
            if not ratio_data.isna().all():
                trend = ratio_data.diff().mean()  # Average yearly change
                latest = ratio_data.iloc[-1]  # Latest value (2024)
                print(f"{company}: Latest = {latest:.2f}, Avg Change/Year = {trend:.2f}")
                if trend > 0:
                    print(f"  {company} is improving in {ratio_name}")
                elif trend < 0:
                    print(f"  {company} is declining in {ratio_name}")
                else:
                    print(f"  {company} is stable in {ratio_name}")

# Section 6: Forecasting
# Purpose: Forecast ratios for 2025 and 2026 using Linear Regression
print("\n=== Forecasting Financial Metrics ===")

# Function to forecast a series
def forecast_series(series, years, forecast_years=[2025, 2026]):
    if series.dropna().empty or len(series.dropna()) < 2:  # Check for valid data
        return pd.Series([np.nan]*len(forecast_years), index=forecast_years)
    X = np.array(years).reshape(-1, 1)  # Years as features
    y = series.values  # Ratio values
    model = LinearRegression()  # Initialize model
    model.fit(X, y)  # Fit model
    future_X = np.array(forecast_years).reshape(-1, 1)  # Future years
    forecast = model.predict(future_X)  # Predict
    return pd.Series(forecast, index=forecast_years)  # Return as Series

# Forecast ratios
forecasted_ratios = {company: {} for company in companies}
for company in companies:
    forecasted_ratios[company] = {
        'Net Margin (%)': None,
        'Current Ratio': None
    }
    for ratio_name in ['Net Margin (%)', 'Current Ratio']:
        ratio_type = 'profitability' if 'Margin' in ratio_name else 'liquidity'
        series = ratios[company][ratio_type].get(ratio_name, pd.Series(np.nan, index=dates))
        if not series.isna().all():
            forecast = forecast_series(series, years)
            forecasted_ratios[company][ratio_name] = forecast

# Plot actual and forecasted ratios
def plot_forecasted_ratio(ratio_name, ratio_type):
    plt.figure(figsize=(10, 6))
    forecast_years = [2025, 2026]
    all_years = years + forecast_years
    for company in companies:
        actual = ratios[company][ratio_type].get(ratio_name, pd.Series(np.nan, index=dates))
        forecast = forecasted_ratios[company][ratio_name]
        if not actual.isna().all() and forecast is not None:
            plt.plot(years, actual.values, marker='o', label=f'{company} Actual')
            plt.plot(forecast_years, forecast.values, marker='x', linestyle='--', label=f'{company} Forecast')
    plt.title(f'{ratio_name} with Forecast (2021-2026)')
    plt.xlabel('Year')
    plt.ylabel(ratio_name)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Plot forecasts
plot_forecasted_ratio('Net Margin (%)', 'profitability')
plot_forecasted_ratio('Current Ratio', 'liquidity')

# Section 7: ESG Risk Analysis
# Purpose: Simulate and analyze ESG ratings (since not provided)
print("\n=== ESG Risk Analysis ===")

# Function to fetch ESG data from Yahoo Finance
def fetch_esg_data(companies):
    """
    Fetch ESG data from Yahoo Finance for given companies
    Returns a dictionary with ESG scores
    """
    # Map company names to their Yahoo Finance tickers
    ticker_map = {
        'Tesla': 'TSLA',
        'Ford': 'F',
        'Volkswagen': 'VOW3.DE'
    }
    
    esg_data = {}
    for company in companies:
        try:
            ticker = yf.Ticker(ticker_map[company])
            esg_scores = ticker.sustainability
            
            if esg_scores is not None:
                esg_data[company] = pd.Series({
                    'Environment': float(esg_scores.loc['environmentScore']),
                    'Social': float(esg_scores.loc['socialScore']),
                    'Governance': float(esg_scores.loc['governanceScore']),
                    'Total ESG': float(esg_scores.loc['totalEsg'])
                })
            else:
                # Fallback values if data not available
                esg_data[company] = pd.Series({
                    'Environment': np.nan,
                    'Social': np.nan,
                    'Governance': np.nan,
                    'Total ESG': np.nan
                })
        except Exception as e:
            print(f"Error fetching ESG data for {company}: {e}")
            esg_data[company] = pd.Series({
                'Environment': np.nan,
                'Social': np.nan,
                'Governance': np.nan,
                'Total ESG': np.nan
            })
    
    return esg_data

# Replace the simulated ESG section with real data
print("\n=== ESG Risk Analysis ===")
esg_data = fetch_esg_data(companies)
esg_df = pd.DataFrame(esg_data)

# Plot ESG comparisons
plt.figure(figsize=(10, 6))
esg_df.T.plot(kind='bar')
plt.title('ESG Risk Ratings Comparison')
plt.ylabel('Score')
plt.tight_layout()
plt.show()

# Section 8: Correlation Analysis
# Purpose: Examine relationship between ESG scores and financial metrics
print("\n=== ESG and Financial Correlation ===")

# Correlate Total ESG with Net Margin (2024)
correlations = {}
for company in companies:
    net_margin_series = ratios[company]['profitability'].get('Net Margin (%)', pd.Series(np.nan, index=dates))
    net_margin = net_margin_series.iloc[-1] if not net_margin_series.isna().all() else np.nan
    esg_total = esg_data[company]['Total ESG']
    correlations[company] = {'Net Margin': net_margin, 'ESG Score': esg_total}

corr_df = pd.DataFrame(correlations).T
print("Correlation between Net Margin and ESG Score:")
print(corr_df.corr())

# Section 9: Final Results Summary
# Purpose: Display key findings
print("\n=== Final Results Summary ===")
for company in companies:
    print(f"\n{company}:")
    for ratio_type in ratios[company]:
        for ratio_name, values in ratios[company][ratio_type].items():
            latest = values.iloc[-1] if not values.isna().all() else np.nan
            print(f"{ratio_name}: {latest:.2f} (2024)")
    print("ESG Scores:")
    print(esg_data[company])

print("\nAnalysis complete.")