# Cedar Nexus

**Subtitle:** Connecting Healthcare Supply Operations  
**Version:** 1.0  
**Last updated:** March 2026

## Overview & Module Map

The Inventory & Procurement module manages the full lifecycle of stock — from raising a requisition request, through supplier orders and goods receipt, to consumption monitoring and compliance reporting.

### Module pages

| Page | What it does |
|---|---|
| Inventory Dashboard | KPI overview, pipeline, alerts, consumption trends, supplier performance. |
| Inventory Items | Master catalogue of all stockable items with batch/expiry/serial tracking flags. |
| Item Categories | Group items logically (Pharmaceutical, Consumable, Equipment, etc.). |
| Stock List | Real-time stock levels per item-batch-location with expiry and reorder indicators. |
| Stock Adjustments | Record write-offs, damage, system corrections, and physical count corrections. |
| Suppliers | Supplier directory with ratings, contract dates, and payment terms. |
| Purchase Orders | Create, approve, and manage supplier purchase orders. |
| Goods Receipt Notes (GRN) | Receive goods against a PO, scan barcodes, record batch/lot/expiry data. |
| Requisitions | Departments request stock items; system routes for approval and fulfilment. |
| Requisition Fulfilment | Inventory team picks and dispatches items against approved requisitions. |
| Physical Stock Audit | Scheduled count sessions to verify actual vs system stock quantities. |
| Expiry Management | Monitor items by expiry bucket (Expired, ≤7d, 8–30d, 31–90d, Safe). |
| Inventory Locations | Define storage areas (wards, pharmacy, store, cold room). |
| Controlled Substance Ledger | Full audit log for Schedule/controlled drugs with witness and verification. |

> **Tip:** Start from the Inventory Dashboard for a holistic view. The Quick Actions panel on the dashboard provides shortcuts to the most common tasks based on your role.

## Role Reference

Access to inventory actions is governed by role code. The table summarises permissions for each role.

| Role | Code | Key capabilities |
|---|---|---|
| Admin | ADMIN | Full access — all create, approve, manage, export, audit, CS ledger. |
| Inventory Manager | INVMGR | Create/approve requisitions, create PO, receive GRN, manage items/locations, adjustments, audit, CS ledger, export. |
| Inventory Clerk | INVCLERK | Create requisition, receive GRN, manage items, stock adjustments, physical audit. |
| Procurement Manager | PROCMGR | Create/approve PO, receive GRN, manage suppliers, export. |
| Finance Approver | FINAPPROV | View and approve PO, export. |
| Pharmacy Manager | PHARMMGR | Create requisition, receive GRN, CS ledger, stock adjustments. |
| Pharmacy Technician | PHARMTECH | Create requisition, CS ledger entries. |
| Nurse / Doctor / Ward Staff | NURSE / DOCTOR / WARDSTF | View dashboard, create requisitions only. |
| Pharmacist | PHRMCST | View, create requisition, receive GRN. |
| Storekeeper | STORESTR | Receive GRN, manage items, stock adjustments. |

> If a button or menu option is missing, your role may not have that permission. Contact your Inventory Manager or Admin.

## Inventory Dashboard

The dashboard provides a real-time overview of the entire inventory operation. All data refreshes automatically on load.

### KPI cards

- **Total Items** — Number of active catalogue items.
- **Low Stock Alerts** — Items at or below their reorder level (pulsing red badge for critical).
- **Expiring Soon** — Items expiring within 30 days.
- **Pending Orders** — Open purchase orders awaiting receipt.
- **Stock Value** — Total estimated inventory value in AED.
- **Pending Requisitions** — Department requests awaiting action.

### Pipeline view

The horizontal pipeline bar shows how many items are at each stage: **Draft → Pending → Approved → PO Issued → In Transit → Received**. Use it to spot bottlenecks.

### Alerts panel

Active alerts are colour-coded by severity: **Critical** (red), **High** (orange), **Medium** (yellow), **Low** (blue). Click any alert to navigate directly to the affected record.

### Quick Actions

Role-aware shortcut buttons appear based on your permissions. Common actions include New Requisition, Create PO, Receive Goods, Stock Adjustments, Expiry Dashboard, Physical Audit, and Controlled Drugs.

