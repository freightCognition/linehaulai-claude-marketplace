# QuickBooks API Integration Plugin

A comprehensive Claude Code plugin for developers building integrations between ERP, CRM, TMS, and other business systems with QuickBooks Online API.

## Overview

The QuickBooks API Integration plugin provides expert guidance, code examples, and workflows for integrating your applications with QuickBooks Online. Whether you're building invoice automation, payment processing, customer management, or full accounting system synchronization, this plugin delivers production-ready patterns and best practices.

## What It Does

This plugin helps developers:

- **OAuth2 Authentication**: Set up and manage QuickBooks API authentication with automatic token refresh
- **Invoice Management**: Create, update, and send invoices with line items, taxes, and custom fields
- **Payment Processing**: Record payments, handle partial payments, and apply payments across multiple invoices
- **Accounting Design Reviews**: Review A/P and A/R ownership, allocation-based reconciliation, and provider overlap; includes a [Laneweaver reference](skills/references/laneweaver-accounting.md)
- **Data Synchronization**: Implement Change Data Capture (CDC) polling and webhook-based real-time sync
- **Batch Operations**: Efficiently process bulk creates, updates, and queries (up to 30 operations per request)
- **Error Handling**: Troubleshoot common API errors with specific resolution patterns
- **Entity Management**: Work with customers, items, accounts, vendors, and all QuickBooks entities
- **Query Language**: Filter and search QuickBooks data using SQL-like query syntax

## Target Audience

This plugin is designed for:

- **Backend Developers** integrating business systems with QuickBooks
- **ERP/CRM Developers** building accounting synchronization features
- **TMS Developers** connecting transportation systems to QuickBooks for invoicing
- **Integration Engineers** automating bookkeeping and financial workflows
- **API Developers** working with QuickBooks Online REST API

## Installation

### From CloudMachines Marketplace

```bash
# Add the CloudMachines marketplace
/plugin marketplace add /Users/linehaul.ai/Developer/repositories/dotfiles cloudmachines-marketplace

# Install the plugin
/plugin install quickbooks-api-integration@cloudmachines-marketplace
```

### From Local Development

```bash
# Add the local plugin directory as a marketplace
/plugin marketplace add /path/to/quickbooks-api-integration

# Install the plugin
/plugin install quickbooks-api-integration@local-dev
```

## Usage

The plugin provides a single command with multiple topic-based workflows:

### Get Started

```bash
/quickbooks
```

Shows an overview of capabilities and available topics.

### Authentication Setup

```bash
/quickbooks auth
```

Guides you through OAuth2 setup, token management, and refresh patterns with Node.js and Python examples.

### Invoice Workflows

```bash
/quickbooks invoice
```

Step-by-step invoice creation including customer lookup, line items, tax handling, and email delivery.

### Payment Recording

```bash
/quickbooks payment
```

Payment application patterns for single invoices, multiple invoices, partial payments, and overpayment handling.

### Data Synchronization

```bash
/quickbooks sync
```

Setup Change Data Capture (CDC) polling or real-time webhooks for keeping systems in sync with QuickBooks.

### Error Troubleshooting

```bash
/quickbooks debug
```

Interactive troubleshooting for common API errors with specific code examples and resolution patterns.

### Batch Operations

```bash
/quickbooks batch
```

Efficient bulk processing patterns for creating, updating, and querying multiple records in a single API call.

### Entity-Specific Operations

```bash
/quickbooks customer
/quickbooks item
/quickbooks account
```

CRUD operations, required fields, and best practices for specific QuickBooks entities.

### Query Language

```bash
/quickbooks query
```

SQL-like filtering syntax, operators, pagination patterns, and query optimization techniques.

## Features

### Comprehensive Code Examples

- **6 Production-Ready Examples**: OAuth2 refresh, invoice creation, customer updates, filtered queries, batch operations, payment application
- **Multi-Language Support**: Node.js and Python examples throughout
- **Error Handling**: All examples include proper exception handling and retry logic
- **Best Practices**: Security, performance, and data integrity patterns

### Complete Workflow Guidance

- **End-to-End Processes**: Complete workflows from authentication through entity management
- **Common Pitfalls**: What to avoid and how to prevent common mistakes
- **Decision Matrices**: When to use CDC vs webhooks, batch vs individual operations
- **Integration Patterns**: Proven approaches for ERP, CRM, and TMS integrations

### Expert Knowledge Base

- **92KB Comprehensive Skill**: Detailed reference covering all aspects of QuickBooks Online API
- **40+ Sections**: Authentication, entities, CRUD operations, queries, batch ops, error handling, webhooks, CDC
- **Context7 Integration**: Automatically stays current with latest QuickBooks API documentation
- **Troubleshooting Guide**: 8+ common error scenarios with specific resolutions

## Available Topics

| Topic | Command | Description |
|-------|---------|-------------|
| Overview | `/quickbooks` | Plugin capabilities and topic menu |
| Authentication | `/quickbooks auth` | OAuth2 setup and token management |
| Invoices | `/quickbooks invoice` | Create and manage invoices |
| Payments | `/quickbooks payment` | Record and apply payments |
| Synchronization | `/quickbooks sync` | CDC and webhook configuration |
| Debugging | `/quickbooks debug` | Error troubleshooting |
| Batch Operations | `/quickbooks batch` | Bulk processing patterns |
| Customers | `/quickbooks customer` | Customer CRUD operations |
| Items | `/quickbooks item` | Product/service item management |
| Accounts | `/quickbooks account` | Chart of accounts operations |
| Queries | `/quickbooks query` | Query language and filtering |

## Example Use Cases

### ERP Integration
Synchronize order data from your ERP to QuickBooks invoices, automatically creating customers and applying payments as they're received.

### Invoice Automation
Automatically generate and send QuickBooks invoices when orders are fulfilled in your e-commerce or order management system.

### Payment Reconciliation
Record payments from your payment gateway (Stripe, Square, etc.) against QuickBooks invoices for automatic bookkeeping.

### Multi-System Sync
Keep customer data synchronized across your CRM, QuickBooks, and support systems using CDC polling or webhooks.

### Financial Reporting
Query QuickBooks data for custom reporting, analytics, and dashboards in your application.

### Data Migration
Batch import historical data into QuickBooks from legacy accounting systems.

## Technical Requirements

- **QuickBooks Online Account**: Sandbox or production company
- **Developer Account**: Register at developer.intuit.com
- **OAuth2 Credentials**: Client ID and Client Secret from Intuit Developer Portal
- **Claude Code**: Latest version installed

## Support & Resources

- **Plugin Documentation**: See [PLUGIN_OVERVIEW.md](PLUGIN_OVERVIEW.md) for architecture details
- **Installation Guide**: See [INSTALL.md](INSTALL.md) for detailed installation steps
- **Quick Start**: See [QUICK_START.md](QUICK_START.md) for fastest path to first integration
- **QuickBooks API Docs**: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/invoice

## Version

Current Version: 1.0.0

## Author

CloudMachines

## Keywords

quickbooks, api, integration, oauth2, accounting, erp, crm, invoicing, payments, bookkeeping

---

Ready to integrate with QuickBooks? Start with `/quickbooks` to see all available workflows.
