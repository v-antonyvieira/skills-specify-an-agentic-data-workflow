import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src/generate_report.py"
ACCOUNTS = ROOT / "data/customer-accounts.csv"
TRANSACTIONS = ROOT / "data/sales-transactions.csv"


class GenerateReportTests(unittest.TestCase):
    def run_generator(self, accounts, transactions, output_dir):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--accounts",
                str(accounts),
                "--transactions",
                str(transactions),
                "--output-dir",
                str(output_dir),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_generation_is_repeatable_and_preserves_sources(self):
        accounts_before = ACCOUNTS.read_bytes()
        transactions_before = TRANSACTIONS.read_bytes()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "new-reports"
            first = self.run_generator(ACCOUNTS, TRANSACTIONS, output_dir)
            self.assertEqual(first.returncode, 0, first.stderr)
            first_outputs = {
                path.name: path.read_bytes() for path in output_dir.iterdir()
            }

            second = self.run_generator(ACCOUNTS, TRANSACTIONS, output_dir)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(
                first_outputs,
                {path.name: path.read_bytes() for path in output_dir.iterdir()},
            )

        self.assertEqual(ACCOUNTS.read_bytes(), accounts_before)
        self.assertEqual(TRANSACTIONS.read_bytes(), transactions_before)
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "reports"
            result = self.run_generator(ACCOUNTS, TRANSACTIONS, output_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            with (output_dir / "customer-account-report.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                report = list(csv.DictReader(handle))
            with (output_dir / "exceptions.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                exceptions = list(csv.DictReader(handle))

        self.assertEqual(
            report,
            [
                {
                    "account_id": "A100",
                    "account_type": "Retail",
                    "region": "North",
                    "transaction_count": "3",
                    "net_sales_cents": "18000",
                },
                {
                    "account_id": "A200",
                    "account_type": "Distributor",
                    "region": "West",
                    "transaction_count": "2",
                    "net_sales_cents": "4000",
                },
                {
                    "account_id": "A300",
                    "account_type": "Retail",
                    "region": "East",
                    "transaction_count": "2",
                    "net_sales_cents": "2000",
                },
                {
                    "account_id": "A400",
                    "account_type": "Retail",
                    "region": "South",
                    "transaction_count": "0",
                    "net_sales_cents": "0",
                },
                {
                    "account_id": "A500",
                    "account_type": "Wholesale",
                    "region": "North",
                    "transaction_count": "1",
                    "net_sales_cents": "-1200",
                },
            ],
        )
        self.assertEqual(
            exceptions,
            [
                {
                    "transaction_id": "T009",
                    "account_id": "X900",
                    "transaction_date": "2026-09-30",
                    "amount_cents": "3000",
                    "reason": "unknown_account",
                },
                {
                    "transaction_id": "T010",
                    "account_id": "X900",
                    "transaction_date": "2026-09-14",
                    "amount_cents": "-250",
                    "reason": "unknown_account",
                },
            ],
        )

    def test_supplied_invalid_fixtures_fail_without_reports(self):
        fixtures = ROOT / "verification/fixtures"
        cases = [
            (fixtures / "duplicate-accounts.csv", TRANSACTIONS),
            (ACCOUNTS, fixtures / "conflicting-transactions.csv"),
            (ACCOUNTS, fixtures / "invalid-amount.csv"),
        ]
        for accounts, transactions in cases:
            with self.subTest(fixture=transactions.name if transactions != TRANSACTIONS else accounts.name):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    output_dir = Path(temporary_directory) / "reports"
                    result = self.run_generator(accounts, transactions, output_dir)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertTrue(result.stderr.strip())
                    self.assertFalse(output_dir.exists())

    def test_invalid_input_does_not_replace_existing_reports(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "reports"
            output_dir.mkdir()
            report = output_dir / "customer-account-report.csv"
            exceptions = output_dir / "exceptions.csv"
            report.write_text("existing report\n", encoding="utf-8")
            exceptions.write_text("existing exceptions\n", encoding="utf-8")
            before = (report.read_bytes(), exceptions.read_bytes())

            result = self.run_generator(
                ACCOUNTS,
                ROOT / "verification/fixtures/invalid-amount.csv",
                output_dir,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(result.stderr.strip())
            self.assertEqual((report.read_bytes(), exceptions.read_bytes()), before)

    def test_invalid_dates_and_noncanonical_amounts_fail(self):
        invalid_rows = [
            ("BAD001,A100,2026-02-30,1\n", "date"),
            ("BAD001,A100,2026-09-01,01\n", "amount"),
            ("BAD001,A100,2026-09-01,-0\n", "amount"),
            ("BAD001,A100,2026-09-01,+1\n", "amount"),
            ("BAD001,A100,2026-09-01,1,extra\n", "fields"),
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            for row, expected_message in invalid_rows:
                with self.subTest(row=row):
                    transaction_path = temporary_path / "transactions.csv"
                    transaction_path.write_text(
                        "transaction_id,account_id,transaction_date,amount_cents\n"
                        + row,
                        encoding="utf-8",
                    )
                    output_dir = temporary_path / "reports"
                    result = self.run_generator(ACCOUNTS, transaction_path, output_dir)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected_message, result.stderr)
                    self.assertFalse(output_dir.exists())

    def test_no_exception_rows_still_produce_header(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            transactions = directory / "transactions.csv"
            transactions.write_text(
                "transaction_id,account_id,transaction_date,amount_cents\n"
                "T001,A100,2026-08-31,1\n",
                encoding="utf-8",
            )
            output_dir = directory / "reports"
            result = self.run_generator(ACCOUNTS, transactions, output_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (output_dir / "exceptions.csv")
                .read_text(encoding="utf-8")
                .splitlines(),
                ["transaction_id,account_id,transaction_date,amount_cents,reason"],
            )


if __name__ == "__main__":
    unittest.main()
