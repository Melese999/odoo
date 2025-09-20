# Coffee Management System - Technical Manual

## API Documentation

### Available Endpoints
1. **Arrivals API**
   - `GET /api/coffee/arrivals` - List arrivals
   - `GET /api/coffee/arrivals/{id}` - Get arrival details
   - `POST /api/coffee/arrivals` - Create new arrival
   - `PUT /api/coffee/arrivals/{id}/evaluate` - Submit quality evaluation

2. **Inventory API**
   - `GET /api/coffee/inventory` - List stock levels
   - `GET /api/coffee/inventory/{product_id}` - Get product stock

3. **Contracts API** 
   - `GET /api/coffee/contracts` - List contracts
   - `POST /api/coffee/contracts` - Create contract
   - `PUT /api/coffee/contracts/{id}/confirm` - Confirm contract

### Authentication
All API endpoints require authentication via:
- API Key (header: `Authorization: Bearer {api_key}`)
- OAuth2 token

### Example Usage
**Python Example:**
```python
import requests

# Get arrivals since specific date
url = "https://your-odoo-instance.com/api/coffee/arrivals"
headers = {"Authorization": "Bearer your_api_key"}
params = {"date_from": "2025-01-01", "limit": 100}

response = requests.get(url, headers=headers, params=params)
print(response.json())
```

**cURL Example:**
```bash
curl -X GET \
  -H "Authorization: Bearer $API_KEY" \
  "https://your-odoo-instance.com/api/coffee/inventory/123"
```

### Rate Limits
- 100 requests/minute per API key
- 1000 requests/minute per OAuth2 client

### Error Codes
| Code | Meaning | Resolution |
|------|---------|------------|
| 401 | Unauthorized | Check API key/token |
| 403 | Forbidden | Verify permissions |
| 429 | Too Many Requests | Reduce request rate |
| 500 | Server Error | Contact support |

## Data Model Reference
Key models and their relationships:
- `coffee.arrival` (main arrival record)
- `coffee.quality.evaluation` (linked to arrival)
- `coffee.contract` (sales contracts)
- `coffee.stock.receiving` (inventory movements)

## Field Reference Guide
Complete list of all fields with descriptions available in the technical documentation.

## System Requirements
- Odoo Enterprise Edition v16.0 or later
- Minimum 4GB RAM (8GB recommended for production)
- PostgreSQL 12 or later

## Performance Optimization
### Database Optimization:
- Schedule regular database maintenance (vacuum/analyze)
- Archive completed arrivals older than 6 months
- Use database partitioning for large datasets

### System Configuration:
- Allocate sufficient RAM to Odoo workers
- Enable database connection pooling
- Configure appropriate worker timeouts

## Security Best Practices
### Access Control:
- Enforce strong password policies
- Implement two-factor authentication
- Regularly review user access rights

### Data Protection:
- Encrypt sensitive data at rest and in transit
- Mask personally identifiable information in reports
- Implement data retention policies

## Upgrade Notes
**Version 2.0 to 3.0:**
- New database schema requires migration script
- Updated quality evaluation scoring algorithm
- Added multi-warehouse support

## System Integration
### Implementation Steps:
1. Identify integration points and data flows
2. Configure API access credentials
3. Set up data mapping between systems

### Common Integration Patterns:
- Real-time API calls for critical operations
- Scheduled batch processing for non-critical data
- Event-based triggers for workflow automation

## Customization Guide
### UI Customizations:
- Add custom fields to forms
- Modify views and layouts
- Create custom reports and dashboards

### Workflow Extensions:
- Add new states to existing workflows
- Create custom validation rules
- Implement additional approval steps

## 7. Advanced Features

### API Integration
The system provides a comprehensive REST API for integration with other systems.

#### Available Endpoints
1. **Arrivals API**
   - `GET /api/coffee/arrivals` - List arrivals
   - `GET /api/coffee/arrivals/{id}` - Get arrival details
   - `POST /api/coffee/arrivals` - Create new arrival
   - `PUT /api/coffee/arrivals/{id}/evaluate` - Submit quality evaluation

2. **Inventory API**
   - `GET /api/coffee/inventory` - List stock levels
   - `GET /api/coffee/inventory/{product_id}` - Get product stock

3. **Contracts API** 
   - `GET /api/coffee/contracts` - List contracts
   - `POST /api/coffee/contracts` - Create contract
   - `PUT /api/coffee/contracts/{id}/confirm` - Confirm contract

#### Authentication
All API endpoints require authentication via:
- API Key (header: `Authorization: Bearer {api_key}`)
- OAuth2 token

#### Example Usage

