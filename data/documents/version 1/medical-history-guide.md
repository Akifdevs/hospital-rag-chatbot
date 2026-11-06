# Medical History

**Subtitle:** Manage patient allergies, medical, surgical, family, social, and vaccination history  
**Version:** 1.0  
**Last updated:** Apr 2026

## Overview

The Medical History section provides a comprehensive view of a patient's health background. It is divided into two tabs — **Past Medical History** and **Vaccination Records**.

### Past Medical History covers

- **Allergy History** — Drug, food, environmental, and miscellaneous allergies with severity and reactions.
- **Medical History** — Chronic conditions and past diagnoses.
- **Surgical History** — Previous surgeries and procedures.
- **Family Medical History** — Hereditary conditions and family diagnoses.
- **Social History** — Lifestyle habits (smoking, alcohol, exercise, etc.).
- **Current Treatment** — Ongoing medications and therapies.
- **History of Present Pregnancy** — Pregnancy details (shown for female patients only).
- **Other History** — Any additional relevant history.

> **Previous Visit Pre-Population:** When opening a new consultation, the system automatically pulls history notes from the most recent **non-insurance** previous visit and pre-fills any empty note fields, saving re-entry time.

## Navigation & Layout

### Two tabs

| Tab | Contents |
|---|---|
| **Past Medical History** | All history categories (Allergies, Medical, Surgical, Family, Social, Current Treatment, Pregnancy, Other). |
| **Vaccination Records** | Full vaccination history for the patient. |

### Expand or collapse categories

1. Click any category header to expand or collapse it individually.
2. Use the **Expand All** / **Collapse All** toggle in the top-right of the Past Medical History sub-header to control all panels at once.

> **Gender-aware filtering:** The **History of Present Pregnancy** category is automatically hidden for male patients and only shown when the patient is female.

## Adding History Entries

Each category supports adding new entries directly from within the section. The form type varies by category.

### Add an entry

1. Expand the desired history category.
2. Click **+ Add New** in the category header.
3. Fill in the required fields in the inline form that appears.
4. Click **Save** to save and close, or **Save & Add Another** to save and immediately start a new entry.

### Required fields by category

| Category | Required fields |
|---|---|
| **Allergy History** | Allergy Type, Allergen, Reaction, Severity, Date Identified. |
| **Family Medical History** | Family Member, Diagnosis, Start Date, Status. |
| **Social History** | Social Habit, Quantity, Status. |
| **All others** (Medical, Surgical, etc.) | Description (free text). |

> **Validation on Save:** If required fields are missing when you click Save, a notification will appear listing the missing fields. All required fields must be filled before the entry can be saved.

> **Custom Allergy Reaction:** When selecting **Other** as the Reaction for an allergy, an additional text box appears to enter the custom reaction description.

## Allergy History

The Allergy History category tracks all known patient allergies. Allergies are particularly important for prescription decisions and procedure safety.

### Allergy type codes

| Allergy type | Code |
|---|---|
| Drug Allergy | DA |
| Food Allergy | FA |
| Environmental Allergy | EA |
| Miscellaneous / Other Allergy | MA |

### Severity levels

| Severity | Display colour |
|---|---|
| Mild | Green |
| Moderate | Yellow |
| Severe | Orange |
| Life-threatening | Red |

> **Allergy change notification:** When an allergy entry is added or deleted, the system notifies the parent consultation screen so allergy-related warnings can be updated across the visit.

## No Known History

Each history category has a **No Known** toggle button. Use it when the patient has explicitly confirmed they have no history in that category.

### Mark No Known

1. Expand the relevant history category.
2. Click **No Known** in the category header.
3. A special entry is created in the system to record that the patient was asked and confirmed no known history.
4. The category displays a “No Known” indicator.
5. Click the button again to reverse the No Known status.

> **No Known vs. Empty:** An **empty** category means history was not yet asked or recorded. A **No Known** entry means the clinician actively confirmed with the patient that no history exists — this distinction is important for clinical documentation.

## Visit Notes

Each history category includes a **Visit Note** textarea at the bottom of the category panel. This allows clinicians to write free-text summary notes specific to this visit.

### How Visit Notes work

1. Expand a history category to find the note textarea section at the bottom.
2. Type your notes in the textarea.
3. Notes are **auto-saved** when you click outside the textarea (on blur).
4. When you have unsaved changes, a small green **save icon (✓)** and gray **discard icon (✗)** appear next to the textarea — click them to manually save or discard.

> **Pre-population from previous visits:** If the current visit's note field is empty, the system automatically pre-fills it with the corresponding note from the most recent non-insurance previous visit.

### Note fields by category

| Note field | Category |
|---|---|
| Patient Allergy Note | Allergy History |
| Patient Medical History Note | Medical History |
| Patient Surgical History Note | Surgical History |
| Patient Family History Note | Family Medical History |
| Patient Social History Note | Social History |
| Patient Current Treatment Note | Current Treatment |

## Editing & Deleting Entries

### Edit an entry

1. Find the entry row within the expanded category.
2. Click the **Edit (✏️)** icon on the entry row.
3. The edit form opens pre-filled with the existing data.
4. Make your changes and click **Update & Close**.

### Delete an entry

1. Find the entry row and click the **Delete (🗑)** icon.
2. A confirmation dialog appears.
3. Click **Delete** to confirm or **Cancel** to abort.

> **Edit & Delete Restrictions:** You can only edit or delete entries that you created **yourself** on the **same day**. Entries created by other users or on previous days are read-only. This protects the clinical record integrity.

## Search & Filters

Within an expanded category, a search bar and filters are available to quickly find specific entries.

| Filter | Available for | Options |
|---|---|---|
| **Search** | All categories | Free text search on entry fields. |
| **Severity** | Allergy History | All / Mild / Moderate / Severe / Life-threatening. |
| **Status** | Family & Social | All / Active / Inactive / Resolved. |
| **Sort** | All categories | Sort by Date or Alphabetically, Ascending / Descending. |

> **Search resets on tab switch:** Switching between categories (clicking a different header) automatically clears the search term and filters so you start fresh in each category.

## Vaccination Records

The **Vaccination Records** tab shows the complete vaccination history for the patient across all visits. Switch to this tab from the top navigation.

- View all vaccinations given with dates and batch numbers.
- Track due dates for upcoming doses.
- Record new vaccinations administered during the current visit.

## Tips & FAQs

### Frequently asked questions

- **Why can't I see the Edit or Delete button on an entry?** — You can only modify entries that you created today. Older entries or entries created by other users are locked for integrity.
- **Why is the “History of Present Pregnancy” category missing?** — This category is automatically hidden for male patients and only shown for female patients.
- **What does “No Known” mean vs. an empty category?** — Empty means not yet asked; No Known means the patient was asked and confirmed no history exists.
- **The visit note seems pre-filled — where did it come from?** — The system pulled the note from the previous non-insurance visit to save data re-entry. You can edit or override it.
- **Why is the previous visit's note not appearing?** — Pre-population only happens if the current visit's note field is empty. If you already have a note saved, it won't be overwritten.
- **Can I add allergies in read-only mode?** — No. The Add New, No Known, and Edit/Delete actions are only available at open (non-read-only) consultations.

### Quick workflow for a new consultation

1. Review pre-populated notes from the previous visit.
2. Update or confirm each category's visit note.
3. Add any new allergies/conditions using **+ Add New**.
4. Mark **No Known** for categories the patient has confirmed no history in.
5. Notes auto-save when you click away.
