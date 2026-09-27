---
name: quickbooks-online-api
description: Design and review QuickBooks Online integrations for A/R invoices, A/P bills, payment reconciliation, OAuth2, and durable synchronization; includes Laneweaver TMS accounting boundaries.
metadata:
  keywords: [quickbooks, accounting, api, oauth2, intuit]
  category: api-integration
  version: 1.0.0
  context7_library: /websites/developer_intuit_app_developer_qbo
---

# QuickBooks Online API Expert Guide

## Overview

The QuickBooks Online API provides comprehensive access to accounting data and operations for QuickBooks Online companies. This skill enables you to build integrations that handle invoicing, payments, customer management, inventory tracking, and financial reporting. The API uses OAuth 2.0 for authentication and supports operations across all major accounting entities including customers, invoices, payments, items, accounts, and more.

The QuickBooks Online API is REST-based, returns JSON or XML responses, and provides SDKs for Java, Python, PHP, Node.js, and C#. It supports both sandbox (development) and production environments.

## When to Use This Skill

Use this skill when:
- Building QuickBooks integrations for accounting automation
- Implementing invoicing workflows or payment processing
- Creating customer or vendor management features
- Working with QuickBooks Online API authentication (OAuth2)
- Troubleshooting API errors or validation failures
- Implementing batch operations for bulk data updates
- Setting up change data capture (CDC) or webhooks for data synchronization
- Designing multi-currency or international accounting integrations
- Building reports or analytics on top of QuickBooks data
- Migrating data to/from QuickBooks Online

## Accounting Integration Design

For accounting sync or specification reviews, trace the existing document and payment
lifecycles before choosing API calls. These requirements govern the simplified API
examples below; examples are not a complete reconciliation implementation.

- **Establish ownership:** identify the local invoice/bill, its business owner, and
  the system authorized to publish it or change settlement. Another provider may
  already publish the same liability to QuickBooks. Match existing records before
  creating more; do not assume every external bill maps one-to-one to a local bill.
- **Separate A/R and A/P:** customer receipts use `Payment`; vendor settlements use
  `BillPayment`. Preserve payment-to-document allocations, partial settlements,
  and unapplied customer cash. Derive balances from the local payment ledger;
  repeatedly setting paid flags or incrementing paid amounts is not reconciliation.
- **Define posting boundaries:** distinguish an editable local draft from an issued
  invoice or approved payable. Choose the export event explicitly. An accounting
  export must not silently send a second customer email or initiate a bank payment.
- **Preserve monetary meaning:** export saved document lines and exact amounts.
  Define item/income/expense mappings, taxes, currency, rounding, fees, credits,
  and gross-versus-net settlement. Excluding full chart-of-accounts sync does not
  eliminate the mappings needed to post transactions.
- **Retain transaction identity:** scope mappings by connection, environment, realm,
  entity type, and local/remote IDs. Include invoices, bills, payments and allocation
  identity, not only customers/vendors. Retain mappings after local voids. A reissue
  is a new document; reconnecting to another company cannot reuse the old mappings.
- **Make delivery recoverable:** persist export work with the business transaction
  and process it through the existing queue/outbox. Saving a remote ID after success
  does not cover a lost create response. Use stable supported request IDs and
  reconciliation for ambiguous outcomes. Use `SyncToken` for updates and apply an
  explicit field-ownership policy before retrying a conflicting accounting edit.
- **Handle corrections:** define voids, credits, refunds, deleted/reallocated
  payments, and replay behavior. Unsupported cases become visible reconciliation
  exceptions; do not silently declare a document paid. Advance polling checkpoints
  only after durable processing; receiving a webhook must not skip a polling window.
- **Protect the connection:** reuse encrypted credential storage, tenant constraints
  and RLS, user/organization-bound expiring OAuth state, and serialized refresh-token
  rotation. Reuse repository patterns instead of adding a second integration framework.

For **Laneweaver TMS** work, read
[Laneweaver A/P and A/R design](references/laneweaver-accounting.md) before proposing
schema, sync triggers, payment imports, or changes to QuickBooks issue #146. Its
repository-specific rules do not apply automatically to other products.

## Authentication & OAuth2 Setup

### OAuth 2.0 Flow

QuickBooks Online API requires OAuth 2.0 authentication. The flow involves:

1. **Register your app** at developer.intuit.com to get Client ID and Client Secret
2. **Direct users to authorization URL** where they grant access to their QuickBooks company
3. **Exchange authorization code for tokens** (access token + refresh token)
4. **Use access token** in API requests (Authorization: Bearer header)
5. **Refresh tokens before expiration** to maintain access

### Token Lifecycle

**Access Tokens**:
- Valid for **3600 seconds (1 hour)**
- Include in Authorization header: `Authorization: Bearer {access_token}`
- Return 401 Unauthorized when expired

**Refresh Tokens**:
- Valid for **100 days** from issuance
- Use to obtain new access token + refresh token pair
- **Previous refresh token expires 24 hours after new one is issued**
- Always use the most recent refresh token

### Token Refresh Pattern

**Node.js Example**:
```javascript
const oauthClient = require('intuit-oauth');

// Refresh access token
oauthClient.refresh()
  .then(function(authResponse) {
    const newAccessToken = authResponse.token.access_token;
    const newRefreshToken = authResponse.token.refresh_token;
    const expiresIn = authResponse.token.expires_in; // 3600 seconds

    // Store new tokens securely (database, encrypted storage)
    console.log('Tokens refreshed successfully');
  })
  .catch(function(e) {
    console.error('Token refresh failed:', e.originalMessage);
    // Handle re-authentication if refresh token is invalid
  });
```

**Python Example**:
```python
from intuitlib.client import AuthClient

auth_client = AuthClient(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    redirect_uri='YOUR_REDIRECT_URI',
    environment='sandbox'  # or 'production'
)

# Refresh tokens
auth_client.refresh(refresh_token='STORED_REFRESH_TOKEN')

# Get new tokens
new_access_token = auth_client.access_token
new_refresh_token = auth_client.refresh_token
```

### Best Practices

- **Refresh proactively**: Refresh tokens before they expire (e.g., after 50 minutes)
- **Store securely**: Encrypt tokens in database, never commit to version control
- **Handle 401 responses**: Automatically attempt token refresh on authentication errors
- **Realm ID (Company ID)**: Store the realmId returned during OAuth - required for all API calls
- **Scopes**: Request only necessary scopes (accounting, payments, etc.)

## Core Entities Reference

### Customer

Represents customers and sub-customers (jobs) in QuickBooks.

**Key Fields**:
- `Id` (string, read-only): Unique identifier
- `DisplayName` (string, required): Customer display name (must be unique)
- `GivenName`, `FamilyName` (string): First and last name
- `CompanyName` (string): Company name for business customers
- `PrimaryEmailAddr` (object): Email address `{ "Address": "email@example.com" }`
- `PrimaryPhone` (object): Phone number `{ "FreeFormNumber": "(555) 123-4567" }`
- `BillAddr`, `ShipAddr` (object): Billing and shipping addresses
- `Balance` (decimal, read-only): Current outstanding balance
- `Active` (boolean): Whether customer is active
- `SyncToken` (string, required for updates): Version number for optimistic locking

**Reference Type**: Use `CustomerRef` in transactions: `{ "value": "123", "name": "Customer Name" }`

### Invoice

Represents sales invoices sent to customers.

**Key Fields**:
- `Id` (string, read-only): Unique identifier
- `DocNumber` (string): Invoice number (auto-generated if not provided)
- `TxnDate` (date): Transaction date (YYYY-MM-DD format)
- `DueDate` (date): Payment due date
- `CustomerRef` (object, required): Reference to customer `{ "value": "customerId" }`
- `Line` (array, required): Invoice line items (see Line Items section)
- `TotalAmt` (decimal, read-only): Calculated total amount
- `Balance` (decimal, read-only): Remaining unpaid balance
- `EmailStatus` (enum): NotSet, NeedToSend, EmailSent
- `BillEmail` (object): Customer email for invoice delivery
- `TxnTaxDetail` (object): Tax calculation details
- `LinkedTxn` (array): Linked transactions (payments, credit memos)
- `SyncToken` (string, required for updates): Version number

**Line Items**:
```json
{
  "Line": [
    {
      "Amount": 100.00,
      "DetailType": "SalesItemLineDetail",
      "SalesItemLineDetail": {
        "ItemRef": { "value": "1", "name": "Services" },
        "Qty": 1,
        "UnitPrice": 100.00,
        "TaxCodeRef": { "value": "TAX" }
      }
    },
    {
      "Amount": 100.00,
      "DetailType": "SubTotalLineDetail",
      "SubTotalLineDetail": {}
    }
  ]
}
```

### Payment

Represents payments received from customers against invoices.

**Key Fields**:
- `Id` (string, read-only): Unique identifier
- `TotalAmt` (decimal, required): Total payment amount
- `CustomerRef` (object, required): Reference to customer
- `PaymentMethodRef` (object): Payment method (cash, check, credit card, etc.)
- `PaymentRefNum` (string): Reference number (check number, transaction ID)
- `TxnDate` (date): Payment date
- `DepositToAccountRef` (object): Bank account for deposit
- `Line` (array): Payment application to invoices/credit memos
- `UnappliedAmt` (decimal, read-only): Amount not applied to invoices
- `SyncToken` (string, required for updates): Version number

**Payment Line Item** (applies payment to invoice):
```json
{
  "Line": [
    {
      "Amount": 100.00,
      "LinkedTxn": [
        {
          "TxnId": "123",
          "TxnType": "Invoice"
        }
      ]
    }
  ]
}
```

### Item

Represents products or services sold.

**Types**:
- `Service`: Services (consulting, labor, etc.)
- `Inventory`: Physical products tracked in inventory
- `NonInventory`: Physical products not tracked
- `Category`: Grouping for other items

**Key Fields**:
- `Id` (string, read-only): Unique identifier
- `Name` (string, required): Item name (must be unique)
- `Type` (enum, required): Service, Inventory, NonInventory, Category
- `Description` (string): Item description
- `UnitPrice` (decimal): Sales price
- `PurchaseCost` (decimal): Purchase/cost price
- `IncomeAccountRef` (object, required): Income account reference
- `ExpenseAccountRef` (object): Expense account for purchases
- `TrackQtyOnHand` (boolean): Whether to track inventory quantity
- `QtyOnHand` (decimal): Current inventory quantity
- `Active` (boolean): Whether item is active

### Account

Represents accounts in the chart of accounts.

**Key Fields**:
- `Id` (string, read-only): Unique identifier
- `Name` (string, required): Account name
- `AccountType` (enum, required): Bank, Accounts Receivable, Accounts Payable, Income, Expense, etc.
- `AccountSubType` (enum): More specific type (CashOnHand, Checking, Savings, etc.)
- `CurrentBalance` (decimal, read-only): Current account balance
- `Active` (boolean): Whether account is active
- `Classification` (enum): Asset, Liability, Equity, Revenue, Expense

