# Laneweaver QuickBooks accounting design

Reviewed against Laneweaver commit `35225c74c` on 2026-09-27 for
[issue #146](https://github.com/freightCognition/laneweaverTMS/issues/146).
Paths below are relative to the Laneweaver repository, not this plugin. Verify the
current implementation before making changes; this reference separates established
ownership rules from proposed integration behavior and unresolved settlement gaps.

## Ownership already implemented

- **A/R belongs to the tender/customer order.** `customer_invoices.tender_id` is
  required; account/tender and optional load/tender relationships are constrained.
  Only one non-void invoice may be active per tender. Export identity is the invoice
  ID, not the load or tender alone: void/reissue produces a new invoice ID. A TONU
  and replacement load must not create two receivables for the same order.
- **A/P belongs to a load execution and its carrier.** Keep each `carrier_bills.id`
  distinct, with its validated load and carrier. TONU and replacement bills can name
  different carriers; never merge those liabilities merely because they share a tender.
- These boundaries were implemented by
  [#1213](https://github.com/freightCognition/laneweaverTMS/issues/1213) and
  [#1214](https://github.com/freightCognition/laneweaverTMS/issues/1214).
  Use the invoice and bill records, not legacy per-load customer paid/invoiced flags.

Sources: `internal/services/customer_invoice.go`, `internal/services/carrier_bill.go`,
`supabase/migrations/20260925120000_customer_invoices_tender_ownership.sql`,
`supabase/migrations/20260924120100_carrier_bills_require_load.sql`.

## Resolve Meow overlap before publishing A/P

Meow already executes carrier payments and can sync bills to QuickBooks. Laneweaver's
`meowBillRequest` creates one Meow bill per **carrier payment**, with the payment's
local bill allocations represented as lines. Issue #146's proposed one-QuickBooks-Bill
per local CarrierBill mapping therefore differs from the existing provider grouping.

Specify one A/P publisher for each payable before enabling direct bill export. Define
how Meow-originated QuickBooks bills/payments correlate with existing local records.
Observing the same settlement through Meow and QuickBooks must not create a second
payment or allocation. Do not bypass the locks on Meow-submitted payments; Meow
reconciliation updates payment state and bill rollups transactionally.

The billed carrier and remittance payee are separate identities. Existing Meow code
resolves factoring companies and freezes payee details. Specify how the QuickBooks
vendor and factor remittance are represented without losing carrier attribution;
do not automatically replace the carrier vendor with the factor.

Sources: `internal/services/meow_submission.go` (`meowBillRequest`, payee resolution),
`internal/services/meow.go` (`meowBillPaySettings`),
`internal/services/carrier_payment.go`, `internal/repository/meow.go`,
[Meow follow-up #1257](https://github.com/freightCognition/laneweaverTMS/issues/1257).

## Reconcile the payment ledgers

| Side | Payment records | Allocations | Derived state |
| --- | --- | --- | --- |
| A/R | `customer_payments` | `customer_payment_invoices` | `CustomerPaymentRepository.TxSyncInvoices` |
| A/P | `carrier_payments` | `carrier_payment_bills` | `CarrierPaymentRepository.TxSyncBills` |

Import remote payment identity and allocations through the appropriate service and
transactional workflow. Support partial payments and multiple documents per payment.
Do not use legacy invoice `MarkPaid` as a scheduled import: it increments paid amounts
on replay, while receipt-ledger reconciliation can later overwrite those amounts.
A/R must also preserve unapplied receipts. Define reversals and allocation corrections;
unsupported credits/refunds need an actionable exception, not a status approximation.

**Known QuickPay gap:** A/P exposes gross amount, fee, and net amount, but
`TxSyncBills` compares settled allocations against gross `carrier_bills.amount`.
Specify how a $1,000 liability, $20 fee, and $980 cash settlement fully discharge the
bill without inventing $1,000 of cash. This is a gap to resolve, not established correct
behavior. Keep carrier QuickPay treatment separate from customer invoice revenue.

Sources: `internal/services/customer_payment.go`,
`internal/repository/customer_payment.go`, `internal/repository/customer_invoice.go`,
`internal/repository/carrier_payment.go`, `internal/models/financial.go`.

## Posting and document lifecycle

**Recommendation for #146:** export customer invoices on issuance/successful sending,
not draft creation. Creation currently produces an editable draft; successful sending
uses River and a transaction that queues Princeton invoice work and marks the invoice
sent. Add durable QuickBooks work at the chosen boundary without sending another email.
If draft export is explicitly required, specify its accounting consequences and update
behavior rather than assuming local and QuickBooks draft semantics match.

Export carrier bills after local approval. Approval evidence matters: payment
reservations can change a bill's status to scheduled. Specify post-export edits,
variance, voids, remote edits, and conflicts rather than treating every status as an
interchangeable QuickBooks field.

Use the saved customer invoice's complete line items and exact total. The billing
queue includes linehaul and customer accessorials; charged cancellations may include
accessorials only. Do not rebuild invoices from one load's `customer_rate`.

Local invoice void currently soft-deletes and marks Cancelled; that alone does not
void an external accounting transaction. Preserve remote mappings and durable void
work. Define handling for already-paid documents and preserve both identities on reissue.

Sources: `internal/services/customer_invoice.go` (creation, sending, void),
`internal/services/billing.go`, `internal/repository/customer_invoice.go`,
`supabase/migrations/20260925130000_tender_ar_billable_amounts.sql`.

## Repository patterns and acceptance evidence

Reuse River/outbox delivery (`internal/jobs/meow_outbox.go`), encrypted integration
credentials (`internal/repository/meow.go`, `internal/repository/slack.go`), and
expiring OAuth state. A deployment serves one brokerage; preserve organization RLS
without introducing multi-brokerage selectors. Issue #146 names two different token
stores; resolve that inconsistency against the actual schema before creating tables.

For implementation, include focused checks for:

- One customer invoice and separate carrier bills across TONU/replacement attempts.
- Chosen draft/approval export boundaries and exact invoice line/total parity.
- Replayed partial payments, multi-document allocations, and unapplied customer cash.
- Meow/QuickBooks duplicate observations and factor changes after submission.
- Gross/fee/net QuickPay settlement, void/reissue, and payment reversal balances.
- Lost create responses, remote edit conflicts, and reconnecting to a different realm.

A spec review reports gaps; it does not authorize editing GitHub issues, publishing
transactions, or changing provider configuration. Follow the user's requested scope.
