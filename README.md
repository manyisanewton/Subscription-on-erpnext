# Subscription Automation for ERPNext

Server scripts that keep the custom `Internal Subscription` flow in sync with purchase invoices, billing cycles, and reminder tasks inside ERPNext/Frappe.

## Repository Layout

| File | Purpose |
| --- | --- |
| `Subscriptions/7dayscher&sendpi.py` | Daily scheduler script that recalculates subscription end dates, keeps the status in sync with the latest payment row, sends a 10‑day ToDo reminder, and drafts a renewal Purchase Invoice when needed. |
| `Subscriptions/cycle_logic.py` | Document Event script for `Internal Subscription` that enforces the start/end‑date cadence derived from the linked plan and validates status transitions. |
| `Subscriptions/Sync_subscription_payment_Script.py` | Document Event script for `Purchase Invoice` that pushes invoice status and posting date updates back to the matching subscription payment rows. |

All scripts rely on the standard `frappe` APIs (`frappe.get_all`, `frappe.get_doc`, `frappe.db.get_value`, `frappe.new_doc`) and the date helpers from `frappe.utils`.

## How to Use the Scripts

1. **Create a Server Script record** in ERPNext (`Settings > Server Script`) for each file.
2. **Paste the source** from the corresponding file into the Script field.
3. **Configure the trigger**:
   - `7dayscher&sendpi.py`: set `Script Type = Scheduler Event` and run it at least once per day so renewals and reminders fire 10 days before the subscription end date.
   - `cycle_logic.py`: set `Script Type = DocType Event`, `Reference Doctype = Internal Subscription`, and trigger `Before Save` (or `Before Submit`) so that every save recalculates the end date, validates the billing cycle, and updates the status.
   - `Sync_subscription_payment_Script.py`: set `Script Type = DocType Event`, `Reference Doctype = Purchase Invoice`, and trigger `After Save`/`After Submit` so invoice status changes propagate to the subscription payment child table.
4. **Test in a sandbox site** (`bench --site <yoursite> console`) before enabling in production.

## Operational Notes

- The scripts assume that `Internal Subscription` uses a child table called `payment_method` that stores `purchase_invoice`, `status`, and `posting_date`.
- Invoice auto-creation in `7dayscher&sendpi.py` avoids duplicates by checking the latest payment row for the same day. Adjust if your workflow has multiple invoices per day.
- Always keep at least one paid row in the payment table; the scripts determine whether a subscription is `Active` by inspecting the last row.
- Wrap long-running scheduler executions in try/except blocks (already done for invoice creation) and monitor the error log via `frappe.log_error`.

Feel free to fork or copy the scripts into your own ERPNext app and adapt the reminders, time windows, or child-table field names to suit your internal subscription model.