**Common Account Types**:
- `Bank`: Bank and cash accounts
- `Accounts Receivable`: Customer balances
- `Accounts Payable`: Vendor balances
- `Income`: Revenue accounts
- `Expense`: Expense accounts
- `Other Current Asset`: Short-term assets
- `Fixed Asset`: Long-term assets

## CRUD Operations Patterns

### Create Operations

**Minimum Required Fields**: Each entity has specific required fields (usually a name/reference and amount).

**Endpoint Pattern**: `POST /v3/company/{realmId}/{entityName}`

**Request Headers**:
```
Authorization: Bearer {access_token}
Accept: application/json
Content-Type: application/json
```

**Python Example - Create Invoice**:
```python
import requests

realm_id = "YOUR_REALM_ID"
access_token = "YOUR_ACCESS_TOKEN"

url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/invoice"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

invoice_data = {
    "Line": [
        {
            "Amount": 100.00,
            "DetailType": "SalesItemLineDetail",
            "SalesItemLineDetail": {
                "ItemRef": {"value": "1"}
            }
        }
    ],
    "CustomerRef": {"value": "1"}
}

response = requests.post(url, json=invoice_data, headers=headers)

if response.status_code == 200:
    invoice = response.json()['Invoice']
    print(f"Invoice created: {invoice['Id']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Read Operations

**Single Entity**: `GET /v3/company/{realmId}/{entityName}/{entityId}`

**Node.js Example - Read Customer**:
```javascript
const axios = require('axios');

async function readCustomer(realmId, customerId, accessToken) {
  const url = `https://sandbox-quickbooks.api.intuit.com/v3/company/${realmId}/customer/${customerId}`;

  try {
    const response = await axios.get(url, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json'
      }
    });

    return response.data.Customer;
  } catch (error) {
    if (error.response && error.response.status === 401) {
      // Token expired, refresh and retry
      console.error('Authentication failed - refresh token needed');
    } else {
      console.error('Read failed:', error.response?.data || error.message);
    }
    throw error;
  }
}
```

### Update Operations

Two types of updates:

**1. Full Update**: All writable fields must be included. Omitted fields are set to NULL.

**2. Sparse Update**: Only specified fields are updated. Set `"sparse": true` in request body.

**Important**: Always include `SyncToken` from the latest read response. This prevents concurrent modification conflicts.

**Python Example - Sparse Update Customer Email**:
```python
import requests

def sparse_update_customer(realm_id, customer_id, sync_token, new_email, access_token):
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/customer"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Sparse update - only updating email
    customer_data = {
        "Id": customer_id,
        "SyncToken": sync_token,
        "sparse": True,
        "PrimaryEmailAddr": {
            "Address": new_email
        }
    }

    response = requests.post(url, json=customer_data, headers=headers)

    if response.status_code == 200:
        updated_customer = response.json()['Customer']
        print(f"Customer updated, new SyncToken: {updated_customer['SyncToken']}")
        return updated_customer
    else:
        print(f"Update failed: {response.text}")
        return None
```

**SyncToken Handling**:
```python
# 1. Read entity to get latest SyncToken
customer = read_customer(realm_id, customer_id, access_token)

# 2. Update with current SyncToken
updated = sparse_update_customer(
    realm_id,
    customer_id,
    customer['SyncToken'],  # Use current sync token
    "newemail@example.com",
    access_token
)

# 3. Store new SyncToken for next update
new_sync_token = updated['SyncToken']
```

### Delete Operations

Most entities use **soft delete** (setting `Active` to false) or **void** operations.

**Soft Delete Pattern**:
```javascript
// Mark customer as inactive
const deleteCustomer = {
  Id: customerId,
  SyncToken: currentSyncToken,
  sparse: true,
  Active: false
};

// POST to update endpoint
axios.post(`${baseUrl}/customer`, deleteCustomer, { headers });
```

**Hard Delete** (limited entities):
`POST /v3/company/{realmId}/{entityName}?operation=delete`

```json
{
  "Id": "123",
  "SyncToken": "2"
}
```

## Query Language & Filtering

QuickBooks uses SQL-like query syntax with limitations.

### Query Syntax

**Basic Pattern**:
```
SELECT * FROM {EntityName} WHERE {field} {operator} '{value}'
```

**Endpoint**: `GET /v3/company/{realmId}/query?query={sqlQuery}`

### Operators

- `=`: Equals
- `<`, `>`, `<=`, `>=`: Comparison
- `IN`: Match any value in list
- `LIKE`: Pattern matching (only `%` wildcard supported, no `_`)

### Examples

**Query customers by name**:
```sql
SELECT * FROM Customer WHERE DisplayName LIKE 'Acme%'
```

**Query invoices by date range**:
```sql
SELECT * FROM Invoice WHERE TxnDate >= '2024-01-01' AND TxnDate <= '2024-12-31'
```

**Query with ordering**:
```sql
SELECT * FROM Customer WHERE Active = true ORDERBY DisplayName
```

**Pagination**:
```sql
SELECT * FROM Invoice STARTPOSITION 1 MAXRESULTS 100
```

**Python Example - Query with Filters**:
```python
import requests
from urllib.parse import quote

def query_invoices_by_customer(realm_id, customer_id, access_token):
    query = f"SELECT * FROM Invoice WHERE CustomerRef = '{customer_id}' ORDERBY TxnDate DESC"
    encoded_query = quote(query)

    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={encoded_query}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        result = response.json()['QueryResponse']
        invoices = result.get('Invoice', [])
        print(f"Found {len(invoices)} invoices")
        return invoices
    else:
        print(f"Query failed: {response.text}")
        return []
```

### Query Limitations

- **No wildcards except %**: LIKE only supports `%` (not `_`)
- **No JOIN operations**: Query single entity at a time
- **Limited functions**: No aggregate functions (SUM, COUNT, etc.)
- **Max 1000 results**: Use pagination for larger result sets
- **All fields returned**: Cannot select specific fields (always returns all)

### Pagination Pattern

```python
def query_all_customers(realm_id, access_token):
    all_customers = []
    start_position = 1
    max_results = 1000

    while True:
        query = f"SELECT * FROM Customer STARTPOSITION {start_position} MAXRESULTS {max_results}"
        encoded_query = quote(query)
        url = f"{base_url}/company/{realm_id}/query?query={encoded_query}"

        response = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
        result = response.json()['QueryResponse']

        customers = result.get('Customer', [])
        if not customers:
            break

        all_customers.extend(customers)

        # Check if more results exist
        if len(customers) < max_results:
            break

        start_position += max_results

    return all_customers
```

## Batch Operations

Batch operations allow multiple API calls in a single HTTP request (up to 30 operations).

### Batch Request Structure

**Endpoint**: `POST /v3/company/{realmId}/batch`

**Request Body**:
```json
{
  "BatchItemRequest": [
    {
      "bId": "bid1",
      "operation": "create",
      "Customer": {
        "DisplayName": "New Customer 1"
      }
    },
    {
      "bId": "bid2",
      "operation": "update",
      "Invoice": {
        "Id": "123",
        "SyncToken": "1",
        "sparse": true,
        "EmailStatus": "NeedToSend"
      }
    },
    {
      "bId": "bid3",
      "operation": "query",
      "Query": "SELECT * FROM Customer WHERE Active = true MAXRESULTS 10"
    }
  ]
}
```

### Batch ID Tracking

Each operation has a unique `bId` (batch ID) for tracking results:

**Response Structure**:
```json
{
  "BatchItemResponse": [
    {
      "bId": "bid1",
      "Customer": {
        "Id": "456",
        "DisplayName": "New Customer 1"
      }
    },
    {
      "bId": "bid2",
      "Invoice": {
        "Id": "123",
        "SyncToken": "2"
      }
    },
    {
      "bId": "bid3",
      "QueryResponse": {
        "Customer": [...]
      }
    }
  ]
}
```

### Node.js Example - Batch Update Customers

```javascript
async function batchUpdateCustomers(realmId, customers, accessToken) {
  const batchItems = customers.map((customer, index) => ({
    bId: `customer_${index}`,
    operation: 'update',
    Customer: {
      Id: customer.Id,
      SyncToken: customer.SyncToken,
      sparse: true,
      Active: true  // Reactivate all customers
    }
  }));

  const url = `https://sandbox-quickbooks.api.intuit.com/v3/company/${realmId}/batch`;

  try {
    const response = await axios.post(url, {
      BatchItemRequest: batchItems
    }, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    });

    const results = response.data.BatchItemResponse;

    // Process results by batch ID
    results.forEach(result => {
      if (result.Fault) {
        console.error(`Error for ${result.bId}:`, result.Fault);
      } else {
        console.log(`Success for ${result.bId}: Customer ${result.Customer.Id}`);
      }
    });

    return results;
  } catch (error) {
    console.error('Batch operation failed:', error.response?.data || error.message);
    throw error;
  }
}
```

### Benefits of Batch Operations

- **Reduced API calls**: 30 operations in one request vs 30 separate requests
- **Lower latency**: Single round-trip instead of multiple
- **Rate limit friendly**: Counts as single API call for rate limiting
- **Atomic per operation**: Each operation succeeds or fails independently

### Batch Operation Types

- `create`: Create new entity
- `update`: Update existing entity
- `delete`: Delete entity
- `query`: Execute query

## Error Handling & Troubleshooting

### HTTP Status Codes

- **200 OK**: Request successful (but may contain `<Fault>` element in body)
- **400 Bad Request**: Invalid syntax or malformed request
- **401 Unauthorized**: Invalid/expired access token
- **403 Forbidden**: Insufficient permissions or restricted resource
- **404 Not Found**: Resource doesn't exist
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side issue (retry once)
- **503 Service Unavailable**: Service temporarily unavailable (retry with backoff)

### Fault Types

Even with 200 OK, response may contain fault element:

```json
{
  "Fault": {
    "Error": [
      {
        "Message": "Duplicate Name Exists Error",
        "Detail": "The name supplied already exists.",
        "code": "6240",
        "element": "Customer.DisplayName"
      }
    ],
    "type": "ValidationFault"
  },
  "time": "2024-12-09T10:30:00.000-08:00"
}
```

**Fault Types**:

1. **ValidationFault**: Invalid request data or business rule violation
   - Fix: Correct request payload, check required fields

2. **SystemFault**: Server-side error
   - Fix: Retry request, contact support if persists

3. **AuthenticationFault**: Invalid credentials
   - Fix: Refresh access token, re-authenticate

4. **AuthorizationFault**: Insufficient permissions
   - Fix: Check OAuth scopes, ensure user has admin access

### Common Error Codes

| Code | Error | Solution |
|------|-------|----------|
| 6000 | Business validation error | Check TotalAmt and required fields |
| 3200 | Stale object (SyncToken mismatch) | Re-read entity to get latest SyncToken |
| 3100 | Invalid reference | Verify referenced entity exists (CustomerRef, ItemRef) |
| 6240 | Duplicate name | Use unique DisplayName for Customer/Item |
| 610 | Object not found | Check entity ID exists |
| 4001 | Invalid token | Refresh access token |

### Exception Handling by SDK

**Java SDK Exceptions**:
- `ValidationException`: Validation faults
- `ServiceException`: Service faults
- `AuthenticationException`: Authentication faults
- `BadRequestException`: 400 status
- `InvalidTokenException`: 401 status
- `InternalServiceException`: 500 status

**Python Exception Handling**:
```python
from intuitlib.exceptions import AuthClientError

