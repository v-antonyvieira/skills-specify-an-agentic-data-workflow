# Lucerne Publishing reporting instructions

## Purpose

Prepare a monthly customer account report and reconcile it against the sales transaction file.

## Audience

The business analyst uses the report to review account-level sales, returns, and transactions that could not be matched to a customer account.

## Inputs

- `data/customer-accounts.csv` is the account reference list. `account_id` identifies each customer; `account_type` and `region` are descriptive fields.
- `data/sales-transactions.csv` contains transaction IDs, account IDs, dates, and signed amounts in cents. Positive amounts are sales and negative amounts are returns or credits.

## Outputs

- `reports/customer-account-report.csv` must contain one row per account in the customer account file, including accounts with no activity. Include `account_id`, the count of distinct transactions, and net sales in cents.
- `reports/exceptions.csv` must contain each distinct transaction for an account ID not present in the customer account file, including its transaction ID, account ID, date, and amount in cents.

## Scope

Use transactions dated September 1 through September 30, 2026, inclusive. Amounts are in US dollars represented as whole cents; do not convert or round them. This report does not cover other months, taxes, currency conversion, or account balances.

## Human approval

The business analyst must check and approve the report before the pull request is merged.

------------------------------

## How to prepare the report

**Reporting period**: Include only transactions whose date is from 2026-09-01 through 2026-09-30, inclusive. Exclude dates outside that period.

**Sales and returns**: Amounts are signed integer cents. Sum positive sales and negative returns/credits to calculate net sales. Count returns as transactions.

**Customers**: Match transactions to the customer reference by exact `account_id`. Include every account in the reference list, even if it has no September transactions; report zero entries and zero net sales for those accounts.

**Repeated entries**: Count each distinct `transaction_id` once. Ignore a repeated row if all of its fields are identical to the first occurrence. Stop and request clarification if the same transaction ID appears with different field values.

## Unmatched customers

**Unmatched entries**: Do not include transactions for unknown account IDs in the customer account report. Include each distinct transaction in `reports/exceptions.csv` and include its net amount in the unmatched-customer reconciliation check.

## When to stop

**Problems with the files**: Stop if a required column is missing, a date cannot be parsed, an amount is not a whole number of cents, or a transaction ID is duplicated with conflicting values. Do not guess or silently discard invalid data. Unknown account IDs are recorded as exceptions rather than treated as file errors.

------------------------------

## Expected results

These expected results are for the supplied test data. Enter whole numbers in cents, without dollar signs or commas. Entry counts include distinct transaction IDs and exclude the repeated identical row `T002`.

| Account ID | Entry count | Net sales in cents |
|------------|-------------|--------------------|
| A100       | 3           | 18000              |
| A200       | 2           | 4000               |
| A300       | 2           | 2000               |
| A400       | 0           | 0                  |
| A500       | 1           | -1200              |

| Check                 | Expected amount in cents |
|-----------------------|--------------------------|
| Known customers       | 22800                    |
| Unmatched customers   | 2750                     |
| All September entries | 25550                    |
