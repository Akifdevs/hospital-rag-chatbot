# Corporate Billing

**Subtitle:** Step-by-step guide for managing corporate billing cycles — from draft creation to payment collection  
**Version:** 1.0  
**Last updated:** March 2026

## Overview

Corporate Billing handles monthly consolidated invoices for corporate payers (companies, employers, group clients). Instead of collecting payment per visit, all corporate-covered invoices for a billing period are grouped into a single Billing Cycle that is reviewed, approved, and sent to the corporate client for payment.

### Key concepts

- **Billing Cycle** — A bundle of all corporate invoices for one payer in one billing month.
- **Corporate Invoices** — Invoices generated with type “CORPORATE” in the Billing Queue.
- **Billing Month** — The calendar month for which services are being billed.
- **Cut-off Date** — An optional date within the month; only invoices up to this date are included.
- **Payable Amount** — Net amount after discounts, plus applicable taxes (VAT).

### Lifecycle at a glance

1. **Create Draft** — Select corporate payer and billing month.
2. **Review & Edit** — Add or remove invoices from the draft.
3. **Submit for Approval** — Generate reports and send for approver review.
4. **Approval** — Approver reviews, approves or rejects.
5. **Send to Corporate** — Email consolidated invoice to corporate client.
6. **Mark as Paid** — Record incoming payment with reference number.

> **Tip:** Corporate invoices must first be created in the Billing Queue (CORP- prefix). Only after an invoice is generated with type “CORPORATE” will it appear as available in a billing cycle.

## Billing Cycle Statuses

Each billing cycle moves through a defined set of statuses. Understanding them helps you act at the right stage.

| Status | Colour | Meaning | Who can act |
|---|---|---|---|
| **DRAFT** | Gray | Cycle created; invoices can still be added or removed. | Billing |
| **GENERATED** | Blue | Submitted for approval; awaiting review. | Approver (BCOORD, BRANCHMGR, FINANCEMGR, ADMIN) |
| **APPROVED** | Purple | Approved and ready to be sent to the corporate client. | Billing |
| **REJECTED** | Red | Returned for corrections; invoices can be edited and re-submitted. | Billing |
| **SENT** | Orange | Invoice emailed to corporate; awaiting payment. | Billing |
| **PAID** | Green | Payment received and recorded. | Billing |

> **Roles:** Only BILLING and ADMIN roles can create drafts, manage invoices, send, and mark paid. BCOORD, BRANCHMGR, FINANCEMGR, ADMIN, and SUPERADMIN can approve or reject.

## Creating a New Billing Cycle

A billing cycle is created as a DRAFT first, so you can review and adjust the included invoices before submitting.

1. Click **New Billing Cycle** (top-right of Corporate Billing page).
2. Select the Corporate Payer from the dropdown. The list shows payer name, code, and billing email.
3. Choose the Billing Month by selecting a Month and Year. Future months are disabled.
4. Optionally set a Cut-off Date — only invoices on or before this date will be included.
5. Click **Create Draft & Preview**. The system shows a preview of how many invoices were found and the total amount.

> **One cycle per month:** Only one billing cycle per payer per month is allowed. If a cycle already exists for that month, the system rejects creation with a “409 Conflict” error.

> **Cut-off date:** If a cut-off date is not provided, all corporate invoices for the entire billing month are automatically included.

## Managing Draft Invoices

While a cycle is in DRAFT or REJECTED status, you can add or remove individual invoices. Open the billing cycle by clicking **View** to go to the Billing Cycle Detail page.

### Add invoices

1. On the Billing Cycle Detail page, click **Add** in the action bar.
2. A modal lists all available corporate invoices for this payer that are not yet in any cycle.
3. Use the checkboxes to select one or multiple invoices. Use the header checkbox to select all.
4. Click **Add Selected**. The selected invoices are added to the cycle and totals recalculate.

### Remove invoices

1. In the **Included Invoices** table, find the row you want to remove.
2. Click the red × icon in the Actions column.
3. Confirm the removal in the dialog. The invoice returns to the available pool.

### View line items

Click the item count button (e.g., “3 ▼”) in the Items column to expand a row and see each individual service line with CPT code, quantity, unit price, discount, VAT rate, and net amount.

> Adding and removing invoices is only possible when the cycle is in DRAFT or REJECTED status.

## Submitting for Approval

Once you are satisfied with the included invoices, submit the cycle for approval. This action is available to BILLING roles.