try:
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()

    # Check for fault in response body
    result = response.json()
    if 'Fault' in result:
        fault = result['Fault']
        print(f"Fault Type: {fault['type']}")
        for error in fault['Error']:
            print(f"  Code {error['code']}: {error['Message']}")
            print(f"  Element: {error.get('element', 'N/A')}")
        return None

    return result

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        # Token expired, refresh
        print("Token expired, refreshing...")
        # Implement token refresh logic
    elif e.response.status_code == 429:
        # Rate limited, implement backoff
        print("Rate limited, backing off...")
    else:
        print(f"HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")

except AuthClientError as e:
    print(f"Auth error: {str(e)}")
```

### Debugging Strategies

1. **Check response body even with 200**: Fault elements can appear in successful responses
2. **Log intuit_tid**: Include in support requests for faster resolution
3. **Validate SyncToken**: Always use latest version from read operations
4. **Test in sandbox first**: Use sandbox companies for development
5. **Implement retry logic**: Exponential backoff for 500/503 errors
6. **Parse error details**: Check `error.code`, `element`, `message` fields

### Retry Pattern with Exponential Backoff

```javascript
async function apiCallWithRetry(apiFunction, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await apiFunction();
    } catch (error) {
      const status = error.response?.status;

      // Retry on server errors
      if (status >= 500 && status < 600 && attempt < maxRetries - 1) {
        const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
        console.log(`Attempt ${attempt + 1} failed, retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }

      // Don't retry on client errors
      throw error;
    }
  }
}
```

## Change Detection & Webhooks

### Change Data Capture (CDC)

CDC returns entities that changed within a specified timeframe (up to 30 days).

**Endpoint**: `GET /v3/company/{realmId}/cdc?entities={entityList}&changedSince={dateTime}`

**Parameters**:
- `entities`: Comma-separated list (e.g., "Invoice,Customer,Payment")
- `changedSince`: ISO 8601 timestamp (e.g., "2024-12-01T09:00:00-07:00")

**Python Example**:
```python
from datetime import datetime, timedelta
from urllib.parse import urlencode

def get_changed_entities(realm_id, entity_types, since_datetime, access_token):
    # Format: 2024-12-01T09:00:00-07:00
    changed_since = since_datetime.strftime('%Y-%m-%dT%H:%M:%S-07:00')

    params = {
        'entities': ','.join(entity_types),
        'changedSince': changed_since
    }

    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/cdc"

    response = requests.get(
        url,
        params=params,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        cdc_response = response.json()['CDCResponse']

        # Process changed entities
        for query_response in cdc_response:
            entity_type = query_response.get('QueryResponse', [{}])[0]

            for entity_name, entities in entity_type.items():
                if entities:
                    for entity in entities:
                        status = entity.get('status', 'Updated')
                        if status == 'Deleted':
                            print(f"Deleted {entity_name}: {entity['Id']}")
                        else:
                            print(f"Changed {entity_name}: {entity['Id']}")

        return cdc_response
    else:
        print(f"CDC request failed: {response.text}")
        return None

# Usage: Get all invoices and customers changed in last 24 hours
since = datetime.now() - timedelta(hours=24)
changes = get_changed_entities(realm_id, ['Invoice', 'Customer'], since, access_token)
```

**Response Structure**:
```json
{
  "CDCResponse": [
    {
      "QueryResponse": [
        {
          "Invoice": [
            {
              "Id": "123",
              "MetaData": {
                "LastUpdatedTime": "2024-12-09T10:30:00-08:00"
              },
              "TotalAmt": 100.00,
              "Balance": 50.00
              // ... full invoice object
            }
          ]
        }
      ]
    },
    {
      "QueryResponse": [
        {
          "Customer": [
            {
              "Id": "456",
              "status": "Deleted"
            }
          ]
        }
      ]
    }
  ],
  "time": "2024-12-09T11:00:00.000-08:00"
}
```

### CDC Best Practices

- **Query shorter periods**: Max 1000 entities per response, use hourly/daily checks
- **Store last sync time**: Track `LastUpdatedTime` to set `changedSince` parameter
- **Handle deletes**: Entities with `status: "Deleted"` only contain ID
- **Fetch full entity**: CDC returns full payload (not just changes)
- **Combine with webhooks**: Use webhooks for real-time, CDC as backup

### Webhooks (Real-time Notifications)

Webhooks send HTTP POST notifications when data changes.

**Setup**:
1. Configure webhook URL in developer dashboard
2. Implement POST endpoint to receive notifications
3. Return 200 OK within 1 second
4. Process notification asynchronously

**Notification Payload**:
```json
{
  "eventNotifications": [
    {
      "realmId": "123456789",
      "dataChangeEvent": {
        "entities": [
          {
            "name": "Invoice",
            "id": "145",
            "operation": "Create",
            "lastUpdated": "2024-12-09T10:30:00.000Z"
          },
          {
            "name": "Payment",
            "id": "456",
            "operation": "Update",
            "lastUpdated": "2024-12-09T10:31:00.000Z"
          },
          {
            "name": "Customer",
            "id": "789",
            "operation": "Merge",
            "lastUpdated": "2024-12-09T10:32:00.000Z",
            "deletedId": "788"
          }
        ]
      }
    }
  ]
}
```

**Node.js Webhook Handler**:
```javascript
const express = require('express');
const crypto = require('crypto');

const app = express();
app.use(express.json());

// Webhook endpoint
app.post('/webhooks/quickbooks', async (req, res) => {
  // Verify webhook signature (recommended)
  const signature = req.headers['intuit-signature'];
  const payload = JSON.stringify(req.body);

  // Return 200 immediately (process async)
  res.status(200).send('OK');

  // Process notifications asynchronously
  processWebhook(req.body).catch(console.error);
});

async function processWebhook(notification) {
  for (const event of notification.eventNotifications) {
    const realmId = event.realmId;

    for (const entity of event.dataChangeEvent.entities) {
      console.log(`${entity.operation} on ${entity.name} ID ${entity.id}`);

      // Fetch full entity data
      if (entity.operation !== 'Delete') {
        await fetchAndProcessEntity(realmId, entity.name, entity.id);
      } else {
        await handleEntityDeletion(realmId, entity.name, entity.id);
      }
    }
  }
}

async function fetchAndProcessEntity(realmId, entityType, entityId) {
  // Fetch full entity using read endpoint
  const url = `https://quickbooks.api.intuit.com/v3/company/${realmId}/${entityType.toLowerCase()}/${entityId}`;
  // ... implement fetch and processing logic
}
```

### Webhook vs CDC Decision Matrix

| Use Case | Recommendation |
|----------|----------------|
| Real-time sync | Webhooks |
| Periodic sync (hourly/daily) | CDC |
| Initial data load | CDC |
| Reconnection after downtime | CDC |
| High-volume changes | CDC (reduces notification overhead) |
| Low-latency requirements | Webhooks |
| Backup/redundancy | Both (webhooks primary, CDC backup) |

### Combined Approach Pattern

```python
class QuickBooksSync:
    def __init__(self):
        self.last_cdc_sync = self.load_last_sync_time()

    def handle_webhook(self, notification):
        """Process real-time webhook"""
        for entity in notification['dataChangeEvent']['entities']:
            self.process_entity_change(entity)

        # Update last known change time
        self.last_cdc_sync = datetime.now()
        self.save_last_sync_time()

    def periodic_cdc_sync(self):
        """Catch any missed changes"""
        changes = get_changed_entities(
            self.realm_id,
            ['Invoice', 'Customer', 'Payment'],
            self.last_cdc_sync,
            self.access_token
        )

        for entity in self.extract_entities(changes):
            if not self.entity_exists_locally(entity):
                # Missed by webhook, process now
                self.process_entity_change(entity)

        self.last_cdc_sync = datetime.now()
        self.save_last_sync_time()
```

## Best Practices

### Performance Optimization

1. **Use batch operations for bulk changes**
   - Combine up to 30 operations in single request
   - Reduces API calls and improves throughput
   - Example: Batch update 30 customers vs 30 individual updates

2. **Implement CDC or webhooks for syncing**
   - Avoid polling all entities repeatedly
   - CDC returns only changed entities
   - Webhooks provide real-time notifications without polling

3. **Sparse updates minimize payload**
   - Only send fields being changed
   - Reduces data transfer and processing time
   - Prevents accidental field overwrites

4. **Cache reference data locally**
   - Payment methods, tax codes, accounts rarely change
   - Query once and cache with TTL
   - Reduces redundant API calls

5. **Paginate large result sets**
   - Use MAXRESULTS to limit query results
   - Process in batches to avoid memory issues
   - Example: Query 100 customers at a time

### Data Integrity

1. **Always use SyncToken for updates**
   - Prevents concurrent modification conflicts
   - Read entity before update to get latest token
   - Handle 3200 errors by re-reading and retrying

2. **Handle concurrent modifications gracefully**
   ```python
   def safe_update(realm_id, customer_id, changes, access_token):
       max_attempts = 3
       for attempt in range(max_attempts):
           # Read latest version
           customer = read_customer(realm_id, customer_id, access_token)

           # Apply changes
           customer.update(changes)
           customer['sparse'] = True

           # Attempt update
           try:
               return update_customer(realm_id, customer, access_token)
           except SyncTokenError:
               if attempt == max_attempts - 1:
                   raise
               continue  # Retry with fresh SyncToken
   ```

3. **Validate required fields before API calls**
   - Check business rules locally first
   - Reduces validation errors from API
   - Example: Verify customer exists before creating invoice

4. **Use webhooks + CDC for reliable tracking**
   - Webhooks for real-time updates
   - Periodic CDC as backup for missed changes
   - Store last sync timestamp

### Token Management

1. **Access tokens expire after 3600 seconds**
   - Set up automatic refresh before expiration
   - Refresh at 50-minute mark to be safe

2. **Refresh tokens proactively**
   ```javascript
   class TokenManager {
     constructor() {
       this.refreshTimer = null;
     }

     scheduleRefresh(expiresIn) {
       // Refresh 5 minutes before expiration
       const refreshTime = (expiresIn - 300) * 1000;

       this.refreshTimer = setTimeout(() => {
         this.refreshAccessToken();
       }, refreshTime);
     }

     async refreshAccessToken() {
       try {
         const newTokens = await oauthClient.refresh();
         this.storeTokens(newTokens);
         this.scheduleRefresh(newTokens.expires_in);
       } catch (error) {
         // Refresh failed, need re-authentication
         this.handleReauthentication();
       }
     }
   }
   ```

3. **Always use latest refresh token**
   - Previous refresh tokens expire 24 hours after new one issued
   - Store refresh token immediately after refresh
   - Never use old refresh tokens

4. **Store tokens securely**
   - Encrypt in database
   - Never commit to version control
   - Use environment variables for development

5. **Handle 401 responses automatically**
   ```python
   def api_call_with_auto_refresh(api_function):
       try:
           return api_function()
       except Unauthorized401Error:
           # Attempt token refresh
           refresh_tokens()
           # Retry with new token
           return api_function()
   ```

### API Rate Limiting

1. **Implement exponential backoff for 429**
   ```python
   def call_with_rate_limit_handling(api_function):
       max_retries = 5
       base_delay = 1

       for attempt in range(max_retries):
           try:
               return api_function()
           except RateLimitError as e:
               if attempt == max_retries - 1:
                   raise

               delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s, 8s, 16s
               time.sleep(delay)
               continue
   ```

2. **Use batch operations to reduce call count**
   - 1 batch request vs 30 individual = 30x reduction
   - Batch counts as single API call for rate limits

3. **Monitor rate limit headers** (if provided)
   - Some endpoints return rate limit info in headers
   - Track usage to stay within limits

### Multi-currency Considerations

1. **CurrencyRef required when multicurrency enabled**
   ```json
   {
     "Invoice": {
       "CurrencyRef": {
         "value": "USD",
         "name": "United States Dollar"
       }
     }
   }
   ```

2. **Exchange rate handling**
   - API automatically applies exchange rates
   - ExchangeRate field shows conversion rate used
   - Home currency amounts calculated automatically

3. **Locale-specific required fields**
   - France: DocNumber required if custom transaction numbers enabled
   - UK: Different tax handling (VAT)
   - Check locale-specific documentation

### Testing & Development

1. **Use sandbox companies** (free with developer account)
   - Create at developer.intuit.com
   - Separate from production data
   - Full API feature parity

2. **Test OAuth flow end-to-end**
   - Authorization URL → code exchange → token refresh
   - Test token expiration handling
   - Verify refresh token rotation

3. **Validate webhook endpoint**
   - Test with sample payloads
   - Ensure < 1 second response time
   - Handle webhook signature verification

4. **Handle all fault types in production**
   - ValidationFault, SystemFault, AuthenticationFault, AuthorizationFault
   - Log error details (code, message, element)
   - Implement appropriate retry logic

5. **Monitor API calls and errors**
   - Track success/failure rates
   - Alert on elevated error rates
   - Log intuit_tid for support requests

## Common Workflows

### Workflow 1: Create and Send Invoice

**Scenario**: Create an invoice for a customer and send via email.

**Steps**:

1. **Query or create customer**
```python
# Check if customer exists
customers = query_customers_by_email(realm_id, "customer@example.com", access_token)

if not customers:
    # Create new customer
    customer = create_customer(realm_id, {
        "DisplayName": "Acme Corp",
        "PrimaryEmailAddr": {"Address": "customer@example.com"},
        "BillAddr": {
            "Line1": "123 Main St",
            "City": "San Francisco",
            "CountrySubDivisionCode": "CA",
            "PostalCode": "94105"
        }
    }, access_token)
else:
    customer = customers[0]

customer_id = customer['Id']
```

2. **Query items for line items**
```python
# Get service item
query = "SELECT * FROM Item WHERE Type = 'Service' AND Name = 'Consulting'"
items = query_entity(realm_id, query, access_token)
service_item = items[0]
```

3. **Create invoice with line items**
```python
invoice_data = {
    "TxnDate": "2024-12-09",
    "DueDate": "2024-12-23",
    "CustomerRef": {"value": customer_id},
    "BillEmail": {"Address": "customer@example.com"},
    "EmailStatus": "NeedToSend",  # Mark for email sending
    "Line": [
        {
            "Amount": 1500.00,
            "DetailType": "SalesItemLineDetail",
            "SalesItemLineDetail": {
                "ItemRef": {"value": service_item['Id']},
                "Qty": 10,
                "UnitPrice": 150.00,
                "TaxCodeRef": {"value": "NON"}  # Non-taxable
            },
            "Description": "Consulting services - December 2024"
        },
        {
            "Amount": 1500.00,
            "DetailType": "SubTotalLineDetail",
            "SubTotalLineDetail": {}
        }
    ]
}

invoice = create_invoice(realm_id, invoice_data, access_token)
print(f"Invoice {invoice['DocNumber']} created: ${invoice['TotalAmt']}")
```

4. **Send invoice email** (automatic if EmailStatus = "NeedToSend")
```python
# QuickBooks automatically sends email when EmailStatus is NeedToSend
# Alternatively, use send endpoint:
send_url = f"{base_url}/company/{realm_id}/invoice/{invoice['Id']}/send"
params = {"sendTo": "customer@example.com"}

response = requests.post(send_url, params=params, headers=headers)
if response.status_code == 200:
    print(f"Invoice sent to {customer['PrimaryEmailAddr']['Address']}")
```

5. **Handle response and linked transactions**
```python
# Check invoice status
print(f"Invoice ID: {invoice['Id']}")
print(f"Balance: ${invoice['Balance']}")
print(f"Email Status: {invoice['EmailStatus']}")

# Track linked transactions
if 'LinkedTxn' in invoice:
    for linked in invoice['LinkedTxn']:
        print(f"Linked {linked['TxnType']}: {linked['TxnId']}")
```

### Workflow 2: Record Payment Against Invoice

**Scenario**: Customer pays an invoice via check.

**Steps**:

1. **Query invoice by DocNumber**
```python
def find_invoice_by_number(realm_id, doc_number, access_token):
    query = f"SELECT * FROM Invoice WHERE DocNumber = '{doc_number}'"
    invoices = query_entity(realm_id, query, access_token)

    if not invoices:
        raise ValueError(f"Invoice {doc_number} not found")

    return invoices[0]

invoice = find_invoice_by_number(realm_id, "1045", access_token)
customer_id = invoice['CustomerRef']['value']
balance = invoice['Balance']
```

2. **Create payment entity**
```python
# Get payment method (Check)
payment_methods = query_entity(realm_id, "SELECT * FROM PaymentMethod WHERE Name = 'Check'", access_token)
payment_method_id = payment_methods[0]['Id']

payment_data = {
    "TotalAmt": balance,  # Pay full amount
    "CustomerRef": {"value": customer_id},
    "PaymentMethodRef": {"value": payment_method_id},
    "PaymentRefNum": "1234",  # Check number
    "TxnDate": "2024-12-09",
    "Line": [
        {
            "Amount": balance,
            "LinkedTxn": [
                {
                    "TxnId": invoice['Id'],
                    "TxnType": "Invoice"
                }
            ]
        }
    ]
}

payment = create_payment(realm_id, payment_data, access_token)
```

3. **Verify balance updates**
```python
# Re-read invoice to see updated balance
updated_invoice = read_invoice(realm_id, invoice['Id'], access_token)

print(f"Original balance: ${balance}")
print(f"Payment amount: ${payment['TotalAmt']}")
print(f"New balance: ${updated_invoice['Balance']}")
print(f"Unapplied payment amount: ${payment.get('UnappliedAmt', 0)}")
```

4. **Handle partial payments**
```python
def apply_partial_payment(realm_id, invoice_id, payment_amount, customer_id, access_token):
    payment_data = {
        "TotalAmt": payment_amount,  # Less than invoice balance
        "CustomerRef": {"value": customer_id},
        "Line": [
            {
                "Amount": payment_amount,
                "LinkedTxn": [
                    {
                        "TxnId": invoice_id,
                        "TxnType": "Invoice"
                    }
                ]
            }
        ]
    }

    payment = create_payment(realm_id, payment_data, access_token)

    # Check unapplied amount
    if payment['UnappliedAmt'] > 0:
        print(f"Warning: ${payment['UnappliedAmt']} unapplied (overpayment or error)")

    return payment
```

5. **Apply payment to multiple invoices**
```python
def pay_multiple_invoices(realm_id, invoice_ids, amounts, customer_id, total_paid, access_token):
    lines = []

    for invoice_id, amount in zip(invoice_ids, amounts):
        lines.append({
            "Amount": amount,
            "LinkedTxn": [{
                "TxnId": invoice_id,
                "TxnType": "Invoice"
            }]
        })

    payment_data = {
        "TotalAmt": total_paid,
        "CustomerRef": {"value": customer_id},
        "Line": lines
    }

    return create_payment(realm_id, payment_data, access_token)

# Example: Pay two invoices with single check
payment = pay_multiple_invoices(
    realm_id,
    ["145", "146"],  # Invoice IDs
    [100.00, 50.00],  # Amounts applied to each
    customer_id,
    150.00,  # Total check amount
    access_token
)
```

### Workflow 3: Customer Management

**Scenario**: Complete customer lifecycle management.

**1. Create customer with address**
```python
def create_customer_complete(realm_id, customer_info, access_token):
    customer_data = {
        "DisplayName": customer_info['display_name'],
        "GivenName": customer_info.get('first_name'),
        "FamilyName": customer_info.get('last_name'),
        "CompanyName": customer_info.get('company_name'),
        "PrimaryEmailAddr": {
            "Address": customer_info['email']
        },
        "PrimaryPhone": {
            "FreeFormNumber": customer_info.get('phone')
        },
        "BillAddr": {
            "Line1": customer_info['address_line1'],
            "City": customer_info['city'],
            "CountrySubDivisionCode": customer_info['state'],
            "PostalCode": customer_info['zip']
        },
        "ShipAddr": {
            "Line1": customer_info.get('ship_line1', customer_info['address_line1']),
            "City": customer_info.get('ship_city', customer_info['city']),
            "CountrySubDivisionCode": customer_info.get('ship_state', customer_info['state']),
            "PostalCode": customer_info.get('ship_zip', customer_info['zip'])
        }
    }

    return create_customer(realm_id, customer_data, access_token)
```

**2. Sparse update to modify email**
```python
def update_customer_email(realm_id, customer_id, new_email, access_token):
    # Read current customer
    customer = read_customer(realm_id, customer_id, access_token)

    # Sparse update - only email
    update_data = {
        "Id": customer_id,
        "SyncToken": customer['SyncToken'],
        "sparse": True,
        "PrimaryEmailAddr": {
            "Address": new_email
        }
    }

    return update_customer(realm_id, update_data, access_token)
```

**3. Query customer transactions**
```python
def get_customer_transactions(realm_id, customer_id, access_token):
    transactions = {}

    # Query invoices
    invoice_query = f"SELECT * FROM Invoice WHERE CustomerRef = '{customer_id}'"
    transactions['invoices'] = query_entity(realm_id, invoice_query, access_token)

    # Query payments
    payment_query = f"SELECT * FROM Payment WHERE CustomerRef = '{customer_id}'"
    transactions['payments'] = query_entity(realm_id, payment_query, access_token)

    # Query estimates
    estimate_query = f"SELECT * FROM Estimate WHERE CustomerRef = '{customer_id}'"
    transactions['estimates'] = query_entity(realm_id, estimate_query, access_token)

    # Calculate totals
    total_invoiced = sum(inv['TotalAmt'] for inv in transactions['invoices'])
    total_paid = sum(pmt['TotalAmt'] for pmt in transactions['payments'])

    transactions['summary'] = {
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'balance': total_invoiced - total_paid
    }

    return transactions
```

**4. Update AR account reference**
```python
# Change default AR account for customer
def update_customer_ar_account(realm_id, customer_id, new_ar_account_id, access_token):
    customer = read_customer(realm_id, customer_id, access_token)

    update_data = {
        "Id": customer_id,
        "SyncToken": customer['SyncToken'],
        "sparse": True,
        "ARAccountRef": {
            "value": new_ar_account_id
        }
    }

    return update_customer(realm_id, update_data, access_token)
```

### Workflow 4: Batch Sync Operation

**Scenario**: Sync changed entities using CDC and batch updates.

**1. Use CDC to get changed entities**
```python
from datetime import datetime, timedelta

def sync_changed_entities(realm_id, last_sync_time, access_token):
    # Get changes since last sync
    entity_types = ['Invoice', 'Customer', 'Payment', 'Item']
    changes = get_changed_entities(realm_id, entity_types, last_sync_time, access_token)

    return changes
```

**2. Build batch operation with updates**
```python
def build_batch_updates(changes):
    batch_items = []
    bid_counter = 0

    # Process each entity type
    for entity_type in ['Customer', 'Invoice', 'Payment']:
        entities = extract_entities_by_type(changes, entity_type)

        for entity in entities:
            if entity.get('status') == 'Deleted':
                # Skip deleted entities or handle separately
                continue

            # Example: Mark all invoices as reviewed
            if entity_type == 'Invoice':
                batch_items.append({
                    "bId": f"invoice_{bid_counter}",
                    "operation": "update",
                    "Invoice": {
                        "Id": entity['Id'],
                        "SyncToken": entity['SyncToken'],
                        "sparse": True,
                        "PrivateNote": f"Synced at {datetime.now().isoformat()}"
                    }
                })
                bid_counter += 1

    return batch_items
```

**3. Execute batch asynchronously**
```python
async def execute_batch_sync(realm_id, batch_items, access_token):
    # Split into batches of 30 (API limit)
    batch_size = 30
    results = []

    for i in range(0, len(batch_items), batch_size):
        batch_chunk = batch_items[i:i+batch_size]

        batch_request = {
            "BatchItemRequest": batch_chunk
        }

        url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/batch"

        response = await async_post(url, batch_request, {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })

        if response.status == 200:
            batch_response = response.json()
            results.extend(batch_response['BatchItemResponse'])
        else:
            print(f"Batch {i//batch_size + 1} failed: {response.text}")

    return results
```

**4. Process batch responses by batch ID**
```python
def process_batch_results(batch_results):
    success_count = 0
    error_count = 0
    errors = []

    for result in batch_results:
        bid = result['bId']

        if 'Fault' in result:
            error_count += 1
            fault = result['Fault']
            errors.append({
                'batch_id': bid,
                'error_code': fault['Error'][0]['code'],
                'message': fault['Error'][0]['Message']
            })
            print(f"Error in {bid}: {fault['Error'][0]['Message']}")
        else:
            success_count += 1
            # Extract updated entity
            entity_type = list(result.keys())[0]
            if entity_type != 'bId':
                entity = result[entity_type]
                print(f"Success {bid}: {entity_type} {entity['Id']} updated")

    summary = {
        'total': len(batch_results),
        'success': success_count,
        'errors': error_count,
        'error_details': errors
    }

    return summary

# Complete workflow
async def sync_workflow(realm_id, last_sync_time, access_token):
    # 1. Get changes via CDC
    changes = sync_changed_entities(realm_id, last_sync_time, access_token)

    # 2. Build batch updates
    batch_items = build_batch_updates(changes)

    if not batch_items:
        print("No changes to sync")
        return

    # 3. Execute batch
    results = await execute_batch_sync(realm_id, batch_items, access_token)

    # 4. Process results
    summary = process_batch_results(results)

    print(f"Sync complete: {summary['success']}/{summary['total']} successful")
    if summary['errors'] > 0:
        print(f"Errors encountered: {summary['errors']}")
        for error in summary['error_details']:
            print(f"  {error['batch_id']}: {error['message']}")

    return summary
```

## Code Examples

### Example 1: OAuth2 Token Refresh (Node.js)

Complete token management with automatic refresh:

```javascript
const OAuthClient = require('intuit-oauth');

class QuickBooksAuth {
  constructor(clientId, clientSecret, redirectUri, environment = 'sandbox') {
    this.oauthClient = new OAuthClient({
      clientId: clientId,
      clientSecret: clientSecret,
      environment: environment,
      redirectUri: redirectUri
    });

    this.accessToken = null;
    this.refreshToken = null;
    this.tokenExpiry = null;
    this.refreshTimer = null;
  }

  // Store tokens after authorization
  async storeTokens(authResponse) {
    this.accessToken = authResponse.token.access_token;
    this.refreshToken = authResponse.token.refresh_token;

    // Calculate expiry time
    const expiresIn = authResponse.token.expires_in; // 3600 seconds
    this.tokenExpiry = Date.now() + (expiresIn * 1000);

    // Schedule automatic refresh (5 minutes before expiry)
    this.scheduleRefresh(expiresIn - 300);

    // Persist tokens to secure storage
    await this.saveToDatabase({
      access_token: this.accessToken,
      refresh_token: this.refreshToken,
      expiry: this.tokenExpiry
    });
  }

  // Schedule automatic token refresh
  scheduleRefresh(delaySeconds) {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    this.refreshTimer = setTimeout(async () => {
      try {
        await this.refreshAccessToken();
      } catch (error) {
        console.error('Scheduled token refresh failed:', error);
        // Notify admin that re-authentication needed
        this.notifyReauthenticationNeeded();
      }
    }, delaySeconds * 1000);
  }

  // Refresh access token
  async refreshAccessToken() {
    try {
      // Set refresh token in client
      this.oauthClient.setToken({
        refresh_token: this.refreshToken
      });

      // Refresh
      const authResponse = await this.oauthClient.refresh();

      console.log('Token refreshed successfully');

      // Store new tokens
      await this.storeTokens(authResponse);

      return authResponse;

    } catch (error) {
      console.error('Token refresh failed:', error.originalMessage);

      // Check if refresh token is invalid
      if (error.error === 'invalid_grant') {
        console.error('Refresh token invalid - re-authentication required');
        this.accessToken = null;
        this.refreshToken = null;
        throw new Error('Re-authentication required');
      }

      throw error;
    }
  }

  // Get valid access token (refresh if needed)
  async getAccessToken() {
    // Check if token is about to expire (within 5 minutes)
    const bufferTime = 5 * 60 * 1000; // 5 minutes

    if (!this.accessToken || Date.now() >= (this.tokenExpiry - bufferTime)) {
      console.log('Token expired or expiring soon, refreshing...');
      await this.refreshAccessToken();
    }

    return this.accessToken;
  }

  // Make API call with automatic token refresh
  async apiCall(url, options = {}) {
    try {
      const token = await this.getAccessToken();

      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json'
        }
      });

      // Handle 401 - token might have expired
      if (response.status === 401) {
        console.log('401 Unauthorized - refreshing token and retrying...');
        await this.refreshAccessToken();

        // Retry with new token
        const newToken = await this.getAccessToken();
        return fetch(url, {
          ...options,
          headers: {
            ...options.headers,
            'Authorization': `Bearer ${newToken}`,
            'Accept': 'application/json'
          }
        });
      }

      return response;

    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    }
  }

  // Save tokens to database (implement based on your storage)
  async saveToDatabase(tokens) {
    // Example: Save to database
    // await db.tokens.update({ realmId }, tokens);
  }

  // Notify admin about re-auth requirement
  notifyReauthenticationNeeded() {
    // Example: Send email or notification
    console.error('Re-authentication required for QuickBooks integration');
  }
}