> **Tip:** Use the branch selector (top-right of the dashboard) to filter all metrics to a specific branch. All charts and counts update automatically.

## Inventory Items (Master Catalogue)

The Items catalogue is the master reference for everything that can be stocked, ordered, or consumed. Every purchasable or storable item must be registered here before it can appear in POs, GRNs, or requisitions.

### Key fields

| Field | Description |
|---|---|
| Item Code | Unique code. Used in POs, GRNs, and reports. |
| Item Name | Display name shown everywhere in the module. |
| Generic Name | INN / generic drug name (for pharmaceuticals). |
| Item Type | Consumable, Pharmaceutical, Equipment, Reagent, PPE, or Other. |
| Category | Logical grouping (links to Item Categories). |
| UOM | Unit of Measure (Tablet, Vial, Box, Kg, Litre, Each, etc.). |
| Pack Size | Number of individual units per pack. |
| Batch Tracked | Enable to require lot/batch numbers on GRN entry. |
| Expiry Tracked | Enable to require expiry dates; feeds the Expiry Dashboard. |
| Expiry Alert Days | How many days before expiry to start alerting (default: 30). |
| Min / Max / Reorder Level | Stock thresholds that drive low-stock and reorder alerts. |
| Standard / Average Cost | Used for stock valuation and reporting. |
| Storage Conditions | Room Temp, Refrigerated, Frozen, or Controlled. |
| Barcode / RFID | Printed on labels and scanned during GRN and fulfilment. |
| Is Critical Item | Flag to highlight critical items with extra urgency indicators. |
| NDC / HS Code | National Drug Code / Harmonised System code for regulatory use. |

### Add or edit an item

1. Go to **Inventory → Inventory Items**.
2. Click **Add Item** or click an existing item row to edit.
3. Fill in Item Code, Item Name, UOM (required fields).
4. Set tracking flags (Batch Tracked, Expiry Tracked) as appropriate.
5. Enter stock levels: Min, Max, Reorder Level.
6. Click **Save**.

### Bulk import via Excel

1. Download the Excel template from the Items list page.
2. Fill in item details following the column headers.
3. Click **Import Excel** and upload the file.
4. Review the validation results panel — errors are highlighted row by row.
5. Click **Confirm Import** to save validated rows.

> **Note:** Changing UOM after stock has been received may cause quantity discrepancies. Always set UOM correctly before the first GRN.

## Stock List

The Stock List shows current on-hand quantity for every item-batch-location combination. It is the primary view for day-to-day stock checking.

### Stock level indicators

| Indicator | Colour | Meaning |
|---|---|---|
| In Stock | Green | Quantity above minimum stock level. |
| Low Stock | Yellow | Quantity ≤ 120% of minimum stock level. |
| Critical | Red | Quantity ≤ 50% of minimum stock level. |
| Out of Stock | Red (bold) | Quantity = 0. |

### Expiry badges

- **Expired** — Shown in red; item is past its expiry date.
- **X days left ⚠** — Shown in red if ≤ 7 days.
- **X days left** — Shown in yellow if ≤ 30 days.
- **Date displayed** — Shown in gray if more than 30 days remain.

### Filters

- Search by item name.
- Filter by Category, Location.
- Toggle **Show Expired** to include or hide expired stock.
- Toggle **Show Quarantined** to see items placed on hold.

> **Tip:** Select items directly from the Stock List to quickly raise a Requisition for replenishment using the **Raise Requisition** button.

## Suppliers

The Supplier directory stores all vendor details used when creating Purchase Orders.

### Key supplier fields

| Field | Description |
|---|---|
| Supplier Code | Unique identifier used in POs and reports. |
| Supplier Type | Pharmaceutical, Medical Consumable, Equipment, General, or Service. |
| Lead Time (Days) | Expected delivery time — used for reorder planning. |
| Payment Terms | Net 30, Net 60, COD, etc. |
| Rating | Internal performance rating (1–5 stars). |
| Quality Score | Quality assessment percentage. |
| Delivery Reliability | On-time delivery percentage. |
| Contract Start / End | Contract validity window; expiry shown as a warning. |
| Is Preferred Supplier | Used to suggest this supplier during PO creation. |
| Blacklist Reason | If populated, the supplier is flagged as blacklisted. |

