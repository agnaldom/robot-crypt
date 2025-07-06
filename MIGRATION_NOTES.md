# Migration Notes: Passlib to Argon2-CFI

## Overview
We have migrated from `passlib` to `argon2-cffi` to resolve Python 3.13 compatibility issues and improve security.

## What Changed

### Dependencies
- **Removed**: `passlib[bcrypt]>=1.7.4`
- **Added**: `argon2-cffi>=23.1.0`

### Password Hashing
- **Old**: BCrypt hashes (format: `$2b$12$...`)
- **New**: Argon2 hashes (format: `$argon2id$v=19$m=65536$...`)

## Impact on Existing Users

### Database Migration Required
Existing user passwords will need to be migrated or reset because:
1. Argon2 cannot verify BCrypt hashes
2. Hash formats are incompatible

### Migration Options

#### Option 1: Password Reset (Recommended)
1. Force all users to reset their passwords
2. Send password reset emails to all users
3. Clear all current password hashes

#### Option 2: Hybrid Verification (Temporary)
If you need to support both formats during transition:

```python
def verify_password_hybrid(plain_password: str, hashed_password: str) -> bool:
    """Verify password supporting both old BCrypt and new Argon2 formats."""
    if hashed_password.startswith('$2b$'):
        # Old BCrypt hash - use bcrypt library
        import bcrypt
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    else:
        # New Argon2 hash
        return verify_password(plain_password, hashed_password)
```

## Benefits of Argon2

1. **Better Security**: Argon2 is the winner of the Password Hashing Competition
2. **Future-Proof**: No deprecated dependencies
3. **Python 3.13 Compatible**: No issues with deprecated `crypt` module
4. **Memory-Hard**: More resistant to GPU/ASIC attacks
5. **Configurable**: Adjustable memory, time, and parallelism parameters

## Running the Migration

1. Update dependencies:
   ```bash
   pip uninstall passlib
   pip install argon2-cffi>=23.1.0
   ```

2. Test the new implementation:
   ```bash
   python -c "from src.core.security import get_password_hash, verify_password; print('Migration successful!')"
   ```

3. Deploy with user password reset flow

## Security Improvements

- **Memory Cost**: 64 MB (configurable)
- **Time Cost**: 3 iterations (configurable)
- **Parallelism**: 1 thread (configurable)
- **Salt**: 16 bytes (automatic)
- **Hash Length**: 32 bytes (configurable)

## Rollback Plan

If rollback is needed:
1. Restore `passlib[bcrypt]>=1.7.4` in requirements.txt
2. Restore original security.py implementation
3. Use database backup with BCrypt hashes
