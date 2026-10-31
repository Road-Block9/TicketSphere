"""
Generate Sample Customer Support Ticket Dataset
Module 1: Project Setup and Dataset Preparation

Generates a realistic 60-ticket dataset with proper CSV quoting,
covering realistic categories, priorities, statuses, timestamps,
and resolution notes.
"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "data" / "raw" / "customer_support_tickets.csv"

TICKETS = [
    (
        "TKT-1001", "CUST-5001", "2026-03-01 08:15:00", "2026-03-01 14:30:00",
        "Delivery & Shipping", "High", "Resolved",
        "Delayed package delivery",
        "Package was scheduled for yesterday but tracking status shows stuck at regional warehouse.",
        "Carrier notified and package dispatched for expedited same-day delivery."
    ),
    (
        "TKT-1002", "CUST-5002", "2026-03-01 09:20:00", "2026-03-01 11:45:00",
        "Billing & Refunds", "Medium", "Resolved",
        "Charged twice for monthly subscription",
        "Bank statement shows duplicate transaction of $29.99 on March 1st.",
        "Duplicate payment identified and refunded back to original card. Refund ref #RFD-8821."
    ),
    (
        "TKT-1003", "CUST-5003", "2026-03-01 10:05:00", "",
        "Technical Support", "Critical", "Open",
        "Cannot login to mobile app",
        "App crashes immediately upon clicking sign in button after latest v2.4 update.",
        ""
    ),
    (
        "TKT-1004", "CUST-5004", "2026-03-01 11:30:00", "2026-03-02 09:15:00",
        "Product Quality", "High", "Closed",
        "Screen cracked on brand new monitor",
        "Unboxed the 27-inch gaming monitor and found a spiderweb crack across display panel.",
        "RMA approved and prepaid return label emailed. Replacement monitor dispatched."
    ),
    (
        "TKT-1005", "CUST-5005", "2026-03-01 13:00:00", "",
        "Customer Service", "Low", "Pending",
        "Agent was abrupt during phone call",
        "Representative John did not let me finish explaining my inquiry before transferring me.",
        "Awaiting supervisor callback review of call recording."
    ),
    (
        "TKT-1006", "CUST-5006", "2026-03-02 08:45:00", "2026-03-02 12:10:00",
        "Delivery & Shipping", "Medium", "Resolved",
        "Package delivered to wrong address",
        "Driver left parcel at apartment 4B instead of 4D. Retrieved it but box was opened.",
        "Apology issued and $15 store credit applied to account for mishandling."
    ),
    (
        "TKT-1007", "CUST-5007", "2026-03-02 09:50:00", "2026-03-03 16:20:00",
        "Billing & Refunds", "High", "Resolved",
        "Invoice missing corporate tax ID",
        "Need revised invoice with VAT ID 9823412 for corporate expense filing.",
        "Updated tax invoice generated with company VAT ID and emailed as PDF."
    ),
    (
        "TKT-1008", "CUST-5008", "2026-03-02 11:15:00", "",
        "Technical Support", "High", "Open",
        "Payment gateway error 504 on checkout",
        "Trying to place an order with Mastercard but receiving gateway timeout error.",
        ""
    ),
    (
        "TKT-1009", "CUST-5009", "2026-03-02 14:00:00", "2026-03-02 17:30:00",
        "Product Quality", "Medium", "Resolved",
        "Missing power adapter in box",
        "Received the desk lamp but power adapter cable was absent from the package.",
        "Spare power adapter shipped via priority courier. Tracking #TRK-9012."
    ),
    (
        "TKT-1010", "CUST-5010", "2026-03-02 16:40:00", "2026-03-04 10:00:00",
        "Delivery & Shipping", "Critical", "Closed",
        "Perishable grocery delivery ruined",
        "Frozen items arrived completely defrosted and warm after 48-hour delivery delay.",
        "Full order refund processed ($84.50) and grocery credit provided."
    ),
    (
        "TKT-1011", "CUST-5011", "2026-03-03 08:30:00", "",
        "Delivery & Shipping", "High", "Open",
        "Tracking number invalid on carrier portal",
        "Tracking code provided in dispatch email returns Not Found on DHL site.",
        ""
    ),
    (
        "TKT-1012", "CUST-5012", "2026-03-03 10:15:00", "2026-03-03 15:00:00",
        "Billing & Refunds", "Low", "Resolved",
        "Promotional discount code not applied",
        "Code SAVE20 was entered during checkout but did not deduct 20% discount.",
        "Verified promo validity and manually issued $12 discount refund to card."
    ),
    (
        "TKT-1013", "CUST-5013", "2026-03-03 11:45:00", "",
        "Customer Service", "Medium", "Pending",
        "No response on email inquiry for 5 days",
        "Sent an inquiry regarding wholesale pricing last week and received zero acknowledgment.",
        "Assigned to B2B enterprise sales team for priority response."
    ),
    (
        "TKT-1014", "CUST-5014", "2026-03-03 13:20:00", "2026-03-04 14:10:00",
        "Technical Support", "Medium", "Resolved",
        "Password reset email never arrives",
        "Requested password reset link 4 times but no email received in inbox or spam.",
        "Mail server deliverability cleared and manual secure password reset link provided."
    ),
    (
        "TKT-1015", "CUST-5015", "2026-03-03 15:50:00", "2026-03-04 11:30:00",
        "Product Quality", "High", "Closed",
        "Defective zipper on winter jacket",
        "The main front zipper split open during first wear and cannot be closed.",
        "Returned to warehouse; replacement jacket in size L dispatched."
    ),
    (
        "TKT-1016", "CUST-5016", "2026-03-04 09:00:00", "",
        "Billing & Refunds", "Critical", "Open",
        "Unauthorized renewal after cancellation",
        "Cancelled subscription on Feb 20 but account was billed $99 on March 3rd.",
        ""
    ),
    (
        "TKT-1017", "CUST-5017", "2026-03-04 10:30:00", "2026-03-04 13:00:00",
        "Delivery & Shipping", "Low", "Resolved",
        "Delivery instructions ignored",
        "Requested driver leave parcel on back porch but it was left on front curb in the rain.",
        "Driver delivery note updated in carrier profile; carrier partner flagged."
    ),
    (
        "TKT-1018", "CUST-5018", "2026-03-04 12:15:00", "",
        "Technical Support", "High", "Open",
        "Two-factor authentication SMS delay",
        "SMS verification code takes over 15 minutes to arrive, causing session expiration.",
        ""
    ),
    (
        "TKT-1019", "CUST-5019", "2026-03-04 14:45:00", "2026-03-05 18:20:00",
        "Product Quality", "Low", "Resolved",
        "Wrong color delivered",
        "Ordered navy blue backpack but received forest green.",
        "Customer opted to keep item in exchange for a 25% partial refund."
    ),
    (
        "TKT-1020", "CUST-5020", "2026-03-04 16:30:00", "2026-03-06 09:00:00",
        "Customer Service", "High", "Closed",
        "Store staff refused valid return receipt",
        "Store branch in Downtown refused return of unopened item with original printed receipt.",
        "Store manager briefed; return accepted at store and formal apology sent."
    ),
    (
        "TKT-1021", "CUST-5021", "2026-03-05 08:20:00", "2026-03-05 16:45:00",
        "Delivery & Shipping", "High", "Resolved",
        "Driver marked delivered but parcel missing",
        "Notification says handed to resident at 2 PM but no one was home at that hour.",
        "Driver re-checked location, found package in parcel locker #12 and sent code."
    ),
    (
        "TKT-1022", "CUST-5022", "2026-03-05 09:40:00", "",
        "Billing & Refunds", "High", "Pending",
        "Refund pending for over 14 business days",
        "Returned defective blender two weeks ago; return tracking confirms delivery but no refund.",
        "Escalated to finance department for bank clearing confirmation."
    ),
    (
        "TKT-1023", "CUST-5023", "2026-03-05 11:00:00", "2026-03-05 14:20:00",
        "Technical Support", "Low", "Resolved",
        "Unable to export transaction history to CSV",
        "Clicking Export CSV produces an empty 0-byte file in browser.",
        "Database query timeout resolved; CSV generated server-side and emailed."
    ),
    (
        "TKT-1024", "CUST-5024", "2026-03-05 13:10:00", "",
        "Delivery & Shipping", "Critical", "Open",
        "Express delivery 3 days overdue",
        "Paid $25 extra for overnight guaranteed delivery for medical supplies, still not delivered.",
        ""
    ),
    (
        "TKT-1025", "CUST-5025", "2026-03-05 15:30:00", "2026-03-06 14:00:00",
        "Product Quality", "Medium", "Resolved",
        "Blender blade loose and vibrating violently",
        "Blender blade assembly came loose on first use and made loud grinding noise.",
        "Replacement blade assembly shipped with assembly guide."
    ),
    (
        "TKT-1026", "CUST-5026", "2026-03-06 08:50:00", "2026-03-06 10:30:00",
        "Billing & Refunds", "Medium", "Resolved",
        "Overcharged sales tax on tax-exempt entity",
        "Non-profit account was charged state sales tax of $42.50 on office chairs.",
        "Tax-exempt certificate verified; sales tax refunded and profile flag enabled."
    ),
    (
        "TKT-1027", "CUST-5027", "2026-03-06 10:15:00", "",
        "Technical Support", "Critical", "Open",
        "Database synchronization error on web dashboard",
        "Changes made to user profile settings revert back to old values upon page refresh.",
        ""
    ),
    (
        "TKT-1028", "CUST-5028", "2026-03-06 12:00:00", "2026-03-07 11:15:00",
        "Customer Service", "Medium", "Resolved",
        "Long wait times on live chat",
        "Waited 45 minutes on live chat before being disconnected without assistance.",
        "Chat queue routing reconfigured and customer contacted directly via phone."
    ),
    (
        "TKT-1029", "CUST-5029", "2026-03-06 14:25:00", "2026-03-07 17:00:00",
        "Delivery & Shipping", "Medium", "Closed",
        "Damaged outer shipping carton",
        "Outer cardboard box was crushed during transit; goods inside were intact but gift box ruined.",
        "$10 courtesy coupon provided for packaging inconvenience."
    ),
    (
        "TKT-1030", "CUST-5030", "2026-03-06 16:10:00", "",
        "Product Quality", "High", "Pending",
        "Smart bulb not connecting to Wi-Fi",
        "Followed setup guide 5 times, bulb refuses to broadcast pairing signal.",
        "Technical team requested router frequency details (2.4GHz vs 5GHz)."
    ),
    (
        "TKT-1031", "CUST-5031", "2026-03-07 09:05:00", "2026-03-07 12:40:00",
        "Billing & Refunds", "Low", "Resolved",
        "Currency conversion rate discrepancy",
        "Billed in USD instead of CAD as selected during checkout.",
        "Currency adjustment credit of 8.20 CAD applied to customer account."
    ),
    (
        "TKT-1032", "CUST-5032", "2026-03-07 10:45:00", "",
        "Delivery & Shipping", "High", "Open",
        "Package held at customs without notification",
        "International shipment tracking indicates clearance delay; no document request received.",
        ""
    ),
    (
        "TKT-1033", "CUST-5033", "2026-03-07 12:30:00", "2026-03-08 15:10:00",
        "Technical Support", "Medium", "Resolved",
        "Error uploading profile photo",
        "JPEG photo upload fails with generic server error 400.",
        "File size restriction increased from 2MB to 5MB and image auto-compressed."
    ),
    (
        "TKT-1034", "CUST-5034", "2026-03-07 14:15:00", "2026-03-08 10:30:00",
        "Product Quality", "High", "Resolved",
        "Headphones only emitting sound from left ear",
        "Audio cuts out completely in right earpiece when cable is moved.",
        "Faulty auxiliary wire identified; new replacement audio cable shipped."
    ),
    (
        "TKT-1035", "CUST-5035", "2026-03-07 16:00:00", "",
        "Customer Service", "Low", "Pending",
        "Unhelpful responses from AI chatbot",
        "Chatbot entered infinite loop asking for order number repeatedly.",
        "Escalated to human supervisor; chatbot dialogue flow ticket submitted to dev team."
    ),
    (
        "TKT-1036", "CUST-5036", "2026-03-08 08:40:00", "2026-03-08 13:20:00",
        "Delivery & Shipping", "Medium", "Resolved",
        "Rescheduled delivery date request",
        "Need delivery pushed back by two days as recipient is traveling.",
        "Delivery window rescheduled with courier for March 10th morning."
    ),
    (
        "TKT-1037", "CUST-5037", "2026-03-08 10:20:00", "",
        "Billing & Refunds", "Critical", "Open",
        "Gift card balance wiped out",
        "Purchased a $100 digital gift card, applied to cart, but system shows $0 balance without applying.",
        ""
    ),
    (
        "TKT-1038", "CUST-5038", "2026-03-08 11:50:00", "2026-03-09 16:00:00",
        "Product Quality", "Medium", "Closed",
        "Missing screws and manual for bookshelf",
        "Flatpack package did not contain hardware blister pack or assembly instructions.",
        "PDF manual emailed and replacement hardware pack dispatched."
    ),
    (
        "TKT-1039", "CUST-5039", "2026-03-08 14:10:00", "",
        "Technical Support", "High", "Open",
        "Session timeout during multi-step form",
        "Filling out 5-page insurance quote form logs user out on step 4 losing all data.",
        ""
    ),
    (
        "TKT-1040", "CUST-5040", "2026-03-08 16:35:00", "2026-03-09 11:15:00",
        "Delivery & Shipping", "High", "Resolved",
        "Driver demanded cash for paid delivery",
        "Courier requested extra fee at doorstep despite shipping being prepaid online.",
        "Courier partner reported for disciplinary action; confirmed no fee required."
    ),
    (
        "TKT-1041", "CUST-5041", "2026-03-09 09:10:00", "2026-03-09 14:40:00",
        "Billing & Refunds", "Medium", "Resolved",
        "Duplicate delivery fee charged",
        "Invoice displays two separate express shipping charges for a single package.",
        "One delivery fee of $15 credited back to payment method."
    ),
    (
        "TKT-1042", "CUST-5042", "2026-03-09 11:00:00", "",
        "Delivery & Shipping", "Critical", "Open",
        "Medical equipment package damaged in transit",
        "Diagnostic scanner arrived with crushed outer box and loose calibration knob.",
        ""
    ),
    (
        "TKT-1043", "CUST-5043", "2026-03-09 13:15:00", "2026-03-10 10:20:00",
        "Customer Service", "Medium", "Resolved",
        "Incorrect information given by phone rep",
        "Phone representative stated warranty was 6 months when website says 2 years.",
        "Confirmed 2-year warranty coverage in system and emailed warranty certificate."
    ),
    (
        "TKT-1044", "CUST-5044", "2026-03-09 15:30:00", "",
        "Technical Support", "Medium", "Pending",
        "Dark mode toggle not saving in preferences",
        "Every time page reloads, theme reverts back to bright light mode.",
        "Developer bug ticket logged (BUG-304); awaiting web release."
    ),
    (
        "TKT-1045", "CUST-5045", "2026-03-09 17:00:00", "2026-03-10 14:30:00",
        "Product Quality", "Low", "Resolved",
        "Minor scratch on laptop lid",
        "Small 1cm cosmetic scratch on aluminum cover straight out of sealed box.",
        "Customer agreed to $30 refund in lieu of returning unit."
    ),
    (
        "TKT-1046", "CUST-5046", "2026-03-10 08:30:00", "2026-03-10 12:00:00",
        "Delivery & Shipping", "High", "Resolved",
        "Wrong item delivered in sealed package",
        "Ordered size 10 running shoes, package label said size 10, but box contained size 7.",
        "Correct size 10 shoes dispatched immediately with courier return pickup for wrong pair."
    ),
    (
        "TKT-1047", "CUST-5047", "2026-03-10 10:10:00", "",
        "Billing & Refunds", "High", "Open",
        "Charged after free trial cancelled",
        "Cancelled 14-day free trial on day 12; credit card was billed $49.99 this morning.",
        ""
    ),
    (
        "TKT-1048", "CUST-5048", "2026-03-10 11:45:00", "2026-03-11 15:30:00",
        "Technical Support", "Low", "Resolved",
        "Forgot username and registered email",
        "Customer cannot recall which email address was tied to loyalty rewards account.",
        "Account verified through phone number + SMS OTP; username confirmed."
    ),
    (
        "TKT-1049", "CUST-5049", "2026-03-10 14:00:00", "",
        "Product Quality", "Critical", "Open",
        "Battery swollen on cordless vacuum",
        "After 3 weeks of usage, lithium battery pack appears visibly swollen and hot during charging.",
        ""
    ),
    (
        "TKT-1050", "CUST-5050", "2026-03-10 16:15:00", "2026-03-11 09:45:00",
        "Customer Service", "Low", "Resolved",
        "Newsletter unsubscribe link broken",
        "Clicking unsubscribe in promotional emails results in 404 page not found.",
        "Marketing email list manually cleaned and subscriber removed from campaign."
    ),
    (
        "TKT-1051", "CUST-5051", "2026-03-11 08:50:00", "",
        "Delivery & Shipping", "Medium", "Pending",
        "Package marked as signature required but customer at work",
        "Recipient wants parcel redirected to nearby parcel locker or pickup point.",
        "Courier redirection request submitted; awaiting courier confirmation."
    ),
    (
        "TKT-1052", "CUST-5052", "2026-03-11 10:30:00", "2026-03-11 14:15:00",
        "Billing & Refunds", "Low", "Resolved",
        "Incorrect item price on promotional sale",
        "Product advertised at $19.99 on banner was billed at $24.99 in shopping cart.",
        "Price match honored; $5 difference refunded to account balance."
    ),
    (
        "TKT-1053", "CUST-5053", "2026-03-11 12:10:00", "2026-03-12 11:00:00",
        "Delivery & Shipping", "High", "Resolved",
        "Package delayed by weather alert",
        "Transit delayed due to snowstorm in central hub; customer requests estimated ETA.",
        "Shipment tracked and verified moving; delivered on March 12th morning."
    ),
    (
        "TKT-1054", "CUST-5054", "2026-03-11 14:20:00", "",
        "Technical Support", "High", "Open",
        "Mobile app crashing on iOS 17.4",
        "App crashes consistently when opening camera scanner for receipt upload.",
        ""
    ),
    (
        "TKT-1055", "CUST-5055", "2026-03-11 16:40:00", "2026-03-13 10:15:00",
        "Product Quality", "High", "Closed",
        "Ceramic dinner set shattered in transit",
        "3 plates and 2 bowls arrived in pieces due to inadequate bubble wrapping.",
        "Full dinnerware set replaced with reinforced fragile packaging."
    ),
    (
        "TKT-1056", "CUST-5056", "2026-03-12 09:00:00", "2026-03-12 15:30:00",
        "Billing & Refunds", "Medium", "Resolved",
        "Payment receipt not emailed",
        "Completed order #49281 but order confirmation email and receipt were not delivered.",
        "Order receipt re-sent to verified customer email address."
    ),
    (
        "TKT-1057", "CUST-5057", "2026-03-12 10:45:00", "",
        "Delivery & Shipping", "Critical", "Open",
        "Package marked delivered 5 days ago, never arrived",
        "Courier status indicates delivered at front door; home security camera shows no vehicle arrived.",
        ""
    ),
    (
        "TKT-1058", "CUST-5058", "2026-03-12 13:00:00", "2026-03-13 14:00:00",
        "Technical Support", "Medium", "Resolved",
        "Cannot update shipping address on existing order",
        "Order placed 10 minutes ago, address field locked and greyed out.",
        "Support agent updated address in warehouse fulfillment system before packing."
    ),
    (
        "TKT-1059", "CUST-5059", "2026-03-12 15:15:00", "",
        "Customer Service", "High", "Pending",
        "Complaint against delivery driver conduct",
        "Driver was aggressively honking in driveway and threw box onto concrete porch.",
        "Customer safety team initiated incident investigation with third-party logistics."
    ),
    (
        "TKT-1060", "CUST-5060", "2026-03-12 17:00:00", "2026-03-14 09:30:00",
        "Product Quality", "Low", "Closed",
        "Fabric stitching frayed on cushion",
        "Decorative throw pillow arrived with unraveled seam stitching.",
        "$8 partial refund offered and accepted by customer."
    ),
]

HEADERS = [
    "ticket_id", "customer_id", "created_at", "resolved_at",
    "category", "priority", "status", "subject",
    "description", "resolution_notes"
]


def generate():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(HEADERS)
        for row in TICKETS:
            writer.writerow(row)
    print(f"[OK] Generated {len(TICKETS)} records cleanly in: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate()
