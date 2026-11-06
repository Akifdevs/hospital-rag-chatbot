# Radiology Module

**Subtitle:** Manage imaging orders, write reports, dispatch results  
**Version:** 2.0  
**Last updated:** Mar 2026

## Introduction

The Radiology Module manages the complete lifecycle of imaging service orders — from a clinician placing an order right through to a signed report being formally dispatched to the referring doctor.

### What you can do in this module

- View and manage all radiology orders for your department.
- Write and auto-save diagnostic reports using a rich-text editor.
- Dictate findings using Voice-to-Text (microphone button).
- Finalize and electronically sign reports (Radiologist).
- Dispatch signed reports — PDF is automatically generated and stored under the patient record.
- Maintain a complete amendment history for corrections to dispatched reports.
- Track workload with live stats cards and modality-specific filters.

## Roles & Permissions

Your role determines which actions and buttons are visible. If a button is missing, you do not have permission for that action — contact your system administrator.

### Permission matrix by role

| Action | Radiographer | Radiologist |
|---|---|---|
| Write & save Draft report | ✅ Yes | ✅ Yes |
| Mark report as Final (sign) | ❌ No | ✅ Yes |
| Dispatch report | ❌ No | ✅ Yes |
| Unlock a Final report | ✅ Yes | ✅ Yes |
| Amend a Dispatched report | ❌ No | ✅ Yes |
| Preview / View PDF | ✅ Yes | ✅ Yes |
| Schedule appointments | ✅ Yes | ✅ Yes |

> **Note:** Radiographers can **unlock** a final (but not yet dispatched) report to fix mistakes. Only a Radiologist can re-finalize and dispatch it.

## Dashboard Overview

### Stats Cards

Four clickable summary cards at the top give you an instant overview of today's workload. Click any card to filter the table to that group.

| Card | What it counts | Clicking filters to… |
|---|---|---|
| 🔴 Urgent Today | Urgent-priority orders placed today | Urgent orders |
| 🟡 Pending | Orders not yet started | Pending orders |
| 🔵 In Progress | Orders currently being processed | In-progress orders |
| 🟢 Completed Today | Orders fully completed today | Today's completed orders |

### Modality Filter Pills

Quick-filter buttons below the stats cards narrow the list by imaging type. The active filter is highlighted in purple.

Available modality filters: **All**, **X-Ray**, **CT**, **MRI**, **Ultrasound**, **Mammography**, **DEXA**, **Nuclear**, and **Interventional**.

### Period Quick-Select

| Button | Date range shown |
|---|---|
| Today (default) | Today only |
| Yesterday | Yesterday only |
| Last Week | Last 7 days including today |

### Priority Icons in the Table

| Icon | Colour | Urgency |
|---|---|---|
| ⚡ | Red | STAT — Act immediately |
| ⚠️ | Orange | Urgent |
| ⚠️ | Yellow | ASAP |
| 🕐 | Green | Routine |

## Radiographer Workflow

**Who this section is for:** Radiographers — role codes **RADIOGRAPHER** or **RADGRAP**.

### Step 1 — Find your orders

1. Open the **Radiology** module.
2. The list defaults to **Today** — use **Last Week** to catch up on older orders.
3. Use the modality pills (e.g. **X-Ray**) to narrow the list to your workstation.
4. Look for orders with status **Scheduled** or **In Progress**.

### Step 2 — Schedule or confirm an appointment

1. In the **Status** column, click the 📅 calendar icon next to *Pending* or *Scheduled* orders.
2. The Appointment Scheduler opens, pre-filled with the patient and Radiology department.
3. Select date, time, and room, then click **Confirm Appointment**.
4. The order status updates to **Scheduled** and the time appears in the row.

### Step 3 — Mark exam as In Progress

1. Select one or more orders using the checkboxes on the left.
2. Use the **Bulk Status Update** control to set status to **In Progress**.

### Step 4 — Write the draft report

