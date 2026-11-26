# Lucerne Publishing reporting instructions

## Purpose

Show each customer's September net sales after returns, including accounts with no activity, and identify unmatched transactions.

## Audience

Finance will use the report for its month-end review. Account managers will use it to identify sales, returns, and inactive accounts that need follow-up.

## Inputs

- `data/customer-accounts.csv` contains account IDs, account types, and regions.
- `data/sales-transactions.csv` contains transaction IDs, account IDs, dates, and signed amounts in US cents.

## Outputs

- `reports/customer-account-report.csv` contains one row per known account, with columns `account_id,account_type,region,transaction_count,net_sales_cents`. Sort by account ID.
- `reports/exceptions.csv` contains each unique September transaction with an unknown account, with columns `transaction_id,account_id,transaction_date,amount_cents,reason`. Use `unknown_account` as the reason and sort by transaction ID. Include the header even when there are no exceptions.

Do not add total rows. Generate repeatable outputs without changing the source files.

## Scope

Report September 2026 net sales in USD cents. Do not infer balances, invoices, payments, taxes, or exchange rates. Live connectors and recurring automation are out of scope.

## Human approval

The business analyst must check and approve the report before the pull request is merged.

---

## How to prepare the report

**Reporting period**: Include September 1 through September 30, 2026, inclusive. Exclude all other dates.

**Sales and returns**: Calculate using integer US cents. Add sales and negative returns with their original signs. Count returns and zero-amount transactions as entries.

**Customers**: Match case-sensitive account IDs. Include every known account, setting entry count and net sales to zero when it has no September activity.

**Repeated entries**: Validate and deduplicate the entire transaction file before filtering by date. Count identical rows with the same transaction ID once. If rows sharing an ID differ in any field, stop and request clarification.

## Unmatched customers

**Unmatched entries**: Put each unique September transaction whose account ID is unknown in the exceptions report, preserving its original amount and sign. Do not include it in customer totals or guess its customer.

## When to stop

**Problems with the files**: Stop if headers or row fields are missing, extra, malformed, empty, or have leading or trailing whitespace; if a date is not a real date in `YYYY-MM-DD` format; if an amount is not a valid signed integer in cents; or if an account ID is duplicated. Amounts must not have a plus sign, decimal point, grouping separators, leading zeros except `0`, or negative zero. Validate all rows, including those outside September. Explain the affected records and do not produce partial reports.

---

## Expected results

Enter whole numbers in cents, without dollar signs or commas.

A100: T001, T002, and T003; 12500 + 7500 - 2000 = 18000.
A200: T004 and T005; 4500 - 500 = 4000.

| Account ID | Entry count | Net sales in cents |
| --- | --- | --- |
| A100 | 3 | 18000 |
| A200 | 2 | 4000 |

The known-customer and unmatched totals must add up to the independently calculated total of all unique September entries.

| Check | Expected amount in cents |
| --- | --- |
| Known customers | 22800 |
| Unmatched customers | 2750 |
| All September entries | 25550 |