### Add or edit a supplier

1. Go to **Inventory → Suppliers**.
2. Click **New Supplier** or click a row to edit.
3. Enter Supplier Code and Supplier Name (required).
4. Optionally set Lead Time, Payment Terms, Rating, and contract dates.
5. Mark **Is Preferred Supplier** if this is the primary vendor for any items.
6. Click **Save**.

### Supplier Items

From the Supplier profile, open the **Supplier Items** tab to link specific catalogue items to this supplier with a payer unit price and lead time. These links drive the **Suggested Items** list when creating a PO.

## Purchase Orders (PO)

A Purchase Order is a formal request sent to a supplier to supply specific items at agreed quantities and prices.

### PO lifecycle

1. **Create Draft** — Select supplier and branch; items are suggested automatically based on supplier-item links and reorder needs.
2. **Add / adjust items** — Set quantity, unit price, and discount per line.
3. **Submit** — Move status from Draft to Issued (or Pending Approval depending on configuration).
4. **Receive** — Create GRN(s) against the PO as deliveries arrive.
5. **Fully Received** — All quantities matched; PO closes automatically.

### Create a PO

1. Go to **Inventory → Purchase Orders → New PO**.
2. Select Supplier. The system loads supplier details including contact and default payment terms.
3. Select Branch for delivery.
4. Click **Load Suggested Items** to auto-populate items associated with this supplier that are at or below reorder level.
5. Add or remove items manually using the item search row.
6. Enter Quantity Ordered and Unit Price for each item. Last purchase price populates automatically when available.
7. Set Delivery Date and add Notes if needed.
8. Click **Save as Draft** or **Submit**.

### PO statuses

| Status | Meaning |
|---|---|
| Draft | Not yet sent to supplier; editable. |
| Issued | Sent to supplier; receipt can begin. |
| Partially Received | Some items received via GRN; remaining open. |
| Fully Received | All ordered quantities received; PO complete. |
| Cancelled | PO cancelled; no receipt allowed. |

### Print a PO

Click **Print / PDF** on the PO detail page to generate a printable PDF with letterhead, item lines, totals, and signature section.

> **Tip:** You can view the **Last Purchase Info** for any line item (click the ⓘ icon next to the item row) to compare the current price against the historical purchase price.

## Goods Receipt Note (GRN)

A GRN records actual receipt of goods from a supplier. It is linked to a PO and updates stock levels when posted.

### Create a GRN

1. Go to **Inventory → GRN → New GRN**.
2. Select the Purchase Order. Items from the PO populate automatically with remaining outstanding quantities.
3. For each item row, enter the Quantity Received.
4. For batch-tracked items, enter Batch/Lot Number and Expiry Date.
5. Optionally enter Invoice Number, Delivery Note, and Received By.
6. Use the barcode scanner (camera or USB wedge) to auto-fill batch numbers from physical labels.
7. Click **Post GRN** to update stock and close the GRN.

### Barcode / QR scanning

- Click **Scan Barcode** to open the scanner panel.
- **Camera mode:** Point the phone/webcam at the barcode label — it auto-fills the matching row.
- **USB Scanner mode (keyboard-wedge):** Click the input field and scan with a physical handheld scanner. Fast keystrokes are detected automatically.
- Switch between camera and USB mode with the toggle button in the scanner panel.

### Partial receipts

You can receive a partial quantity against a PO line. The PO moves to **Partially Received** status and the remaining quantity stays open for a subsequent GRN.

> **Important:** Once a GRN is posted, stock levels update immediately. A posted GRN cannot be deleted — use a Stock Adjustment if a correction is needed.

### Print a GRN

Click **Print GRN** on a posted GRN to generate a printable receipt document for filing.

## Requisitions

Requisitions allow any department to formally request stock items. The Inventory team reviews, approves, and fulfils these requests.

### Requisition Progress Tracker

Every submitted requisition shows a live progress tracker when you expand it in the list. The tracker has two sections:

