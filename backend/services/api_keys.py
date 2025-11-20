"""API key service implementation."""
import secrets
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime
import bcrypt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models import APIKey, User
from backend.schemas.api_key import APIKeyCreate
from backend.services.interfaces import IAPIKeyService


class APIKeyService(IAPIKeyService):
    """API key service with bcrypt hashing."""

    KEY_PREFIX = "ft_"
    KEY_LENGTH = 32  # 32 bytes = 43 chars in base64

    async def create_api_key(
        self, db: Session, user_id: UUID, key_data: APIKeyCreate
    ) -> Tuple[APIKey, str]:
        """
        Create API key with bcrypt hash.

        Args:
            db: Database session
            user_id: User ID
            key_data: API key creation data

        Returns:
            Tuple of (APIKey object, plaintext key)

        Note:
            Plaintext key is only returned once! Store it securely.
        """
        # Generate secure random key
        plaintext_key = self._generate_key()

        # Hash the key with bcrypt (12 rounds)
        key_hash = self._hash_key(plaintext_key)

        # Create API key record
        api_key = APIKey(
            user_id=user_id,
            name=key_data.name,
            key_hash=key_hash,
            key_prefix=plaintext_key[:8],  # First 8 chars for identification
            is_active=True,
            scopes=key_data.scopes or "*",
            expires_at=key_data.expires_at,
            total_requests=0,
            total_tokens=0,
        )

        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        return api_key, plaintext_key

    async def get_api_key(
        self, db: Session, key_id: UUID, user_id: UUID
    ) -> APIKey:
        """
        Get API key by ID (with ownership check).

        Args:
            db: Database session
            key_id: API key ID
            user_id: User ID for ownership verification

        Returns:
            APIKey object

        Raises:
            HTTPException: 404 if not found or access denied
        """
        api_key = (
            db.query(APIKey)
            .filter(APIKey.id == key_id, APIKey.user_id == user_id)
            .first()
        )

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or access denied",
            )

        return api_key

    async def list_api_keys(
        self, db: Session, user_id: UUID
    ) -> List[APIKey]:
        """
        List user's API keys.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of APIKey objects
        """
        return db.query(APIKey).filter(APIKey.user_id == user_id).all()

    async def revoke_api_key(
        self, db: Session, key_id: UUID, user_id: UUID
    ) -> APIKey:
        """
        Revoke an API key.

        Args:
            db: Database session
            key_id: API key ID
            user_id: User ID for ownership verification

        Returns:
            Revoked APIKey object

        Raises:
            HTTPException: 404 if not found or access denied
        """
        api_key = await self.get_api_key(db, key_id, user_id)

        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()

        db.commit()
        db.refresh(api_key)

        return api_key

    async def verify_api_key(self, db: Session, plaintext_key: str) -> Optional[User]:
        """
        Verify API key and return associated user.

        Args:
            db: Database session
            plaintext_key: Plaintext API key from request

        Returns:
            User object if key is valid, None otherwise
        """
        # Extract prefix for efficient lookup
        key_prefix = plaintext_key[:8]

        # Get all active keys with matching prefix
        api_keys = (
            db.query(APIKey)
            .filter(
                APIKey.key_prefix == key_prefix,
                APIKey.is_active == True,
            )
            .all()
        )

        # Check each key with bcrypt (constant-time comparison)
        for api_key in api_keys:
            if self._verify_key(plaintext_key, api_key.key_hash):
                # Verify key is still valid
                if not api_key.is_valid():
                    return None

                # Update last used timestamp and usage stats
                api_key.last_used_at = datetime.utcnow()
                api_key.total_requests += 1
                db.commit()

                # Get and return user
                user = db.query(User).filter(User.id == api_key.user_id).first()
                return user

        return None

    def _generate_key(self) -> str:
        """
        Generate secure random API key.

        Returns:
            API key string (ft_xxxxx...)
        """
        random_bytes = secrets.token_urlsafe(self.KEY_LENGTH)
        return f"{self.KEY_PREFIX}{random_bytes}"

    def _hash_key(self, plaintext_key: str) -> str:
        """
        Hash API key with bcrypt (12 rounds).

        Args:
            plaintext_key: Plaintext API key

        Returns:
            Bcrypt hash
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(plaintext_key.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def _verify_key(self, plaintext_key: str, key_hash: str) -> bool:
        """
        Verify API key against bcrypt hash.

        Args:
            plaintext_key: Plaintext API key
            key_hash: Bcrypt hash

        Returns:
            True if key matches hash
        """
        return bcrypt.checkpw(
            plaintext_key.encode('utf-8'),
            key_hash.encode('utf-8')
        )


# Create singleton instance
api_key_service = APIKeyService()
