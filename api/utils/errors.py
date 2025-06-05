from fastapi import HTTPException, status

def raise_404_if_none(item, name: str):
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{name} not found"
        )