QUESTIONS = [
    # ============================================================
    # BILLING
    # ============================================================

    {
        "id": 1,
        "category": "billing",
        "question": "What are the three billing modes?",
        "expected_document": "billing-guide",
        "expected_concepts": ["Cash", "Insurance", "Corporate"],
    },
    {
        "id": 2,
        "category": "billing",
        "question": "What filters are available in the Billing Queue?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "Period",
            "Billing Status",
            "Doctor",
            "Department",
            "Insurance",
            "Search",
        ],
    },
    {
        "id": 3,
        "category": "billing",
        "question": "What does a CSH- invoice number mean?",
        "expected_document": "billing-guide",
        "expected_concepts": ["CSH-", "Cash invoice"],
    },
    {
        "id": 4,
        "category": "billing",
        "question": "What does the Can Apply advance indicator mean?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "Can Apply",
            "advance",
            "offset",
            "current visit invoice",
        ],
    },
    {
        "id": 5,
        "category": "billing",
        "question": "How can a doctor add a service to a consultation?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "service ordering",
            "consultation",
            "doctor",
        ],
    },
    {
        "id": 6,
        "category": "billing",
        "question": "What are the three ways to add services in the Service Order Modal?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "Service Order Modal",
            "services",
            "Order Sets",
            "Packages",
        ],
    },
    {
        "id": 7,
        "category": "billing",
        "question": "What pricing is used for insurance services?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "insurance",
            "pricing",
            "contracted",
        ],
    },
    {
        "id": 8,
        "category": "billing",
        "question": "What happens when a service has PreAuthRequired coverage?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "PreAuthRequired",
            "pre-authorisation",
            "insurance",
        ],
    },
    {
        "id": 9,
        "category": "billing",
        "question": "Which services can be invoiced?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "invoice",
            "services",
            "billable",
        ],
    },
    {
        "id": 10,
        "category": "billing",
        "question": "How are invoice-level discounts calculated?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "invoice-level discount",
            "discount",
            "invoice",
        ],
    },
    {
        "id": 11,
        "category": "billing",
        "question": "Can insurance services receive a manual discount?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "manual discount",
            "Cash",
            "insurance",
            "corporate",
            "contracted pricing",
            "cannot be manually discounted",
        ],
    },
    {
        "id": 12,
        "category": "billing",
        "question": "How is a pre-authorisation service converted to cash?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "pre-authorisation",
            "cash",
            "service",
        ],
    },
    {
        "id": 13,
        "category": "billing",
        "question": "What happens when an invoice is generated?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "invoice generated",
            "invoice",
            "payment",
        ],
    },
    {
        "id": 14,
        "category": "billing",
        "question": "What is Manual Billing used for?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "Manual Billing",
            "walk-in",
            "cash",
            "without consultation",
        ],
    },
    {
        "id": 15,
        "category": "billing",
        "question": "How can a cash invoice be paid?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "cash invoice",
            "payment",
            "payment collection",
        ],
    },
    {
        "id": 16,
        "category": "billing",
        "question": "What happens when an invoice is cancelled?",
        "expected_document": "billing-guide",
        "expected_concepts": [
            "invoice",
            "cancelled",
        ],
    },

    # ============================================================
    # CORPORATE BILLING
    # ============================================================

    {
        "id": 17,
        "category": "corporate_billing",
        "question": "What is a Billing Cycle?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "Billing Cycle",
            "corporate invoices",
            "billing month",
        ],
    },
    {
        "id": 18,
        "category": "corporate_billing",
        "question": "What are the statuses of a corporate billing cycle?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "DRAFT",
            "GENERATED",
            "APPROVED",
            "REJECTED",
            "SENT",
            "PAID",
        ],
    },
    {
        "id": 19,
        "category": "corporate_billing",
        "question": "Who can create a billing cycle?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "BILLING",
            "ADMIN",
            "create",
        ],
    },
    {
        "id": 20,
        "category": "corporate_billing",
        "question": "How do I create a new billing cycle?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "New Billing Cycle",
            "Corporate Payer",
            "Billing Month",
            "Cut-off Date",
            "Create Draft & Preview",
        ],
    },
    {
        "id": 21,
        "category": "corporate_billing",
        "question": "Can I create two billing cycles for the same corporate payer and month?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "one cycle per month",
            "payer",
            "month",
            "409 Conflict",
        ],
    },
    {
        "id": 22,
        "category": "corporate_billing",
        "question": "What is the purpose of the cut-off date?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "cut-off date",
            "invoices",
            "billing month",
        ],
    },
    {
        "id": 23,
        "category": "corporate_billing",
        "question": "When can invoices be added or removed from a billing cycle?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "DRAFT",
            "add",
            "remove",
            "invoices",
        ],
    },
    {
        "id": 24,
        "category": "corporate_billing",
        "question": "How do I submit a billing cycle for approval?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "Submit for Approval",
            "reports",
            "approval",
        ],
    },
    {
        "id": 25,
        "category": "corporate_billing",
        "question": "Which roles can approve or reject a billing cycle?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "BCOORD",
            "BRANCHMGR",
            "FINANCEMGR",
            "ADMIN",
            "SUPERADMIN",
            "approve",
            "reject",
        ],
    },
    {
        "id": 26,
        "category": "corporate_billing",
        "question": "What rejection reasons are available?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "rejection",
            "reason",
        ],
    },
    {
        "id": 27,
        "category": "corporate_billing",
        "question": "What happens after a billing cycle is rejected?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "REJECTED",
            "corrections",
            "edit",
            "re-submit",
        ],
    },
    {
        "id": 28,
        "category": "corporate_billing",
        "question": "How is a corporate invoice sent to the corporate client?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "Send to Corporate",
            "email",
            "APPROVED",
            "SENT",
        ],
    },
    {
        "id": 29,
        "category": "corporate_billing",
        "question": "How do I mark a corporate billing cycle as paid?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "Mark Paid",
            "Payment Reference",
            "Confirm Payment",
            "PAID",
        ],
    },
    {
        "id": 30,
        "category": "corporate_billing",
        "question": "What happens after a cycle is marked as PAID?",
        "expected_document": "corporate-billing-guide",
        "expected_concepts": [
            "PAID",
            "closed",
            "Paid This Month",
        ],
    },

    # ============================================================
    # INVENTORY
    # ============================================================

    {
        "id": 31,
        "category": "inventory",
        "question": "What modules are included in Inventory & Procurement?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "Inventory",
            "Procurement",
        ],
    },
    {
        "id": 32,
        "category": "inventory",
        "question": "What does the Inventory Dashboard show?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "Inventory Dashboard",
            "stock",
        ],
    },
    {
        "id": 33,
        "category": "inventory",
        "question": "What is the difference between Low Stock and Critical stock?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "Low Stock",
            "Critical",
            "threshold",
        ],
    },
    {
        "id": 34,
        "category": "inventory",
        "question": "What does the Expiry Dashboard track?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "Expiry Dashboard",
            "expiry",
            "stock",
        ],
    },
    {
        "id": 35,
        "category": "inventory",
        "question": "What fields are required when creating an inventory item?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "inventory item",
            "required fields",
        ],
    },
    {
        "id": 36,
        "category": "inventory",
        "question": "What does Batch Tracked mean?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "Batch Tracked",
            "batch",
        ],
    },
    {
        "id": 37,
        "category": "inventory",
        "question": "What does Expiry Tracked mean?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "Expiry Tracked",
            "expiry",
        ],
    },
    {
        "id": 38,
        "category": "inventory",
        "question": "How can inventory items be imported using Excel?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "Excel",
            "import",
            "inventory items",
        ],
    },
    {
        "id": 39,
        "category": "inventory",
        "question": "What information is stored for suppliers?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "supplier",
            "supplier information",
        ],
    },
    {
        "id": 40,
        "category": "inventory",
        "question": "How are supplier items used when creating a PO?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "supplier items",
            "PO",
            "Purchase Order",
        ],
    },
    {
        "id": 41,
        "category": "inventory",
        "question": "What are the stages of the Purchase Order lifecycle?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "Purchase Order",
            "lifecycle",
            "stages",
        ],
    },
    {
        "id": 42,
        "category": "inventory",
        "question": "What does a Partially Received PO mean?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "Partially Received",
            "PO",
            "received",
        ],
    },
    {
        "id": 43,
        "category": "inventory",
        "question": "How is a GRN created?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "GRN",
            "create",
        ],
    },
    {
        "id": 44,
        "category": "inventory",
        "question": "What happens when a GRN is posted?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "GRN",
            "posted",
            "stock",
        ],
    },
    {
        "id": 45,
        "category": "inventory",
        "question": "Can a posted GRN be deleted?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "posted GRN",
            "delete",
        ],
    },
    {
        "id": 46,
        "category": "inventory",
        "question": "How does barcode scanning work during GRN creation?",
        "expected_document": "inventory-guide",
        "expected_concepts": [
            "barcode",
            "GRN",
            "scanning",
        ],
    },

    # ============================================================
    # RADIOLOGY
    # ============================================================

    {
        "id": 47,
        "category": "radiology",
        "question": "What can a Radiographer do in the Radiology module?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "Radiographer",
            "Radiology",
        ],
    },
    {
        "id": 48,
        "category": "radiology",
        "question": "What can only a Radiologist do?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "Radiologist",
            "permissions",
        ],
    },
    {
        "id": 49,
        "category": "radiology",
        "question": "What are the radiology order priority levels?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "priority",
            "radiology order",
        ],
    },
    {
        "id": 50,
        "category": "radiology",
        "question": "How does a Radiographer schedule an appointment?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "Radiographer",
            "schedule",
            "appointment",
        ],
    },
    {
        "id": 51,
        "category": "radiology",
        "question": "How does a Radiographer create a draft report?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "Radiographer",
            "draft report",
        ],
    },
    {
        "id": 52,
        "category": "radiology",
        "question": "How often does auto-save run?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "auto-save",
        ],
    },
    {
        "id": 53,
        "category": "radiology",
        "question": "How does Voice-to-Text work?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "Voice-to-Text",
        ],
    },
    {
        "id": 54,
        "category": "radiology",
        "question": "What happens when a Radiologist finalizes a report?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "Radiologist",
            "finalizes",
            "report",
            "Final",
        ],
    },
    {
        "id": 55,
        "category": "radiology",
        "question": "What happens when a report is dispatched?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "dispatched",
            "report",
        ],
    },
    {
        "id": 56,
        "category": "radiology",
        "question": "When is the PDF generated?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "PDF",
            "generated",
            "dispatched",
        ],
    },
    {
        "id": 57,
        "category": "radiology",
        "question": "Where is the dispatched PDF stored?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "dispatched PDF",
            "stored",
        ],
    },
    {
        "id": 58,
        "category": "radiology",
        "question": "Can a Radiographer amend a dispatched report?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "Radiographer",
            "amend",
            "dispatched report",
        ],
    },
    {
        "id": 59,
        "category": "radiology",
        "question": "What is the difference between Unlock and Amend?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "Unlock",
            "Amend",
        ],
    },
    {
        "id": 60,
        "category": "radiology",
        "question": "What happens to the order status when a report is dispatched?",
        "expected_document": "radiology-guide",
        "expected_concepts": [
            "order status",
            "dispatched",
        ],
    },

    # ============================================================
    # MEDICAL HISTORY
    # ============================================================

    {
        "id": 61,
        "category": "medical_history",
        "question": "What categories are included in Past Medical History?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "Past Medical History",
            "categories",
        ],
    },
    {
        "id": 62,
        "category": "medical_history",
        "question": "What is stored in Vaccination Records?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "Vaccination Records",
            "vaccination",
        ],
    },
    {
        "id": 63,
        "category": "medical_history",
        "question": "Which fields are required for an allergy entry?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "allergy",
            "required fields",
        ],
    },
    {
        "id": 64,
        "category": "medical_history",
        "question": "What are the allergy type codes?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "allergy type",
            "codes",
        ],
    },
    {
        "id": 65,
        "category": "medical_history",
        "question": "What are the available allergy severity levels?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "allergy",
            "severity",
        ],
    },
    {
        "id": 66,
        "category": "medical_history",
        "question": "What does No Known mean?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "No Known",
        ],
    },
    {
        "id": 67,
        "category": "medical_history",
        "question": "What is the difference between an empty category and No Known?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "empty category",
            "No Known",
            "difference",
        ],
    },
    {
        "id": 68,
        "category": "medical_history",
        "question": "How are Visit Notes saved?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "Visit Notes",
            "saved",
        ],
    },
    {
        "id": 69,
        "category": "medical_history",
        "question": "When are previous visit notes automatically pre-populated?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "previous visit notes",
            "pre-populated",
        ],
    },
    {
        "id": 70,
        "category": "medical_history",
        "question": "Which previous visit is used for pre-population?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "previous visit",
            "pre-population",
        ],
    },
    {
        "id": 71,
        "category": "medical_history",
        "question": "Can a user edit another user's history entry?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "edit",
            "another user",
            "history entry",
        ],
    },
    {
        "id": 72,
        "category": "medical_history",
        "question": "Can an old medical history entry be deleted?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "old",
            "medical history entry",
            "delete",
        ],
    },
    {
        "id": 73,
        "category": "medical_history",
        "question": "Why might the pregnancy history category be hidden?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "pregnancy history",
            "hidden",
        ],
    },
    {
        "id": 74,
        "category": "medical_history",
        "question": "What happens when an allergy is added or deleted?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "allergy",
            "added",
            "deleted",
        ],
    },
    {
        "id": 75,
        "category": "medical_history",
        "question": "How does the search/filter system work within a history category?",
        "expected_document": "medical-history-guide",
        "expected_concepts": [
            "search",
            "filter",
            "history category",
        ],
    },
]


assert len(QUESTIONS) == 75