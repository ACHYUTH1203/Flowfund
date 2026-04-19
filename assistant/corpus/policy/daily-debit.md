# How Daily Debit Works

ClickPe Lite converts your monthly loan burden into small daily repayments. Each day, the system attempts to debit the daily repayment amount from your linked wallet. This happens automatically once per day in the morning.

The order of operations each day is:
1. Your wallet accrues whatever income you add to it.
2. The system checks whether your wallet balance is at least the daily repayment amount.
3. If yes, the amount is debited and the payment is recorded as successful.
4. If not, the payment is marked as skipped and no money is taken.

The daily repayment amount is fixed when the loan is created and does not change day to day. It is calculated from the total payable (principal plus flat interest) divided by the loan duration in days, and capped at a safe percentage of your average daily income.
