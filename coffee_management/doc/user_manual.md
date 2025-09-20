# Coffee Management System - User Manual
---

## Table of Contents
1.  [Introduction](#1-introduction)
    *   [Purpose of the Module](#purpose-of-the-module)
    *   [Key Benefits](#key-benefits)
    *   [System Requirements](#system-requirements)
2.  [Master Data Configuration (First-Time Setup)](#2-master-data-configuration-first-time-setup)
    *   [User Permissions Guide](#user-permissions-guide)
3.  [Core Workflows: An Overview](#3-core-workflows-an-overview)
    *   [Procurement Workflow: From Arrival to Graded Stock](#procurement-workflow)
    *   [Sales Workflow: From Contract to Production](#sales-workflow)
    *   [Workflow Diagrams](#workflow-diagrams)
4.  [Detailed Step-by-Step Guides](#4-detailed-step-by-step-guides)
    *   [4.1 Managing a New Coffee Arrival](#managing-a-new-coffee-arrival)
    *   [4.2 Performing a Quality Evaluation](#performing-a-quality-evaluation)
    *   [4.3 Recording the Weight](#recording-the-weight)
    *   [4.4 Receiving the Coffee into Stock](#receiving-the-coffee-into-stock)
    *   [4.5 Creating and Managing a Coffee Contract](#creating-and-managing-a-coffee-contract)
5.  [Reporting and Analytics](#5-reporting-and-analytics)
    *   [5.1 Wizard-Based PDF Reports](#wizard-based-pdf-reports)
    *   [5.2 On-Screen Analytics](#on-screen-analytics)
    *   [5.3 Custom Report Development](#custom-report-development)
6.  [Frequently Asked Questions (FAQ) & Troubleshooting](#6-frequently-asked-questions-faq--troubleshooting)
7.  [Advanced Features](#7-advanced-features)
    *   [API Integration](#api-integration)
    *   [Data Export/Import](#data-exportimport)
8.  [Glossary of Terms](#8-glossary-of-terms)
9.  [Implementation Best Practices](#9-implementation-best-practices)
10. [Technical Appendix](#10-technical-appendix)
    *   [Data Model Reference](#data-model-reference)
    *   [Field Reference Guide](#field-reference-guide)

---

## 1. Introduction

### Quick Start Guide
Follow these steps to get started quickly with the Coffee Management System:

**Day 1 Setup:**
1. Configure master data (zones, districts, coffee types)
2. Set up ECX product templates
3. Create user accounts with appropriate permissions

**First Arrival Process:**
1. Create arrival record
2. Evaluate quality (system creates product automatically)
3. Record weight
4. Receive into stock

**First Contract Process:**
1. Create contract for finished product
2. Confirm contract (system creates delivery/manufacturing orders)
3. Process delivery and production

### Purpose of the Module
The Coffee Management System is a specialized module for Odoo designed to manage the entire coffee supply chain. It provides a robust, traceable, and controlled workflow from the moment raw coffee arrives at your facility to the final delivery of a manufactured product to a customer.

### Key Benefits
*   **Full Traceability:** Every batch of coffee is tracked from arrival, through quality grading, to a specific location in your inventory.
*   **Data Integrity:** The system ensures that inventory is categorized by its **true, evaluated grade**, not just a generic name, thanks to its dynamic product creation feature.
*   **Process Control:** Provides explicit, button-driven control over the creation of deliveries and manufacturing orders, removing ambiguity from the workflow.
*   **Centralized Data:** All information related to an arrival (quality, weight, stock location) or a sale (delivery, manufacturing) is linked and accessible from a single screen.

### System Requirements
* Odoo Enterprise Edition v16.0 or later
* Minimum 4GB RAM (8GB recommended for production)
* PostgreSQL 12 or later
* Modern web browser (Chrome, Firefox, Edge)

### Localization & Internationalization
The Coffee Management System supports multiple languages and regional configurations:

**Supported Languages:**
- English (default)
- Amharic
- Spanish
- French
- Arabic

**Regional Adaptations:**
- Date/time formats
- Number formatting
- Measurement units (metric/imperial)
- Currency support (USD, EUR, ETB, etc.)

To configure:
1. Go to Settings > Translations > Languages
2. Install additional languages as needed
3. Set user-specific language preferences

### Training Resources
Enhance your team's skills with these training materials:

**Official Training:**
- [Coffee Management System Certification Course]()
- [Train-the-Trainer Program]()

**Video Tutorials:**
- [Getting Started Playlist]()
- [Advanced Features Series]()
- [Troubleshooting Guide]()

**Documentation:**
- [Implementation Guide]()
- [API Reference Manual]()
- [Best Practices Handbook]()

**Community Resources:**
- User forums
- Monthly webinars
- Knowledge base articles

### Upgrade Notes
Important considerations when upgrading between versions:

**Version 2.0 to 3.0:**
- New database schema requires migration script
- Updated quality evaluation scoring algorithm
- Added multi-warehouse support

**Version 1.5 to 2.0:**
- Changed contract confirmation workflow
- Added new mandatory fields for arrivals
- Requires data migration for existing contracts

**General Upgrade Best Practices:**
1. Always backup database before upgrading
2. Test upgrades in staging environment first
3. Review changelog for breaking changes
4. Schedule upgrades during low-usage periods
5. Verify all customizations after upgrade

### System Integration Guide
The Coffee Management System can integrate with various business applications:

**ERP Integration:**
- Odoo native integration with Accounting, Inventory, and Sales modules
- SAP integration via OData services
- Microsoft Dynamics integration through REST API

**Logistics Systems:**
- Warehouse Management System (WMS) integration
- Transportation Management System (TMS) connectivity
- Barcode scanning system interfaces

**Financial Systems:**
- Accounting software integration
- Payment gateway connections
- Tax calculation services

**Implementation Steps:**
1. Identify integration points and data flows
2. Configure API access credentials
3. Set up data mapping between systems
4. Test integration in staging environment
5. Monitor initial data synchronization

**Common Integration Patterns:**
- Real-time API calls for critical operations
- Scheduled batch processing for non-critical data
- Event-based triggers for workflow automation

### Customization Guide
Extend and adapt the Coffee Management System to your specific needs:

**UI Customizations:**
- Add custom fields to forms
- Modify views and layouts
- Create custom reports and dashboards

**Workflow Extensions:**
- Add new states to existing workflows
- Create custom validation rules
- Implement additional approval steps

**Business Logic:**
- Override default calculations
- Add custom validation methods
- Implement new business rules

**Custom Modules:**
- Create new coffee-related modules
- Extend existing models
- Add new automation features

**Best Practices:**
1. Always inherit from base classes
2. Use Odoo's extension mechanisms
3. Document all customizations
4. Test changes thoroughly
5. Maintain upgrade compatibility

### Release Notes
Version history and significant changes:

**Version 3.0 (2025-08-15)**
- Added multi-warehouse support
- Redesigned quality evaluation interface
- Improved performance for large datasets
- Added new API endpoints for mobile access

**Version 2.5 (2025-05-20)**
- Enhanced contract management features
- Added barcode scanning support
- Improved data export capabilities
- Fixed several minor bugs

**Version 2.0 (2025-02-10)**
- Major workflow improvements
- New reporting engine
- Enhanced security features
- Database schema changes (requires migration)

**Version 1.5 (2024-11-15)**
- Initial production release
- Core coffee management features
- Basic reporting capabilities
- API version 1.0

**View Full Changelog:**
For complete details of all changes, visit the project repository or contact support.

### Developer Documentation
Technical resources for extending the Coffee Management System:

**Core Models:**
- `coffee.arrival`: Main arrival record model
- `coffee.quality.evaluation`: Quality assessment model
- `coffee.contract`: Sales contracts model
- `coffee.stock.receiving`: Inventory movements model

**Extension Points:**
1. Override methods using `@api.model` or `@api.multi`
2. Extend views using XML inheritance
3. Add new workflow states via `workflow` module
4. Create custom reports using QWeb templates

**API Development:**
- Use Odoo's RPC protocol for external integrations
- Follow REST API best practices for new endpoints
- Implement proper authentication and authorization
- Document endpoints using OpenAPI/Swagger

**Testing Guidelines:**
1. Write unit tests for all new functionality
2. Include integration tests for workflows
3. Perform load testing for performance-critical features
4. Document test cases and expected results

**Code Samples:**
```python
# Example of extending the arrival model
class CoffeeArrival(models.Model):
    _inherit = 'coffee.arrival'
    
    custom_field = fields.Char(string="Custom Info")
    
    @api.multi
    def custom_method(self):
        # Custom logic here
        return True
```

```xml
<!-- Example of extending a view -->
<record id="view_coffee_arrival_form_extended" model="ir.ui.view">
    <field name="name">coffee.arrival.form.extended</field>
    <field name="model">coffee.arrival</field>
    <field name="inherit_id" ref="coffee_management.view_coffee_arrival_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='vehicle_plate_no']" position="after">
            <field name="custom_field"/>
        </xpath>
    </field>
</record>
```

### System Architecture Overview
High-level design of the Coffee Management System:

**Core Components:**
1. **Data Layer**
   - PostgreSQL database
   - Odoo ORM models
   - Data validation rules

2. **Business Logic Layer**
   - Workflow engines
   - Automated processes
   - Calculation services

3. **Presentation Layer**
   - Web interface
   - Mobile apps
   - Reporting tools

4. **Integration Layer**
   - REST API
   - Webhooks
   - Scheduled jobs

**Key Architectural Patterns:**
- Model-View-Controller (MVC) for web interface
- Service-oriented architecture for integrations
- Event-driven architecture for workflow automation

**Data Flow:**
1. User actions trigger business processes
2. System validates and processes data
3. Results are persisted and made available via views/APIs
4. External systems can interact via integration points

**Scalability Considerations:**
- Horizontal scaling for web workers
- Database partitioning for large datasets
- Caching strategies for frequently accessed data

### Contribution Guidelines
How to contribute to the Coffee Management System:

**Getting Started:**
1. Fork the repository
2. Set up development environment
3. Create a feature branch
4. Make your changes
5. Submit a pull request

**Coding Standards:**
- Follow Odoo coding guidelines
- Use PEP 8 style for Python
- Document all public methods
- Include unit tests for new features

**Commit Message Format:**
```
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

**Types:**
- feat (new feature)
- fix (bug fix)
- docs (documentation changes)
- style (formatting changes)
- refactor (code restructuring)
- test (test additions)
- chore (maintenance tasks)

**Review Process:**
1. Automated CI checks
2. Peer code review
3. Maintainer approval
4. Merge into main branch

**Community Guidelines:**
- Be respectful and inclusive
- Provide constructive feedback
- Follow the project's code of conduct
- Help improve documentation

### API Reference
Detailed documentation of all API endpoints:

**Arrivals API**
- `GET /api/coffee/arrivals`
  - Parameters:
    - `date_from` (optional): Filter arrivals from date (YYYY-MM-DD)
    - `date_to` (optional): Filter arrivals to date (YYYY-MM-DD)
    - `status` (optional): Filter by status (draft, evaluated, recorded, done)
    - `limit` (optional): Maximum results to return (default: 100)
  - Response:
    ```json
    {
      "data": [
        {
          "id": 123,
          "name": "ARR-2025-001",
          "date": "2025-01-15",
          "supplier": "Coffee Supplier A",
          "status": "evaluated",
          "product": "Raw-Guji-Washed-G1-Coffee"
        }
      ],
      "count": 1
    }
    ```

- `POST /api/coffee/arrivals`
  - Request Body:
    ```json
    {
      "date": "2025-01-16",
      "supplier": "Coffee Supplier B",
      "vehicle_plate": "ABC123",
      "ecx_product": "Guji-Washed-G1",
      "woreda": "Arsi"
    }
    ```
  - Response:
    ```json
    {
      "id": 124,
      "name": "ARR-2025-002",
      "status": "draft"
    }
    ```

**Quality Evaluation API**
- `PUT /api/coffee/arrivals/{id}/evaluate`
  - Request Body:
    ```json
    {
      "moisture": 11.5,
      "defects": 2.1,
      "acidity": 8,
      "body": 7,
      "flavor": 9,
      "evaluator": "Quality Staff 1"
    }
    ```
  - Response:
    ```json
    {
      "success": true,
      "grade": "G1",
      "product_created": "Raw-Guji-Washed-G1-Coffee"
    }
    ```

**Error Responses**
All endpoints return errors in this format:
```json
{
  "error": {
    "code": "invalid_parameter",
    "message": "Invalid date format",
    "details": {
      "parameter": "date_from",
      "expected_format": "YYYY-MM-DD"
    }
  }
}
```

### Performance Tuning Guide
Advanced optimization techniques for the Coffee Management System:

**Database Optimization**
1. **Indexing Strategies**
   - Add indexes to frequently queried fields
   - Use partial indexes for filtered queries
   - Consider composite indexes for common query patterns

2. **Query Optimization**
   - Use `EXPLAIN ANALYZE` to identify slow queries
   - Avoid N+1 query problems
   - Use `prefetch_related` for related data access

3. **Partitioning**
   - Partition large tables by date ranges
   - Consider hash partitioning for evenly distributed data

**Application Optimization**
1. **Caching**
   - Implement Redis caching for frequent queries
   - Cache complex calculations
   - Use HTTP caching headers for API responses

2. **Background Processing**
   - Move long-running tasks to Celery workers
   - Use message queues for asynchronous processing
   - Schedule reports during off-peak hours

3. **Memory Management**
   - Monitor and optimize memory usage
   - Implement pagination for large datasets
   - Use streaming responses where possible

**System Configuration**
1. **Odoo Configuration**
   - Adjust worker count based on available CPUs
   - Configure appropriate timeouts
   - Enable database connection pooling

2. **Server Tuning**
   - Configure appropriate swap space
   - Adjust kernel parameters for high concurrency
   - Enable compression for network traffic

**Monitoring & Maintenance**
1. **Performance Monitoring**
   - Set up Prometheus/Grafana dashboards
   - Monitor key metrics:
     - Request latency
     - Database query times
     - Memory usage
     - CPU utilization

2. **Regular Maintenance**
   - Schedule weekly database maintenance
   - Monitor and archive old data
   - Regularly review and optimize indexes

### Implementation Case Studies
Real-world examples of Coffee Management System implementations:

**Case Study 1: Large-Scale Cooperative (Ethiopia)**
- **Challenge:** Managing 50,000+ arrivals annually from 200+ smallholder farmers
- **Solution:**
  - Implemented mobile data collection for field evaluations
  - Automated quality grading with machine learning
  - Integrated with ECX trading system
- **Results:**
  - 40% reduction in processing time
  - 99.5% data accuracy
  - Full traceability from farm to export

**Case Study 2: Specialty Roaster (USA)**
- **Challenge:** Tracking micro-lots and maintaining quality consistency
- **Solution:**
  - Customized quality evaluation forms
  - Added sensory analysis tracking
  - Integrated with roasting equipment
- **Results:**
  - Improved cup score consistency
  - Reduced green coffee waste by 25%
  - Enhanced marketing with provenance data

**Case Study 3: Multi-Site Processor (Colombia)**
- **Challenge:** Coordinating operations across 5 processing sites
- **Solution:**
  - Centralized database with regional replication
  - Standardized workflows across locations
  - Real-time dashboard for management
- **Results:**
  - 30% improved utilization of processing capacity
  - Reduced inventory discrepancies
  - Faster decision-making with unified data

**Lessons Learned:**
1. Start with well-configured master data
2. Train super-users before go-live
3. Phase implementation by location/process
4. Monitor system performance closely during peak
5. Gather user feedback for continuous improvement

## 2. Master Data Configuration (First-Time Setup)
Before you can use the module, a system administrator must perform a one-time setup of the core data.

1.  **Geographical Data:**
    *   Navigate to `Coffee Management > Configuration > Zones/Province` to define your operational zones.
    *   Navigate to `Coffee Management > Configuration > Woredas/District` to define the districts within those zones.
2.  **Coffee Classification Data:**
    *   In the `Configuration` menu, define your company's master list for:
        *   **Coffee Types** (e.g., Washed, Unwashed)
        *   **Coffee Origins** (e.g., Guji, Sidamo)
        *   **ECX Coffee Grades** (The official grades you purchase)
3.  **ECX Product Master:**
    *   Go to `Configuration > ECX Coffee Products`.
    *   Here, you must create the base combinations of Origin, Type, and Grade that you expect to receive. These are used as templates during the arrival process.
4.  **Finished Goods & BoMs:**
    *   Go to `Inventory > Products > Products`.
    *   For any coffee product you intend to manufacture and sell (e.g., "Roasted Guji G1 Coffee"), you must manually create it as a **Storable Product** and define a **Bill of Materials (BoM)** for it. The raw material components you add to the BoM will be the products that are dynamically created by the arrival workflow.

### User Permissions Guide
The following permissions are required for key operations:

| Operation | Required Access Rights |
|-----------|-----------------------|
| Coffee Arrival Creation | Coffee Management: User |
| Quality Evaluation | Coffee Management: Quality Technician |
| Weight Recording | Coffee Management: Warehouse Operator |
| Stock Receiving | Inventory: User |
| Contract Creation | Sales: User |
| Configuration Changes | Coffee Management: Administrator |

## 3. Core Workflows: An Overview

### Procurement Workflow: From Arrival to Graded Stock
This is the process for bringing new, raw coffee into your inventory.

### Sales Workflow: From Contract to Production
This is the process for selling a finished (manufactured) coffee product.

### Workflow Diagrams
![Procurement Workflow](images/procurement_workflow.png)
*Figure 1: Coffee Procurement Workflow - From arrival to graded stock*

![Sales Workflow](images/sales_workflow.png) 
*Figure 2: Coffee Sales Workflow - From contract to production*

## 4. Detailed Step-by-Step Guides

### 4.1 Managing a New Coffee Arrival
This process starts when a truck with raw coffee arrives at your facility.

1.  Navigate to `Coffee Management > Operations > Coffee Arrival`.
2.  Click **New**.
3.  Fill in the required fields:
    *   **Supplier Name:** The vendor who supplied the coffee.
    *   **Vehicle Plate No.:** The license plate of the delivery vehicle.
    *   **ECX Coffee Product:** Select the expected coffee classification from your pre-configured master list.
    *   **Woreda / District:** Select the specific geographical origin. The Zone will populate automatically.
4.  Click **Save**. The arrival is now in the `Draft` state. The `Product` field will be empty for now.

### 4.2 Performing a Quality Evaluation
This is the most critical step, where the coffee is graded and a specific product is assigned.

1.  From the `Draft` arrival record, click the **Evaluate Quality** button.
2.  A popup window will appear. Enter all the required quality metrics:
    *   Moisture Content (%)
    *   Primary & Secondary Defect scores
    *   All Cup Attribute scores (Acidity, Body, etc.)
3.  Click **Save** on the popup.
4.  **System Automation:** The system will now:
    *   Calculate the **Total Score** and the final **AMG Grade**.
    *   Construct a unique product name (e.g., "Raw-Guji-Washed-G1-Coffee").
    *   Search your inventory for a product with this exact name. If it doesn't exist, it will **create a new product automatically**.
    *   The **Product** field on the Coffee Arrival form will now be filled with this specific, graded product.
    *   The arrival's status will change to `Quality Evaluated`.

> **Important:** If the calculated AMG Grade is "UG" (Under Grade), the arrival will be moved to a rejected state, and you will not be able to proceed.

### 4.3 Recording the Weight
1.  From the `Quality Evaluated` arrival record, click the **Record Weight** button.
2.  In the popup, enter the weight details:
    *   Number of Bags
    *   Gross Weight (KG)
    *   Truck Weight (KG)
3.  Click the **Confirm Weight** button in the popup.
4.  The system will log the details and the arrival's status will change to `Weight Recorded`.

### 4.4 Receiving the Coffee into Stock
This is the final step of the procurement process.

1.  Navigate to `Coffee Management > Operations > Stock Receiving`.
2.  Click **New**.
3.  Select the **Arrival Record** you just processed. The product, grade, and weight information will populate automatically.
4.  Select the **Warehouse** and specific **Block (Location)** where you want to store the coffee.
5.  Click **Save**, then click the **Receive Stock** button.
6.  The system will create and validate an inventory transfer. The "On Hand" quantity for your specific graded product will now be increased, and the parent Coffee Arrival will be moved to the `Done` state.

### 4.5 Creating and Managing a Coffee Contract
This process is for selling your finished coffee products.

1.  Navigate to `Coffee Management > Contracts > Coffee Contracts`.
2.  Click **New**.
3.  Fill in the contract details:
    *   **Buyer Name:** The customer purchasing the coffee.
    *   **Warehouse:** The warehouse that will fulfill the order.
    *   **Contract Date**.
4.  Under the **Contract Lines** tab, click "Add a line".
    *   Select the **finished product** you are selling (e.g., "Roasted Guji G1 Coffee").
    *   Enter the **Quantity (Tons)** and **Unit Price (USD/LB)**. The subtotal will calculate automatically.
5.  Click **Save**. The contract is now in `Draft`.
6.  Click **Confirm**.
7.  **System Automation:** The system will immediately create a **Delivery Order** and, if a BoM exists for the product, a **Manufacturing Order**. The smart buttons at the top of the form will update with a count of `1`. The contract status moves to `Confirmed`.
8.  You can now use the **smart buttons** to view the associated delivery and manufacturing orders.

## 5. Reporting and Analytics

### 5.1 Wizard-Based PDF Reports
For formal reporting, navigate to `Coffee Management > Reporting`. Here you can select a report type, enter a date range, and generate a professional PDF.

*   **Arrival & Quality Report:** A summary of all incoming batches with their final quality scores and grades.
*   **Warehouse Stock Report:** A stock movement report showing balances and movements for coffee products.
*   **Contract Fulfillment Report:** Tracks the progress and financial value of sales contracts.
*   **Manufacturing Report:** An overview of all production orders linked to your coffee contracts.

### 5.2 On-Screen Analytics
For interactive analysis, navigate to `Coffee Management > Reporting > Analytics & Reports`.

*   These menu items open **pivot tables and graph views**, allowing you to filter, group, and analyze your data in real-time directly on the screen. You can analyze arrivals by supplier, quality by grade, and much more.
*   You can export any of this data to **Excel** using the standard Odoo export button.

## 6. Frequently Asked Questions (FAQ) & Troubleshooting

*   **Q: A Manufacturing Order was not created when I confirmed a contract.**
    *   **A:** This is almost always a configuration issue. Ensure that:
        1.  You are selling a **finished product**, not a raw material.
        2.  The finished product has a **Bill of Materials (BoM)** defined.
        3.  The finished product has the **"Manufacture"** and **"Replenish on Order (MTO)"** routes checked on its Inventory tab.

*   **Q: The balance on my Stock Receiving form is negative.**
    *   **A:** This happens if the product being received is accidentally set to the "Consumable" product type. All coffee you track in inventory **must** be a **"Storable Product"**.

*   **Q: I cannot select a supplier/product in the dropdowns.**
    *   **A:** This is by design to ensure data quality.
        *   **Suppliers** will only appear after you have created a Purchase Order for them in the Purchase app.
        *   **Products** will only appear after you have checked the "Is a Coffee Product" box on their product form.

*   **Q: The system is running slowly during peak arrival times.**
    *   **A:** Consider these optimizations:
        1. Schedule non-critical reports to run during off-peak hours
        2. Increase server resources during peak seasons
        3. Use the batch processing feature for large arrivals

*   **Q: How do I correct an incorrect quality evaluation?**
    *   **A:** Follow this procedure:
        1. Cancel the stock receiving linked to the arrival
        2. Reset the arrival to Draft state
        3. Re-evaluate the quality
        4. Complete the workflow again