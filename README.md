# Steadfast Bulk Fraud Report Automation

A Python automation script that automatically submits fraud reports to the Steadfast website (steadfast.com.bd) for multiple users at once. This tool reads user data from a CSV file and automatically fills out fraud report forms with standardized descriptions.

## 🚀 Features

- **Bulk Processing**: Automatically process up to 20 users (configurable)
- **Auto-Login**: Handles authentication automatically
- **Smart Field Detection**: Uses multiple strategies to find form fields
- **Error Handling**: Robust error handling with detailed logging
- **Configurable**: Easy to customize for different use cases
- **Visual Feedback**: Watch the automation in action (configurable headless mode)

## 📋 Prerequisites

- Python 3.7 or higher
- Google Chrome browser installed
- Steadfast account with fraud reporting permissions
- CSV file with user data

## 🛠️ Installation

### 1. Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd steadfast-bulk-submit

# Or simply download the files to a folder
```

### 2. Install Required Python Packages
```bash
pip install selenium pandas webdriver-manager openpyxl
```

### 3. Prepare Your Data File
Create a CSV file named `users.csv` with the following structure:

```csv
recipient_name,recipient_phone
Joya,01960277336
Samir,01916674247
Md rashed,01975723004
হুমায়ন,01806128031
হাবিবুর,01723756789
```

**Important**: 
- First column: `recipient_name` (user's name)
- Second column: `recipient_phone` (11-digit phone number with leading 0)
- Include header row
- Save as UTF-8 encoding for Bengali text support

## ⚙️ Configuration

### Basic Settings
Edit the configuration section in `steadfast_bulk_submit.py`:

```python
# ------------------------------ CONFIGURE THESE ------------------------------

EXCEL_PATH = "users.csv"          # Path to your CSV file
MAX_USERS = 20                     # Maximum number of users to process

STEADFAST_CREATE_URL = "https://steadfast.com.bd/user/frauds/create"
STEADFAST_LOGIN_URL  = "https://steadfast.com.bd/login"

# Your credentials (set environment variables for security)
USERNAME = os.getenv("STEADFAST_USERNAME", "your_email@example.com")
PASSWORD = os.getenv("STEADFAST_USERNAME", "your_password")

# Browser settings
HEADLESS = False                   # Set to True for invisible browser

# Timing settings
SLEEP_BETWEEN_SUBMISSIONS = 1     # Seconds between submissions
```

### Environment Variables (Recommended)
For security, set your credentials as environment variables:

**Windows (PowerShell):**
```powershell
$env:STEADFAST_USERNAME="your_email@example.com"
$env:STEADFAST_PASSWORD="your_password"
```

**Windows (Command Prompt):**
```cmd
set STEADFAST_USERNAME=your_email@example.com
set STEADFAST_PASSWORD=your_password
```

**Linux/Mac:**
```bash
export STEADFAST_USERNAME="your_email@example.com"
export STEADFAST_PASSWORD="your_password"
```

## 🚀 Usage

### 1. Basic Usage
```bash
python steadfast_bulk_submit.py
```

### 2. The Script Will:
1. **Read Data**: Load user information from `users.csv`
2. **Open Browser**: Launch Chrome and navigate to Steadfast
3. **Auto-Login**: Handle authentication if needed
4. **Process Users**: For each user:
   - Fill name field
   - Fill phone number field
   - Fill description field with standardized text
   - Submit the form
   - Navigate back to fresh form
5. **Complete**: Process all users and close browser

### 3. Monitor Progress
The script provides detailed logging:
```
Reading Excel…
Loaded 20 users (capped at 20).
Opening site…
[1] Submitting: name='Joya' phone='01960277336'
  Looking for name field...
  ✓ Filled name: Joya
  Looking for phone field...
  ✓ Filled phone: 01960277336
  Looking for description field...
  ✓ Filled description
  ✓ Successfully returned to fraud form
```

## 🔧 Customization

### Change Description Text
Edit the `DESCRIPTION_TEXT` variable:

```python
DESCRIPTION_TEXT = (
    "Your custom fraud description text here. "
    "This will be filled in for every user."
)
```

### Modify Field Locators
If the website changes, update the field locators:

```python
# Name field locators
NAME_LOCATORS = [
    (By.CSS_SELECTOR, 'input[name="customer_name"]'),  # Add new selectors
    (By.CSS_SELECTOR, 'input[name="name"]'),
    # ... existing locators
]
```

### Adjust Timing
```python
PAGE_LOAD_TIMEOUT = 30           # Page load timeout
ELEM_TIMEOUT = 20                # Element find timeout
SLEEP_BETWEEN_SUBMISSIONS = 1    # Delay between submissions
```

## 📁 Project Structure

```
steadfast-bulk-submit/
├── steadfast_bulk_submit.py     # Main automation script
├── users.csv                    # User data file
├── README.md                    # This file
└── requirements.txt             # Python dependencies
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "ChromeDriver not found"
**Solution**: The script automatically downloads ChromeDriver. Ensure you have Chrome browser installed.

#### 2. "Could not find element"
**Solution**: The website structure may have changed. Check the field locators and update them.

#### 3. "Phone numbers missing leading zeros"
**Solution**: Ensure your CSV uses the `dtype={'recipient_phone': str}` setting (already configured).

#### 4. "Wrong page after submission"
**Solution**: The script now always navigates back to the fraud form URL to avoid redirects.

### Debug Mode
The script includes built-in debugging:
- Detailed logging for each step
- Element inspection when fields can't be found
- Page URL verification

### Manual Testing
1. Run with `HEADLESS = False` to watch the automation
2. Check console output for detailed information
3. Verify the CSV format matches the expected structure

## ⚠️ Important Notes

### Rate Limiting
- The script includes delays between submissions to be respectful to the website
- Don't reduce delays too much to avoid being blocked
- Consider running during off-peak hours for large datasets

### Data Accuracy
- Verify all phone numbers are correct before running
- Ensure names are properly formatted
- Test with a small dataset first

### Website Changes
- Steadfast may update their website structure
- If the script stops working, check if field names/IDs have changed
- Update the locators accordingly

## 🔒 Security Considerations

- **Never commit credentials to version control**
- Use environment variables for sensitive information
- Consider using a dedicated test account
- Regularly update your passwords

## 📞 Support

If you encounter issues:

1. **Check the console output** for detailed error messages
2. **Verify your CSV format** matches the expected structure
3. **Ensure all dependencies** are properly installed
4. **Check if the website structure** has changed

## 📝 License

This project is for educational and legitimate business use only. Ensure you have permission to submit fraud reports and comply with Steadfast's terms of service.

## 🚀 Future Enhancements

Potential improvements for future versions:
- Support for Excel (.xlsx) files
- Configurable field mappings
- Success/failure reporting
- Retry mechanisms for failed submissions
- Database integration
- Web interface for easier configuration

---

**Disclaimer**: This tool is designed for legitimate fraud reporting purposes. Use responsibly and in compliance with Steadfast's terms of service and applicable laws.