1. Click the ✏️ **Edit Report** button in the Actions column. Blue = no report yet; Green = report exists.
2. Fill in the **Report** text area with your findings.
3. Optionally fill in **Impression** and **Recommendations** sections.
4. The status selector shows **📝 Draft** — keep it as Draft.
5. Click **Save Draft** or wait 30 seconds for auto-save.
6. The *"Last saved at HH:MM"* timestamp confirms the save.

#### Voice-to-Text

Click the 🎤 microphone icon in the toolbar to dictate your findings hands-free. Works best in Google Chrome.

#### Templates

Select a template from the dropdown to insert pre-structured text for common studies (e.g. Chest X-Ray, Abdominal Ultrasound). Tokens like **{{PATIENT_NAME}}** are replaced automatically.

### Step 5 — Unlock a Final report (if correction needed)

1. Open the finalized report. It shows a green *"Report Finalized — Awaiting Dispatch"* banner.
2. Click the 🔓 **Unlock** button (orange, top-right area of the editor page).
3. The report reverts to **Draft** and becomes editable.
4. Make corrections, **Save Draft**, then notify the Radiologist to re-finalize.

> **Warning — Cannot unlock after dispatch:** Once a report is **Dispatched**, only a Radiologist can amend it. The Unlock button is not shown for Dispatched reports.

## Radiologist Workflow

**Who this section is for:** Radiologists — role codes **RADIOLOGY**, **RADIOLOGIST**, or **RAD**.

### Step 1 — Review the worklist

1. Open the **Radiology** module.
2. Filter the Status dropdown to **Reported** to see orders with completed drafts awaiting your review.
3. Optionally filter by modality to focus on your specialty (CT, MRI, etc.).

### Step 2 — Open and review the draft

1. Click the ✏️ **Edit Report** button.
2. Review all three sections: **Report**, **Impression**, **Recommendations**.
3. Edit directly in the rich-text editor as needed.
4. Click **👁 Preview** (purple button) to see how the printed PDF will look.

### Step 3 — Finalize & sign

1. In the status selector (top-left of editor), click **✅ Final**.
2. A yellow warning banner appears: *"Report will be electronically signed and cannot be modified."*
3. Click **Save Final**.
4. The system records your name and timestamp as signer, marks the order **Reported**, and sends a notification to the referring doctor.
5. A green *"Report Finalized — Awaiting Dispatch"* banner appears.
6. The **🚀 Dispatch** and **🔓 Unlock** buttons now appear.

### Step 4 — Dispatch the report

1. Click **🚀 Dispatch** in the editor button bar, *or* click the teal ✓ button in the order list row.
2. The system marks the order **Completed**, records the dispatch timestamp, and triggers PDF generation in the background.
3. The banner changes to teal: *"Report Dispatched — Read Only"*.
4. A teal 📄 View PDF button appears in the order list row.

> **PDF generated automatically:** You do not need to manually generate the PDF. It is created in the background immediately after dispatch and stored under the patient's clinical documents. When anyone clicks **View PDF**, the cached file is served instantly.

### Step 5 — Amend a dispatched report

1. Open the dispatched report (teal *"Report Dispatched"* banner).
2. Click **✏️ Amend** (orange button — visible to Radiologists only on Dispatched reports).
3. In the Amendment modal, enter a reason (recommended) and click **Unlock**.
4. A confirmation toast shows the amendment version number (e.g. *"Amendment v2 created"*).
5. Make corrections in the editor, then re-finalize and re-dispatch.

> **Important — Amendment history is permanent:** Every amendment creates an auditable snapshot of the original content (text, impression, recommendations, status, who changed it, and when). This history cannot be deleted.

## The Report Editor

The Report Editor contains three independent rich-text sections — Report, Impression, and Recommendations — each with its own formatting toolbar.

### Toolbar features

| Feature | Description |
|---|---|
| **B / I / U** | Bold, Italic, Underline |
| **H1 / H2** | Heading levels |
| **• / 1.** | Bullet and numbered lists |
| **Table** | Insert measurement or findings table |
| **🎤 Microphone** | Voice-to-text dictation — click to start, click again to stop |
| **Color / Highlight** | Text and background colours |
| **Align** | Left / Centre / Right alignment |

