# Z-MAIL RECOVERY — Implementation status

| Module | Status | Details |
|---|---|---|
| Premium dashboard | Implemented | Real SQLite counts, no fake statistics |
| Light/dark themes | Implemented | Switchable in Settings |
| Local scanner | Implemented | Recursive EML/MBOX discovery; source files opened read-only |
| Thunderbird discovery | Partial | Common Linux profile paths; profile scanning through Local Recovery |
| MBOX parsing | Implemented | Iterates messages individually |
| EML parsing | Implemented | MIME-aware parsing |
| Maildir | Partial | Not yet a dedicated mailbox importer |
| ZIP/TAR backup parsing | Not implemented | Archive discovery/extraction planned |
| Attachments | Implemented | Extract on demand from stored original message |
| Duplicate detection | Implemented | Exact-byte SHA-256; not semantic duplicate matching |
| Search | Implemented | Sender, recipient, subject and body substring search |
| EML export | Implemented | Saves original stored message bytes |
| JSON report | Implemented | Counts and indexed-message metadata |
| Gmail OAuth/API | Not implemented | Phase 2 |
| Deleted-file/raw disk recovery | Not implemented | Requires specialist tools and forensic validation |
| PDF reports | Not implemented | Planned |
| Pause/resume | Partial | Stop/cancel supported; pause/resume planned |
| Automated tests | Implemented | Parser, database and scanner smoke tests |

A feature is marked implemented only to the extent described above. Recovery is never guaranteed.
