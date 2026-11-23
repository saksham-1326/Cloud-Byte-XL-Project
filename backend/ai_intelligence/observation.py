"""Local append-only evidence, never a second prediction database."""
import hashlib
import json
import math
import os
from pathlib import Path
from datetime import datetime, timezone

from .github import scrub


class ObservationError(RuntimeError):
    """Only fixed safe codes are exposed; underlying exceptions are not logged."""


def utc():
    return datetime.now(timezone.utc)


def canonical(value):
    def encode(item):
        if isinstance(item, datetime):
            if item.tzinfo is None:
                raise ObservationError('naive_timestamp')
            return item.astimezone(timezone.utc).isoformat()
        return str(item)
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=encode,
                      ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def aware(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value, str) else value
        if not isinstance(result, datetime) or result.tzinfo is None:
            raise ValueError()
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        raise ObservationError('invalid_timestamp') from None


class Ledger:
    """One writer per file, fsync per event, strict hash-chain restart validation.

    The advisory file lock is process-wide on Windows/POSIX. Separate ledgers
    may observe the same database; the existing shadow unique index arbitrates.
    This detects damage, not tampering by an administrator who rewrites a chain.
    """
    def __init__(self, path, secrets=(), now=utc):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.secrets = tuple(s for s in secrets if s and len(s) >= 5)
        self.now = now
        self.lock = self.path.with_suffix(self.path.suffix + '.lock').open('a+b')
        self.lock.seek(0, 2)
        if self.lock.tell() == 0:
            self.lock.write(b'0'); self.lock.flush()
        self.lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock.close()
            raise ObservationError('ledger_in_use') from None
        self.records = []
        self.failed = False
        try:
            if self.path.exists():
                raw = self.path.read_bytes()
                if raw and not raw.endswith(b'\n'):
                    raise ObservationError('incomplete_ledger_record')
                previous = '0' * 64
                for number, line in enumerate(raw.splitlines(), 1):
                    record = json.loads(line)
                    checksum = record.pop('sha256')
                    if record['sequence'] != number or record['previous'] != previous or digest(record) != checksum:
                        raise ObservationError('invalid_ledger_chain')
                    record['sha256'] = checksum
                    self.records.append(record)
                    previous = checksum
            self.file = self.path.open('ab', buffering=0)
        except Exception:
            self.lock.close()
            raise ObservationError('invalid_or_inaccessible_ledger') from None

    def append(self, event, **data):
        if self.failed:
            raise ObservationError('ledger_not_writable')
        # JSON roundtrip removes custom object representations; redact both
        # environment secrets and explicitly supplied token/DSN passwords.
        def remove_auth(value):
            if isinstance(value,dict):
                return {k:('[REDACTED]' if k.lower() in ('authorization','cookie','set-cookie')
                           else remove_auth(v)) for k,v in value.items()}
            if isinstance(value,list):
                return [remove_auth(v) for v in value]
            return value
        clean = canonical(scrub(remove_auth(json.loads(canonical(data)))))
        for secret in self.secrets:
            clean = clean.replace(json.dumps(secret)[1:-1], '[REDACTED]')
        record = dict(sequence=len(self.records)+1, event=event,
                      at=aware(self.now()).isoformat(),
                      previous=self.records[-1]['sha256'] if self.records else '0'*64,
                      data=json.loads(clean))
        record['sha256'] = digest(record)
        encoded=(canonical(record)+'\n').encode()
        try:
            if self.file.write(encoded)!=len(encoded):
                raise ObservationError('ledger_short_write')
            os.fsync(self.file.fileno())
        except (OSError,ObservationError):
            self.failed=True
            raise ObservationError('ledger_write_failed') from None
        self.records.append(record)
        return record

    def close(self):
        if hasattr(self, 'file'):
            self.file.close()
        self.lock.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def positive(value, name, minimum=1):
    if isinstance(value, bool) or not math.isfinite(value) or value < minimum:
        raise ObservationError('invalid_' + name)
    return value
