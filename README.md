# Customer CRM

A comprehensive call center and customer follow-up system for ERPNext.

## Features

### 📞 Customer Call Management
- Track all customer interactions (calls, meetings, emails)
- Record call outcomes, duration, and conversation notes
- Auto-populate customer phone numbers
- Smart follow-up date suggestions based on call outcomes

### 📅 Automated Follow-ups
- Automatic follow-up scheduling (7 days default, skips weekends)
- Creates ToDo tasks for assigned agents
- Email notifications to assigned users
- Daily reminder emails sent 1 day before follow-up date

### 🎯 Call Center Dashboard
- Centralized dashboard at `/call-center`
- View pending follow-ups for today
- See recent calls and outcomes
- Quick access to create new calls
- Agent-specific filtering

### 📊 Reporting & Analytics
- Call Summary report with filtering
- Agent performance tracking
- Call outcome statistics
- Duration and follow-up analysis

### 🔔 Smart Notifications
- Email notifications when follow-ups are assigned
- Real-time in-app notifications
- Daily reminder system
- Direct links to call records

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app customer_crm
bench migrate
```

## Usage

### For Sales Users
1. Login to ERPNext - you'll see the Call Center Dashboard
2. View pending follow-ups and today's calls
3. Click "New Call" to log customer interactions
4. System automatically sets follow-up dates and sends notifications

### For Managers
1. Access "Call Summary" report for analytics
2. Filter by agent, date range, or call outcomes
3. Monitor team performance and follow-up completion

## Configuration

### Roles & Permissions
- **Sales User**: Full access to calls and dashboard
- **System Manager**: Full administrative access

### Follow-up Rules
- **Default**: 7 days (skips weekends)
- **Callback Required**: 1 day
- **Interested**: 3 days
- **Weekends**: Auto-moved to next Monday

### Notifications
- Immediate email when follow-up assigned
- Daily reminders sent at system scheduled time
- In-app real-time notifications

## Doctypes

### Customer Call
- Main doctype for logging all customer interactions
- Links to ERPNext Customer records
- Tracks outcomes, notes, and follow-up dates

### Call Dashboard
- Configuration doctype for dashboard settings
- Single doctype with filtering options

## API Endpoints

```python
# Get call statistics
frappe.call('customer_crm.customer_crm.api.call_api.get_call_stats')

# Get agent-specific calls
frappe.call('customer_crm.customer_crm.api.call_api.get_agent_calls', {
    'agent': 'user@example.com',
    'date': '2024-01-01'
})
```

## Scheduled Tasks

- **Daily**: Send follow-up reminder emails (runs every day)

## Contributing

This app uses `pre-commit` for code formatting and linting:

```bash
cd apps/customer_crm
pre-commit install
```

Tools used:
- ruff (Python linting)
- eslint (JavaScript linting)
- prettier (Code formatting)
- pyupgrade (Python syntax updates)

## CI/CD

- **CI**: Runs tests on every push to `develop`
- **Linters**: Runs security and code quality checks on PRs

## License

MIT
