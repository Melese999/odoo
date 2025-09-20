# AMG Coffee Management System

## Overview

The **Coffee Management System** is a comprehensive Odoo module designed to manage the end-to-end coffee supply chain, from the initial procurement of raw green coffee beans to the sale and delivery of finished, processed coffee products.

This module seamlessly integrates with Odoo's native **Inventory**, **Purchase**, and **Manufacturing** applications to provide a robust, traceable, and automated workflow. It is built to support both **Make to Stock** and **Make to Order** production strategies, giving you full control over your coffee processing operations.

## Key Features

-   **Procurement & Arrival:** Manage incoming deliveries of raw coffee with a dedicated workflow, including vehicle details and supplier information.
-   **Quality Control:** A built-in quality evaluation process to grade coffee based on raw and cup attributes, ensuring only qualified beans enter your stock.
-   **Weight Management:** Accurately record gross, truck, and net weights, with automatic calculations for damage and moisture loss.
-   **Sales Contracts:** A dedicated contract management system that behaves like Odoo's Sales Orders, allowing you to manage customer agreements for finished coffee products.
-   **Automated Production (Make to Order):** Confirming a coffee contract automatically generates the necessary warehouse delivery orders, which in turn trigger Manufacturing Orders based on product routes.
-   **Inventory Integration:** All stock movements—from raw material reception to finished good delivery—are handled through standard Odoo inventory transfers, ensuring accurate stock levels at all times.
-   **Full Traceability:** Every step is linked. A sales contract can be traced to its delivery order, which can be traced to the manufacturing order, which in turn can be traced back to the raw materials used.

---

## The Workflow

The module is designed around two primary business flows: **Procurement (Purchase)** and **Sales & Manufacturing**.

### 1. Procurement: From Purchase Order to Raw Coffee Stock

This flow mimics the standard Purchase workflow, adding value with specialized coffee-related steps.

1.  **Create Purchase Order:** A standard Odoo Purchase Order is created for a raw coffee product (e.g., `"Raw Green Coffee - Guji G1"`).
2.  **Create Coffee Arrival:** When the truck arrives at the facility, the user opens the confirmed PO and clicks the **"Create Coffee Arrival"** button. This creates a `Coffee Arrival` record, pre-filled with the supplier and product information.
3.  **Evaluate Quality:** The user clicks **"Evaluate Quality"** on the Arrival form to enter metrics like moisture content, defects, and cup attributes. The system calculates an `AMG Grade`. Unqualified coffee (UG Grade) is rejected and cannot proceed.
4.  **Record Weight:** The user clicks **"Record Weight"** to log the truck's weight data. The system calculates the final net weight of the coffee beans.
5.  **Receive Stock:** A `Stock Receiving` (GRN) record is created, linked to the `Coffee Arrival`. The user clicks **"Receive Stock"**. This action finds the original inbound shipment created by the Purchase Order and validates it with the final recorded weight, officially adding the raw coffee to a specific warehouse location.

### 2. Sales & Manufacturing: From Contract to Finished Product Delivery

This flow mimics the standard Sales "Make to Order" (MTO) workflow.

1.  **Product Configuration (One-Time Setup):**
    *   Create a finished product (e.g., `"Roasted Coffee - Guji G1"`).
    *   On its **Inventory Tab**, ensure the **Manufacture** and **Replenish on Order (MTO)** routes are checked.
    *   Create a **Bill of Materials (BoM)** for this product, listing the required raw coffee as a component.
2.  **Create Coffee Contract:** A user creates a `Coffee Contract` (which acts as a sales agreement) for a customer, adding one or more finished coffee products as contract lines.
3.  **Confirm Contract:** The user clicks the **"Confirm"** button.
4.  **Automated Logistics:**
    *   The system automatically creates a **Delivery Order** (`stock.picking`) for the products on the contract.
    *   The Delivery Order's demand for the finished product triggers the **MTO route**.
    *   Because the product is set to "Manufacture", Odoo automatically creates a **Manufacturing Order (MO)** to produce the required quantity.
5.  **Traceability & Fulfillment:**
    *   A **"Deliveries" smart button** appears on the contract, linking directly to the warehouse shipment.
    *   The source document on both the Delivery Order and the Manufacturing Order is the contract number, providing end-to-end traceability.
    *   The production team fulfills the MO, and the warehouse team processes the Delivery Order to ship the final goods.

---

## Setup & Configuration

Before using the module, a one-time configuration is required.

### 1. Install Dependencies

Ensure the following Odoo applications are installed:
-   **Inventory** (`stock`)
-   **Manufacturing** (`mrp`)
-   **Purchase** (`purchase`)
-   **Sales** (`sale`)

### 2. Configure Coffee Attributes

The module uses Odoo's native Product Attributes to classify coffee.

1.  Navigate to `Inventory -> Configuration -> Products -> Attributes`.
2.  Create the following attributes (the names must be exact):
    *   `Coffee Type`
    *   `Coffee Origin`
    *   `Coffee Grade`
3.  For each attribute, add the corresponding values (e.g., for "Origin", add values like "Guji", "Sidamo", "Yirgacheffe").

### 3. Configure Coffee Products

For every type of coffee you handle, you should create at least two products: the raw material and the finished good.

1.  Navigate to `Inventory -> Products -> Products`.
2.  **Create a Raw Material Product:**
    *   **Name:** e.g., `"Raw Green Coffee - Guji G1"`
    *   **Product Type:** `Storable Product`
    *   Check the box **"Is a Coffee Product"**.
    *   A **"Coffee Configuration"** tab will appear. Select the correct Type, Origin, and Grade from the dropdowns you created in the previous step.
3.  **Create a Finished Good Product:**
    *   **Name:** e.g., `"Roasted Coffee - Guji G1"`
    *   **Product Type:** `Storable Product`
    *   Check the box **"Is a Coffee Product"**.
    *   Go to the **Inventory Tab** and select the **Manufacture** and **Replenish on Order (MTO)** routes.
    *   Go to the **"Coffee Configuration"** tab and set its attributes.

## Module Structure

-   `models/`: Contains all the Python logic for the custom models.
    -   `coffee_arrival.py`: Manages incoming raw coffee deliveries.
    -   `coffee_contract.py`: Manages sales agreements for finished goods.
    -   `coffee_contract_line.py`: Line items for the contracts.
    -   `coffee_quality.py`: Logic for the quality evaluation process.
    -   `coffee_stock_receiving.py`: Manages the Goods Receiving Note (GRN) process.
    -   `product_template_extension.py`: Adds coffee-specific fields to the standard product model.
    -   `stock_picking_extension.py`: Adds a link from Delivery Orders back to the Coffee Contract.
-   `views/`: Contains all the XML definitions for the user interface (forms, trees, menus).
-   `security/`: Defines the access rights and security groups.
-   `data/`: Contains initial data loaded on installation, such as `ir.sequence` records.
-   `reports/`: Contains the QWeb templates and definitions for printable PDF reports.