### Auto-Save

The system automatically saves your work as a Draft every **30 seconds**. The *'Last saved at HH:MM:SS'* timestamp at the top of the page confirms when the last save occurred. Auto-save only runs while the report is in Draft status.

### Templates

1. Select a template from the **Templates** dropdown at the top of the editor.
2. The template content inserts with placeholders automatically filled using patient and order data.
3. Review all pre-filled text and edit as required before saving.

#### Voice-to-Text tip

When you click 🎤, your browser asks for microphone permission. Allow it once and it remembers. Speak clearly and pause briefly between phrases for best recognition. Works in Google Chrome.

## Report Status Explained

| Status | Who sets it | Meaning | PDF saved? | Editable? |
|---|---|---|---|---|
| 📝 **Draft** | Radiographer or Radiologist | Work in progress | Preview only (not saved) | ✅ Yes |
| ✅ **Final** | Radiologist only | Signed, awaiting dispatch | Preview only (not saved) | ❌ Read-only |
| 🚀 **Dispatched** | Radiologist only | Released to referring doctor | ✅ Saved to patient record | ❌ Read-only |

### How this maps to the Order Status

| Report Status | Order Status becomes |
|---|---|
| Draft | In Progress |
| Final | Reported |
| Dispatched | Completed |
| After Amend unlock | In Progress |

## Viewing & Downloading PDFs

| Situation | PDF behaviour |
|---|---|
| Click Preview on a Draft or Final report | Generated in-memory, shown in viewer — **not saved** to patient record |
| Dispatch a report | PDF generated automatically in background and **saved** to patient's clinical documents |
| Click View PDF on a Dispatched report | Cached PDF served instantly from disk |

### Viewing from the Order List

1. Find the order — the Actions column shows a teal 📄 icon for Dispatched reports.
2. Click 📄 — an in-page PDF viewer opens.
3. Click the **⬇ Download** button (top-right of modal) to save a copy.

### PDF contents

- **Header:** Clinic/branch logo, patient name, MRN, DOB, age, gender, referring doctor, department, visit date.
- **Body:** Test name, full report text with formatting preserved.
- **Signature block:** Radiologist name, DHA licence number, signing timestamp; Radiographer name and licence (when applicable).
- **Footer:** Clinic address bar, accreditation, page numbers.
- **Watermark:** 'DRAFT' (light grey diagonal) on Draft previews only.

## Dispatching a Report

**Radiologist only:** Only users with Radiologist role codes can dispatch a report.

### From the Report Editor

1. Open a finalized report (green *"Finalized — Awaiting Dispatch"* banner).
2. Click **🚀 Dispatch** in the top button bar.
3. The banner changes to teal: *"Report Dispatched — Read Only"*.

### From the Order List

1. Find the order — the report status badge shows **Final** and a teal ✓ button appears.
2. Click the teal ✓ **Dispatch** button.
3. A success toast confirms: *"Report dispatched for [patient name]"*.

### What happens automatically on dispatch

- Order status changes to **Completed**.
- Referring doctor receives an in-system notification.
- PDF is generated in the background and stored under the patient's clinical documents.
- The View PDF button (teal 📄) appears in the order list row.

## Amending or Unlocking

### Two amendment scenarios

| Scenario | Condition | Who can do it | Button shown |
|---|---|---|---|
| **Unlock** — fix before dispatch | Report is *Final* | Radiographer + Radiologist | 🔓 Unlock (orange) |
| **Amend** — correct after dispatch | Report is *Dispatched* | Radiologist only | ✏️ Amend (orange) |

### How to Unlock (Final → Draft)

1. Open the report showing the green *Finalized* banner.
2. Click **🔓 Unlock** (orange button, top-right of editor).
3. The report immediately reverts to **Draft** and is editable.
4. Make corrections. If you are a Radiographer, notify the Radiologist to re-finalize.

### How to Amend (Dispatched)

