bank_data_json = """
{
    "user": "John F. Doe",
    "billing-address": "123 Any Street Apt. 45 / Smallville, KS 1235",
    "account": {
        "account-type": "checking",
        "routing-number": "056004241",
        "account-number": "123456789",
        "account-ballance": 1234.56,
        "deposited": {
            "0": {
                "amount": 1057.21,
                "utc-unix": 1457476491,
                "time-zone": "UTC-8",
                "source": {
                    "type": "mobile-deposit",
                    "ref": " #IB3GFRZG31",
                    "routing-number": "944145221",
                    "account-number": "123123123",
                    "check-number": "1229361",
                    "note": "bi-weekly paycheck"
                }
            },
            "1": {
                "amount": "500.00",
                "utc-unix": 1459376666,
                "time-zone": "UTC-8",
                "source": {
                    "type": "online-transfer",
                    "ref": "#IBS5RWGWMM",
                    "routing-number": "044072324",
                    "account-number": "987654321",
                    "note": "monthly refill"
                }
            }
            
        },
        "withdrawn": {
            "0": {
                "amount": 23.03,
                "utc-unix": 1457476491,
                "time-zone": "UTC-8",
                "source": {
                    "card": "0123456789101112",
                    "type": "purchase",
                    "ref": "S567013305806010",
                    "name": "Average-Restaurant"
                }
            },
            "1": {
                "amount": 5.37,
                "utc-unix": 1457447400,
                "time-zone": "UTC-8",
                "card": "0123456789101112",
                "source": {
                    "type": "purchase",
                    "ref": "S466013457060112",
                    "name": "That-Super-Market"
                }
            }
        }
    }
}
"""

narrow_csv = """Person,Variable,Value
Bob,Age,32
Bob,Weight,178
Alice,Age,24
Alice,Weight,150
Steve,Age,64
Steve,Weight,195
"""

wide_csv = """Person,Age,Weight
Bob,32,178
Alice,24,150
Steve,64,195
"""