// Usage
const auth = new QuickBooksAuth(
  'YOUR_CLIENT_ID',
  'YOUR_CLIENT_SECRET',
  'https://yourapp.com/callback',
  'sandbox'
);

// After OAuth authorization
auth.storeTokens(authResponse);

// Make API calls - automatic token refresh
const response = await auth.apiCall(
  'https://sandbox-quickbooks.api.intuit.com/v3/company/123/customer/456',
  { method: 'GET' }
);
```

### Example 2: Create Invoice (Python)

Complete invoice creation with line items and tax:

```python
import requests
from datetime import datetime, timedelta

class QuickBooksInvoice:
    def __init__(self, realm_id, access_token, base_url='https://sandbox-quickbooks.api.intuit.com'):
        self.realm_id = realm_id
        self.access_token = access_token
        self.base_url = base_url

    def create_invoice(self, customer_id, line_items, due_days=30, tax_code='TAX', memo=None):
        """
        Create an invoice with multiple line items

        Args:
            customer_id: QuickBooks customer ID
            line_items: List of dicts with 'item_id', 'quantity', 'unit_price', 'description'
            due_days: Days until due date
            tax_code: Tax code ('TAX' for taxable, 'NON' for non-taxable)
            memo: Customer memo

        Returns:
            Created invoice dict or None if error
        """
        # Calculate dates
        txn_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=due_days)).strftime('%Y-%m-%d')

        # Build line items
        lines = []
        subtotal = 0

        for idx, item in enumerate(line_items, start=1):
            amount = item['quantity'] * item['unit_price']
            subtotal += amount

            lines.append({
                "LineNum": idx,
                "Amount": amount,
                "DetailType": "SalesItemLineDetail",
                "Description": item.get('description', ''),
                "SalesItemLineDetail": {
                    "ItemRef": {
                        "value": item['item_id']
                    },
                    "Qty": item['quantity'],
                    "UnitPrice": item['unit_price'],
                    "TaxCodeRef": {
                        "value": tax_code
                    }
                }
            })

        # Add subtotal line
        lines.append({
            "Amount": subtotal,
            "DetailType": "SubTotalLineDetail",
            "SubTotalLineDetail": {}
        })

        # Build invoice payload
        invoice_data = {
            "TxnDate": txn_date,
            "DueDate": due_date,
            "CustomerRef": {
                "value": customer_id
            },
            "Line": lines,
            "BillEmail": {},  # Will be populated from customer
            "EmailStatus": "NotSet"
        }

        # Add memo if provided
        if memo:
            invoice_data["CustomerMemo"] = {
                "value": memo
            }

        # Make API request
        url = f"{self.base_url}/v3/company/{self.realm_id}/invoice"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=invoice_data, headers=headers)
            response.raise_for_status()

            # Check for fault in response
            result = response.json()

            if 'Fault' in result:
                self._handle_fault(result['Fault'])
                return None

            invoice = result['Invoice']

            print(f"✓ Invoice {invoice['DocNumber']} created")
            print(f"  Customer: {invoice['CustomerRef']['value']}")
            print(f"  Total: ${invoice['TotalAmt']:.2f}")
            print(f"  Due: {invoice['DueDate']}")
            print(f"  Balance: ${invoice['Balance']:.2f}")

            return invoice

        except requests.exceptions.HTTPError as e:
            print(f"✗ HTTP Error: {e.response.status_code}")
            print(f"  Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"✗ Error creating invoice: {str(e)}")
            return None

    def send_invoice(self, invoice_id, email_address):
        """Send invoice via email"""
        url = f"{self.base_url}/v3/company/{self.realm_id}/invoice/{invoice_id}/send"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

        params = {"sendTo": email_address}

        try:
            response = requests.post(url, params=params, headers=headers)
            response.raise_for_status()

            result = response.json()

            if 'Fault' in result:
                self._handle_fault(result['Fault'])
                return False

            invoice = result['Invoice']
            print(f"✓ Invoice {invoice['DocNumber']} sent to {email_address}")
            print(f"  Email Status: {invoice['EmailStatus']}")

            return True

        except Exception as e:
            print(f"✗ Error sending invoice: {str(e)}")
            return False

    def _handle_fault(self, fault):
        """Handle fault responses"""
        print(f"✗ Fault Type: {fault['type']}")
        for error in fault['Error']:
            print(f"  Error {error['code']}: {error['Message']}")
            if 'element' in error:
                print(f"  Element: {error['element']}")

# Usage example
invoice_manager = QuickBooksInvoice(realm_id='123456789', access_token='your_token')

# Create invoice with multiple items
invoice = invoice_manager.create_invoice(
    customer_id='42',
    line_items=[
        {
            'item_id': '1',
            'quantity': 10,
            'unit_price': 150.00,
            'description': 'Consulting services - December 2024'
        },
        {
            'item_id': '5',
            'quantity': 1,
            'unit_price': 500.00,
            'description': 'Project management - December 2024'
        }
    ],
    due_days=30,
    tax_code='TAX',  # or 'NON' for non-taxable
    memo='Thank you for your business!'
)

if invoice:
    # Send invoice via email
    invoice_manager.send_invoice(invoice['Id'], 'customer@example.com')
```

### Example 3: Sparse Update Customer (Node.js)

Demonstrate sparse update pattern with error handling:

```javascript
const axios = require('axios');

class QuickBooksCustomer {
  constructor(realmId, accessToken, baseUrl = 'https://sandbox-quickbooks.api.intuit.com') {
    this.realmId = realmId;
    this.accessToken = accessToken;
    this.baseUrl = baseUrl;
  }

  async readCustomer(customerId) {
    const url = `${this.baseUrl}/v3/company/${this.realmId}/customer/${customerId}`;

    try {
      const response = await axios.get(url, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Accept': 'application/json'
        }
      });

      return response.data.Customer;
    } catch (error) {
      console.error('Read customer failed:', error.response?.data || error.message);
      throw error;
    }
  }

  async sparseUpdate(customerId, updates) {
    // First, read customer to get current SyncToken
    const customer = await this.readCustomer(customerId);

    // Build sparse update payload
    const updateData = {
      Id: customerId,
      SyncToken: customer.SyncToken,
      sparse: true,
      ...updates
    };

    const url = `${this.baseUrl}/v3/company/${this.realmId}/customer`;

    try {
      const response = await axios.post(url, updateData, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      // Check for fault
      if (response.data.Fault) {
        this.handleFault(response.data.Fault);
        return null;
      }

      const updatedCustomer = response.data.Customer;

      console.log(`✓ Customer ${updatedCustomer.DisplayName} updated`);
      console.log(`  New SyncToken: ${updatedCustomer.SyncToken}`);

      return updatedCustomer;

    } catch (error) {
      if (error.response?.status === 400) {
        const fault = error.response.data.Fault;

        // Handle SyncToken mismatch
        if (fault.Error[0].code === '3200') {
          console.log('SyncToken mismatch - retrying with fresh token...');
          // Recursive retry with new token
          return this.sparseUpdate(customerId, updates);
        }
      }

      console.error('Update failed:', error.response?.data || error.message);
      throw error;
    }
  }

  // Example: Update email
  async updateEmail(customerId, newEmail) {
    return this.sparseUpdate(customerId, {
      PrimaryEmailAddr: {
        Address: newEmail
      }
    });
  }

  // Example: Update phone
  async updatePhone(customerId, newPhone) {
    return this.sparseUpdate(customerId, {
      PrimaryPhone: {
        FreeFormNumber: newPhone
      }
    });
  }

  // Example: Update billing address
  async updateBillingAddress(customerId, address) {
    return this.sparseUpdate(customerId, {
      BillAddr: {
        Line1: address.line1,
        City: address.city,
        CountrySubDivisionCode: address.state,
        PostalCode: address.zip
      }
    });
  }

  // Example: Deactivate customer
  async deactivateCustomer(customerId) {
    return this.sparseUpdate(customerId, {
      Active: false
    });
  }

  // Example: Update multiple fields at once
  async updateMultipleFields(customerId, updates) {
    const sparseUpdates = {};

    if (updates.email) {
      sparseUpdates.PrimaryEmailAddr = { Address: updates.email };
    }

    if (updates.phone) {
      sparseUpdates.PrimaryPhone = { FreeFormNumber: updates.phone };
    }

    if (updates.displayName) {
      sparseUpdates.DisplayName = updates.displayName;
    }

    if (updates.notes) {
      sparseUpdates.Notes = updates.notes;
    }

    return this.sparseUpdate(customerId, sparseUpdates);
  }

  handleFault(fault) {
    console.error(`✗ Fault Type: ${fault.type}`);
    fault.Error.forEach(error => {
      console.error(`  Error ${error.code}: ${error.Message}`);
      if (error.element) {
        console.error(`  Element: ${error.element}`);
      }
    });
  }
}