1. Open the dispatched report (teal *"Dispatched — Read Only"* banner).
2. Click **✏️ Amend** (only visible to Radiologists).
3. Enter an amendment reason in the modal (strongly recommended for audit trail).
4. Click **Unlock**.
5. Make corrections, re-finalize, then re-dispatch.

> **Important — Every amendment is permanently recorded:** Each unlock/amend action saves a snapshot of the original content with: original text, who changed it, when, and the reason. Version numbers increment (v1, v2…). This cannot be undone or deleted.

## Filtering & Searching

### To open the filter panel

1. Click the **⚙ Filter** button (top-right of the order list page).
2. The filter panel expands below the header.

### Filters

| Filter | Options |
|---|---|
| Search | Patient name, MRN, or order ID — updates live as you type |
| From / To Date | Date range pickers |
| Urgency | All / Routine / Urgent / STAT |
| Status | All / Scheduled / In Progress / Reported / Completed / Cancelled |
| Modality | Use the pill buttons above the table (always visible) |
| Per Page | 20 / 50 / 100 rows |

#### Quick Reset

Click **Clear Filters** inside the filter panel to reset all filters. The date resets to today.

#### Sorting

Click any **column header** to sort by that column. Click again to reverse the sort direction.

## Quick Reference

### Radiographer — Daily Checklist

| Task | Where to do it | Action |
|---|---|---|
| View today's orders | Order List | Period: Today (default) |
| Filter by modality | Modality pills | Click imaging type |
| Schedule appointment | Status column | 📅 Calendar icon |
| Start exam | Checkbox + Bulk | Set to In Progress |
| Write draft report | Actions column | ✏️ Edit Report |
| Save draft | Report Editor | Save Draft button or wait 30s |
| Unlock a Final report | Report Editor | 🔓 Unlock (orange) |

### Radiologist — Daily Checklist

| Task | Where to do it | Action |
|---|---|---|
| Find reports to sign | Status filter | Set to Reported |
| Review draft | Actions column | ✏️ Edit Report |
| Preview PDF | Report Editor | 👁 Preview (purple) |
| Finalize & sign | Report Editor | Select ✅ Final → Save Final |
| Dispatch to referrer | Editor or List | 🚀 Dispatch (teal) or ✓ button |
| View dispatched PDF | Order List (row) | 📄 View PDF (teal) |
| Amend dispatched report | Report Editor | ✏️ Amend (orange) |
| Unlock pre-dispatch | Report Editor | 🔓 Unlock (orange) |

### Button Visibility by Report Status

| Report Status | 🚀 Dispatch | 🔓 Unlock | ✏️ Amend | 📄 View PDF |
|---|---|---|---|---|
| Draft | — | — | — | Preview only |
| Final | ✅ Radiologist | ✅ Radiologist + Radiographer | — | Preview only |
| Dispatched | — | — | ✅ Radiologist only | ✅ All |

## FAQ

### I can't see the Final or Dispatch buttons

These buttons are only visible to Radiologists (role codes: RADIOLOGY, RADIOLOGIST, RAD). Radiographers can write drafts and unlock final reports, but cannot finalize or dispatch.

### The referring doctor did not receive a notification

Notifications are sent to the Consultation's assigned doctor first, then the Ordering Doctor. If neither is set on the order, no notification is sent. Contact your system administrator to verify the consultation record.

### I accidentally dispatched with an error

Use the ✏️ Amend button (Radiologist only) on the dispatched report. This creates a permanent audit record and unlocks the report for correction. Correct, re-finalize, and re-dispatch.

### Auto-save stopped showing 'Last saved'

Auto-save only runs while the report is in Draft status, the editor is not read-only, and there is at least 10 characters of content. Check that the report is in Draft and that you are connected to the network.

### The draft preview looks different from the final dispatched PDF

Draft and Final previews show a 'DRAFT' watermark and are generated on-the-fly without being saved. The dispatched PDF is the official document, has no watermark, and includes the formal signature block.

### I can't find an old order

The default date filter shows today only. Click **Last Week** (top-right), or open the Filter panel and set a From Date / To Date that covers the order date.
