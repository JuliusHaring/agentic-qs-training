from typing import Literal, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Mock AI Automation System")

# In-memory database
customers = {
    "C123": {"name": "Max Mustermann", "email": "max@example.com", "tier": "Gold"},
    "C456": {"name": "Erika Musterfrau", "email": "erika@example.com", "tier": "Silver"}
}

tickets = []

class Ticket(BaseModel):
    id: Optional[int] = None
    customer_id: str = Field(pattern=r"^C\d+$")
    issue: str = Field(min_length=5, max_length=500)
    status: Literal["open", "in_progress", "resolved"] = "open"
    priority: Literal["low", "medium", "high"] = "medium"


class StatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved"]

@app.get("/customer/{customer_id}")
async def get_customer(customer_id: str):
    if customer_id not in customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customers[customer_id]

@app.post("/tickets")
async def create_ticket(ticket: Ticket):
    if ticket.customer_id not in customers:
        raise HTTPException(status_code=400, detail="Invalid customer ID")
    
    ticket.id = len(tickets) + 1
    tickets.append(ticket.model_dump())
    return ticket

@app.put("/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: int, update: StatusUpdate):
    if ticket_id < 1 or ticket_id > len(tickets):
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    tickets[ticket_id - 1]["status"] = update.status
    return tickets[ticket_id - 1]

@app.get("/tickets")
async def list_tickets():
    return tickets

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