// Usage
const customerManager = new QuickBooksCustomer('123456789', 'your_access_token');

// Update email
await customerManager.updateEmail('42', 'newemail@example.com');

// Update phone
await customerManager.updatePhone('42', '(555) 987-6543');

// Update address
await customerManager.updateBillingAddress('42', {
  line1: '456 New Street',
  city: 'San Francisco',
  state: 'CA',
  zip: '94105'
});

// Update multiple fields
await customerManager.updateMultipleFields('42', {
  email: 'updated@example.com',
  phone: '(555) 111-2222',
  displayName: 'Updated Customer Name',
  notes: 'VIP customer - priority support'
});

// Deactivate customer
await customerManager.deactivateCustomer('42');
```

### Example 4: Query with Filters (Python)

Complex query with date range and sorting:

```python
import requests
from urllib.parse import quote
from datetime import datetime, timedelta

class QuickBooksQuery:
    def __init__(self, realm_id, access_token, base_url='https://sandbox-quickbooks.api.intuit.com'):
        self.realm_id = realm_id
        self.access_token = access_token
        self.base_url = base_url

    def query(self, sql_query):
        """Execute SQL-like query"""
        encoded_query = quote(sql_query)
        url = f"{self.base_url}/v3/company/{self.realm_id}/query?query={encoded_query}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            result = response.json()

            if 'Fault' in result:
                print(f"Query error: {result['Fault']}")
                return []

            query_response = result.get('QueryResponse', {})

            # Extract entities (keys vary by entity type)
            for key, value in query_response.items():
                if key not in ['startPosition', 'maxResults', 'totalCount']:
                    return value if isinstance(value, list) else []

            return []

        except Exception as e:
            print(f"Query failed: {str(e)}")
            return []

    def query_invoices_by_date_range(self, start_date, end_date, customer_id=None):
        """Query invoices within date range, optionally filtered by customer"""
        query = f"SELECT * FROM Invoice WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"

        if customer_id:
            query += f" AND CustomerRef = '{customer_id}'"

        query += " ORDERBY TxnDate DESC"

        invoices = self.query(query)

        print(f"Found {len(invoices)} invoices between {start_date} and {end_date}")

        # Calculate totals
        total_amount = sum(inv['TotalAmt'] for inv in invoices)
        total_balance = sum(inv['Balance'] for inv in invoices)

        print(f"Total invoiced: ${total_amount:.2f}")
        print(f"Outstanding balance: ${total_balance:.2f}")

        return invoices

    def query_overdue_invoices(self, as_of_date=None):
        """Query invoices past due date"""
        if not as_of_date:
            as_of_date = datetime.now().strftime('%Y-%m-%d')

        query = f"SELECT * FROM Invoice WHERE Balance > '0' AND DueDate < '{as_of_date}' ORDERBY DueDate"

        invoices = self.query(query)

        print(f"Found {len(invoices)} overdue invoices as of {as_of_date}")

        # Group by customer
        by_customer = {}
        for inv in invoices:
            customer_id = inv['CustomerRef']['value']
            if customer_id not in by_customer:
                by_customer[customer_id] = {
                    'customer_name': inv['CustomerRef'].get('name', 'Unknown'),
                    'invoices': [],
                    'total_overdue': 0
                }

            by_customer[customer_id]['invoices'].append(inv)
            by_customer[customer_id]['total_overdue'] += inv['Balance']

        # Print summary
        for customer_id, data in by_customer.items():
            print(f"\nCustomer: {data['customer_name']}")
            print(f"  Overdue invoices: {len(data['invoices'])}")
            print(f"  Total overdue: ${data['total_overdue']:.2f}")

        return invoices

    def query_customers_by_balance(self, min_balance=0):
        """Query customers with balance greater than minimum"""
        query = f"SELECT * FROM Customer WHERE Balance > '{min_balance}' ORDERBY Balance DESC"

        customers = self.query(query)

        print(f"Found {len(customers)} customers with balance > ${min_balance}")

        total_ar = sum(cust['Balance'] for cust in customers)
        print(f"Total accounts receivable: ${total_ar:.2f}")

        return customers

    def query_items_by_type(self, item_type='Service'):
        """Query items by type (Service, Inventory, NonInventory, Category)"""
        query = f"SELECT * FROM Item WHERE Type = '{item_type}' AND Active = true ORDERBY Name"

        items = self.query(query)

        print(f"Found {len(items)} active {item_type} items")

        return items

    def search_customers_by_name(self, search_term):
        """Search customers by display name"""
        query = f"SELECT * FROM Customer WHERE DisplayName LIKE '%{search_term}%' ORDERBY DisplayName"

        customers = self.query(query)

        print(f"Found {len(customers)} customers matching '{search_term}'")

        for cust in customers:
            print(f"  {cust['DisplayName']} - Balance: ${cust['Balance']:.2f}")

        return customers

    def query_recent_payments(self, days=30):
        """Query payments from last N days"""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = f"SELECT * FROM Payment WHERE TxnDate >= '{start_date}' ORDERBY TxnDate DESC"

        payments = self.query(query)

        print(f"Found {len(payments)} payments in last {days} days")

        total_received = sum(pmt['TotalAmt'] for pmt in payments)
        print(f"Total payments received: ${total_received:.2f}")

        return payments

