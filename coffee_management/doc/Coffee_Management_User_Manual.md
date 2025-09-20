# Coffee Management Module User Manual

## Table of Contents
1. [Module Overview](#1-module-overview)
2. [User Roles](#2-user-roles)  
3. [Key Workflows](#3-key-workflows)
4. [Detailed Processes](#4-detailed-processes)
5. [Reporting](#5-reporting)
6. [Troubleshooting](#6-troubleshooting)
7. [Version History](#7-version-history)

*Note: Screenshots will be added in future updates to illustrate key screens and workflows*

## 1. Module Overview
The Coffee Management module provides end-to-end supply chain management for coffee products, integrating with Odoo's core Inventory, Manufacturing, and Sales applications. Key features include:

- **Coffee Arrival Tracking**: Record incoming coffee deliveries with supplier, vehicle, and product details
- **Quality Evaluation**: Comprehensive quality assessment with automatic grading
- **Weight Management**: Track gross/net weights and calculate moisture loss adjustments
- **Contract Management**: Manage supplier contracts and purchase agreements
- **Traceability**: Full audit trail from arrival through processing to delivery

## 2. User Roles
- **Coffee User**: Can create and update records but cannot delete
- **Coffee Admin**: Full CRUD access to all coffee management functions

## 3. Key Workflows

### 3.1 Coffee Arrival Process
1. Create new arrival record
2. Complete quality evaluation
3. Record weight measurements
4. Approve for processing

### 3.2 Quality Evaluation
1. Assess raw attributes (defects, odor)
2. Perform cup testing (cleanliness, acidity, body, flavor)
3. System calculates total score and assigns grade
4. UG grade coffee is automatically rejected

### 3.3 Weight Management
1. Record number of bags
2. Enter gross and truck weights
3. System calculates net weight
4. Apply moisture loss adjustment if needed

## 4. Detailed Processes

### 4.1 Creating an Arrival Record
1. Navigate to Coffee Management → Arrivals
2. Click Create
3. Enter:
   - Supplier information
   - Vehicle details
   - Coffee product and origin
4. Save record

*Screenshot: Arrival record creation form*

### 4.2 Performing Quality Evaluation
1. From arrival record, click "Evaluate Quality"
2. Enter:
   - Moisture content (%)
   - Screen percentage (%)
   - Defect percentages
   - Cup test scores
3. System will:
   - Calculate total score
   - Assign AMG grade
   - Update arrival status

### 4.3 Recording Weight Measurements
1. From arrival record, click "Record Weight"
2. Enter:
   - Number of bags
   - Gross weight (kg)
   - Truck weight (kg)
   - Empty jute bag weight (kg)
3. System will:
   - Calculate net weight
   - Apply moisture loss adjustment if quality evaluation shows >12% moisture
   - Update arrival status

### 4.4 Managing Contracts
1. Navigate to Coffee Management → Contracts
2. Click Create
3. Enter:
   - Buyer information
   - Contract date and expected delivery date
   - Add contract lines with products and quantities
4. Click Confirm to:
   - Create delivery orders
   - Generate manufacturing orders (if configured)
   - Update contract status to Confirmed
5. Monitor fulfillment percentage as deliveries are completed

## 5. Reporting

The module provides several reports to analyze coffee operations:

### 5.1 Arrival Reports
- Daily/Monthly arrival summaries
- Supplier performance analysis
- Quality grade distribution

*Example Report:*
```
Date       | Supplier     | Bags | Grade | Avg Score
-------------------------------------------
2025-09-01 | Farm A      | 120  | AA    | 87.5
2025-09-01 | Farm B      | 80   | A     | 82.3
```

### 5.2 Contract Reports
- Fulfillment status by contract
- Delivery timelines
- Manufacturing order status

*Screenshot: Contract fulfillment dashboard*

### 5.3 Inventory Reports
- Coffee stock levels by grade
- Aging analysis
- Movement history

*Screenshot: Inventory aging report*

## 6. Troubleshooting
- **High moisture content warning**: Coffee exceeds 12% moisture
- **UG grade rejection**: Quality score below 31
- **Missing product**: Ensure coffee origin and type are specified

## 7. Version History
- **v1.1 (2025-09-15)**: 
  - Added moisture loss adjustment calculation
  - Improved quality evaluation scoring
  - Fixed contract fulfillment reporting

- **v1.0 (2025-08-31)**: Initial release
  - Covers all core workflows
  - Includes detailed process documentation
  - Adds troubleshooting guide

## 8. Glossary of Terms
- **AMG Grade**: Quality grading system (AA, A, B, UG)
- **Moisture Loss Adjustment**: Weight correction for high moisture content
- **Cup Testing**: Sensory evaluation of coffee quality

## 9. Keyboard Shortcuts
- **Ctrl+N**: Create new record
- **Ctrl+S**: Save current form
- **Ctrl+F**: Search within module

## 10. Frequently Asked Questions
**Q: How do I correct a wrongly entered weight?**
A: Use the "Adjust Weight" action before approval

**Q: What happens to rejected (UG grade) coffee?**
A: It's automatically moved to quarantine stock

## 11. Demo Data
### Loading Demo Data
1. Go to Settings → Technical → Demo Data
2. Select "Coffee Management Demo"
3. Click "Load Demo Data"

### Included Demo Scenarios
- Sample arrival records (10 entries)
- Quality evaluation examples (AA, A, B, UG grades)
- Contract management workflow samples
- Complete reporting examples

### Resetting Demo Data
1. Go to Settings → Technical → Demo Data
2. Select "Coffee Management Demo"
3. Click "Reset Demo Data"

### Demo Data Notes
- Demo data is marked with "[DEMO]" prefix
- Does not affect real production data
- Can be used for training purposes

## 12. Advanced Configuration
### System Requirements
- Odoo 17.0 or later
- 4GB RAM minimum for reporting functions

### Integration Points
- Inventory: Automatic stock updates
- Manufacturing: Production order generation
- Sales: Contract fulfillment tracking

## 12. Mobile Access
The module is fully accessible via:
- Odoo Mobile App
- Mobile-optimized web interface

## 13. Training Materials
### New User Training Program
1. **Basic Navigation (2 hours)**
   - Module overview
   - Core screens and menus
   - Basic data entry exercises

2. **Core Workflows (4 hours)**
   - Coffee arrival simulation
   - Quality evaluation practice
   - Contract creation exercises

3. **Reporting (2 hours)**
   - Generating standard reports
   - Custom report creation
   - Data analysis techniques

### Training Evaluation Checklist
- [ ] Can navigate all main screens
- [ ] Can complete arrival process
- [ ] Can generate basic reports

## 14. Implementation Guide
### Pre-Implementation Checklist
1. **System Requirements**
   - Verify Odoo version compatibility
   - Confirm server specifications
   - Schedule backup window

2. **Data Preparation**
   - Clean existing product data
   - Prepare supplier master list
   - Map existing inventory locations

### User Adoption Strategies
- Phased rollout by department
- Super user training program
- Weekly Q&A sessions

## 15. Advanced Features
### Custom Reporting
- Using the Report Designer
- Creating custom pivot tables
- Scheduled report generation

### API Integration
- Available endpoints
- Authentication methods
- Sample API calls

## 16. Best Practices
### Data Entry Standards
- Consistent naming conventions
- Required fields checklist
- Data validation rules

### Quality Control
- Daily verification procedures
- Audit trail review
- Sample testing protocol

## 17. Appendices
### Technical Specifications
- Database tables overview
- Key field definitions
- Performance benchmarks

## 18. Support Information
For assistance contact:
- Email: support@coffeemgmt.com
- Phone: +1 (800) 555-COFFEE
- Online: https://help.coffeemgmt.com
