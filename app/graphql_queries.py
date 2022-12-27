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

create_customer_metafield_gql = """
    mutation CreateMetafieldDefinition($definition: MetafieldDefinitionInput!) {
      metafieldDefinitionCreate(definition: $definition) {
        createdDefinition {
          id
          name
          namespace
          key
        }
        userErrors {
          field
          message
          code
        }
      }
    }
"""
