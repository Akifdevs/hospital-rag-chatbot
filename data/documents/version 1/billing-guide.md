# Billing & Invoicing

**Subtitle:** From service ordering to payment collection — complete workflow guide  
**Version:** 2.0  
**Last updated:** Mar 2026

## Overview

The Billing & Invoicing module manages the complete financial lifecycle of a patient visit — from the moment a doctor orders a service, through invoice generation, right through to payment collection and reconciliation.

### Billing lifecycle

1. **Service Ordering** — Doctor orders lab, radiology, or procedure services from the consultation screen.
2. **Invoice Estimation** — Billing staff review ordered services, add extra services if needed, apply discounts, and generate invoices.
3. **Manual Billing** — Direct cash billing for walk-in patients without a consultation (e.g. lab-only visits).
4. **Payment Collection** — Cash, insurance claim, or corporate billing is completed and the invoice is settled.

### Billing modes

| Mode | How it works |
|---|---|
| **Cash** | Patient pays directly. |
| **Insurance** | Copay is collected from the patient; the balance is claimed from the insurer. |
| **Corporate** | Services are billed to an employer/corporate entity under a contract. |

## Billing Queue

The Billing Queue is the main landing screen for all billing staff. It lists every patient visit that has billing activity for the selected date range.

### Filters and search

| Filter | Options | Purpose |
|---|---|---|
| **Period** | Today / Yesterday / This Month / Custom dates | Narrow the list to a specific date range. |
| **Billing Status** | ALL / Draft / In Progress / Fully Settled / Cancelled | Filter by invoice lifecycle stage. |
| **Doctor** | Dropdown of active doctors | Show only visits for a specific doctor. |
| **Department** | Dropdown of departments | Show only visits from a department. |
| **Insurance** | Dropdown of insurance companies | Show only insurance-covered visits. |
| **Search** | Free text | Search by patient name, MRN, or invoice number. |

### Queue columns

| Column | What it shows |
|---|---|
| Patient Information | Full name, MRN, advance balance available (💰), total outstanding (📋), and credit status warnings. |
| Visit Date | Date of the visit. |
| Doctor & Department | Treating doctor and their department. |
| Insurance & Amount | Insurance company (or “Cash Patient”), total invoice amount, advance that can be applied, and net due. |
| Unbilled | Number of services not yet included in any invoice. A red badge means action is needed. |
| Invoices | Clickable invoice badges: 🔵 Cash (CSH-), 🟠 Insurance (INV-), 🟣 Corporate (CORP-). |
| Actions | 📄 Estimate/Invoice button, 💲 Advance payment, 🔔 Patient notes. |

### Invoice badge examples

| Example | Meaning |
|---|---|
| `CSH-12345` Unpaid | Cash invoice, unpaid (blue). |
| `CSH-12345` ✓ Paid | Cash invoice, paid (green). |
| `CSH-12345` ✕ Cancelled | Cash invoice, cancelled (red). |
| `INV-12345` Insurance | Insurance invoice (orange). |
| `CORP-12345` Corporate | Corporate invoice (purple). |

### Advance balance indicator

If a patient has an advance on file, the queue shows **💰 Available: AED X.XX** in green. The **💡 Can Apply: AED X.XX** indicator shows how much advance can offset the current visit's invoice.

## Service Ordering (Consultation)

Services are typically ordered by a doctor from the Consultation screen. The Service Order Modal supports Lab, Radiology, and Procedure services, and is aware of the patient's payment mode (Cash, Insurance, or Corporate).

### Open the Order Modal

1. From the active consultation, scroll to the **Service Orders** section.
2. Click **+ Add Orders** to open the Service Order Modal.
3. The modal shows the patient's payment mode at the top (Cash / Insurance / Corporate).

### Three ways to add services

| Tab | Use when… | How it works |
|---|---|---|
| **Search** | You know the service name or CPT code. | Type in the search box; results load automatically. Filter by All / Lab / Radiology / Procedure. |
| **Packages** | Patient is enrolled in a bundled package. | Expand a package to see included services, then click **Order Package**. |
| **Order Sets** | You want to order a pre-defined group of services in one click. | Search order sets, expand to preview services, then click **Order Set**. |

