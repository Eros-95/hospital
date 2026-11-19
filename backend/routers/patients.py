from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from .. import database
from ..schemas import Patient, PatientCreate, PatientUpdate
from ..utils import mask_id_card

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.post("", response_model=Patient, status_code=201)
def create_patient(data: PatientCreate):
    now = datetime.now().isoformat(timespec="seconds")
    id_card = mask_id_card(data.id_card) if data.id_card else data.id_card
    conn = database.get_connection()
    cur = conn.execute(
        "INSERT INTO patients (name, gender, age, phone, id_card, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data.name, data.gender, data.age, data.phone, id_card, now, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM patients WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@router.get("")
def list_patients(
    keyword: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
):
    conn = database.get_connection()
    where = ""
    params = []
    if keyword:
        where = "WHERE name LIKE ? OR phone LIKE ?"
        params = [f"%{keyword}%", f"%{keyword}%"]

    total = conn.execute(f"SELECT COUNT(*) FROM patients {where}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = conn.execute(
        f"SELECT * FROM patients {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [page_size, offset],
    ).fetchall()
    conn.close()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [dict(r) for r in rows],
    }


@router.get("/{patient_id}", response_model=Patient)
def get_patient(patient_id: int):
    conn = database.get_connection()
    row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="患者不存在")
    return dict(row)


@router.put("/{patient_id}", response_model=Patient)
def update_patient(patient_id: int, data: PatientUpdate):
    conn = database.get_connection()
    row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="患者不存在")

    fields = data.model_dump(exclude_unset=True)
    if fields.get("id_card") is not None:
        fields["id_card"] = mask_id_card(fields["id_card"])
    if fields:
        fields["updated_at"] = datetime.now().isoformat(timespec="seconds")
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(
            f"UPDATE patients SET {set_clause} WHERE id = ?",
            list(fields.values()) + [patient_id],
        )
        conn.commit()

    row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    return dict(row)


@router.delete("/{patient_id}", status_code=204)
def delete_patient(patient_id: int):
    conn = database.get_connection()
    row = conn.execute("SELECT id FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="患者不存在")
    conn.execute("DELETE FROM visits WHERE patient_id = ?", (patient_id,))
    conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()
    return None
