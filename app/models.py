from pydantic import BaseModel, Field
from typing import Union, Optional


class ProgramConfiguration(BaseModel):
    high_engagement_threshold: Optional[int] = Field(
        description="""This value is the number of actions establishing a user as 'highly engaged'
            (your best customers) for the purposes of inclusion in the engagement model. 
        """,
        gt=1
    )
    event_relevance_decay: Optional[int] = Field(
        description="""This value is the number of days for events to lose half their weight
            (also called event half-life), implemented as a decay curve over time.
            This value is used to account for recency relevance so newer actions 
            can carry extra weight in calculations.
            """,
        gt=2
    )
    action_weight_floor: Optional[float] = Field(
        description="""This value is the minimum user action recommendation weight required 
            for the action to be included in the final recommendations. Higher numbers bring higher
            confidence in the recommendations but also limit the number of recommendations 
            provided.
        """,
        lt=1
    )