1. Open the billing cycle detail page.
2. Click **Submit for Approval** (shown when status is DRAFT) or **Re-submit for Approval** (when REJECTED).
3. The system generates the consolidated reports and moves the cycle to GENERATED status.
4. A blue banner appears in the detail page confirming the cycle is awaiting review.

After submitting, the cycle status changes to **GENERATED (Pending Approval)** and approvers are notified.

On the Corporate Billing list page, GENERATED and APPROVED cycles count towards the **Pending Approval** summary card.

## Approval Process

Approvers (BCOORD, BRANCHMGR, FINANCEMGR, ADMIN, SUPERADMIN) review the billing cycle and either approve or reject it.

### Open the Approval modal

- **From the list page:** Click **Review** or **Approve** in the Actions column for a GENERATED cycle.
- **From the detail page:** Click **Approve / Reject** in the action bar, or the quick **Review & Approve** button in the blue banner.

### Approve

1. Review the cycle summary: corporate name, billing period, total amount.
2. Check the Prior Approval History if applicable.
3. Select the **Approve** radio button.
4. Optionally add comments.
5. Click **Approve Cycle**. Status moves to APPROVED.

### Reject

1. Select the **Reject** radio button.
2. Choose a Reason for Rejection from the dropdown:
   - Calculation Error
   - Missing Invoices
   - Incorrect Dates
   - Duplicate Invoices
   - Policy Violation
   - Needs Additional Documentation
   - Other
3. Enter mandatory Comments explaining what needs to be corrected.
4. Click **Reject & Return**. Status reverts to REJECTED.

When rejected, the billing team sees a red banner in the detail page showing the rejection reason and comments. They can edit invoices and re-submit.

## Handling Rejections

A rejected cycle is returned to BILLING for corrections. The rejection reason and approver comments are visible as a red banner at the top of the detail page.

1. Read the rejection reason and comments in the red banner.
2. Click **Edit Invoices** to add or remove invoices as needed.
3. Review the financial summary to confirm the corrected total.
4. Click **Re-submit for Approval** to send the corrected cycle back for review.

> **Tip:** All previous approval and rejection events are preserved in the Workflow Audit Log on the detail page — useful for internal accountability.

## Sending Invoice to Corporate

Once approved, a BILLING user sends the consolidated invoice to the corporate client via email.

1. Open the billing cycle detail page (status must be APPROVED).
2. Click **Send to Corporate** (in the purple approval banner or the action bar).
3. The email form pre-fills with the corporate contact email, a subject line, and a body that includes the total amount and invoice count.
4. Adjust recipients — separate multiple addresses with commas.
5. Edit the subject and message body as needed.
6. Click **Send & Mark as Sent**. The system emails the invoice and moves the cycle to SENT status.

> **Note:** The corporate contact email is pulled from the payer profile. Always verify it is current before sending.

> **Resend:** If you need to resend (e.g., recipient changed), open a SENT cycle and click **Resend** in the action bar.

## Recording Payment (Mark as Paid)

When the corporate client pays, record the payment to close the cycle.

1. Open the billing cycle detail page (status must be SENT).
2. Click **Mark Paid** in the action bar.
3. Enter the Payment Reference (bank transfer ref, cheque number, etc.) — optional but recommended.
4. Add any Remarks about the payment — optional.
5. Click **Confirm Payment**. The cycle moves to PAID status.

Paid cycles contribute to the **Paid This Month** total on the Corporate Billing summary cards.

> **Important:** Once marked as PAID, the cycle is closed. If a reversal is needed, contact a Finance Manager or Admin.

## Documents & Reports

Several downloadable documents are available from the billing cycle detail page.

| Document | Button | Description | Available when |
|---|---|---|---|
| Tax Invoice (PDF) | **Tax Invoice** | Formal A4 tax invoice with TRN, itemised totals, and VAT breakdown. | Any status |
| Statement of Invoices | **View Statement** | Landscape A4 HTML print-ready statement with all patient rows, gross/discount/VAT/total columns. | Any status with invoices |
| Consolidated PDF | **PDF** | Pre-generated consolidated report PDF. | When generated by system |
| Detailed Excel | **Excel** | Excel breakdown of all included line items. | When generated by system |

### Download the Tax Invoice

1. Click **Tax Invoice** in the action bar.
2. Wait for “Generating…” to complete — the PDF is downloaded automatically.
3. The file is named `TaxInvoice-[CorporateName]-[Month-Year].pdf`.

### View the Statement of Invoices

