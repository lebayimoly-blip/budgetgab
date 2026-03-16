from app import models

def log_action(db, user_id: int, action: str, cible_type: str, cible_id: int):
    log = models.LogAction(
        user_id=user_id,
        action=action,
        cible_type=cible_type,
        cible_id=cible_id
    )
    db.add(log)
    db.commit()