**Python Example:**
```python
import requests

# Get arrivals since specific date
url = "https://your-odoo-instance.com/api/coffee/arrivals"
headers = {"Authorization": "Bearer your_api_key"}
params = {"date_from": "2025-01-01", "limit": 100}

response = requests.get(url, headers=headers, params=params)
print(response.json())

# Submit quality evaluation
eval_url = f"{url}/{arrival_id}/evaluate"
eval_data = {
    "moisture": 11.5,
    "defects": 2.1,
    "acidity": 8,
    "body": 7,
    "flavor": 9
}
response = requests.put(eval_url, headers=headers, json=eval_data)
```

**cURL Example:**
```bash
# Get inventory for product
curl -X GET \
  -H "Authorization: Bearer $API_KEY" \
  "https://your-odoo-instance.com/api/coffee/inventory/123"
```

#### Rate Limits
- 100 requests/minute per API key
- 1000 requests/minute per OAuth2 client

#### Error Codes
| Code | Meaning | Resolution |
|------|---------|------------|
| 401 | Unauthorized | Check API key/token |
| 403 | Forbidden | Verify permissions |
| 429 | Too Many Requests | Reduce request rate |
| 500 | Server Error | Contact support |

### Data Export/Import
You can export data to Excel or CSV format using:
1. Standard Odoo export functionality
2. Scheduled automated exports
3. Custom report generation

#### Sample Datasets
For training and testing purposes, we provide sample datasets:

**Sample Arrival Data (CSV):**
```csv
arrival_date,supplier,ecx_product,woreda,expected_grade
2025-01-15,Coffee Supplier A,Guji-Washed-G1,Arsi,G1
2025-01-16,Coffee Supplier B,Sidamo-Unwashed-G2,Bale,G2
```

**Sample Quality Evaluation Data (JSON):**
```json
{
  "arrival_id": 123,
  "moisture": 11.2,
  "defects": 2.4,
  "acidity": 8,
  "body": 7,
  "flavor": 8,
  "evaluator": "Quality Staff 1"
}
```

**Sample Contract Data (Excel Template):**
Available for download from `Coffee Management > Documentation > Templates`

#### Mobile Access
The Coffee Management System is fully accessible on mobile devices:

**Mobile App Features:**
- View and update arrivals
- Submit quality evaluations
- Record weights
- Check stock levels
- View contracts

**Responsive Web Interface:**
All features are available through the mobile browser with:
- Optimized touch controls
- Offline data caching
- Barcode scanning support

**Installation:**
1. Download the Odoo Mobile app from App Store or Google Play
2. Configure your server URL
3. Log in with your credentials
4. Enable Coffee Management module in app settings

#### Performance Optimization
Follow these recommendations to ensure optimal system performance:

**Database Optimization:**
- Schedule regular database maintenance (vacuum/analyze)
- Archive completed arrivals older than 6 months
- Use database partitioning for large datasets

**System Configuration:**
- Allocate sufficient RAM to Odoo workers
- Enable database connection pooling
- Configure appropriate worker timeouts

**Workflow Best Practices:**
- Process arrivals in batches during peak seasons
- Schedule reports to run during off-peak hours
- Use the bulk update feature for mass operations

**Hardware Recommendations:**
- Minimum 8GB RAM for production use
- SSD storage for database server
- Dedicated server for high-volume operations

#### Security Best Practices
Implement these security measures to protect your system:

**Access Control:**
- Enforce strong password policies
- Implement two-factor authentication
- Regularly review user access rights

**Data Protection:**
- Encrypt sensitive data at rest and in transit
- Mask personally identifiable information in reports
- Implement data retention policies

**System Security:**
- Keep Odoo and all dependencies updated
- Configure firewall rules to restrict access
- Monitor for suspicious activity

**Backup Strategy:**
- Perform daily database backups
- Store backups in a secure offsite location
- Test restore procedures quarterly

---

## 8. Glossary of Terms

| Term | Definition |
|------|-----------|
| AMG Grade | The internal quality grade assigned after evaluation |
| ECX Grade | The official Ethiopian Commodity Exchange grade |
| Woreda | Administrative district in Ethiopia |
| BoM | Bill of Materials - defines product components |
| MTO | Make-to-Order production strategy |

---

## 9. Implementation Best Practices

1. **Data Preparation**
   - Complete all master data setup before processing arrivals
   - Validate all geographical data with local authorities

2. **User Training**
   - Train quality evaluators separately from warehouse staff
   - Conduct role-specific training sessions

3. **Process Optimization**
   - Schedule large data operations during off-peak hours
   - Use barcode scanners for faster data entry

4. **Maintenance**
   - Regularly review and update master data
   - Perform monthly data audits

---

## 10. Technical Appendix

### Data Model Reference
Key models and their relationships:
- `coffee.arrival` (main arrival record)
- `coffee.quality.evaluation` (linked to arrival)
- `coffee.contract` (sales contracts)
- `coffee.stock.receiving` (inventory movements)

### Field Reference Guide
Complete list of all fields with descriptions available in the technical documentation.