get_order_customer_journey_gql = """
    {{
        order(id: "gid://shopify/Order/{order_id}") {{
            id
            customerJourneySummary {{
                firstVisit {{
                    landingPage 
                    referrerUrl 
                    source 
                    sourceType 
                }}
                lastVisit {{
                    landingPage 
                    referrerUrl 
                    source 
                    sourceType 
                }}
                ready 
            }}
        }}
    }}
    """