- **Workflow stepper** — Four stages: Submitted → Approved → Issued. Active stage is highlighted in blue; completed stages in green.
- **Procurement Pipeline** — Visible once a requisition is Approved or Partially Fulfilled. For each item that cannot be immediately issued from stock, the pipeline shows whether a Purchase Order has been raised and its current stage: PO Drafted → With Supplier → Receiving → Received.
- If no PO exists for an out-of-stock item, an amber warning **No Purchase Order raised yet** prompts the inventory team to create one.
- A receipt progress bar under each PO shows how much of the ordered quantity has been received via GRN.

### Requisition types

- **Stock** — Standard replenishment request for existing catalogue items.
- **Non-Stock / Special** — Request for items not yet in the catalogue or one-time purchases.

### Create a requisition

1. Go to **Inventory → Requisitions → New Requisition**.
2. Select Requisition Type (Stock or Non-Stock).
3. Department and Branch are auto-filled from your user profile; adjust if needed.
4. Set Priority: Normal, Urgent, or Emergency.
5. Enter Required By Date.
6. Add Justification (free text explaining the need).
7. For clinical items, add Clinical Indication.
8. Search for items (type at least 3 characters) and add them to the list.
9. For each item, enter Quantity Requested and optional Notes.
10. Click **Submit**. The requisition enters **Pending** status.

### Requisition statuses

| Status | Meaning |
|---|---|
| Draft | Saved but not yet submitted. |
| Pending | Submitted; awaiting review by inventory/approver. |
| Approved | Ready for fulfilment. |
| Partially Fulfilled | Some items dispatched; remainder pending. |
| Fulfilled | All items dispatched to requesting department. |
| Rejected | Rejected by inventory manager with reason. |
| Cancelled | Cancelled by the requester. |

> **Tip:** Urgent and Emergency requisitions appear highlighted in the Requisition List and generate dashboard alerts. Use these priorities only when genuinely needed.

## Requisition Fulfilment

After a requisition is approved, the Inventory team picks and dispatches items to the requesting department.

1. Go to **Inventory → Requisitions** and open an Approved requisition.
2. Click **Fulfil** or open the Fulfilment view.
3. For each line item, select the Batch to issue using the Batch Selection modal (shows stock per batch with lot number, expiry, and quantity).
4. Enter the Quantity to Fulfil (cannot exceed approved quantity or available stock).
5. Use the barcode scanner to verify the correct batch by scanning the physical label.
6. Click **Fulfil Items**. Stock is deducted and the requisition status updates.

### Batch Selection

The Batch Selection modal lists all available batches for an item sorted by expiry date (FEFO — First Expire, First Out). Always issue the earliest-expiring batch first to minimise wastage.

> **Important:** Stock is deducted from the selected batch and location immediately on fulfilment. Partial fulfilment is allowed — the requisition moves to **Partially Fulfilled** and can be completed later.

> **Tip:** Scan the batch label with the camera or USB scanner during fulfilment to confirm you are issuing the correct physical stock.

## Stock Adjustments

Stock Adjustments correct the system quantity when the actual physical count differs, or record losses such as damage, expiry write-offs, or donations.

### Adjustment types

| Type | When to use |
|---|---|
| Physical Count | After a stock audit reveals a discrepancy between system and physical count. |
| Write-Off | Destroyed or unusable stock that cannot be returned. |
| Damage | Items damaged in storage or handling. |
| Expiry Write-Off | Removing expired stock from active inventory. |
| System Correction | Correcting a data entry error in a previous transaction. |
| Transfer | Moving stock between branches or locations. |
| Donation | Donated to another facility. |
| Found Stock | Previously unaccounted stock found during a count. |

### Create an adjustment

1. Go to **Inventory → Stock Adjustments → New Adjustment**.
2. Select Adjustment Type.
3. Enter Reason (mandatory for all types).
4. A Reference Number is auto-generated (`ADJ-YYYYMMDD-HHMM-random`).
5. Search for items and add them to the adjustment.
6. For each item, enter the Quantity Change (positive for found stock, negative for write-offs).
7. Load Stock Snapshot to see current batch quantities and select the correct batch.
8. Submit for Approval or save as Draft.

