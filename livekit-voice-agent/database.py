# database.py
from dataclasses import dataclass, field

@dataclass
class HospitalState:
    specialties_db: dict = field(default_factory=lambda: {
        "ophthalmology": [
            {"id": "ophtho_1", "name": "Dr. Sarah Smith", "available_slots": ["2026-03-16T09:00:00", "2026-03-16T14:00:00", "2026-03-17T10:00:00"]},
            {"id": "ophtho_2", "name": "Dr. Charles Davis", "available_slots": ["2026-03-18T08:00:00", "2026-03-19T15:00:00", "2026-03-20T11:00:00"]}
        ],
        "cardiology": [
            {"id": "cardio_1", "name": "Dr. Robert Jones", "available_slots": ["2026-03-17T09:00:00", "2026-03-19T14:00:00", "2026-03-20T16:00:00"]},
            {"id": "cardio_2", "name": "Dr. Emily Taylor", "available_slots": ["2026-03-16T11:00:00", "2026-03-18T10:00:00", "2026-03-19T08:00:00"]}
        ],
        "neurology": [
            {"id": "neuro_1", "name": "Dr. Paul Walker", "available_slots": ["2026-03-16T13:00:00", "2026-03-17T15:00:00", "2026-03-18T09:00:00"]},
            {"id": "neuro_2", "name": "Dr. Julia Adams", "available_slots": ["2026-03-19T10:00:00", "2026-03-20T08:00:00", "2026-03-20T14:00:00"]}
        ]
    })
    current_doctors: list = field(default_factory=list)
    bookings: list = field(default_factory=list)
    triage_patient: list = field(default_factory=list)

db = HospitalState()