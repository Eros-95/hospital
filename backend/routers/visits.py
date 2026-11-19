from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from .. import database
from ..schemas import Visit, VisitCreate, VisitUpdate

router = APIRouter(prefix="/api/visits", tags=["visits"])


def _validate_patient(conn, patient_id):
    row = conn.execute("SELECT id FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="患者不存在")


@router.post("", response_model=Visit, status_code=201)
def create_visit(data: VisitCreate):
    conn = database.get_connection()
    _validate_patient(conn, data.patient_id)
    now = datetime.now().isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO visits (patient_id, department, diagnosis, doctor, chief_complaint, treatment, visit_time, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.patient_id,
            data.department,
            data.diagnosis,
            data.doctor,
            data.chief_complaint,
            data.treatment,
            data.visit_time,
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM visits WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@router.get("")
def list_visits(
    keyword: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
):
    conn = database.get_connection()
    where = ""
    params = []
    if keyword:
        where = "WHERE p.name LIKE ? OR v.diagnosis LIKE ? OR v.department LIKE ?"
        params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]

    total = conn.execute(
        f"SELECT COUNT(*) FROM visits v JOIN patients p ON v.patient_id = p.id {where}",
        params,
    ).fetchone()[0]
    offset = (page - 1) * page_size
    rows = conn.execute(
        f"SELECT v.*, p.name AS patient_name FROM visits v JOIN patients p ON v.patient_id = p.id "
        f"{where} ORDER BY v.visit_time DESC, v.id DESC LIMIT ? OFFSET ?",
        params + [page_size, offset],
    ).fetchall()
    conn.close()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [dict(r) for r in rows],
    }


@router.get("/{visit_id}")
def get_visit(visit_id: int):
    conn = database.get_connection()
    row = conn.execute(
        "SELECT v.*, p.name AS patient_name, p.gender AS patient_gender, p.age AS patient_age, "
        "p.phone AS patient_phone FROM visits v JOIN patients p ON v.patient_id = p.id WHERE v.id = ?",
        (visit_id,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="就诊记录不存在")
    return dict(row)


@router.put("/{visit_id}", response_model=Visit)
def update_visit(visit_id: int, data: VisitUpdate):
    conn = database.get_connection()
    row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="就诊记录不存在")

    fields = data.model_dump(exclude_unset=True)
    if fields.get("patient_id") is not None:
        _validate_patient(conn, fields["patient_id"])
    if fields:
        fields["updated_at"] = datetime.now().isoformat(timespec="seconds")
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(
            f"UPDATE visits SET {set_clause} WHERE id = ?",
            list(fields.values()) + [visit_id],
        )
        conn.commit()

    row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
    conn.close()
    return dict(row)


@router.delete("/{visit_id}", status_code=204)
def delete_visit(visit_id: int):
    conn = database.get_connection()
    cur = conn.execute("DELETE FROM visits WHERE id = ?", (visit_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="就诊记录不存在")
    return None