### Approval workflow

| Status | Meaning |
|---|---|
| Draft | Not yet submitted. |
| Pending Approval | Submitted; awaiting ADMIN, INVMGR, or FINAPPROV review. |
| Approved | Approved; stock quantities updated. |
| Rejected | Returned with comments. |
| Cancelled | Withdrawn by submitter. |

> **Warning:** Approved adjustments immediately change stock quantities and cannot be reversed. Double-check quantities and batch numbers before approving.

## Physical Stock Audit

Physical Stock Audits are formal counting sessions that compare the system's recorded stock against an actual physical count. Variances are identified and can be resolved via stock adjustments.

### Audit types

- **Full** — Count all items across the entire store/facility.
- **Partial** — Count specific item categories or a selected group of items.
- **Spot Check** — Random sampling of a small number of items.
- **Annual** — Scheduled yearly full-count.
- **Regulatory** — Mandated audit for compliance purposes.

### Run an audit

1. Go to **Inventory → Physical Stock Audit → New Audit**.
2. Select Audit Type, Location (optional), and Scheduled Date.
3. Click **Create**. The system takes a stock snapshot at this moment (system quantities are locked for reference).
4. Open the audit and count each item row in the list.
5. Enter the Physical Count quantity for each item.
6. Use **Show Only Variances** to focus on items where actual ≠ system.
7. Click **Complete Audit** when all items are counted.

### Audit statuses

| Status | Colour | Meaning |
|---|---|---|
| Planned | Blue | Scheduled but not yet started. |
| In Progress | Yellow | Counts being entered. |
| Completed | Green | All counts entered and audit closed. |
| Cancelled | Gray | Cancelled before completion. |

> **Tip:** After completing an audit with variances, create a Stock Adjustment of type **Physical Count** using the variance data to bring the system in line with actual stock.

## Expiry Management Dashboard

The Expiry Dashboard provides a visual overview of all batch-tracked items categorised by how close they are to their expiry date.

### Expiry buckets

| Bucket | Colour | Days remaining |
|---|---|---|
| Expired | Red (dark) | 0 or fewer days. |
| ≤ 7 Days | Red | 1–7 days. |
| 8–30 Days | Orange | 8–30 days. |
| 31–90 Days | Yellow | 31–90 days. |
| > 90 Days (Safe) | Green | More than 90 days. |

### Use the dashboard

1. Click a bucket card to filter the list to that expiry range.
2. Use the Search box to find a specific item.
3. Filter by Category to focus on a product group (e.g., Pharmaceuticals).
4. Sort by expiry date (ascending = shortest remaining first).
5. For expired items, create a Stock Adjustment with type **Expiry Write-Off** to remove them from active stock.

> **Important:** The **Total Expired Value** figure shown in the dashboard is calculated as: expired quantity × unit cost. This is a key operational loss metric.

> **Tip:** Items with an Expiry Alert Days threshold set on their catalogue record will generate dashboard alerts before entering the critical bucket.

## Inventory Locations

Locations represent physical storage areas within a branch where stock is kept. They are used in the Stock List, GRN, Physical Audits, and Fulfilment to specify exactly where an item is stored.

- Examples: Main Store, Pharmacy Cold Room, Ward A Cabinet, Emergency Trolley, Surgical Store.
- Each item-batch can be associated with a specific location, enabling precise stock tracking.
- Locations are selectable in the Stock List filter for location-specific views.
- During Physical Audit creation, you can scope the audit to a single location.

### Add a location

1. Go to **Inventory → Inventory Locations**.
2. Click **Add Location**.
3. Enter Location Name, Code, and Description.
4. Set Location Type (Store, Ward, Pharmacy, Cold Room, etc.).
5. Click **Save**.

## Controlled Substance Ledger

The Controlled Substance (CS) Ledger provides a legally compliant audit trail for Schedule/controlled drugs. Every movement — receipt, dispense, return, wastage — must be individually recorded and witnessed.

### Who can use it

- **View ledger entries:** ADMIN, INVMGR, PHARMMGR, PHARMTECH, INVCLERK.
- **Verify entries:** ADMIN, INVMGR, PHARMMGR, DOCTOR.

