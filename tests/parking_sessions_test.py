import random
import string
from httpx import AsyncClient
import pytest

from app.models.gate import Gate
from app.models.reservation import Reservation
from app.schemas.gate import GateDecision, GateDirection, GateEventIn, GateEventOut

from datetime import datetime

from app.schemas.parking_session import ParkingSessionOut


@pytest.mark.anyio
async def test_create_anonymous_parking_session(
    async_client: AsyncClient, gate_in_db: Gate, auth_headers_admin: dict[str, str]
):
    # Enter parking space
    gate = gate_in_db
    plate = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    payload = GateEventIn(
        gate_id=gate.id,
        parking_lot_id=gate.parking_lot_id,
        license_plate=plate,
        direction=GateDirection.entry,
        timestamp=datetime.now(),
    )
    resp_gate = await async_client.post(
        f"/gate/{gate.id}",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )

    assert resp_gate.status_code == 200
    data_gate = GateEventOut.model_validate(resp_gate.json())
    assert data_gate.gate_id == gate.id
    assert data_gate.decision == GateDecision.open

    # Ensure parking session has started
    resp_session = await async_client.get(
        f"/parking_sessions/{data_gate.session_id}", headers=auth_headers_admin
    )
    assert resp_session.status_code == 200
    data_session = ParkingSessionOut.model_validate(resp_session.json())
    assert data_session.parking_lot_id == gate.parking_lot_id
    assert data_session.entry_gate_id == gate.id


@pytest.mark.anyio
async def test_create_parking_session(
    async_client: AsyncClient,
    gate_in_db: Gate,
    reservation_in_db: Reservation,
    auth_headers_admin: dict[str, str],
):
    # Enter parking space
    gate = gate_in_db

    payload = GateEventIn(
        gate_id=gate.id,
        parking_lot_id=gate.parking_lot_id,
        license_plate=reservation_in_db.license_plate,
        direction=GateDirection.entry,
        timestamp=datetime.now(),
    )
    resp_gate = await async_client.post(
        f"/gate/{gate.id}",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )

    assert resp_gate.status_code == 200
    data_gate = GateEventOut.model_validate(resp_gate.json())
    assert data_gate.gate_id == gate.id
    assert data_gate.decision == GateDecision.open

    # Ensure parking session has started
    resp_session = await async_client.get(
        f"/parking_sessions/{data_gate.session_id}", headers=auth_headers_admin
    )
    assert resp_session.status_code == 200
    data_session = ParkingSessionOut.model_validate(resp_session.json())
    assert data_session.parking_lot_id == gate.parking_lot_id
    assert data_session.entry_gate_id == gate.id
    assert data_session.reservation_id == reservation_in_db.id
    assert data_session.license_plate == reservation_in_db.license_plate
