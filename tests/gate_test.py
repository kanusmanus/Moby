from httpx import AsyncClient
import pytest

from app.models.gate import Gate
from app.models.parking_lot import ParkingLot
from app.models.payment import PaymentStatus
from app.schemas.gate import (
    GateDecision,
    GateDirection,
    GateEventIn,
    GateEventOut,
    GateIn,
    GateOut,
)

from datetime import datetime

from app.schemas.payment import PaymentIn, PaymentOut


@pytest.mark.anyio
async def test_add_gate(
    async_client: AsyncClient, lot_in_db: ParkingLot, auth_headers_admin: dict[str, str]
):
    payload = GateIn(
        parking_lot_id=lot_in_db.id,
    )
    resp = await async_client.post(
        "/gate", json=payload.model_dump(mode="json"), headers=auth_headers_admin
    )

    assert resp.status_code == 201
    data = GateOut.model_validate(resp.json())
    assert data.parking_lot_id == lot_in_db.id
    assert data.id is not None


@pytest.mark.anyio
async def test_gate_entry(async_client: AsyncClient, gate_in_db: Gate):
    gate = gate_in_db
    payload = GateEventIn(
        gate_id=gate.id,
        parking_lot_id=gate.parking_lot_id,
        license_plate="abcdefg",
        direction=GateDirection.entry,
        timestamp=datetime.now(),
    )
    resp = await async_client.post(
        f"/gate/{gate.id}", json=payload.model_dump(mode="json")
    )

    assert resp.status_code == 200
    data = GateEventOut.model_validate(resp.json())
    assert data.gate_id == gate.id
    assert data.decision == GateDecision.open


@pytest.mark.anyio
async def test_gate_exit_not_paid(async_client: AsyncClient, gate_in_db: Gate):
    # Entry
    gate = gate_in_db
    payload = GateEventIn(
        gate_id=gate.id,
        parking_lot_id=gate.parking_lot_id,
        license_plate="abcdefg",
        direction=GateDirection.entry,
        timestamp=datetime.now(),
    )
    resp_entry = await async_client.post(
        f"/gate/{gate.id}", json=payload.model_dump(mode="json")
    )

    assert resp_entry.status_code == 200
    data = GateEventOut.model_validate(resp_entry.json())
    assert data.gate_id == gate.id
    assert data.decision == GateDecision.open

    # Exit without paying
    payload_exit = GateEventIn(
        gate_id=gate.id,
        parking_lot_id=gate.parking_lot_id,
        license_plate="abcdefg",
        direction=GateDirection.exit,
        timestamp=datetime.now(),
    )

    resp_exit = await async_client.post(
        f"/gate/{gate.id}", json=payload_exit.model_dump(mode="json")
    )

    assert resp_exit.status_code == 200
    data_exit = GateEventOut.model_validate(resp_exit.json())
    assert data_exit.gate_id == gate.id
    assert data_exit.decision == GateDecision.deny
    assert data_exit.reason == "session_not_paid"


@pytest.mark.anyio
async def test_gate_exit_paid(
    async_client: AsyncClient,
    gate_in_db: Gate,
    auth_headers_parking_meter: dict[str, str],
):
    # Entry
    gate = gate_in_db
    payload_entry = GateEventIn(
        gate_id=gate.id,
        parking_lot_id=gate.parking_lot_id,
        license_plate="abcdefg",
        direction=GateDirection.entry,
        timestamp=datetime.now(),
    )
    resp_entry = await async_client.post(
        f"/gate/{gate.id}", json=payload_entry.model_dump(mode="json")
    )

    assert resp_entry.status_code == 200
    data_entry = GateEventOut.model_validate(resp_entry.json())
    assert data_entry.gate_id == gate.id
    assert data_entry.decision == GateDecision.open

    payload_payment = PaymentIn(
        parking_lot_id=gate.parking_lot_id,
        license_plate=payload_entry.license_plate,
    )

    resp_payment = await async_client.post(
        "/payments/pay",
        json=payload_payment.model_dump(mode="json"),
        headers=auth_headers_parking_meter,
    )

    assert resp_payment.status_code == 200
    data_payment = PaymentOut.model_validate(resp_payment.json())
    assert data_payment.status == PaymentStatus.paid

    # Exit after paying
    payload_exit = GateEventIn(
        gate_id=gate.id,
        parking_lot_id=gate.parking_lot_id,
        license_plate="abcdefg",
        direction=GateDirection.exit,
        timestamp=datetime.now(),
    )

    resp_exit = await async_client.post(
        f"/gate/{gate.id}", json=payload_exit.model_dump(mode="json")
    )

    assert resp_exit.status_code == 200
    data_exit = GateEventOut.model_validate(resp_exit.json())
    assert data_exit.gate_id == gate.id
    assert data_exit.decision == GateDecision.open
    assert data_exit.reason == "session_closed"