### Transaction types

| Type | Stock effect | Description |
|---|---|---|
| Receipt | + | Received from supplier (usually via GRN). |
| Dispense | − | Administered or dispensed to a patient. |
| Return | + | Returned unused portion from patient/ward. |
| Wastage | − | Discarded (unused dose, breakage, etc.). |
| Transfer | ± | Moved to another ward or location. |
| Adjustment | ± | Quantity correction with reason. |
| Opening Balance | + | Initial balance when ledger is set up. |

### Add a ledger entry

1. Go to **Inventory → Controlled Substance Ledger**.
2. Select the controlled item from the list to open its ledger.
3. Click **Add Entry**.
4. Select Transaction Type.
5. Enter Quantity and Batch Number.
6. Select Witnessed By (mandatory for all dispensing and wastage events).
7. For patient-related transactions, enter Patient ID and Prescription ID.
8. Add a Reference Number and Notes.
9. Click **Submit**.

### Verification

All entries start as unverified. An authorised ADMIN, INVMGR, PHARMMGR, or DOCTOR must verify each entry. Unverified entries count in the compliance dashboard card.

### Compliance dashboard

- **Unverified Count** — Entries requiring verification, shown with an alert if > 0.
- **Total Today** — Number of transactions entered today.

> **Warning:** CS ledger entries are permanent and cannot be deleted. If an error is made, add a corrective Adjustment entry with a clear explanation in the Notes field.

## Item Categories & UOM

Categories group inventory items for reporting, filtering, and dashboard breakdowns. Units of Measure (UOM) define how quantities are counted and tracked.

### Item Categories

- Manage via **Inventory → Item Categories**.
- Common categories: Pharmaceutical, Consumable, PPE, Surgical, Reagent, Equipment, Stationery.
- Each item in the catalogue must belong to one category.
- The dashboard pie chart shows stock value distribution by category.

### Units of Measure (UOM)

- Examples: Tablet, Capsule, Vial, Ampoule, Bottle, Box, Strip, Litre, Kg, Each, Pack.
- UOM is set per item and must be consistent across all transactions (PO, GRN, Requisition).
- Pack Size allows splitting (e.g., a Box of 100 Tablets — UOM is Tablet, Pack Size is 100).

## Tips & Frequently Asked Questions

### Standard Procurement Workflow (Quick-Start)

1. Check Stock List for items at or below reorder level.
2. Create a Purchase Order for the preferred supplier, using **Load Suggested Items**.
3. Submit the PO and await supplier delivery.
4. When goods arrive, create a GRN against the PO — scan barcodes, enter batch numbers and expiry dates.
5. Post the GRN → stock levels update automatically.
6. Fulfil pending approved requisitions by picking from the updated stock.

### Common questions

- **An item is not appearing when I search in a Requisition or GRN.** — The item must first be added to the Inventory Items catalogue with `IsActive = true`.
- **Stock quantity is wrong after a GRN.** — Verify that the GRN was posted (not just saved as draft). Posted GRNs show a green **Posted** badge.
- **The batch scanner is not working.** — Try switching between Camera and USB Scanner modes. Ensure the browser has camera permission if using camera mode.
- **I cannot approve a stock adjustment.** — Only ADMIN, INVMGR, and FINAPPROV roles can approve adjustments.
- **How do I remove expired stock properly?** — Create a Stock Adjustment with type **Expiry Write-Off**, listing the expired batches with negative quantities.
- **A PO is showing Partially Received but all goods were delivered.** — Open the PO and create a GRN for the remaining outstanding quantity.
- **A controlled substance entry was made in error.** — You cannot delete CS entries. Add a correction Adjustment entry with a clear explanatory note.

> **Tip:** Run a Physical Stock Audit at least monthly (Spot Check) and annually (Full Audit) to keep system quantities aligned with physical reality and satisfy regulatory requirements.

> **Warning:** Do not adjust stock directly without proper documentation. All reductions should be traceable to a GRN, Requisition Fulfilment, Expiry Write-Off, or Physical Count Adjustment.