### Select services from Search

1. Tick the checkbox next to each service you want to order.
2. Adjust **Quantity** if more than 1 unit is needed.
3. Optionally add **Urgency** (Routine / ASAP / Urgent / STAT) and clinical notes.
4. Use **Favorites** (❤️ icon) to browse saved service shortcuts by folder.
5. The running **Selected Services** tray at the bottom shows your cart.
6. When ready, click **Order Services**.

### Pricing by payment mode

| Mode | Price used | Coverage type set | Copay |
|---|---|---|---|
| Cash | Cash list price (`GrossPrice`) | Cash | None |
| Insurance | Insurance pricelist price | Covered or PreAuthRequired | Calculated from copay % |
| Corporate | Corporate contract price | Covered | None — billed to corporate |

### Pre-Authorisation (PreAuth) services

If a service requires pre-approval by the insurer (marked `PreAuth = true` in the pricelist), its `InsuranceCoverType` is set to **PreAuthRequired** and its status to **PreAuth Pending**. These services **cannot be invoiced** until authorisation is approved. See [Pre-Auth → Cash Conversion](#pre-auth--cash-conversion) for conversion after denial or expiry.

### Pre-Approval Limit Check

If the patient's insurance policy has a `PreApprovalLimit`, the system checks whether the cumulative insurance price of all orders (existing + new) will exceed that limit. If it does, a warning dialog appears showing **Current total / Adding / New total / Limit**.

- Click **Continue & Mark for Pre-Auth** — orders are saved and all Covered services on this consultation are automatically set to PreAuthRequired.
- Click **Cancel** — no orders are saved; reduce the selection and retry.

### Insurance Liability Limit Check

If the patient's policy has a maximum liability cap, a second check is applied. If the total estimated insurance payable exceeds the cap, a warning shows the overage amount.

- Click **Convert to Cash** — all insurance services in this order are saved as Cash instead.
- Click **Keep as Insurance** — services are saved as normal (useful when partial coverage is still valid).

### Force-as-Cash Override

On any Insurance or Corporate visit, a doctor can force individual services to be billed as cash (doctor override). The saved order note is automatically prefixed with `** FORCED AS CASH - Doctor Override **` for audit purposes.

## Service Orders Panel

After services are ordered, they appear in the **Service Orders** panel on the consultation screen, grouped by type: Investigations (Lab), Radiology, and Procedures.

| Column | Meaning |
|---|---|
| CPT Code | Standard clinical procedure code. |
| Internal Code | Facility's own service code. |
| Service | Service name. |
| Type | Badge: Lab / Radiology / Procedure / Package. |
| Qty | Quantity ordered. |
| Price | Gross unit price (hidden for Doctors if configured). |
| Co-Pay | Patient portion for insurance visits (hidden for cash visits). |
| Ordered | Who ordered it and when (relative time). |
| Status | Pending / In Progress / Completed. |
| Coverage | Covered / Cash / PreAuthRequired / Corporate. |
| Actions | 🗑 Delete (if eligible) / 🔁 Repeat / 📄 View Report / 🔬 View Lab Result. |

### Repeated orders

If the same service was ordered on a previous visit, a 🔁 **Repeat** badge appears on the row. Click the repeat icon to quickly re-order it with the same parameters.

### Deleting orders

Orders can only be deleted if they have not yet been invoiced and the user has delete permissions. Once an invoice is generated for a service, the service can no longer be removed from the order list.

## Invoice Estimation

The Invoice Estimation screen is the billing staff's primary workspace. Access it from the Billing Queue by clicking the 📄 **Estimate/Invoice** button on any patient row.

### What the screen shows

- **Visit Information** — Patient name, MRN, visit date, payment mode, doctor, insurance/corporate details.
- **Services Table** — All ordered services with checkboxes, coverage type, price, quantity, discount, and status.
- **Packages** — Any enrolled packages listed separately with their bundled price.
- **Financial Summary** — Gross total, discounts, copay, patient payable, insurance payable.
- **Copay Calculator** — Expandable panel for insurance visits showing deductibles and copay breakdown.

### Service coverage badges

| Coverage type | Badge color |
|---|---|
| Covered | Green |
| Cash | Blue |
| PreAuthRequired | Orange |
| Corporate | Purple |

### Which services can be invoiced?

| Coverage type or state | Invoiceable? | Condition |
|---|---|---|
| Cash | Yes | Always. |
| Covered | Yes | Always. |
| Corporate | Yes | Always. |
| PreAuthRequired | Only if authorised | Must have an **Authorization Number** and status = Approved or Partially Approved. |
| Already invoiced | No | Service is greyed out and checkbox is disabled. |

### Select or deselect services for an invoice

1. Tick or untick individual service checkboxes.
2. Use **Select All** to tick all invoiceable services in one click.
3. Package checkboxes toggle the entire package for invoicing.
4. The **Financial Summary** panel updates in real time as you change the selection.

### Add extra services

1. Click **+ Add Services** in the estimation header.
2. A service selection panel (same as Manual Billing) slides open below.
3. Search by name or browse Order Sets and Packages.
4. Select services and click **Add to Visit** — they are saved as patient orders and refresh the estimation.
5. Newly added services appear in the table and can be immediately included in the invoice.

> **Same-day restriction:** Additional services can only be added if the visit was created **today** (or within the allowed billing window configured for your branch). Older visits are read-only for service additions.

## Applying Discounts

Discounts can be applied at two levels — per individual service line item, or at the entire invoice level. Discount permissions are role-controlled.

### Item-level discount

1. Click the discount icon (🏷️) next to any service row.
2. Choose **Discount Type**: Percentage or Fixed Amount.
3. Choose **Calculation Base**: Applied Price (net price) or Gross Price.
4. Enter the discount value and optional remarks.
5. Click **Apply** — the discounted price shows immediately in the row.

### Invoice-level discount

1. Click **Invoice Discount** in the financial summary panel.
2. Choose **Percentage** (e.g. 10%) or **Fixed Amount** (e.g. AED 50).
3. The discount is applied after all item-level discounts are summed.
4. The **Final Total** line in the summary reflects both discount layers.

> **Cash-only restriction:** Discounts are only available for **Cash** invoice items. Insurance and corporate services follow contracted pricing and cannot be manually discounted from this screen.

### How the totals are calculated

| Field | Formula |
|---|---|
| Gross Amount | Sum of all selected service gross prices × quantity. |
| Item Discounts | Sum of all individual service discounts. |
| Subtotal after items | Gross Amount − Item Discounts. |
| Invoice Discount | Applied as % or fixed amount on subtotal. |
| Final Total | Subtotal − Invoice Discount. |
| Copay (Insurance) | Sum of patient copay portions for covered services. |
| VAT | Applied for corporate visits where VAT is not exempt. |

## Pre-Auth → Cash Conversion

When a pre-authorisation request is denied by the insurer, the service can be converted to a cash payment so the patient can still be billed.

1. In the Invoice Estimation screen, locate the service with the **PreAuthRequired** badge.
2. If the authorisation was denied (or expired), a **Convert to Cash** button (🔄) appears on the row.
3. Click the button; a confirmation dialog appears.
4. Enter optional **Remarks** explaining the reason (e.g. “Pre-auth denied by insurer”).
5. Click **Confirm** — the service's coverage is changed to Cash and the full cash price applies.

> **Audit trail:** The conversion is logged with the user identity, timestamp, and any remarks entered, providing a complete audit trail for insurance disputes.

## Generating an Invoice

Once the services are reviewed and discounts applied, click **Generate Invoice** (or **Update Invoice** if one already exists) in the estimation footer.

### What happens when an invoice is generated

1. The system identifies which selected services are **Regular** (Cash + Insurance) and which are **Corporate**.
2. If the visit is a Corporate visit, all selected services and packages route to a **Corporate Invoice**.
3. If there is a mix of regular and corporate services, two separate invoices are created simultaneously.
4. Each invoice gets a unique number: **CSH-XXXXX** (Cash), **INV-XXXXX** (Insurance), or **CORP-XXXXX** (Corporate).
5. After successful creation, the estimation refreshes and the Billing Queue is updated.
6. The system automatically opens the appropriate invoice print/payment modal for the first created invoice.

### Invoice types by payment mode

| Visit type | Invoice type created | Invoice prefix | API endpoint |
|---|---|---|---|
| Cash visit | Cash Invoice | CSH- | `/api/billing/create` |
| Insurance visit | Insurance Invoice | INV- | `/api/billing/create` |
| Corporate visit | Corporate Invoice | CORP- | `/api/billing/create-corporate` |
| Mixed (Ins + Corporate) | Both types | Both | Both endpoints called in parallel. |

> **Corporate invoice confirmation:** For Corporate and mixed-type visits, a confirmation dialog appears listing the number of corporate items and the corporate entity name before the invoice is created. Review and click **Continue** to proceed.

### Update versus Generate

If a **Draft** invoice already exists for the visit, the button reads **Update Invoice**. New unbilled services are appended to the existing invoice rather than creating a duplicate.

## Manual Billing

Manual Billing is used for walk-in patients who need direct cash billing **without** going through a doctor's consultation (e.g. returning for a lab test only). It is always **Cash only**.

### Access Manual Billing

1. From the Billing Queue header, click **+ Manual Billing**.
2. A four-step wizard opens.

### Step 1 — Patient

1. Search for an existing patient by **MRN**, **Mobile Number**, or **Name** (minimum 2 characters).
2. Click the patient from the results list to select them — a green confirmation card appears.
3. If the patient is not in the system, click **New Patient** to open the quick-registration form and enter their details.
4. Click **Next** to proceed.

### Step 2 — Orders

1. Search for services by name or CPT code in the **Services** tab.
2. Filter by type (Lab / Radiology / Procedure) using the filter buttons.
3. Browse the **Order Sets** tab for pre-defined bundles of services.
4. Browse the **Packages** tab for bundled packages.
5. Use the **Favorites** panel (❤️) to access saved service shortcuts.
6. Adjust quantities using the + / − buttons in the selected services tray.
7. Click **Next** when all services are added.

### Step 3 — Invoice

1. The system creates a **ManualBilling** visit under a default department.
2. All services are saved as patient orders at **Cash price**.
3. A cash invoice is automatically generated showing the itemised breakdown.
4. Review the invoice preview.
5. Click **Save & Generate Invoice** to finalise.

### Step 4 — Done

1. A success confirmation screen is shown.
2. Click **Print Invoice** to print or **Complete & Return** to go back to the Billing Queue.

> **Cash only:** Manual Billing always uses cash pricing. Insurance and corporate billing are not available in this workflow. For insurance patients, use the standard visit + consultation + invoice estimation pathway.

## Payment Collection

After an invoice is generated, payment can be collected directly from the Billing Queue.

### Open the Payment Modal

1. In the Billing Queue, click the invoice badge (e.g. **CSH-12345**) for the patient.
2. The corresponding invoice print/payment modal opens.
3. Alternatively, immediately after generating an invoice from the estimation screen, the system automatically opens the payment modal.

### Collect an advance payment

1. Click the 💲 **Advance** button (green/blue dollar icon) in the Actions column.
2. Enter the advance amount the patient is paying.
3. Select payment method (Cash, Card, Bank Transfer).
4. Click **Collect Advance** — the advance receipt is created.
5. The Billing Queue now shows **💰 Available: AED X.XX** on the patient row.
6. When an invoice is later generated, the available advance is shown and can be applied to reduce the patient's outstanding balance.

### Pay a cash invoice

1. Open the Cash Invoice modal by clicking the CSH- badge.
2. Review itemised services and total.
3. Click **Collect Payment**.
4. Choose payment method: Cash / Card / Bank Transfer / Apply Advance.
5. Enter the amount and confirm.
6. Invoice status changes to **PAID** and the badge turns green (✓).

### Insurance invoice

For insurance visits, the invoice shows the **patient copay portion** and the **insurance claim amount** separately. Billing staff collect copay from the patient, and the insurance claim amount is submitted to the insurer separately.

### Corporate invoice

Corporate invoices are billed directly to the corporate entity. The purple CORP- badges represent these invoices. Payment is tracked against the corporate account and reconciled periodically.

## Refunds & Cancellations

### Cancel an invoice

1. Open the invoice modal from the Billing Queue.
2. Click **Cancel Invoice** (requires cancel permission).
3. In the Cancel Invoice confirmation modal, enter the cancellation reason.
4. Click **Confirm Cancellation**.
5. The invoice badge changes to **✕ Cancelled** (red) in the queue.
6. Services linked to the cancelled invoice are freed — they can be re-invoiced.

### Create a refund

1. Open the paid invoice modal.
2. Click **Refund** — the Refund Request Modal opens.
3. Select the services or items to be refunded and enter the refund reason.
4. Click **Submit Refund Request**.
5. A **↩** symbol appears on the invoice badge in the queue to indicate a refund was processed.

> **Permissions required:** Cancellation and refund actions require specific role permissions. If the buttons are not visible, contact your branch manager or system administrator.

## Status Reference

### Invoice status

| Status | Meaning | Badge color |
|---|---|---|
| **DRAFT** | Invoice created but not yet fully paid. | Gray 📝 |
| **PAID** | Full payment collected. | Green ✓ |
| **CANCELLED** | Invoice voided — services can be re-invoiced. | Red ✕ |
| **PARTIALLY PAID** | Some payment collected, balance outstanding. | Blue |

### Service/order status

| Status | Meaning |
|---|---|
| **Pending** | Ordered, awaiting processing. |
| **In Progress** | Being processed (lab running, scan in progress). |
| **Completed** | Service fully rendered and result available. |
| **PreAuth Pending** | Waiting for insurer pre-authorisation. |
| **Cancelled** | Order cancelled. |

### Insurance coverage type

| Type | Meaning | Billing impact |
|---|---|---|
| **Covered** | Insurance will pay contracted price. | Copay collected from patient. |
| **Cash** | Patient pays full price. | Full cash price billed. |
| **PreAuthRequired** | Needs insurer approval before service. | Cannot invoice until approved. |
| **Corporate** | Billed to employer/corporate entity. | No patient payment; billed to corporate. |

## Tips & FAQs

### Frequently asked questions

- **Why is a service greyed out in the estimation screen?** — The service has already been invoiced in a previous invoice for this visit.
- **Why can't I invoice a PreAuthRequired service?** — It needs an authorisation number from the insurer with Approved or Partially Approved status. Contact the pre-auth team.
- **Can I add services after the invoice is generated?** — Yes. Use **+ Add Services** in the estimation screen to add new orders, then click **Update Invoice**.
- **The patient's advance isn't being applied. What do I do?** — Advances must be manually applied during the payment collection step. Open the invoice and choose **Apply Advance** as the payment method.
- **The doctor doesn't see the Price or Co-Pay columns.** — These are hidden for Doctor roles by the `REACT_APP_DOCTOR_CAREBOARD_SHOWPRICE` configuration flag.
- **I need to bill an insurance patient for a service at cash price.** — Use the **Force as Cash** toggle in the Service Order Modal before ordering the service.

### Refresh the queue

After making changes (generating invoices, collecting payments), click the 🔄 **Refresh** button in the Billing Queue header to reload the latest data.

### Bulk ordering with Order Sets

Order Sets let you order groups of commonly-ordered services in a single click. They are defined per branch and cover common clinical pathways (e.g. “Cardiac Workup”, “Pre-op Blood Panel”). Both the Service Order Modal and the Invoice Estimation's Add Services panel support Order Sets.

### Complete billing workflow in five steps

1. Doctor orders services in Consultation.
2. Billing staff opens Invoice Estimation from the queue.
3. Review services, add any missing items, and apply discounts.
4. Click **Generate Invoice**.
5. Collect payment in the invoice modal that opens automatically.
