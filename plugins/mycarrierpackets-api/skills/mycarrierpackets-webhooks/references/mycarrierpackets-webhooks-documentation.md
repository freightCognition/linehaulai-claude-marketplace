  [![](https://mycarrierpackets.com/Images/descartes_mcp_logo@2x.png)](https://mycarrierportal.com/ "MyCarrierPortal")

#### Webhook Documentation

### About webhook events and payloads

MCP offers webhooks to notify you in real-time when certain events happen. Webhooks are HTTPS requests made to an endpoint of your choice that you can then implement custom business logic for. For example, you can receive a webhook when a carrier completes a packet. Your endpoint that receives this webhook can then process the payload of the webhook to automate some internal process you have based on the packet completion. These processes may include updating records in your database, calling our APIs to get more information, or sending out notifications.

You can create webhooks that subscribe to the events listed on this page. To limit the number of HTTP requests to your server, you should only subscribe to the specific events that you plan on handling. Each webhook event on this page includes a description of the webhook properties for that event.

### Requirements and limitations

Applications need at least one reachable notification URL to receive and process webhook events from MCP. The notification URL endpoint must:

- Require a connection that uses HTTPS.

- Expect JSON data from a POST request.

- Respond to MCP with a `2xx` HTTP status code as soon as possible to acknowledge the successful receipt of the event notification. If your application fails to acknowledge the notification in a timely manner, another request is sent and your application. See the Notification Retries schedule below.


Notification URLs are specified on the **[Webhook Subscriptions](https://mycarrierpackets.com/Webhooks)** page.

### Delivery Headers

The HTTP POST payloads that are delivered to your webhook's notification URL will contain special headers:

- MCP-Event: The name of the event that triggered the delivery.
- MCP-Signature: This is the HMAC hex digest of the request body and is used to verify the events sent to your endpoints. It is generated using the SHA-256 hash function and the webhook secret as the HMAC key. For more information, see Verifying Signatures.

### Verifying Signatures

Before you respond to a webhook delivery, you need to verify that the webhook was sent from MCP. You can verify the webhook by calculating a digital signature.

Each webhook delivery includes a `MCP-Signature` hex digest field in the payload header, which is generated using the webhook secret along with the data sent in the request.

To calculate the digital signature, HMAC with SHA-256 the request body with a hex digest version of the secret. For example:

1. Compute the HMAC hash
2. Extract the text of the plain text JSON payload as an array of bytes. The entire body of the POST request is used, including line endings.
3. Compute a SHA-256 HMAC hash for the array of bytes.
4. Convert the hash to a hex digest.
5. Compare the MCP-Signature. If they match, then you can trust that the event payload was issued by Calendly and has not been tampered with.

The signature is sensitive to any changes, so even a small change in the body will cause the signature to be completely different. This means that you should not change the request body in any way before calculating the signature.

Here's a c# example. For other languages, refer to [Examples of creating base64 hashes using HMAC SHA256 in different languages](https://www.jokecamp.com/blog/examples-of-creating-base64-hashes-using-hmac-sha256-in-different-languages/). Note that instead of converting the hash to a base64 encoded value as these examples show, the hash should be converted to a hex digest.

```

using System.Security.Cryptography;

namespace Test
{
    public class MyHmac
    {
        private string CreateToken(string message, string secret)
        {
            Encoding encoding = new System.Text.UTF8Encoding();
            byte[] keyByte = encoding.GetBytes(secret);
            byte[] messageBytes = encoding.GetBytes(message);

            using (HMACSHA256 cryptographer = new HMACSHA256(keyByte))
            {
                byte[] hashmessage = cryptographer.ComputeHash(messageBytes);
                string computedHash = BitConverter.ToString(hashmessage).Replace("-", string.Empty).ToLowerInvariant();
                return computedHash;
            }
        }
    }
}
```

This generated signature should match the one in the `MCP-Signature` header.

### Notification Retries

If a `2xx` status code isn't received in a timely manner after the initial event notification, MCP will attempt to send the notification up to 5 times per cycle. After 5 attempts have been made in a cycle, no more attempts will be made. At this point, the webhook can manually be resent from the **[Webhook Requests](https://mycarrierpackets.com/Webhooks/WebhookRequests)** page. Manually resending a webhook will start a new cycle and up to 5 more attempts will be made.

For example, if a `2xx` status code isn't received in a timely manner on the 1st attempt, MCP will immediately resend the notification (attempt 2). If a `2xx` status code still isn't received, MCP will resend the notification after 5 minutes (attempt 3).

The retry schedule is as follows:

| Attempt | Time since last attempt | Time since event |
| --- | --- | --- |
| 1 | -- | -- |
| 2 | 0 minutes | 0 minutes |
| 3 | 5 minutes | 5 minutes |
| 4 | 10 minutes | 15 minutes |
| 5 | 15 minutes | 30 minutes |

### Webhook Events

Each webhook payload contains an `eventType`, `eventDateTime`, and `eventData`. The `eventData` payload differs based on the `eventType` and contains detailed information about the event that occurred.

| Field Name | Type | Description |
| --- | --- | --- |
| `eventType` | String | The type of the event. This usually provides a description of what happened. |
| `eventDateTime` | DateTime | An ISO 8601 datetime indicating when the event occurred in UTC. |
| `eventData` | Object | Data specific to the `eventType` that occurred. |

The event types that can be subscribed to are listed here. Examples of each payload is further down.

| Event Type | Description |
| --- | --- |
| `carrier.packet.completed` | This event occurs when a carrier onboards with a broker or shipper and completes an MCP online packet. |
| `carrier.incident_report.created` | This event occurs when an incident report on a carrier is created. |
| `carrier.incident_report.updated` | This event occurs when an incident report on a carrier is updated. |
| `carrier.incident_report.retracted` | This event occurs when an incident report on a carrier is retracted. |
| `carrier.vin_verification.completed` | This event occurs when a carrier submits an image of their truck's VIN in response to a VIN verification request. |
| `carrier.user_verification.completed` | This event occurs when a carrier user verification has been completed in response to a user verification request. |

* * *

#### Carrier Packet Completed Event

EVENT TYPEcarrier.packet.completed

The carrier.packet.completed event occurs when a carrier onboards with a broker or shipper and completes an MCP online packet.

Enums used in the payload

| Field Name | Values |
| --- | --- |
| agreement.geolocation.method | DeviceOrBrowser, IPAddress |

Event Payload Example

```

{
    "eventType": "carrier.packet.completed",
    "eventDateTime": "2025-04-29T22:16:41.5102923Z",
    "eventData": {
        "agreement": {
            "signatureDate": "2025-04-29T22:16:20.6352903",
            "signaturePerson": "MCP Test Carrier",
            "signaturePersonTitle": "President",
            "signaturePersonEmail": "test9999997@test.com",
            "signaturePersonPhoneNumber": "9999999999",
            "agreementImageBlobName": "company-agreement/6/b7453f55-3f3b-454d-8726-89f746082a06",
            "ipAddress": {
                "address": "127.0.0.1",
                "city": "New York City",
                "region": "New York",
                "country": "United States of America"
            },
            "geolocation": {
                "latitude": 34.0544,
                "longitude": -118.244,
                "error": null,
                "method": "IPAddress"
            }
        },
        "carrier": {
            "dotNumber": 9999997,
            "docketNumber": "MC9999997",
            "legalName": "MCP TEST CARRIER 9999997",
            "dbaName": null
        },
        "customer": {
            "customerID": 6,
            "companyName": "MCP Test Customer"
        }
    }
}
```

* * *

#### Carrier Incident Report Created Event

EVENT TYPEcarrier.incident\_report.created

The carrier.incident\_report.created event occurs when an incident report on a carrier is created.

Enums used in the payload

| Field Name | Values |
| --- | --- |
| incidentReport.comments.commenterType | ReportingParty, RespondingParty |

Event Payload Example

```

{
    "eventType": "carrier.incident_report.created",
    "eventDateTime": "2025-04-23T06:27:36.3903875Z",
    "eventData": {
        "incidentReport": {
            "incidentDate": "04/22/2025",
            "originCity": "Salt Lake City",
            "originStateProvinceName": "UT",
            "originCountryName": "United States",
            "destinationCity": "Lincoln",
            "destinationStateProvinceName": "NE",
            "destinationCountryName": "United States",
            "reportedByCompany": "MCP Test Company",
            "carrierEmails": "test9999997@test.com",
            "createdBy": "MCP Test User",
            "createdDate": "2025-04-23T06:27:14.8587937",
            "modifiedBy": "MCP Test User",
            "modifiedDate": "2025-04-23T06:27:14.8587937",
            "incidentTypes": [\
                "Theft or Unjustified Loss of Freight",\
                "Wrong Equipment",\
                "Operated Under Alias",\
                "No Show without Notification",\
                "Pickup or Delivery Service Failure"\
            ],
            "comments": [\
                {\
                    "commenterType": "ReportingParty",\
                    "commentBy": "MCP Test User",\
                    "commentDate": "2025-04-23T06:27:15.0159957",\
                    "comment": "Damaged cargo"\
                }\
            ]
        },
        "carrier": {
            "dotNumber": 9999997,
            "docketNumber": "MC9999997",
            "legalName": "MCP TEST CARRIER 9999997",
            "dbaName": null
        },
        "customer": {
            "customerID": 6,
            "companyName": "MCP Test Customer"
        }
    }
}
```

* * *

#### Carrier Incident Report Updated Event

EVENT TYPEcarrier.incident\_report.updated

The carrier.incident\_report.updated event occurs when an incident report on a carrier is updated.

Enums used in the payload

| Field Name | Values |
| --- | --- |
| incidentReport.comments.commenterType | ReportingParty, RespondingParty |

Event Payload Example

```

{
    "eventType": "carrier.incident_report.updated",
    "eventDateTime": "2025-04-23T06:27:36.3903875Z",
    "eventData": {
        "incidentReport": {
            "incidentDate": "04/22/2025",
            "originCity": "Salt Lake City",
            "originStateProvinceName": "UT",
            "originCountryName": "United States",
            "destinationCity": "Lincoln",
            "destinationStateProvinceName": "NE",
            "destinationCountryName": "United States",
            "reportedByCompany": "MCP Test Company",
            "carrierEmails": "test9999997@test.com",
            "createdBy": "MCP Test User",
            "createdDate": "2025-04-23T06:27:14.8587937",
            "modifiedBy": "MCP Test User",
            "modifiedDate": "2025-04-23T06:27:14.8587937",
            "incidentTypes": [\
                "Theft or Unjustified Loss of Freight",\
                "Wrong Equipment",\
                "Operated Under Alias",\
                "No Show without Notification",\
                "Pickup or Delivery Service Failure"\
            ],
            "comments": [\
                {\
                    "commenterType": "ReportingParty",\
                    "commentBy": "MCP Test User",\
                    "commentDate": "2025-04-23T06:27:15.0159957",\
                    "comment": "Damaged cargo"\
                }\
            ]
        },
        "carrier": {
            "dotNumber": 9999997,
            "docketNumber": "MC9999997",
            "legalName": "MCP TEST CARRIER 9999997",
            "dbaName": null
        },
        "customer": {
            "customerID": 6,
            "companyName": "MCP Test Customer"
        }
    }
}
```

* * *

#### Carrier Incident Report Retracted Event

EVENT TYPEcarrier.incident\_report.retracted

The carrier.incident\_report.retracted event occurs when an incident report on a carrier is retracted.

Enums used in the payload

| Field Name | Values |
| --- | --- |
| incidentReport.comments.commenterType | ReportingParty, RespondingParty |

Event Payload Example

```

{
    "eventType": "carrier.incident_report.retracted",
    "eventDateTime": "2025-04-23T06:27:36.3903875Z",
    "eventData": {
        "incidentReport": {
            "incidentDate": "04/22/2025",
            "originCity": "Salt Lake City",
            "originStateProvinceName": "UT",
            "originCountryName": "United States",
            "destinationCity": "Lincoln",
            "destinationStateProvinceName": "NE",
            "destinationCountryName": "United States",
            "reportedByCompany": "MCP Test Company",
            "carrierEmails": "test9999997@test.com",
            "createdBy": "MCP Test User",
            "createdDate": "2025-04-23T06:27:14.8587937",
            "modifiedBy": "MCP Test User",
            "modifiedDate": "2025-04-23T06:27:14.8587937",
            "incidentTypes": [\
                "Theft or Unjustified Loss of Freight",\
                "Wrong Equipment",\
                "Operated Under Alias",\
                "No Show without Notification",\
                "Pickup or Delivery Service Failure"\
            ],
            "comments": [\
                {\
                    "commenterType": "ReportingParty",\
                    "commentBy": "MCP Test User",\
                    "commentDate": "2025-04-23T06:27:15.0159957",\
                    "comment": "Damaged cargo"\
                }\
            ]
        },
        "carrier": {
            "dotNumber": 9999997,
            "docketNumber": "MC9999997",
            "legalName": "MCP TEST CARRIER 9999997",
            "dbaName": null
        },
        "customer": {
            "customerID": 6,
            "companyName": "MCP Test Customer"
        }
    }
}
```

* * *

#### Carrier VIN Verification Completed Event

EVENT TYPEcarrier.vin\_verification.completed

The carrier.vin\_verification.completed event occurs when a carrier submits an image of their truck's VIN in response to a VIN verification request.

Enums used in the payload

| Field Name | Values |
| --- | --- |
| vinVerificationDetail.imageUploadedGeolocation.method | DeviceOrBrowser, IPAddress |
| vinVerificationDetail.vinVerificationStatus | VINRequestSent, VINBelongsToCarrier, VINBelongsToAnotherCarrier, VINCarrierUndetermined |

Event Payload Example

```

{
    "eventType": "carrier.vin_verification.completed",
    "eventDateTime": "2025-05-01T15:57:12.6350582Z",
    "eventData": {
        "vinVerificationDetail": {
            "imageUploadedByFirstName": "FirstName",
            "imageUploadedByLastName": "LastName",
            "imageUploadedDateTime": "2025-05-01T15:57:05.2815289Z",
            "imageUploadedIPAddress": {
                "address": "127.0.0.1",
                "city": "Arlington",
                "region": "Virginia",
                "country": "United States of America"
            },
            "imageUploadedGeolocation": {
                "latitude": 34.0544,
                "longitude": -118.244,
                "error": null,
                "method": "IPAddress"
            },
            "vin": "3AKJGLD55ESFW7639",
            "vinVerificationStatus": "VINBelongsToAnotherCarrier",
            "otherDOTNumber": 3083762
            "vinVerificationRequestID" = 102,
            "requesteePhoneNumber" = "9999999999",
            "vinImageUrl" = "downloadUrl",
        },
        "carrier": {
            "dotNumber": 9999997,
            "docketNumber": "MC9999997",
            "legalName": "MCP TEST CARRIER 9999997",
            "dbaName": null
        },
        "customer": {
            "customerID": 6,
            "companyName": "MCP Test Customer"
        }
    }
}
```

* * *

#### Carrier User Verification Completed Event

EVENT TYPEcarrier.user\_verification.completed

The carrier.user\_verification.completed event occurs when a carrier user verification has been completed in response to a user verification request.

Enums used in the payload

| Field Name | Values |
| --- | --- |
| userVerificationDetail.role | Admin, Driver, Dispatcher, Accounting, Other |
| userVerificationDetail.verificationStatus | Pending, Verified, Denied, FollowUp |

Event Payload Example

```

{
    "eventType": "carrier.user_verification.completed",
    "eventDateTime": "2025-05-01T18:21:31.2784222Z",
    "eventData": {
        "userVerificationDetail": {
            "firstName": "FirstName",
            "lastName": "LastName",
            "phoneNumber": "(888) 888-8888",
            "role": "Driver",
            "otherRole": null,
            "verificationStatus": "Verified",
            "verificationDatetime": "2025-05-01T18:21:30.8445657Z"
        },
        "carrier": {
            "dotNumber": 9999997,
            "docketNumber": "MC9999997",
            "legalName": "MCP TEST CARRIER 9999997",
            "dbaName": null
        },
        "customer": {
            "customerID": 6,
            "companyName": "MCP Test Customer"
        }
    }
}
```