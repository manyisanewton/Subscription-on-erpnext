from frappe.utils import add_months, getdate, nowdate

# --- HELPER: Get Frequency in Months ---
def get_months_to_add(plan_name):
    if not plan_name: return 1
    # Fetch billing cycle from the Plan Doctype
    cycle = frappe.db.get_value("Internal Subscription Plan", plan_name, "billing_cycles")
    
    if cycle == "Annually": return 12
    if cycle == "Biannually": return 6
    if cycle == "Quarterly": return 3
    # Default to Monthly
    return 1

# --- MAIN LOGIC ---

# 1. Determine Cycle Length
if doc.subscription_plan:
    # Assuming the plan is in the first row
    plan_name = doc.subscription_plan[0].plan
    months_to_add = get_months_to_add(plan_name)
else:
    months_to_add = 1

# 2. AUTO-CALCULATE END DATE 
# We strictly enforce: End Date = Start Date + Frequency
# This ensures the dates are always correct based on the plan.
if doc.subscription_start_date:
    doc.subscription_end_date = add_months(getdate(doc.subscription_start_date), months_to_add)

# 3. Check the LATEST Payment Status
# We check the LAST row in the table. If the newest invoice is paid, we are good.
is_latest_paid = False
if doc.payment_method and len(doc.payment_method) > 0:
    last_row = doc.payment_method[-1]
    if last_row.status == "Paid":
        is_latest_paid = True

# 4. Update Status based on Payment & Dates
if is_latest_paid:
    doc.status = "Active"
else:
    # If not paid, check if we are past the calculated end date
    if doc.subscription_end_date and getdate(nowdate()) > getdate(doc.subscription_end_date):
        doc.status = "Past Due Date"
    else:
        # If not paid, but time remains, it is "Active" (Pending Payment)
        doc.status = "Active"

# 5. Final Validation (Safety Check)
if doc.subscription_end_date and getdate(doc.subscription_end_date) < getdate(doc.subscription_start_date):
    frappe.throw("Error: Subscription End Date cannot be before Start Date")