1. Click **View Statement**. A new browser tab opens with the A4 landscape statement.
2. Click **Print / Save as PDF** inside the tab.
3. In the print dialog, set Orientation to Landscape and Paper Size to A4.

> If the statement popup is blocked, allow pop-ups for this site in your browser settings.

## Financial Summary

The Financial Summary panel on the detail page shows a breakdown of how the payable amount is calculated.

| Line | Description |
|---|---|
| Gross Amount | Sum of all invoice gross amounts before any discounts. |
| Discounts | Total discount applied across all invoices (shown as negative). |
| Tax (VAT) | Total VAT/tax across all invoices. |
| Final Payable | Net amount due from the corporate client = Gross − Discounts + Tax. |

The **Final Amount** displayed in the cycle header and summary cards uses the same Final Payable value.

## Workflow Audit Log

The Workflow Audit Log (right side of the detail page) records every significant event in the cycle's life, providing a full audit trail.

| Event | Icon colour | Details shown |
|---|---|---|
| Cycle Created | Blue | Creator name and timestamp. |
| Submitted for Approval | Indigo | Submitter name and timestamp. |
| Approved | Green | Approver name, timestamp, and optional comments. |
| Rejected | Red | Approver name, timestamp, comments, and rejection reason. |
| Invoice Sent | Orange | Recipient email and timestamp. |
| Payment Received | Green | Payment reference and timestamp. |

> **Tip:** All approval history entries are also visible in the Approval modal before submitting a new decision.

## Corporate Billing List Page

The main Corporate Billing page lists all billing cycles with filtering, sorting, and quick actions.

### Summary cards

- **Draft Bills** — Cycles currently in DRAFT state.
- **Pending Approval** — Cycles in GENERATED or APPROVED state.
- **Sent & Unpaid** — Cycles in SENT state (invoice delivered but payment not received).
- **Paid This Month** — Total AED value of cycles paid in the current calendar month.

### Filtering

Click the Filter icon to reveal advanced filters: free-text search, date range, corporate payer, status, and billing month.

### Table actions

| Button | Available when | Action |
|---|---|---|
| **View** | Always | Open the detail page for the cycle. |
| **Generate** | DRAFT + BILLING role | Submit cycle for approval from the list directly. |
| **Review / Approve** | GENERATED + Approver role | Opens the approval modal. |
| **Docs** | GENERATED or APPROVED | View/download generated documents. |
| **Mark Paid** | SENT + BILLING role | Opens the status update modal to mark PAID. |
| **PDF** | When PDF is generated | Download the consolidated PDF. |

> **Tip:** Use **Export** to download the current list to CSV for reporting purposes.

## Role Reference

Access to corporate billing actions is controlled by the user's role code.

| Role | Code | Permissions |
|---|---|---|
| Billing Staff | BILLING | Create, manage, submit, send, mark paid. |
| Branch Coordinator | BCOORD | Approve or reject. |
| Branch Manager | BRANCHMGR | Approve or reject. |
| Finance Manager | FINANCEMGR | Approve or reject. |
| Admin | ADMIN | Full access — both billing and approval. |
| Super Admin | SUPERADMIN | Full access — both billing and approval. |

> If an action button is not visible (e.g., **Approve**), your role may not have the required permission. Contact your Administrator.

## Tips & Frequently Asked Questions

### Quick-start checklist

1. Ensure all corporate invoices for the month are generated in the Billing Queue with type “CORPORATE”.
2. Create a new Draft Billing Cycle for the payer and billing month.
3. Review included invoices — add any missing ones, remove duplicates.
4. Submit for approval. Notify the approver.
5. Approver reviews and approves. Billing sends the invoice email.
6. When payment arrives, mark the cycle as Paid with the payment reference.

### Common questions

- **I cannot find an invoice in the “Add Invoices” modal.** — The invoice may already be included in another billing cycle for the same payer, or it may not be a CORPORATE-type invoice. Check the Billing Queue.
- **The “Submit for Approval” button is missing.** — This is only shown when the cycle is in DRAFT status and you have a BILLING role.
- **Can I edit invoices after submitting?** — No. You must wait for the approver to review and reject the cycle, which will return it to REJECTED status for editing.
- **The Tax Invoice download shows an error.** — Ensure the billing cycle has at least one included invoice and the branch details (TRN, address) are configured.
- **Can two people approve the same cycle?** — The system records all approval events, but the status change happens on the first APPROVE action.

> **Warning:** Never delete a billing cycle that has been sent to the corporate client. If cancellation is needed, consult your Finance Manager to ensure proper documentation.