# Usage
query_service = QuickBooksQuery(realm_id='123456789', access_token='your_token')

# Query invoices for date range
invoices = query_service.query_invoices_by_date_range(
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# Query invoices for specific customer
customer_invoices = query_service.query_invoices_by_date_range(
    start_date='2024-01-01',
    end_date='2024-12-31',
    customer_id='42'
)

# Find overdue invoices
overdue = query_service.query_overdue_invoices()

# Find customers with high balances
high_balance_customers = query_service.query_customers_by_balance(min_balance=1000.00)

# Search for customer
customers = query_service.search_customers_by_name('Acme')

# Get recent payments
recent_payments = query_service.query_recent_payments(days=30)
```

### Example 5: Batch Operations (Node.js)

Batch create/update multiple entities:

```javascript
const axios = require('axios');

class QuickBooksBatch {
  constructor(realmId, accessToken, baseUrl = 'https://sandbox-quickbooks.api.intuit.com') {
    this.realmId = realmId;
    this.accessToken = accessToken;
    this.baseUrl = baseUrl;
  }

  async executeBatch(batchItems) {
    const url = `${this.baseUrl}/v3/company/${this.realmId}/batch`;

    try {
      const response = await axios.post(url, {
        BatchItemRequest: batchItems
      }, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      const results = response.data.BatchItemResponse;

      // Process results
      const summary = {
        total: results.length,
        success: 0,
        errors: 0,
        results: []
      };

      results.forEach(result => {
        if (result.Fault) {
          summary.errors++;
          console.error(`✗ Error for ${result.bId}:`);
          result.Fault.Error.forEach(err => {
            console.error(`  ${err.code}: ${err.Message}`);
          });
          summary.results.push({
            bId: result.bId,
            status: 'error',
            error: result.Fault
          });
        } else {
          summary.success++;
          // Extract entity from result
          const entityType = Object.keys(result).find(k => k !== 'bId');
          const entity = result[entityType];

          console.log(`✓ Success for ${result.bId}: ${entityType} ${entity.Id}`);
          summary.results.push({
            bId: result.bId,
            status: 'success',
            entityType: entityType,
            entity: entity
          });
        }
      });

      console.log(`\nBatch complete: ${summary.success}/${summary.total} successful`);

      return summary;

    } catch (error) {
      console.error('Batch operation failed:', error.response?.data || error.message);
      throw error;
    }
  }

  // Batch create customers
  async batchCreateCustomers(customers) {
    const batchItems = customers.map((customer, index) => ({
      bId: `customer_create_${index}`,
      operation: 'create',
      Customer: {
        DisplayName: customer.displayName,
        PrimaryEmailAddr: { Address: customer.email },
        PrimaryPhone: { FreeFormNumber: customer.phone },
        BillAddr: {
          Line1: customer.address,
          City: customer.city,
          CountrySubDivisionCode: customer.state,
          PostalCode: customer.zip
        }
      }
    }));

    return this.executeBatch(batchItems);
  }

  // Batch update invoices
  async batchUpdateInvoices(updates) {
    const batchItems = updates.map((update, index) => ({
      bId: `invoice_update_${index}`,
      operation: 'update',
      Invoice: {
        Id: update.id,
        SyncToken: update.syncToken,
        sparse: true,
        ...update.changes
      }
    }));

    return this.executeBatch(batchItems);
  }

  // Batch query multiple entities
  async batchQuery(queries) {
    const batchItems = queries.map((query, index) => ({
      bId: `query_${index}`,
      operation: 'query',
      Query: query.sql
    }));

    const results = await this.executeBatch(batchItems);

    // Extract query results
    const queryResults = {};
    results.results.forEach(result => {
      if (result.status === 'success' && result.entity.QueryResponse) {
        queryResults[result.bId] = result.entity.QueryResponse;
      }
    });

    return queryResults;
  }

  // Mixed batch operations
  async mixedBatch(operations) {
    const batchItems = operations.map((op, index) => {
      const item = {
        bId: `op_${index}_${op.type}`,
        operation: op.operation
      };

      // Add entity or query data
      if (op.operation === 'query') {
        item.Query = op.data;
      } else {
        item[op.entityType] = op.data;
      }

      return item;
    });

    return this.executeBatch(batchItems);
  }
}

// Usage Examples

const batchService = new QuickBooksBatch('123456789', 'your_access_token');

// Example 1: Batch create customers
const newCustomers = [
  {
    displayName: 'Acme Corp',
    email: 'contact@acme.com',
    phone: '(555) 111-1111',
    address: '123 Main St',
    city: 'San Francisco',
    state: 'CA',
    zip: '94105'
  },
  {
    displayName: 'TechStart Inc',
    email: 'hello@techstart.com',
    phone: '(555) 222-2222',
    address: '456 Market St',
    city: 'San Francisco',
    state: 'CA',
    zip: '94103'
  }
];

const createResults = await batchService.batchCreateCustomers(newCustomers);

// Example 2: Batch update invoices (mark as sent)
const invoiceUpdates = [
  { id: '145', syncToken: '0', changes: { EmailStatus: 'NeedToSend' } },
  { id: '146', syncToken: '0', changes: { EmailStatus: 'NeedToSend' } },
  { id: '147', syncToken: '0', changes: { EmailStatus: 'NeedToSend' } }
];

const updateResults = await batchService.batchUpdateInvoices(invoiceUpdates);

// Example 3: Batch queries
const queries = [
  { sql: 'SELECT * FROM Customer WHERE Active = true MAXRESULTS 10' },
  { sql: 'SELECT * FROM Invoice WHERE Balance > 0 MAXRESULTS 10' },
  { sql: 'SELECT * FROM Payment MAXRESULTS 10' }
];

const queryResults = await batchService.batchQuery(queries);

// Example 4: Mixed batch operations
const mixedOps = [
  {
    type: 'create_customer',
    operation: 'create',
    entityType: 'Customer',
    data: {
      DisplayName: 'New Customer',
      PrimaryEmailAddr: { Address: 'new@example.com' }
    }
  },
  {
    type: 'update_invoice',
    operation: 'update',
    entityType: 'Invoice',
    data: {
      Id: '145',
      SyncToken: '1',
      sparse: true,
      CustomerMemo: { value: 'Thank you!' }
    }
  },
  {
    type: 'query_items',
    operation: 'query',
    data: 'SELECT * FROM Item WHERE Type = \'Service\' MAXRESULTS 5'
  }
];

const mixedResults = await batchService.mixedBatch(mixedOps);

console.log(`Mixed batch: ${mixedResults.success}/${mixedResults.total} successful`);
```

### Example 6: Payment Application (Python)

Apply payment to multiple invoices:

```python
import requests

class QuickBooksPayment:
    def __init__(self, realm_id, access_token, base_url='https://sandbox-quickbooks.api.intuit.com'):
        self.realm_id = realm_id
        self.access_token = access_token
        self.base_url = base_url

    def create_payment(self, customer_id, total_amount, payment_method_id,
                       payment_ref_num, txn_date, invoice_applications):
        """
        Create payment and apply to one or more invoices

        Args:
            customer_id: QuickBooks customer ID
            total_amount: Total payment amount
            payment_method_id: Payment method ID
            payment_ref_num: Check number or transaction reference
            txn_date: Payment date (YYYY-MM-DD)
            invoice_applications: List of {'invoice_id': str, 'amount': float}

        Returns:
            Created payment dict or None if error
        """
        # Build line items for invoice applications
        lines = []
        total_applied = 0

        for application in invoice_applications:
            lines.append({
                "Amount": application['amount'],
                "LinkedTxn": [
                    {
                        "TxnId": application['invoice_id'],
                        "TxnType": "Invoice"
                    }
                ]
            })
            total_applied += application['amount']

        # Check for unapplied amount
        unapplied = total_amount - total_applied
        if unapplied < 0:
            print(f"Warning: Applied amount (${total_applied}) exceeds payment (${total_amount})")
            return None

        # Build payment payload
        payment_data = {
            "TotalAmt": total_amount,
            "CustomerRef": {
                "value": customer_id
            },
            "TxnDate": txn_date,
            "PaymentMethodRef": {
                "value": payment_method_id
            },
            "PaymentRefNum": payment_ref_num,
            "Line": lines
        }

        # Make API request
        url = f"{self.base_url}/v3/company/{self.realm_id}/payment"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payment_data, headers=headers)
            response.raise_for_status()

            result = response.json()

            if 'Fault' in result:
                self._handle_fault(result['Fault'])
                return None

            payment = result['Payment']

            print(f"✓ Payment created: ID {payment['Id']}")
            print(f"  Customer: {payment['CustomerRef']['value']}")
            print(f"  Total Amount: ${payment['TotalAmt']:.2f}")
            print(f"  Applied Amount: ${total_applied:.2f}")
            print(f"  Unapplied Amount: ${payment.get('UnappliedAmt', 0):.2f}")
            print(f"  Reference: {payment.get('PaymentRefNum', 'N/A')}")

            # Show invoice applications
            for line in payment['Line']:
                if 'LinkedTxn' in line:
                    for linked in line['LinkedTxn']:
                        print(f"  Applied ${line['Amount']:.2f} to {linked['TxnType']} {linked['TxnId']}")

            return payment

        except requests.exceptions.HTTPError as e:
            print(f"✗ HTTP Error: {e.response.status_code}")
            print(f"  Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"✗ Error creating payment: {str(e)}")
            return None

    def apply_payment_to_invoices(self, customer_id, check_number, check_amount,
                                   check_date, invoices):
        """
        Apply a single check payment to multiple invoices

        Args:
            customer_id: Customer ID
            check_number: Check number
            check_amount: Total check amount
            check_date: Check date
            invoices: List of {'id': str, 'amount_to_apply': float, 'balance': float}

        Returns:
            Payment dict or None
        """
        # Get check payment method ID
        payment_methods = self.query_payment_methods()
        check_method = next((pm for pm in payment_methods if pm['Name'].lower() == 'check'), None)

        if not check_method:
            print("Check payment method not found")
            return None

        # Build invoice applications
        applications = []
        total_to_apply = 0

        for invoice in invoices:
            amount = min(invoice['amount_to_apply'], invoice['balance'])
            applications.append({
                'invoice_id': invoice['id'],
                'amount': amount
            })
            total_to_apply += amount

            print(f"Will apply ${amount:.2f} to Invoice {invoice['id']}")

        # Check if payment covers all applications
        if total_to_apply > check_amount:
            print(f"Warning: Total applications (${total_to_apply}) exceeds check amount (${check_amount})")
            return None

        # Create payment
        payment = self.create_payment(
            customer_id=customer_id,
            total_amount=check_amount,
            payment_method_id=check_method['Id'],
            payment_ref_num=check_number,
            txn_date=check_date,
            invoice_applications=applications
        )

        return payment

    def apply_partial_payment(self, customer_id, payment_amount, payment_method_id,
                              invoice_id, partial_amount):
        """Apply partial payment to invoice"""
        if partial_amount > payment_amount:
            print("Partial amount cannot exceed total payment")
            return None

        applications = [{
            'invoice_id': invoice_id,
            'amount': partial_amount
        }]

        payment = self.create_payment(
            customer_id=customer_id,
            total_amount=payment_amount,
            payment_method_id=payment_method_id,
            payment_ref_num='',
            txn_date=datetime.now().strftime('%Y-%m-%d'),
            invoice_applications=applications
        )

        if payment and payment.get('UnappliedAmt', 0) > 0:
            print(f"\nNote: ${payment['UnappliedAmt']:.2f} remains unapplied")
            print("This amount can be applied to future invoices or refunded")

        return payment

    def query_payment_methods(self):
        """Get available payment methods"""
        from urllib.parse import quote

        query = "SELECT * FROM PaymentMethod"
        encoded_query = quote(query)

        url = f"{self.base_url}/v3/company/{self.realm_id}/query?query={encoded_query}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers)
        result = response.json()

        return result.get('QueryResponse', {}).get('PaymentMethod', [])

    def _handle_fault(self, fault):
        """Handle fault responses"""
        print(f"✗ Fault Type: {fault['type']}")
        for error in fault['Error']:
            print(f"  Error {error['code']}: {error['Message']}")
            if 'element' in error:
                print(f"  Element: {error['element']}")

# Usage Examples

payment_service = QuickBooksPayment(realm_id='123456789', access_token='your_token')

# Example 1: Apply single check to multiple invoices
payment = payment_service.apply_payment_to_invoices(
    customer_id='42',
    check_number='1234',
    check_amount=1500.00,
    check_date='2024-12-09',
    invoices=[
        {'id': '145', 'amount_to_apply': 1000.00, 'balance': 1000.00},
        {'id': '146', 'amount_to_apply': 500.00, 'balance': 750.00}
    ]
)

# Example 2: Partial payment on single invoice
partial_payment = payment_service.apply_partial_payment(
    customer_id='42',
    payment_amount=500.00,
    payment_method_id='1',  # Cash
    invoice_id='147',
    partial_amount=500.00  # Invoice balance is $1000, paying $500
)

# Example 3: Payment with unapplied amount (credit for future invoices)
credit_payment = payment_service.create_payment(
    customer_id='42',
    total_amount=2000.00,  # Customer pays $2000
    payment_method_id='1',
    payment_ref_num='',
    txn_date='2024-12-09',
    invoice_applications=[
        {'invoice_id': '145', 'amount': 1000.00}  # Only $1000 applied
    ]
    # $1000 remains unapplied as credit
)
```

## API Reference Quick Links

**Context7 Library**: Use Context7 MCP to fetch latest documentation:
- Library ID: `/websites/developer_intuit_app_developer_qbo`
- Use for up-to-date code examples and API changes

**Official Resources**:
- **QuickBooks API Explorer**: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/account
  - Interactive API reference with sandbox testing
  - Entity-specific documentation and sample requests

- **Developer Dashboard**: https://developer.intuit.com/app/developer/myapps
  - Manage apps, keys, webhooks
  - Create sandbox companies

**SDKs**:
- **Node.js**: https://github.com/intuit/intuit-oauth (OAuth) + axios for API calls
- **Python**: https://github.com/intuit/intuit-oauth-python (OAuth) + requests
- **Java**: https://github.com/intuit/QuickBooks-V3-Java-SDK
- **PHP**: https://github.com/intuit/QuickBooks-V3-PHP-SDK
- **C#/.NET**: https://github.com/intuit/QuickBooks-V3-DotNET-SDK

**Common Endpoints**:
- Base URL (Sandbox): `https://sandbox-quickbooks.api.intuit.com/v3/company/{realmId}`
- Base URL (Production): `https://quickbooks.api.intuit.com/v3/company/{realmId}`
- Token endpoint: `https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer`
- OAuth authorization: `https://appcenter.intuit.com/connect/oauth2`

## Troubleshooting Common Issues

### SyncToken Mismatch (Error 3200)

**Symptom**: "stale object error" when updating entities

**Cause**: SyncToken in request doesn't match current version (concurrent modification)

**Solution**:
```python
def safe_update_with_retry(entity_id, updates, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            # Read latest version
            entity = read_entity(entity_id)

            # Apply changes
            entity.update(updates)
            entity['sparse'] = True

            # Attempt update
            return update_entity(entity)

        except SyncTokenError as e:
            if attempt == max_attempts - 1:
                raise
            print(f"SyncToken mismatch, retrying... (attempt {attempt + 1})")
            continue
```

### Required Field Missing (Error 6000)

**Symptom**: "business validation error" or "required field missing"

**Cause**: Missing required fields like TotalAmt, CustomerRef, or entity-specific requirements

**Solution**:
- Check API documentation for entity-specific required fields
- For Payment: TotalAmt and CustomerRef are required
- For Invoice: CustomerRef and Line array are required
- Validate data locally before API call

**Common Required Fields**:
- Customer: DisplayName (must be unique)
- Invoice: CustomerRef, Line (at least one)
- Payment: TotalAmt, CustomerRef
- Item: Name, Type, IncomeAccountRef (for Service)

### OAuth Token Expiration (401 Unauthorized)

**Symptom**: "invalid_token" or "token_expired" errors

**Cause**: Access token expired (after 3600 seconds)

**Solution**:
```javascript
async function apiCallWithAutoRefresh(apiFunction) {
  try {
    return await apiFunction();
  } catch (error) {
    if (error.response?.status === 401) {
      // Token expired, refresh
      await refreshAccessToken();
      // Retry with new token
      return await apiFunction();
    }
    throw error;
  }
}
```

**Prevention**:
- Implement proactive token refresh (every 50 minutes)
- Store token expiry time and check before requests
- Handle 401 responses automatically

### Invalid Reference (Error 3100)

**Symptom**: "object not found" when referencing CustomerRef, ItemRef, etc.

**Cause**: Referenced entity doesn't exist or was deleted

**Solution**:
```python
def validate_reference(entity_type, entity_id):
    """Verify entity exists before creating reference"""
    try:
        entity = read_entity(entity_type, entity_id)
        return True
    except NotFoundError:
        print(f"{entity_type} {entity_id} not found")
        return False

# Before creating invoice
if validate_reference('Customer', customer_id):
    if validate_reference('Item', item_id):
        create_invoice(customer_id, item_id)
```

### Rate Limiting (429 Too Many Requests)

**Symptom**: "throttle_limit_exceeded" or 429 status code

**Cause**: Exceeded API rate limits

**Solution** - Exponential backoff with jitter:
```python
import time
import random

def api_call_with_backoff(api_function, max_retries=5):
    for attempt in range(max_retries):
        try:
            return api_function()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff with jitter
            delay = (2 ** attempt) + random.uniform(0, 1)
            print(f"Rate limited, waiting {delay:.1f}s...")
            time.sleep(delay)
```

**Prevention**:
- Use batch operations to reduce call count
- Implement request queuing with rate limiting
- Cache frequently accessed reference data

### Batch Operation Failures

**Symptom**: Some operations in batch fail while others succeed

**Cause**: Each batch operation is independent; one failure doesn't affect others

**Solution**:
```javascript
function processBatchResults(results) {
  const failed = results.filter(r => r.Fault);
  const succeeded = results.filter(r => !r.Fault);

  console.log(`Batch: ${succeeded.length} success, ${failed.length} failed`);

  // Retry failed operations individually
  for (const failure of failed) {
    console.log(`Retrying ${failure.bId}...`);
    // Implement individual retry logic
  }

  return { succeeded, failed };
}
```

### Multi-currency Validation Errors

**Symptom**: "currency not enabled" or "exchange rate required"

**Cause**: Multi-currency features not enabled or missing CurrencyRef

**Solution**:
```json
{
  "Invoice": {
    "CurrencyRef": {
      "value": "USD",
      "name": "United States Dollar"
    },
    "ExchangeRate": 1.0
  }
}
```

**Check**:
- Verify multi-currency enabled in QuickBooks company preferences
- Always include CurrencyRef when multi-currency is enabled
- For foreign currency, API calculates exchange rate automatically

### Webhook Not Receiving Notifications

**Symptom**: Webhook endpoint configured but not receiving POST requests

**Cause**: Endpoint issues, SSL problems, or slow response time

**Solution**:
1. **Verify endpoint is publicly accessible** (not localhost)
2. **Use HTTPS** (required for webhooks)
3. **Respond within 1 second** (return 200 OK immediately, process async)
4. **Test with sample payload**:
   ```bash
   curl -X POST https://yourapp.com/webhooks/quickbooks \
     -H "Content-Type: application/json" \
     -d '{"eventNotifications":[]}'
   ```
5. **Check webhook logs in developer dashboard**

### Deleted Entities in CDC Response

**Symptom**: Entities with status="Deleted" only contain ID

**Cause**: CDC returns minimal data for deleted entities

**Solution**:
```python
def process_cdc_changes(changes):
    for entity in changes:
        if entity.get('status') == 'Deleted':
            # Only ID available
            handle_deletion(entity['Id'])
        else:
            # Full entity data available
            process_entity_update(entity)
```

---

This skill provides comprehensive guidance for QuickBooks Online API integration. For the most current API documentation and changes, use Context7 with library ID `/websites/developer_intuit_app_developer_qbo`.
