{
  "account": "DNS:NET",
  "api_rectify": false,
  "dnssec": false,
  "id": "pixelpark.ag.",
  "kind": "Master",
  "last_check": 0,
  "masters": [],
  "name": "pixelpark.ag.",
  "notified_serial": 2018061201,
  "nsec3narrow": false,
  "nsec3param": "",
  "rrsets": [
    {
      "comments": [],
      "name": "www.pixelpark.ag.",
      "records": [
        {
          "content": "217.66.55.28",
          "disabled": false
        }
      ],
      "ttl": 3600,
      "type": "A"
    },
    {
      "comments": [
        {
          "account": "frank.brehm",
          "content": "local",
          "modified_at": 1518186464
        }
      ],
      "name": "local.pixelpark.ag.",
      "records": [
        {
          "content": "ns1-local.pixelpark.com.",
          "disabled": false
        },
        {
          "content": "ns2-local.pixelpark.com.",
          "disabled": false
        },
        {
          "content": "ns3-local.pixelpark.com.",
          "disabled": false
        }
      ],
      "ttl": 3600,
      "type": "NS"
    },
    {
      "comments": [],
      "name": "live.pixelpark.ag.",
      "records": [
        {
          "content": "www.pixelpark.ag.",
          "disabled": false
        }
      ],
      "ttl": 3600,
      "type": "CNAME"
    },
    {
      "comments": [
        {
          "account": "frank.brehm",
          "content": "",
          "modified_at": 1520325479
        }
      ],
      "name": "web02.pixelpark.ag.",
      "records": [
        {
          "content": "217.66.55.28",
          "disabled": true
        }
      ],
      "ttl": 3600,
      "type": "A"
    },
    {
      "comments": [],
      "name": "pixelpark.ag.",
      "records": [
        {
          "content": "10 mx01.pixelpark.com.",
          "disabled": false
        },
        {
          "content": "10 mx02.pixelpark.com.",
          "disabled": false
        }
      ],
      "ttl": 3600,
      "type": "MX"
    },
    {
      "comments": [],
      "name": "pixelpark.ag.",
      "records": [
        {
          "content": "ns1.pp-dns.com. hostmaster.pixelpark.net. 2018061201 10800 3600 604800 3600",
          "disabled": false
        }
      ],
      "ttl": 3600,
      "type": "SOA"
    },
    {
      "comments": [],
      "name": "pixelpark.ag.",
      "records": [
        {
          "content": "ns3.pp-dns.com.",
          "disabled": false
        },
        {
          "content": "ns1.pp-dns.com.",
          "disabled": false
        },
        {
          "content": "ns2.pp-dns.com.",
          "disabled": false
        },
        {
          "content": "ns4.pp-dns.com.",
          "disabled": false
        }
      ],
      "ttl": 3600,
      "type": "NS"
    }
  ],
  "serial": 2018061201,
  "soa_edit": "",
  "soa_edit_api": "INCEPTION-INCREMENT",
  "url": "/api/v1/servers/localhost/zones/pixelpark.ag."
}
