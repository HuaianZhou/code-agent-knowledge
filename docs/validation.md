# Validation record

Local validation on Windows, Python 3.12, Git 2.53, PyYAML 6.0.3 and sqlite-vec 0.1.9:

- Editable package build/install and CLI entry point work.
- Integration tests exercise real temporary Git repositories and sqlite-vec, not
  mocked repository/index operations.
- Complete local demo passed: isolated proposal → review → explicit fixture
  acceptance → bare-remote sync → separate reader → A → B ← C → rename impact.
- Zero-candidate demo produces zero writes. Both skill frontmatters validated.
- Failure injection demonstrated index rollback; simultaneous writers produced
  coherent snapshots. Offline-sync regression retains the last accepted revision.

Not executed: an approved transformer model download/inference, hosted GitHub/GitLab
requests, scheduled agent execution, autonomous extraction, or controlled fresh-agent
behavioral evaluation. These results establish local mechanics, not adoption value.

Local setup and acceptance coverage: new repository/config/index creation, repeatable
setup, preservation of existing directories, no-remote synchronization, explicit
reviewed-commit acceptance and index refresh, stale/concurrent review rejection,
dirty-checkout preservation, acceptance locking and remote-workflow separation.
All 33 automated tests passed after this change. The Windows `install.ps1` script
built and installed the wheel, created a separate demo knowledge repository and
index, and the installed CLI was checked from outside the source root.
