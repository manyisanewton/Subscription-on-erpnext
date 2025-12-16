from frappe.utils import add_months, add_years, getdate, nowdate

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

# 1. Get the frequency from the first plan in the list
if doc.subscription_plan:
    plan_name = doc.subscription_plan[0].plan
    months_to_add = get_months_to_add(plan_name)
else:
    months_to_add = 1

# 2. Check the latest Payment Status
is_paid = False
if doc.payment_method:
    # Check the last row (assuming chronological order) or iterate to find 'Paid'
    for row in doc.payment_method:
        if row.status == "Paid":
            is_paid = True

# 3. Cycle Counting Logic
# Calculate the theoretical end date based on Start Date + Frequency
current_cycle_end = add_months(getdate(doc.subscription_start_date), months_to_add)

if is_paid:
    doc.status = "Active"
    
    # LOGIC: If the current period is fully paid and passed, auto-advance the dates?
    # Or simply ensure the End Date reflects the paid period.
    # Here we set the End Date to the Calculated Cycle End
    doc.subscription_end_date = current_cycle_end
    
    # If the payment was for a RENEWAL (i.e., we are already past the old end date),
    # You might want to shift the Start Date. 
    # UNCOMMENT BELOW LINES IF YOU WANT START DATE TO SHIFT FORWARD ON RENEWAL
    # if getdate(nowdate()) > getdate(doc.subscription_start_date):
    #     doc.subscription_start_date = nowdate()
    #     doc.subscription_end_date = add_months(nowdate(), months_to_add)

else:
    # If not paid, check if we are past the due date
    if getdate(nowdate()) > getdate(current_cycle_end):
        doc.status = "Past Due Date"
    else:
        # If not paid, but time remains, it is technically "Active" or "Pending"
        doc.status = "Active"

# 4. Final Validation
if doc.subscription_end_date and getdate(doc.subscription_end_date) < getdate(doc.subscription_start_date):
    frappe.throw("Subscription End Date cannot be before Start Date")